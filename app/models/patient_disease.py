from datetime import date
from typing import Optional

from sqlalchemy import ForeignKey, Enum, Text, func
from sqlalchemy.orm import Mapped

from app.db.database import Base
from app.models import mapped_column
from app.utils.enums import DiseaseSeverity, PatientDiseaseStatus
from app.utils.mixins import AutoActivationMixin, ModifiedMixin


class PatientDisease(AutoActivationMixin, ModifiedMixin, Base):
    __tablename__ = 'patient_disease'

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(ForeignKey('patient.id'))
    disease_id: Mapped[int] = mapped_column(ForeignKey('disease.id'))

    diagnosis_date: Mapped[date] = mapped_column(default=func.now())
    severity: Mapped[str] = mapped_column(Enum(DiseaseSeverity))
    status: Mapped[str] = mapped_column(Enum(PatientDiseaseStatus), name='patient_disease_status')
    notes: Mapped[Optional[str]] = mapped_column(Text)
    # medication
