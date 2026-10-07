import uuid
from uuid_utils import uuid7
from sqlalchemy import ForeignKey, Index, func, CheckConstraint, UniqueConstraint, DateTime, BIGINT, CHAR, BigInteger, Uuid
from sqlalchemy.orm import Mapped, mapped_column 

from datetime import datetime

from infrastructure.database import Base

class ACCOUNTS(Base):
    __tablename__ = "accounts"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    owner_type: Mapped[str] = mapped_column(nullable=False)
    owner_id: Mapped[str] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("owner_type IN ('merchant', 'platform', 'customer')", name="ck_own_type"),
        UniqueConstraint("owner_type", "owner_id", "currency", name="uq_account_owner_currency")
    )

class TRANSACTIONS(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    type: Mapped[str] = mapped_column(nullable=False)
    source_event_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("type IN ('charge', 'refund', 'payout', 'fee')", name="ck_txn_type"),
        UniqueConstraint("source_event_id", name="uq_transactions_source_event_id"),
    )

class ENTRIES(Base): 
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("transactions.id", name="fk_entries_transaction"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("accounts.id", name="fk_entries_account"), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BIGINT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_entries_account", account_id, created_at),
        Index("ix_entries_transaction", transaction_id),
        CheckConstraint("amount_minor <> 0", name="ck_entries_nonzero"),
    )

class PROCESSED_EVENTS(Base):
    __tablename__ = "processed_events"

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
