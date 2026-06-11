from datetime import datetime

from sqlalchemy import String, ForeignKey, Enum, JSON, func
from sqlalchemy.orm import relationship, Mapped
from typing import Any, Dict

from app.db.database import Base
from app.models import mapped_column
from app.utils.enums import EntryType
from app.utils.mixins import TimestampMixin


class MedicalHistory(TimestampMixin, Base):
    __tablename__ = 'medical_history'

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(ForeignKey('patient.id'))

    entry_type: Mapped[str] = mapped_column(Enum(EntryType), name='entry_type')
    value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # flexible e.g., {"bmi": 28.5}
    recorded_at: Mapped[datetime] = mapped_column(default=func.now())
    source: Mapped[str] = mapped_column(String(255))  #  e.g., 'chatbot input'

    patient = relationship('Patient', back_populates='medical_histories')
