"""Construcción de registros RIPS a partir de factura e historia clínica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, List, Optional, Tuple

from .models import (
    AnnexData,
    ConsultationInfo,
    InvoiceData,
    InvoiceLine,
    PatientInfo,
    RipsConsultationRecord,
    RipsMedicationRecord,
    RipsOtherServiceRecord,
    RipsInvoiceRecord,
    RipsProcedureRecord,
    RipsUserRecord,
)


ATTENTION_TYPE_MAP = {
    "urgencias": "02",
    "consulta externa": "01",
    "consulta": "01",
    "hospitalización": "04",
    "hospitalizacion": "04",
    "vacunacion": "13",
}

SERVICE_PURPOSE_MAP = {
    "consulta de primera vez": "01",
    "consulta de control": "02",
    "programa pf": "03",
    "detección": "04",
    "deteccion": "04",
    "consulta de urgencias": "10",
    "no aplica": "14",
    "vacunacion": "14",
    "terapia": "07",
}

DOCUMENT_TYPE_DEFAULT = "CC"


@dataclass
class RipsBuilder:
    """Combina datos de factura e historia para producir registros RIPS."""

    invoice: InvoiceData
    patient: PatientInfo
    provider_code: Optional[str] = None
    annex_data: Optional[AnnexData] = None

    def build_procedure_records(self) -> List[RipsProcedureRecord]:
        provider_code = self.provider_code or self.invoice.supplier_tax_id or ""
        document_type = self.resolve_document_type()
        document_number = self.resolve_document_number()

        service_date = self._resolve_service_date()
        attention_code = self._map_attention_type(self.patient.service_type)
        purpose_code = self._map_service_purpose(self.patient.service_purpose)

        records: List[RipsProcedureRecord] = []
        for line in self.invoice.lines:
            record = RipsProcedureRecord(
                provider_code=provider_code,
                invoice_number=self.invoice.invoice_id,
                document_type=document_type,
                document_number=document_number,
                service_date=service_date,
                authorization_number=None,
                service_code=line.line_id or "1",
                cups_code=line.cups_code or "",
                diagnosis_code=self.patient.principal_diagnosis_code,
                diagnosis_related=None,
                service_purpose_code=purpose_code,
                attention_type_code=attention_code,
                copayment_value=Decimal("0"),
                net_value=line.line_extension_amount or line.price_amount,
                modality_code=None,
            )
            records.append(record)
        return records

    def build_consultation_records(self) -> List[RipsConsultationRecord]:
        provider_code = self.provider_code or self.invoice.supplier_tax_id or ""
        document_type = self.resolve_document_type()
        document_number = self.resolve_document_number()
        diagnosis_code = self.patient.principal_diagnosis_code

        records: List[RipsConsultationRecord] = []
        for consultation in self.patient.consultations or []:
            consultation_datetime = consultation.datetime or self._resolve_service_date()
            consultation_code = consultation.code
            purpose_text = consultation.purpose_text or self.patient.service_purpose
            purpose_code = self._map_consultation_purpose(purpose_text)
            line_value = self._match_line_value(consultation_code)

            records.append(
                RipsConsultationRecord(
                    provider_code=provider_code,
                    invoice_number=self.invoice.invoice_id,
                    document_type=document_type,
                    document_number=document_number,
                    consultation_date=consultation_datetime,
                    authorization_number=consultation.authorization_number,
                    consultation_code=consultation_code,
                    consultation_purpose=purpose_code,
                    external_cause=None,
                    principal_diagnosis=diagnosis_code,
                    related_diagnosis1=None,
                    related_diagnosis2=None,
                    related_diagnosis3=None,
                    diagnosis_type=consultation.diagnosis_type or "1",
                    consultation_value=line_value,
                    copayment_value=Decimal("0"),
                    net_value=line_value,
                )
            )
        return records

    def build_medication_records(self) -> List[RipsMedicationRecord]:
        if not self.annex_data:
            return []

        provider_code = self.provider_code or self.invoice.supplier_tax_id or ""
        document_type = self.resolve_document_type()
        document_number = self.resolve_document_number()

        records: List[RipsMedicationRecord] = []
        for med in self.annex_data.medications:
            entry_document_type = med.document_type or document_type
            entry_document_number = med.document_number or document_number
            if entry_document_number and document_number and entry_document_number != document_number:
                entry_document_number = document_number
            if entry_document_type and document_type and entry_document_type != document_type:
                entry_document_type = document_type

            records.append(
                RipsMedicationRecord(
                    provider_code=med.provider_code or provider_code,
                    invoice_number=self.invoice.invoice_id,
                    document_type=entry_document_type,
                    document_number=entry_document_number,
                    authorization_number=med.authorization_number,
                    medication_code=med.medication_code,
                    medication_name=med.medication_name,
                    medication_type=med.medication_type,
                    pharmaceutical_form=med.pharmaceutical_form,
                    concentration=med.concentration,
                    unit_measure=med.unit_measure,
                    treatment_days=med.treatment_days,
                    quantity=med.quantity,
                    unit_value=med.unit_value,
                    total_value=med.total_value,
                    mipres_id=med.mipres_id,
                    principal_diagnosis=med.diagnosis_code or self.patient.principal_diagnosis_code,
                    related_diagnosis=med.related_diagnosis,
                    administration_date=med.administration_date,
                )
            )
        return records

    def build_other_service_records(self) -> List[RipsOtherServiceRecord]:
        if not self.annex_data:
            return []

        provider_code = self.provider_code or self.invoice.supplier_tax_id or ""
        document_type = self.resolve_document_type()
        document_number = self.resolve_document_number()

        records: List[RipsOtherServiceRecord] = []
        for other in self.annex_data.other_services:
            entry_document_type = other.document_type or document_type
            entry_document_number = other.document_number or document_number
            if entry_document_number and document_number and entry_document_number != document_number:
                entry_document_number = document_number
            if entry_document_type and document_type and entry_document_type != document_type:
                entry_document_type = document_type

            records.append(
                RipsOtherServiceRecord(
                    provider_code=other.provider_code or provider_code,
                    invoice_number=self.invoice.invoice_id,
                    document_type=entry_document_type,
                    document_number=entry_document_number,
                    authorization_number=other.authorization_number,
                    service_code=other.service_code,
                    service_name=other.service_name,
                    service_type=other.service_type,
                    service_date=other.service_date,
                    quantity=other.quantity,
                    unit_value=other.unit_value,
                    total_value=other.total_value,
                    mipres_id=other.mipres_id,
                    principal_diagnosis=other.diagnosis_code or self.patient.principal_diagnosis_code,
                    related_diagnosis=other.related_diagnosis,
                )
            )
        return records

    def build_invoice_record(self) -> RipsInvoiceRecord:
        provider_code = self.provider_code or self.invoice.supplier_tax_id or ""
        document_type = self.resolve_document_type()
        document_number = self.resolve_document_number()
        return RipsInvoiceRecord(
            provider_code=provider_code,
            provider_name=self.invoice.supplier_name,
            invoice_number=self.invoice.invoice_id,
            invoice_date=self.invoice.issue_date,
            total_value=self.invoice.total_amount,
            document_type=document_type,
            document_number=document_number,
            contract_number=None,
            policy_number=None,
        )

    def build_user_record(self) -> Optional[RipsUserRecord]:
        document_number = self.resolve_document_number()
        if not document_number:
            return None

        document_type = self.resolve_document_type()
        full_name = self._resolve_full_name()
        first_last, second_last, first_name, second_name = self._split_names(full_name)

        gender = None
        age = None
        age_unit = None
        department_code = None
        municipality_code = None
        residence_area = None

        if self.annex_data:
            patient_info = self.annex_data.patient
            gender = (patient_info.gender or "").upper() or None
            if patient_info.birth_date:
                service_date = self._resolve_service_date()
                age = self._calculate_age(patient_info.birth_date, service_date)
                age_unit = "A" if age is not None else None
            municipality_code = patient_info.municipality_code
            if municipality_code:
                department_code = municipality_code[:2]
            residence_area = patient_info.residence_zone

        return RipsUserRecord(
            document_type=document_type,
            document_number=document_number,
            last_name=first_last,
            second_last_name=second_last,
            first_name=first_name,
            second_name=second_name,
            age=age,
            age_unit=age_unit,
            gender=gender,
            department_code=department_code,
            municipality_code=municipality_code,
            residence_area=residence_area,
        )

    def resolve_document_type(self) -> str:
        cached = getattr(self, "_resolved_document_type", None)
        if cached:
            return cached
        candidates = [
            self.patient.document_type,
            self.patient.admission_document_type,
            self.annex_data.patient.document_type if self.annex_data else None,
            DOCUMENT_TYPE_DEFAULT,
        ]
        for candidate in candidates:
            if candidate:
                result = candidate.upper()
                self._resolved_document_type = result
                return result
        self._resolved_document_type = DOCUMENT_TYPE_DEFAULT
        return DOCUMENT_TYPE_DEFAULT

    def resolve_document_number(self) -> str:
        cached = getattr(self, "_resolved_document_number", None)
        if cached is not None:
            return cached
        candidates = [
            self.patient.document_number,
            self.patient.admission_document_number,
            self.annex_data.patient.document_number if self.annex_data else None,
        ]
        for candidate in candidates:
            if candidate:
                result = candidate.replace(" ", "")
                self._resolved_document_number = result
                return result
        self._resolved_document_number = ""
        return ""

    def _resolve_full_name(self) -> Optional[str]:
        if self.patient.full_name:
            return self.patient.full_name
        if self.annex_data and self.annex_data.patient.full_name:
            return self.annex_data.patient.full_name
        return None

    def _resolve_service_date(self) -> datetime:
        if self.patient.admission_datetime:
            return self.patient.admission_datetime
        return self.invoice.issue_date

    @staticmethod
    def _map_attention_type(raw: Optional[str]) -> Optional[str]:
        if not raw:
            return None
        raw_norm = raw.lower()
        for key, value in ATTENTION_TYPE_MAP.items():
            if key in raw_norm:
                return value
        return None

    @staticmethod
    def _map_service_purpose(raw: Optional[str]) -> Optional[str]:
        if not raw:
            return None
        raw_norm = raw.lower()
        for key, value in SERVICE_PURPOSE_MAP.items():
            if key in raw_norm:
                return value
        return None

    @staticmethod
    def _map_consultation_purpose(raw: Optional[str]) -> Optional[str]:
        return RipsBuilder._map_service_purpose(raw)

    @staticmethod
    def _split_names(full_name: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        if not full_name:
            return None, None, None, None
        tokens = [tok for tok in full_name.replace("  ", " ").strip().split(" ") if tok]
        if len(tokens) == 1:
            return None, None, tokens[0], None
        if len(tokens) == 2:
            return tokens[1], None, tokens[0], None
        if len(tokens) == 3:
            return tokens[2], tokens[1], tokens[0], None
        # Assume last two tokens are surnames, first two are given names
        first_last = tokens[-2]
        second_last = tokens[-1]
        first_name = tokens[0]
        second_name = " ".join(tokens[1:-2]) if len(tokens) > 4 else tokens[1]
        return first_last, second_last, first_name, second_name

    @staticmethod
    def _calculate_age(birth_date: datetime, reference_date: datetime) -> Optional[int]:
        if birth_date > reference_date:
            return None
        years = reference_date.year - birth_date.year
        if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
            years -= 1
        return years

    def _match_line_value(self, cups_code: Optional[str]) -> Decimal:
        if not cups_code:
            return Decimal("0")
        for line in self.invoice.lines:
            if (line.cups_code or "").strip() == cups_code:
                return line.line_extension_amount or line.price_amount or Decimal("0")
        return Decimal("0")
