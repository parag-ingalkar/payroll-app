from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.holidays.domain.entities import Holiday

if TYPE_CHECKING:
    from app.businesses.infrastructure.models import BusinessModel

class HolidayModel(Base):
    __tablename__ = "holidays"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    business_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    holiday_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    holiday_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_paid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    business: Mapped["BusinessModel"] = relationship(
        back_populates="holidays",
    )

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "holiday_date",
            name="uq_holiday_business_date",
        ),
    )

    def to_entity(self) -> Holiday:
        return Holiday(
            business_id=self.business_id,
            holiday_date=self.holiday_date,
            holiday_name=self.holiday_name,
            is_paid=self.is_paid,
            id=self.id,
        )
    
    @classmethod
    def from_entity(cls, entity: Holiday) -> HolidayModel:
        return cls(
            id=entity.id,
            business_id=entity.business_id,
            holiday_date=entity.holiday_date,
            holiday_name=entity.holiday_name,
            is_paid=entity.is_paid,
        )