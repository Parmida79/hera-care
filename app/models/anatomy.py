from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped

from app.db.database import Base
from app.models import mapped_column
from app.utils.mixins import ModifiedMixin, ActivationMixin


class Anatomy(ActivationMixin, ModifiedMixin, Base):
    __tablename__ = 'anatomy'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255), unique=True)  # e.g., ovaries, pancreas, thyroid gland, central nervous system
    category: Mapped[str] = mapped_column(String(255))  # e.g., organ, tissue, system, cell type
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    latin_name: Mapped[str] = mapped_column(String(255), nullable=True)  # scientific name

    diseases = relationship('DiseaseAnatomy', back_populates='anatomy')
