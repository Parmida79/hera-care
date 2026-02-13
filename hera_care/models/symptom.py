from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped

from hera_care.db.database import Base
from hera_care.models import mapped_column
from hera_care.utils.mixins import ModifiedMixin, ActivationMixin


class Symptom(ActivationMixin, ModifiedMixin, Base):
    __tablename__ = 'symptom'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    diseases = relationship('DiseaseSymptom', back_populates='symptom')
