from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped

from app.db.database import Base
from app.models import mapped_column
from app.utils.enums import DiseaseSeverity
from app.utils.mixins import ActivationMixin, TimestampMixin


class DiseaseSymptom(ActivationMixin, TimestampMixin, Base):
    __tablename__ = 'disease_symptom'

    id: Mapped[int] = mapped_column(primary_key=True)

    disease_id: Mapped[int] = mapped_column(ForeignKey('disease.id'))
    symptom_id: Mapped[int] = mapped_column(ForeignKey('symptom.id'))

    severity: Mapped[str] = mapped_column(Enum(DiseaseSeverity))

    disease = relationship('Disease', back_populates='symptoms')
    symptom = relationship('Symptom', back_populates='diseases')
