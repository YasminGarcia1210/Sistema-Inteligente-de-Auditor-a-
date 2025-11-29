#!/usr/bin/env python3
"""Genera un dataset preliminar con diagnósticos/procedimientos extraídos (parser vs heurística NLP)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rips_generator import ClinicalEntityExtractor, HistoryParser  # noqa: E402
from rips_generator.history_nlp import TransformerConfig  # noqa: E402
from rips_generator.pdf_utils import extract_pdf_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construye un dataset de comparación (parser vs heurística NLP) para anotación.")
    parser.add_argument(
        "input_paths",
        nargs="+",
        help="Historias clínicas en PDF (acepta directorios y globs).",
    )
    parser.add_argument("--output-json", default="nlp_dataset.json", help="Archivo de salida (JSON).")
    parser.add_argument("--disable-transformer", action="store_true", help="Solo heurísticas; no intenta cargar modelos grandes.")
    return parser.parse_args()


def iter_histories(paths: Iterable[str]) -> Iterable[Path]:
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            yield from path.rglob("*.pdf")
        elif "*" in raw:
            yield from Path().glob(raw)
        else:
            yield path


def main() -> None:
    args = parse_args()
    config = TransformerConfig(enabled=not args.disable_transformer, local_files_only=True)
    extractor = ClinicalEntityExtractor(config=config)

    dataset: List[dict] = []

    for pdf_path in iter_histories(args.input_paths):
        try:
            parser = HistoryParser(pdf_path)
            parsed = parser.parse()
            text = extract_pdf_text(pdf_path)
            nlp_result = extractor.extract(text)
        except Exception as exc:
            dataset.append(
                {
                    "history": str(pdf_path),
                    "error": str(exc),
                }
            )
            continue

        dataset.append(
            {
                "history": str(pdf_path),
                "parser_principal_diagnosis": parsed.principal_diagnosis_code,
                "parser_consultations": [c.code for c in parsed.consultations],
                "nlp_diagnoses": [
                    {"code": ent.code, "text": ent.text, "score": ent.score, "label": ent.label}
                    for ent in nlp_result.diagnoses
                ],
                "nlp_procedures": [
                    {"code": ent.code, "text": ent.text, "score": ent.score, "label": ent.label}
                    for ent in nlp_result.procedures
                ],
            }
        )

    Path(args.output_json).write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Dataset generado con {len(dataset)} registros en {args.output_json}")


if __name__ == "__main__":
    main()
