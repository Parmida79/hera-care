from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped

from hera_care.db.database import Base
from hera_care.models import mapped_column
from hera_care.utils.enums import DiseaseSeverity
from hera_care.utils.mixins import ActivationMixin, TimestampMixin


class DiseaseSymptom(ActivationMixin, TimestampMixin, Base):
    __tablename__ = 'disease_symptom'

    id: Mapped[int] = mapped_column(primary_key=True)

    disease_id: Mapped[int] = mapped_column(ForeignKey('disease.id'))
    symptom_id: Mapped[int] = mapped_column(ForeignKey('symptom.id'))

    severity: Mapped[str] = mapped_column(Enum(DiseaseSeverity))

    disease = relationship('Disease', back_populates='symptoms')
    symptom = relationship('Symptom', back_populates='diseases')
