"""Reglas de validación para los registros RIPS generados."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Optional

from .models import (
    RipsConsultationRecord,
    RipsInvoiceRecord,
    RipsMedicationRecord,
    RipsOtherServiceRecord,
    RipsProcedureRecord,
    RipsUserRecord,
    ValidationMessage,
)

DECIMAL_ZERO = Decimal("0")
TOLERANCE = Decimal("1.00")  # tolerancia en pesos


def validate_rips(
    invoice: RipsInvoiceRecord,
    user: Optional[RipsUserRecord],
    procedures: Iterable[RipsProcedureRecord],
    consultations: Iterable[RipsConsultationRecord],
    medications: Iterable[RipsMedicationRecord],
    other_services: Iterable[RipsOtherServiceRecord],
) -> List[ValidationMessage]:
    messages: List[ValidationMessage] = []

    target_doc_type = invoice.document_type
    target_doc_number = invoice.document_number
    if user:
        target_doc_type = user.document_type or target_doc_type
        target_doc_number = user.document_number or target_doc_number

    _validate_documents(
        target_doc_type,
        target_doc_number,
        procedures,
        consultations,
        medications,
        other_services,
        messages,
    )
    _validate_totals(invoice, procedures, consultations, medications, other_services, messages)
    _validate_diagnoses(procedures, consultations, medications, other_services, messages)
    _validate_cups(procedures, messages)

    if not messages:
        messages.append(ValidationMessage("INFO", "VAL000", "Registros validados sin inconsistencias detectadas."))

    return messages


def _validate_documents(
    target_doc_type: Optional[str],
    target_doc_number: Optional[str],
    procedures: Iterable[RipsProcedureRecord],
    consultations: Iterable[RipsConsultationRecord],
    medications: Iterable[RipsMedicationRecord],
    other_services: Iterable[RipsOtherServiceRecord],
    messages: List[ValidationMessage],
) -> None:
    mismatches: List[str] = []

    def check(record_type: str, doc_type: Optional[str], doc_number: Optional[str]) -> None:
        if not doc_number:
            mismatches.append(f"{record_type}: documento vacío")
            return
        if target_doc_number and doc_number != target_doc_number:
            mismatches.append(f"{record_type}: documento {doc_number} != {target_doc_number}")
        if target_doc_type and doc_type and doc_type != target_doc_type:
            mismatches.append(f"{record_type}: tipo {doc_type} != {target_doc_type}")

    for record in procedures:
        check("AP", record.document_type, record.document_number)
    for record in consultations:
        check("AC", record.document_type, record.document_number)
    for record in medications:
        check("AM", record.document_type, record.document_number)
    for record in other_services:
        check("AT", record.document_type, record.document_number)

    if mismatches:
        messages.append(
            ValidationMessage(
                "WARNING",
                "DOC001",
                "Inconsistencias en tipo/número de documento: " + "; ".join(mismatches),
            )
        )


def _validate_totals(
    invoice: RipsInvoiceRecord,
    procedures: Iterable[RipsProcedureRecord],
    consultations: Iterable[RipsConsultationRecord],
    medications: Iterable[RipsMedicationRecord],
    other_services: Iterable[RipsOtherServiceRecord],
    messages: List[ValidationMessage],
) -> None:
    def safe_sum(values: Iterable[Decimal]) -> Decimal:
        total = DECIMAL_ZERO
        for value in values:
            if value is None:
                continue
            total += value
        return total

    total_procedures = safe_sum(record.net_value for record in procedures)
    total_consultations = safe_sum(record.net_value for record in consultations)
    total_medications = safe_sum(record.total_value for record in medications)
    total_other_services = safe_sum(record.total_value for record in other_services)

    extras_total = total_consultations + total_medications + total_other_services

    if total_procedures > DECIMAL_ZERO:
        calculated_total = total_procedures
        if extras_total > DECIMAL_ZERO:
            messages.append(
                ValidationMessage(
                    "INFO",
                    "TOT002",
                    "Valores en AC/AM/AT detectados adicionales a AP; se usa AP para conciliación de totales.",
                )
            )
    else:
        calculated_total = extras_total

    difference = (invoice.total_value or DECIMAL_ZERO) - calculated_total
    if difference.copy_abs() > TOLERANCE:
        messages.append(
            ValidationMessage(
                "WARNING",
                "TOT001",
                f"Total factura ({invoice.total_value}) difiere de suma registros ({calculated_total}) por {difference}.",
            )
        )


def _validate_diagnoses(
    procedures: Iterable[RipsProcedureRecord],
    consultations: Iterable[RipsConsultationRecord],
    medications: Iterable[RipsMedicationRecord],
    other_services: Iterable[RipsOtherServiceRecord],
    messages: List[ValidationMessage],
) -> None:
    missing: List[str] = []

    for idx, record in enumerate(procedures, start=1):
        if not record.diagnosis_code:
            missing.append(f"AP[{idx}] sin diagnóstico principal")
    for idx, record in enumerate(consultations, start=1):
        if not record.principal_diagnosis:
            missing.append(f"AC[{idx}] sin diagnóstico principal")
    for idx, record in enumerate(medications, start=1):
        if not record.principal_diagnosis:
            missing.append(f"AM[{idx}] sin diagnóstico principal")
    for idx, record in enumerate(other_services, start=1):
        if not record.principal_diagnosis:
            missing.append(f"AT[{idx}] sin diagnóstico principal")

    if missing:
        messages.append(
            ValidationMessage(
                "ERROR",
                "DX001",
                "Diagnósticos ausentes: " + "; ".join(missing),
            )
        )


def _validate_cups(procedures: Iterable[RipsProcedureRecord], messages: List[ValidationMessage]) -> None:
    missing = [str(idx) for idx, record in enumerate(procedures, start=1) if not record.cups_code]
    if missing:
        messages.append(
            ValidationMessage(
                "ERROR",
                "CUPS001",
                f"Procedimientos sin código CUPS en registros: {', '.join(missing)}.",
            )
        )
