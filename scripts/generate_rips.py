#!/usr/bin/env python3
"""CLI para generar registros RIPS (procedimientos) a partir de factura e historia clínica."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rips_generator import HistoryParser, InvoiceParser, RipsBuilder, RipsJsonAnnexParser, ValidationMessage, validate_rips
from rips_generator.pdf_utils import extract_pdf_text
from rips_generator.rips_exporter import write_rips_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera registros RIPS (procedimientos) a partir de factura electrónica e historia clínica.")
    parser.add_argument("--invoice-pdf", required=True, type=Path, help="Ruta al PDF de la factura electrónica.")
    parser.add_argument("--history-pdf", required=True, type=Path, help="Ruta al PDF de la historia clínica.")
    parser.add_argument("--annex-rips-json", type=Path, help="Ruta opcional al JSON de RIPS (anexo FEV) para enriquecer datos.")
    parser.add_argument("--output-json", required=True, type=Path, help="Ruta de salida en formato JSON.")
    parser.add_argument("--output-dir", type=Path, help="Directorio opcional para archivos planos RIPS (AF/US/AP/AC/AM/AT).")
    parser.add_argument("--include-nlp-details", action="store_true", help="Incluye resultados del extractor NLP/heurístico en el JSON final.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    invoice = InvoiceParser(args.invoice_pdf).parse()
    patient = HistoryParser(args.history_pdf).parse()

    annex_data = None
    if args.annex_rips_json:
        annex_data = RipsJsonAnnexParser(args.annex_rips_json).parse()

    builder = RipsBuilder(invoice=invoice, patient=patient, annex_data=annex_data)
    procedure_records = builder.build_procedure_records()
    consultation_records = builder.build_consultation_records()
    medication_records = builder.build_medication_records()
    other_service_records = builder.build_other_service_records()
    invoice_record = builder.build_invoice_record()
    user_record = builder.build_user_record()
    validation_messages = validate_rips(
        invoice_record,
        user_record,
        procedure_records,
        consultation_records,
        medication_records,
        other_service_records,
    )

    nlp_details = None
    if args.include_nlp_details:
        from rips_generator.history_nlp import ClinicalEntityExtractor, TransformerConfig

        text_content = extract_pdf_text(args.history_pdf)
        nlp_extractor = ClinicalEntityExtractor(TransformerConfig(enabled=False))
        nlp_result = nlp_extractor.extract(text_content)
        nlp_details = {
            "diagnoses": [
                {"code": ent.code, "text": ent.text, "label": ent.label, "score": ent.score}
                for ent in nlp_result.diagnoses
            ],
            "procedures": [
                {"code": ent.code, "text": ent.text, "label": ent.label, "score": ent.score}
                for ent in nlp_result.procedures
            ],
        }

    if args.output_dir:
        write_rips_files(
            args.output_dir,
            af_records=[invoice_record],
            us_records=[user_record] if user_record else [],
            ap_records=procedure_records,
            ac_records=consultation_records,
            am_records=medication_records,
            at_records=other_service_records,
        )

    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "invoice": {
            "invoice_id": invoice.invoice_id,
            "issue_date": invoice.issue_date.isoformat(),
            "customer_name": invoice.customer_name,
            "total_amount": str(invoice.total_amount),
            "line_count": len(invoice.lines),
        },
        "patient": {
            "document_type": builder.resolve_document_type(),
            "document_number": builder.resolve_document_number(),
            "full_name": patient.full_name or (annex_data.patient.full_name if annex_data else None),
            "principal_diagnosis_code": patient.principal_diagnosis_code,
            "source_document_type": {
                "history": patient.document_type,
                "annex_original": annex_data.patient.document_type if annex_data else None,
                "resolved": builder.resolve_document_type(),
            },
            "source_document_number": {
                "history": patient.document_number,
                "annex_original": annex_data.patient.document_number if annex_data else None,
                "resolved": builder.resolve_document_number(),
            },
        },
        "rips_procedures": [
            {
                "provider_code": record.provider_code,
                "invoice_number": record.invoice_number,
                "document_type": record.document_type,
                "document_number": record.document_number,
                "service_date": record.service_date.isoformat(),
                "cups_code": record.cups_code,
                "diagnosis_code": record.diagnosis_code,
                "service_purpose_code": record.service_purpose_code,
                "attention_type_code": record.attention_type_code,
                "net_value": str(record.net_value),
            }
            for record in procedure_records
        ],
        "rips_consultations": [
            {
                "consultation_code": record.consultation_code,
                "consultation_date": record.consultation_date.isoformat(),
                "consultation_value": f"{record.consultation_value:.2f}",
                "diagnosis_code": record.principal_diagnosis,
            }
            for record in consultation_records
        ],
        "rips_medications": [
            {
                "medication_code": record.medication_code,
                "medication_name": record.medication_name,
                "total_value": f"{record.total_value:.2f}",
                "diagnosis_code": record.principal_diagnosis,
            }
            for record in medication_records
        ],
        "rips_other_services": [
            {
                "service_code": record.service_code,
                "service_name": record.service_name,
                "total_value": f"{record.total_value:.2f}",
                "diagnosis_code": record.principal_diagnosis,
            }
            for record in other_service_records
        ],
        "rips_invoice": {
            "invoice_number": invoice_record.invoice_number,
            "total_value": str(invoice_record.total_value),
        },
        "validation_messages": [
            {
                "severity": message.severity,
                "code": message.code,
                "message": message.message,
            }
            for message in validation_messages
        ],
        "nlp_support": nlp_details,
        "output_dir": str(args.output_dir) if args.output_dir else None,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    message = (
        f"[OK] Se generaron {len(procedure_records)} registros AP, {len(consultation_records)} registros AC, "
        f"{len(medication_records)} registros AM y {len(other_service_records)} registros AT en {args.output_json}"
    )
    if args.output_dir:
        message += f" y archivos planos en {args.output_dir}"
    errors = sum(1 for msg in validation_messages if msg.severity.upper() == "ERROR")
    warnings = sum(1 for msg in validation_messages if msg.severity.upper() == "WARNING")
    if errors or warnings:
        message += f" | Validación -> {errors} errores, {warnings} advertencias."
    else:
        message += " | Validación sin inconsistencias."
    print(message)


if __name__ == "__main__":
    main()
