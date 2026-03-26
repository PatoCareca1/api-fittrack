"""SQLAlchemy ORM model for the ``analyses`` table."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    JSONB,
    UUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Analysis(Base):
    """Persisted body composition analysis result."""

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    poses_used: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
    )
    height_cm: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    weight_kg: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    sex: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    measurements: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    metrics: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
