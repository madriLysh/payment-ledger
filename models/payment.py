import uuid

from sqlalchemy import ForeignKey, Index, func, Uuid, PrimaryKeyConstraint, CheckConstraint, DateTime, BIGINT, CHAR, text
from sqlalchemy.orm import Mapped, mapped_column 
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from infrastructure.database import Base

class MERCHANTS(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(nullable=False)
    api_key_hash: Mapped[str] = mapped_column(unique=True, nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

class IDEMPOTENCY_KEYS(Base):
    __tablename__ = "idempotency_keys"

    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column()
    request_hash: Mapped[str] = mapped_column(nullable=False)
    response_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now() + interval '24 hours'"))

    __table_args__ = (
        PrimaryKeyConstraint("merchant_id", "key", 
            name="pk_idempotency_merchant_key"),
        CheckConstraint("status IN ('processing', 'completed')", name="ck_idem_status")
        )

class PAYMENTS(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BIGINT, nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    idempotency_key: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column( DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column( DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("amount_minor > 0 AND currency = upper(currency) AND status IN ('pending', 'settled', 'failed', 'refunded')", name="ck_payments_status"),
        Index("ix_payment_merchant_created_at", merchant_id, created_at.desc())
    )

class OUTBOX(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    aggregate_type: Mapped[str] = mapped_column(nullable=False)
    aggregate_id: Mapped[str] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(nullable=False, server_default="0")
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_outbox_pending", next_attempt_at,
      postgresql_where=(published_at.is_(None)))
    )
