"""Exportadores para archivos planos RIPS (AF, US, AP, AC, AM, AT)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable, List, Optional

from .models import (
    RipsConsultationRecord,
    RipsInvoiceRecord,
    RipsMedicationRecord,
    RipsOtherServiceRecord,
    RipsProcedureRecord,
    RipsUserRecord,
)


def write_rips_files(
    output_dir: Path,
    af_records: Iterable[RipsInvoiceRecord],
    us_records: Iterable[RipsUserRecord],
    ap_records: Iterable[RipsProcedureRecord],
    ac_records: Iterable[RipsConsultationRecord] = (),
    am_records: Iterable[RipsMedicationRecord] = (),
    at_records: Iterable[RipsOtherServiceRecord] = (),
    delimiter: str = ",",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_file(output_dir / "AF.txt", [r for r in af_records], _af_row, delimiter)
    _write_file(output_dir / "US.txt", [r for r in us_records if r is not None], _us_row, delimiter)
    _write_file(output_dir / "AP.txt", [r for r in ap_records], _ap_row, delimiter)
    _write_file(output_dir / "AC.txt", [r for r in ac_records], _ac_row, delimiter)
    _write_file(output_dir / "AM.txt", [r for r in am_records], _am_row, delimiter)
    _write_file(output_dir / "AT.txt", [r for r in at_records], _at_row, delimiter)


def _write_file(path: Path, records: List, formatter, delimiter: str) -> None:
    if not records:
        return
    lines = []
    for record in records:
        row = formatter(record)
        row = ["" if value is None else _format_value(value) for value in row]
        lines.append(delimiter.join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _af_row(record: RipsInvoiceRecord) -> List[Optional[str]]:
    return [
        record.provider_code,
        record.invoice_number,
        record.invoice_date.strftime("%Y-%m-%d"),
        _format_decimal(record.total_value),
        record.document_type,
        record.document_number,
        record.contract_number,
        record.policy_number,
        _format_decimal(record.copayment_value),
        _format_decimal(record.commission_value),
        _format_decimal(record.discount_value),
    ]


def _us_row(record: RipsUserRecord) -> List[Optional[str]]:
    return [
        record.document_type,
        record.document_number,
        record.last_name,
        record.second_last_name,
        record.first_name,
        record.second_name,
        str(record.age) if record.age is not None else None,
        record.age_unit,
        record.gender,
        record.department_code,
        record.municipality_code,
        record.residence_area,
    ]


def _ap_row(record: RipsProcedureRecord) -> List[Optional[str]]:
    return [
        record.provider_code,
        record.invoice_number,
        record.document_type,
        record.document_number,
        record.service_date.strftime("%Y-%m-%d"),
        record.authorization_number,
        record.service_code,
        record.cups_code,
        record.diagnosis_code,
        record.diagnosis_related,
        record.service_purpose_code,
        record.attention_type_code,
        _format_decimal(record.copayment_value),
        _format_decimal(record.net_value),
        record.modality_code,
    ]


def _ac_row(record: RipsConsultationRecord) -> List[Optional[str]]:
    return [
        record.provider_code,
        record.invoice_number,
        record.document_type,
        record.document_number,
        record.consultation_date.strftime("%Y-%m-%d"),
        record.authorization_number,
        record.consultation_code,
        record.consultation_purpose,
        record.external_cause,
        record.principal_diagnosis,
        record.related_diagnosis1,
        record.related_diagnosis2,
        record.related_diagnosis3,
        record.diagnosis_type,
        _format_decimal(record.consultation_value),
        _format_decimal(record.copayment_value),
        _format_decimal(record.net_value),
    ]


def _am_row(record: RipsMedicationRecord) -> List[Optional[str]]:
    return [
        record.provider_code,
        record.invoice_number,
        record.document_type,
        record.document_number,
        record.authorization_number,
        record.medication_code,
        record.mipres_id,
        record.medication_type,
        record.medication_name,
        record.pharmaceutical_form,
        record.concentration,
        record.unit_measure,
        str(record.treatment_days) if record.treatment_days is not None else None,
        _format_decimal(record.quantity),
        _format_decimal(record.unit_value),
        _format_decimal(record.total_value),
        record.principal_diagnosis,
        record.related_diagnosis,
        record.administration_date.strftime("%Y-%m-%d") if record.administration_date else None,
    ]


def _at_row(record: RipsOtherServiceRecord) -> List[Optional[str]]:
    return [
        record.provider_code,
        record.invoice_number,
        record.document_type,
        record.document_number,
        record.authorization_number,
        record.service_type,
        record.service_code,
        record.service_name,
        record.service_date.strftime("%Y-%m-%d") if record.service_date else None,
        _format_decimal(record.quantity),
        _format_decimal(record.unit_value),
        _format_decimal(record.total_value),
        record.mipres_id,
        record.principal_diagnosis,
        record.related_diagnosis,
    ]


def _format_value(value) -> str:
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _format_decimal(value: Decimal) -> str:
    return f"{value:.2f}"
