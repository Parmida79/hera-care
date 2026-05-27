from typing import Any

from sqlalchemy.orm import mapped_column as column

# import models
from anatomy import Anatomy
from disease import Disease
from disease_anatomy import DiseaseAnatomy
from disease_symptom import DiseaseSymptom
from disease_treatment import DiseaseTreatment
from medical_history import MedicalHistory
from member import SuperAdmin, Admin, Patient, Member
from patient_disease import PatientDisease
from symptom import Symptom
from treatment import Treatment, Medication, LifeStyle


def mapped_column(*args: Any, **kwargs: Any):
    """Wrapper around mapped_column with nullable=False by default."""
    kwargs.setdefault("nullable", False)
    return column(*args, **kwargs)
