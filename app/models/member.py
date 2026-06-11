from sqlalchemy import ForeignKey, Unicode, String, Enum
from sqlalchemy.orm import Mapped, relationship

from datetime import date

from app.db.database import Base
from app.utils import AutoActivationMixin, TimestampMixin, ModifiedMixin, \
    Gender, MaritalStatus, BloodGroup
from app.models import mapped_column


class Member(AutoActivationMixin, TimestampMixin, Base):
    __tablename__ = "member"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Unicode(255), index=True, unique=True)
    hashed_password: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    role: Mapped[str] = mapped_column(Unicode(50), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": "role",
        "polymorphic_identity": "member",
    }


class SuperAdmin(Member):
    __mapper_args__ = {"polymorphic_identity": "super-admin"}


class Admin(Member):
    __mapper_args__ = {"polymorphic_identity": "admin"}


class Patient(ModifiedMixin, Member):
    __tablename__ = 'patient'

    id: Mapped[int] = mapped_column(ForeignKey("member.id"), primary_key=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)

    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(nullable=True)
    gender: Mapped[str] = mapped_column(Enum(Gender), nullable=True)
    marital_status: Mapped[str] = mapped_column(Enum(MaritalStatus), default=MaritalStatus.UNKNOWN)
    blood_group: Mapped[str] = mapped_column(Enum(BloodGroup), default=BloodGroup.UNKNOWN)
    weight_kg: Mapped[float] = mapped_column(nullable=True)
    height_cm: Mapped[float] = mapped_column(nullable=True)
    bmi: Mapped[float] = mapped_column(nullable=True)
    # BMI should be calculated based on weight and height
    # age could be calculated based on DOB

    medical_histories = relationship('MedicalHistory', back_populates='patient', lazy="selectin")

    __mapper_args__ = {"polymorphic_identity": "patient"}
