import uuid
from uuid_utils import uuid7
from sqlalchemy import Index, func, DateTime, ForeignKey, CheckConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column 

from datetime import datetime

from infrastructure.database import Base

class WEBHOOK_DELIVERIES(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    payment_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, server_default="pending")
    attempts: Mapped[int] = mapped_column(nullable=False, server_default="0")
    next_retry_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True)
    last_status_code: Mapped[int] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'delivered', 'failed')", name="ck_webhook_status"),
        Index("ix_webhook_pending", next_retry_at, postgresql_where=(status == "pending")),
    )
