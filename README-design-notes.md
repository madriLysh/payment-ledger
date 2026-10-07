# Payment-Ledger — Design Notes

Production-grade payment backend: merchants create payments via API, a
double-entry ledger tracks money movement, events flow through an outbox to
webhook delivery workers.

Stack: Python 3.14 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · Alembic (one
migration tree per service) · uv

---

## Architecture: one database, per-service ownership

Three logical services — **payments**, **ledger**, **notifications** — share
one Postgres today, but each owns its schema and migrates independently:

- One Alembic tree per service (`services/<name>/alembic/`), each with its
  own bookkeeping table (`alembic_version_payment`, `alembic_version_ledger`,
  `alembic_version_notifications`). Trees never read each other's state.
- Services do **not** foreign-key across service boundaries (see the
  webhook note below). References between services are by UUID value only.
- Roadmap (per Step-0 spec): per-service Postgres schemas + per-service DB
  roles; the ledger's append-only guarantee is enforced by role permissions
  (INSERT/SELECT only, REVOKE UPDATE/DELETE), not by convention.

## Hard rules (enforced in code and schema)

1. API keys are never stored plaintext — only `sha256(api_key)` in
   `merchants.api_key_hash`.
2. UUIDv7 primary keys, generated app-side (`default=uuid7`, never `uuid7()`).
3. Ledger rows (`transactions`, `entries`) are immutable: no UPDATE, no
   DELETE — enforced by DB role permissions (ledger migration 0002).
4. Commits live in the service layer, one commit per business operation
   (e.g. payment insert + outbox row are atomic).
5. Every constraint and index has an explicit name (`ck_*`, `uq_*`, `fk_*`,
   `pk_*`, `ix_*`).
6. All timestamps are `DateTime(timezone=True)` — naive timestamps forbidden.
7. Every ledger transaction's entries sum to zero, verified in code before
   commit; a validation query (`GROUP BY transaction_id HAVING SUM <> 0`)
   runs as a CI check and, later, as a nightly job.

## Idempotency contract (locked — implementation in the API phase)

`POST /payments` accepts an `Idempotency-Key` header. The flow:

1. **Gate insert first.** Insert `(merchant_id, key, request_hash,
   status='processing')` into `idempotency_keys` with
   `ON CONFLICT DO NOTHING`, before any processing.
2. **No conflict** → process: insert payment, insert outbox event, set the
   key row to `completed` with the stored response — **all in one
   transaction**, then commit.
3. **Conflict, same `request_hash`** → replay the stored `response_json`
   (same HTTP status + body as the first call). Safe to retry forever.
4. **Conflict, different `request_hash`** → **422** (same key, different
   payload — a client bug).
5. **Conflict, status = `processing`, row younger than ~60s** → **409** +
   `Retry-After` (another request is genuinely in flight).
6. **Conflict, `processing`, older than ~60s** → treat as crashed: reclaim
   the key and process (the previous attempt died mid-flight). This is the
   stuck-in-processing contract — without it, a crash between steps 1 and 2
   would brick the key until the 24h TTL.

Keys expire after 24h (`expires_at = now() + interval '24 hours'`). Postgres
has no TTL: expired rows are removed by a cleanup query
(`DELETE FROM idempotency_keys WHERE expires_at < now()`), run by a scheduled
job or manually.

## Ledger conventions

- **Sign convention (LOCKED — positive = money IN):** `amount_minor` is
  signed, from the **account owner's perspective**:
  - **Positive** = money entered the account (balance goes up).
  - **Negative** = money left the account (balance goes down).
  Do not use the words debit/credit in code or comments — they flip meaning
  depending on whose books you're looking at (a deposit is a credit to the
  customer, a debit on the bank's side), which is the entire reason the two
  source documents contradicted each other. "Money in / money out" has one
  meaning. Consequence: a balance is always
  `SELECT SUM(amount_minor) FROM entries WHERE account_id = :id` — no
  sign-flipping at read time — and every transaction still sums to zero
  (money into one account is money out of another). Note: this supersedes
  the Step-0 report's "positive = debit" (that was the bank's-books
  perspective); the report should be annotated accordingly.
- **Worked example — customer charge of 100 with a 5 platform fee:**
  one transaction, three entries: `customer account −100` (money out),
  `merchant account +95` (money in), `platform fee account +5` (money in).
  Sum = 0. Balances read correctly as plain sums: the merchant's account
  grew by 95.
- `CHECK (amount_minor <> 0)` on entries — zero-amount movements are
  meaningless in a ledger.
- Balances are **never stored**; they are derived by summing entries per
  `(owner_type, owner_id, currency)` account. The unique constraint on that
  triple prevents one owner+currency from splitting across two account rows.

## `updated_at` mechanism

Exactly one mechanism, applied consistently: database trigger
`set_updated_at()` / `trg_payments_updated_at` on `payments` (created in the
payments service's initial migration). App code never writes `updated_at`.

## Design note: why `webhook_deliveries.payment_id` has no foreign key

`webhook_deliveries` (notifications service) references payments by UUID
value only — deliberately **not** an FK to `payments.id` (payments service).

Rationale: a cross-service FK couples the two services' schemas and
migrations (notifications' migration tree would have to model payments'
tables, and the trees could no longer migrate independently — verified
empirically when this exact coupling made notifications' initial migration
try to recreate the entire payments schema). Rows are created only from
consumed payment events, which is itself the proof the payment exists;
payments are never deleted, so orphans can only arise from bugs. Detection:
an occasional reconciliation query
(`SELECT w.payment_id FROM webhook_deliveries w LEFT JOIN payments p ON w.payment_id = p.id WHERE p.id IS NULL`)
— consistent with the ledger's "validate by query" philosophy (rule 7).

Decision informed by: Chris Richardson (Microservices Patterns — don't share
databases across services), Sam Newman (database-per-service), and
event-driven creation practices from public payment-platform engineering
blogs. Alternatives considered and rejected: shared-schema FK (couples
migration trees; ON DELETE CASCADE would also destroy delivery history);
application-level join validation at write time (adds a cross-service read
on the hot path for a bug-class that reconciliation catches).

## Migration workflow

- One tree per service. Autogenerate, then **review**, then hand-add what
  autogenerate can't see (triggers, extensions, roles, data migrations).
- Migrations are additive-then-contract: new things first, destructive
  changes only in a later migration once nothing references the old shape.
- Never edit a pushed migration; fix forward.
