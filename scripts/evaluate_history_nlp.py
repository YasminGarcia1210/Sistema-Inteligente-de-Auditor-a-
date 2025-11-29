#!/usr/bin/env python3
"""Evalúa el extractor NLP vs. el parser determinístico sobre un conjunto de historias."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rips_generator import ClinicalEntityExtractor, HistoryParser  # noqa: E402
from rips_generator.history_nlp import TransformerConfig  # noqa: E402
from rips_generator.pdf_utils import extract_pdf_text


@dataclass
class EvaluationRecord:
    history_path: Path
    parser_diagnosis: Optional[str]
    parser_consultations: List[str]
    nlp_diagnoses: List[str]
    nlp_procedures: List[str]
    matched_diagnosis: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evalúa el extractor NLP contra el parser tradicional sobre múltiples historias en PDF.")
    parser.add_argument(
        "history_paths",
        type=Path,
        nargs="+",
        help="Rutas a historias clínicas en PDF (acepta glob).",
    )
    parser.add_argument("--output-json", type=Path, help="Reporte de resultados en JSON.")
    parser.add_argument("--model-name", default="PlanTL-GOB-ES/roberta-base-biomedical-es", help="Modelo HuggingFace a utilizar.")
    parser.add_argument("--local-files-only", action="store_true", help="No intenta descargar modelos (solo archivos locales).")
    parser.add_argument("--disable-transformer", action="store_true", help="Usar exclusivamente heurísticas (sin modelo).")
    return parser.parse_args()


def iter_history_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from path.rglob("*.pdf")
        elif "*" in str(path):
            yield from Path().glob(str(path))
        else:
            yield path


def evaluate_histories(args: argparse.Namespace) -> Tuple[List[EvaluationRecord], Counter]:
    config = TransformerConfig(
        model_name=args.model_name,
        local_files_only=args.local_files_only,
        enabled=not args.disable_transformer,
    )
    extractor = ClinicalEntityExtractor(config=config)
    stats = Counter()
    records: List[EvaluationRecord] = []

    for history_path in iter_history_files(args.history_paths):
        try:
            parser = HistoryParser(history_path)
            parsed = parser.parse()
        except Exception as exc:
            stats["parse_error"] += 1
            records.append(
                EvaluationRecord(
                    history_path=history_path,
                    parser_diagnosis=None,
                    parser_consultations=[],
                    nlp_diagnoses=[],
                    nlp_procedures=[],
                    matched_diagnosis=False,
                )
            )
            continue

        text = extract_pdf_text(history_path)
        nlp_result = extractor.extract(text)

        parser_diag = parsed.principal_diagnosis_code
        nlp_diag_codes = [ent.code for ent in nlp_result.diagnoses if ent.code]
        nlp_proc_codes = [ent.code for ent in nlp_result.procedures if ent.code]
        matched = parser_diag in nlp_diag_codes if parser_diag else False

        stats["total"] += 1
        if parser_diag:
            stats["parser_diag_present"] += 1
        if nlp_diag_codes:
            stats["nlp_diag_present"] += 1
        if matched:
            stats["diag_match"] += 1

        records.append(
            EvaluationRecord(
                history_path=history_path,
                parser_diagnosis=parser_diag,
                parser_consultations=[c.code for c in parsed.consultations],
                nlp_diagnoses=nlp_diag_codes,
                nlp_procedures=nlp_proc_codes,
                matched_diagnosis=matched,
            )
        )

    return records, stats


def main() -> None:
    args = parse_args()

    records, stats = evaluate_histories(args)

    summary = {
        "total_histories": stats.get("total", 0),
        "parser_diag_present": stats.get("parser_diag_present", 0),
        "nlp_diag_present": stats.get("nlp_diag_present", 0),
        "diag_match": stats.get("diag_match", 0),
        "transformer_enabled": not args.disable_transformer,
    }

    # Prepare detailed records
    details = [
        {
            "history": str(record.history_path),
            "parser_diagnosis": record.parser_diagnosis,
            "parser_consultations": record.parser_consultations,
            "nlp_diagnoses": record.nlp_diagnoses,
            "nlp_procedures": record.nlp_procedures,
            "matched_diagnosis": record.matched_diagnosis,
        }
        for record in records
    ]

    output = {"summary": summary, "details": details}

    if args.output_json:
        args.output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] Reporte guardado en {args.output_json}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
