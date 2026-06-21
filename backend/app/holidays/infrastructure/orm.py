from __future__ import annotations
from typing import TYPE_CHECKING

from uuid import UUID
from datetime import date

from sqlalchemy import (
    Date,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.core.db import Base
from app.holidays.domain.entities import Holiday

if TYPE_CHECKING:
    from app.business.infrastructure.orm import BusinessModel


class HolidayModel(Base):
    __tablename__ = "holidays"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    business_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    business: Mapped["BusinessModel"] = relationship(back_populates="holidays")

    __table_args__ = (
        UniqueConstraint("business_id", "date", name="uq_holiday_business_date"),
    )

    @classmethod
    def from_entity(cls, holiday: Holiday) -> "HolidayModel":
        return cls(
            id=holiday.id,
            business_id=holiday.business_id,
            date=holiday.date,
            name=holiday.name,
        )

    def to_entity(self) -> Holiday:
        return Holiday(
            id=self.id,
            business_id=self.business_id,
            date=self.date,
            name=self.name,
        )
