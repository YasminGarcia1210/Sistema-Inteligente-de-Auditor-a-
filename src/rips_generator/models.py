"""Modelos de datos para el generador de RIPS."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


@dataclass
class InvoiceLine:
    """Información relevante de un ítem dentro de la factura electrónica."""

    line_id: Optional[str]
    cups_code: Optional[str]
    description: Optional[str]
    quantity: Decimal
    price_amount: Decimal
    line_extension_amount: Decimal


@dataclass
class InvoiceData:
    """Información general de la factura electrónica."""

    invoice_id: str
    issue_date: datetime
    supplier_tax_id: Optional[str]
    supplier_name: Optional[str]
    customer_tax_id: Optional[str]
    customer_name: Optional[str]
    total_amount: Decimal
    currency: str
    lines: List[InvoiceLine] = field(default_factory=list)


@dataclass
class PatientInfo:
    """Datos extraídos de la historia clínica."""

    document_type: Optional[str] = None
    document_number: Optional[str] = None
    full_name: Optional[str] = None
    admission_document_type: Optional[str] = None
    admission_document_number: Optional[str] = None
    admission_id: Optional[str] = None
    admission_datetime: Optional[datetime] = None
    discharge_datetime: Optional[datetime] = None
    service_type: Optional[str] = None
    entry_service: Optional[str] = None
    principal_diagnosis: Optional[str] = None
    principal_diagnosis_code: Optional[str] = None
    service_purpose: Optional[str] = None
    triage_level: Optional[str] = None
    consultations: List["ConsultationInfo"] = field(default_factory=list)


@dataclass
class RipsProcedureRecord:
    """Registro RIPS de procedimientos (archivo AP)."""

    provider_code: str
    invoice_number: str
    document_type: str
    document_number: str
    service_date: datetime
    authorization_number: Optional[str]
    service_code: str
    cups_code: str
    diagnosis_code: Optional[str]
    diagnosis_related: Optional[str]
    service_purpose_code: Optional[str]
    attention_type_code: Optional[str]
    copayment_value: Decimal
    net_value: Decimal
    modality_code: Optional[str]


@dataclass
class RipsInvoiceRecord:
    """Registro RIPS cabecera (archivo AF)."""

    provider_code: str
    provider_name: Optional[str]
    invoice_number: str
    invoice_date: datetime
    total_value: Decimal
    document_type: Optional[str]
    document_number: Optional[str]
    contract_number: Optional[str] = None
    policy_number: Optional[str] = None
    copayment_value: Decimal = Decimal("0")
    commission_value: Decimal = Decimal("0")
    discount_value: Decimal = Decimal("0")


@dataclass
class RipsUserRecord:
    """Registro RIPS de usuarios (archivo US)."""

    document_type: str
    document_number: str
    last_name: Optional[str]
    second_last_name: Optional[str]
    first_name: Optional[str]
    second_name: Optional[str]
    age: Optional[int]
    age_unit: Optional[str]
    gender: Optional[str]
    department_code: Optional[str]
    municipality_code: Optional[str]
    residence_area: Optional[str]


@dataclass
class AnnexPatientInfo:
    """Información complementaria obtenida de anexos (ej. JSON RIPS)."""

    document_type: Optional[str]
    document_number: Optional[str]
    full_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    municipality_code: Optional[str] = None
    residence_zone: Optional[str] = None


@dataclass
class ConsultationInfo:
    """Información de consulta obtenida de la historia clínica."""

    code: str
    description: Optional[str]
    datetime: Optional[datetime]
    purpose_text: Optional[str]
    authorization_number: Optional[str] = None
    diagnosis_type: Optional[str] = None


@dataclass
class AnnexMedicationEntry:
    """Información de medicamentos extraída del anexo RIPS JSON."""

    provider_code: str
    document_type: Optional[str]
    document_number: Optional[str]
    authorization_number: Optional[str]
    medication_code: str
    medication_name: Optional[str]
    medication_type: Optional[str]
    unit_value: Decimal
    total_value: Decimal
    quantity: Decimal
    unit_measure: Optional[str]
    treatment_days: Optional[int]
    diagnosis_code: Optional[str]
    related_diagnosis: Optional[str]
    mipres_id: Optional[str]
    administration_date: Optional[datetime]
    pharmaceutical_form: Optional[str]
    concentration: Optional[str]


@dataclass
class AnnexOtherServiceEntry:
    """Información de otros servicios extraída del anexo RIPS JSON."""

    provider_code: str
    document_type: Optional[str]
    document_number: Optional[str]
    authorization_number: Optional[str]
    service_code: str
    service_name: Optional[str]
    service_type: Optional[str]
    service_date: Optional[datetime]
    unit_value: Decimal
    total_value: Decimal
    quantity: Decimal
    diagnosis_code: Optional[str]
    related_diagnosis: Optional[str]
    mipres_id: Optional[str]


@dataclass
class AnnexData:
    """Contenedor general con información del anexo RIPS JSON."""

    patient: AnnexPatientInfo
    medications: List[AnnexMedicationEntry] = field(default_factory=list)
    other_services: List[AnnexOtherServiceEntry] = field(default_factory=list)


@dataclass
class RipsConsultationRecord:
    """Registro RIPS de consultas (archivo AC)."""

    provider_code: str
    invoice_number: str
    document_type: str
    document_number: str
    consultation_date: datetime
    authorization_number: Optional[str]
    consultation_code: str
    consultation_purpose: Optional[str]
    external_cause: Optional[str]
    principal_diagnosis: Optional[str]
    related_diagnosis1: Optional[str]
    related_diagnosis2: Optional[str]
    related_diagnosis3: Optional[str]
    diagnosis_type: Optional[str]
    consultation_value: Decimal
    copayment_value: Decimal
    net_value: Decimal


@dataclass
class RipsMedicationRecord:
    """Registro RIPS de medicamentos (archivo AM)."""

    provider_code: str
    invoice_number: str
    document_type: str
    document_number: str
    authorization_number: Optional[str]
    medication_code: str
    medication_name: Optional[str]
    medication_type: Optional[str]
    pharmaceutical_form: Optional[str]
    concentration: Optional[str]
    unit_measure: Optional[str]
    treatment_days: Optional[int]
    quantity: Decimal
    unit_value: Decimal
    total_value: Decimal
    mipres_id: Optional[str]
    principal_diagnosis: Optional[str]
    related_diagnosis: Optional[str]
    administration_date: Optional[datetime]


@dataclass
class RipsOtherServiceRecord:
    """Registro RIPS de otros servicios (archivo AT)."""

    provider_code: str
    invoice_number: str
    document_type: str
    document_number: str
    authorization_number: Optional[str]
    service_code: str
    service_name: Optional[str]
    service_type: Optional[str]
    service_date: Optional[datetime]
    quantity: Decimal
    unit_value: Decimal
    total_value: Decimal
    mipres_id: Optional[str]
    principal_diagnosis: Optional[str]
    related_diagnosis: Optional[str]


@dataclass
class ValidationMessage:
    """Resultado de una regla de validación sobre los registros RIPS generados."""

    severity: str  # e.g. INFO, WARNING, ERROR
    code: str
    message: str


@dataclass
class ClinicalEntity:
    """Entidad clínica detectada en texto libre."""

    label: str
    text: str
    code: Optional[str] = None
    score: Optional[float] = None


@dataclass
class ClinicalExtractionResult:
    """Resultado del extractor NLP sobre una historia clínica."""

    diagnoses: List[ClinicalEntity] = field(default_factory=list)
    procedures: List[ClinicalEntity] = field(default_factory=list)
