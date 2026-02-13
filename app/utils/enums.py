from enum import Enum


class Gender(Enum):
    MALE = 'male'
    FEMALE = 'female'
    UNKNOWN = 'unknown'
    OTHERS = 'others'


class MaritalStatus(Enum):
    SINGLE = 'single'
    MARRIED = 'married'
    DIVORCED = 'divorced'
    WIDOWED = 'widow'
    UNKNOWN = 'unknown'


class DiseaseType(Enum):
    PHYSICAL = 'physical'
    MENTAL = 'mental'
    HYBRID = 'hybrid'


class DiseaseSeverity(Enum):
    MILD = 'mild'
    MODERATE = 'moderate'
    SEVERE = 'severe'


class PatientDiseaseStatus(Enum):
    ACTIVE = 'active'
    REMITTED = 'remitted'
    CHRONIC = 'chronic'


class DiseaseAnatomySeverity(Enum):
    MILD = 'mild'
    MODERATE = 'moderate'
    SEVERE = 'severe'
    VARIABLE = 'variable'


class EntryType(Enum):
    VITAL = 'vital'
    SYMPTOM_REPORT = 'symptom_report'
    LAB_RESULT = 'lab_result'
    NOTE = 'note'


class BloodGroup(Enum):
    A_POSITIVE = 'A+'
    B_POSITIVE = 'B+'
    AB_POSITIVE = 'AB+'
    O_POSITIVE = 'O+'
    A_NEGATIVE = 'A-'
    B_NEGATIVE = 'B-'
    AB_NEGATIVE = 'AB-'
    O_NEGATIVE = 'O-'
    UNKNOWN = 'unknown'
