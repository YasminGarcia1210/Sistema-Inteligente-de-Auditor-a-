#!/usr/bin/env python3
"""Compara la extracción basada en reglas vs. el prototipo NLP sobre historias clínicas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rips_generator import ClinicalEntityExtractor, HistoryParser  # noqa: E402
from rips_generator.pdf_utils import extract_pdf_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compara parser tradicional vs extractor NLP en historias clínicas PDF.")
    parser.add_argument("history_pdf", type=Path, help="Ruta a la historia clínica en PDF.")
    parser.add_argument("--output-json", type=Path, help="Archivo donde guardar la comparación (JSON).")
    parser.add_argument("--model-name", default="PlanTL-GOB-ES/roberta-base-biomedical-es", help="Modelo HuggingFace a utilizar (si está disponible).")
    parser.add_argument("--local-files-only", action="store_true", help="No intenta descargar modelos; usa solo archivos locales.")
    parser.add_argument("--disable-transformer", action="store_true", help="Desactiva el uso de transformers y ejecuta únicamente el extractor heurístico.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    parser = HistoryParser(args.history_pdf)
    parsed = parser.parse()

    from rips_generator.history_nlp import TransformerConfig  # import tardío

    config = TransformerConfig(
        model_name=args.model_name,
        local_files_only=args.local_files_only,
        enabled=not args.disable_transformer,
    )
    extractor = ClinicalEntityExtractor(config=config)

    text = extract_pdf_text(args.history_pdf)
    nlp_result = extractor.extract(text)

    comparison: Dict[str, List[Dict[str, str]]] = {
        "parser": {
            "principal_diagnosis_code": parsed.principal_diagnosis_code,
            "principal_diagnosis_text": parsed.principal_diagnosis,
            "service_purpose": parsed.service_purpose,
            "consultations": [c.code for c in parsed.consultations],
        },
        "nlp": {
            "diagnoses": [
                {"code": ent.code, "text": ent.text, "label": ent.label, "score": ent.score}
                for ent in nlp_result.diagnoses
            ],
            "procedures": [
                {"code": ent.code, "text": ent.text, "label": ent.label, "score": ent.score}
                for ent in nlp_result.procedures
            ],
        },
        "metadata": {
            "history_pdf": str(args.history_pdf),
            "transformer_enabled": extractor.enabled,
        },
    }

    if args.output_json:
        args.output_json.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] Comparación guardada en {args.output_json}")
    else:
        print(json.dumps(comparison, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
