#!/usr/bin/env python3
"""Convierte el dataset JSON (parser vs NLP) en un CSV listo para anotación manual."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convierte nlp_dataset.json en un CSV para anotación.")
    parser.add_argument("--input-json", default="nlp_dataset.json", help="Archivo JSON generado por build_nlp_dataset.py.")
    parser.add_argument("--output-csv", default="nlp_dataset.csv", help="Archivo CSV de salida para anotación.")
    return parser.parse_args()


def normalize_codes(entries: List[Dict[str, Any]]) -> str:
    unique = {entry.get("code") for entry in entries if entry.get("code")}
    return ";".join(sorted(unique)) if unique else ""


def main() -> None:
    args = parse_args()
    data = json.loads(Path(args.input_json).read_text())

    fieldnames = [
        "history",
        "parser_principal_diagnosis",
        "parser_consultations",
        "nlp_diagnoses",
        "nlp_procedures",
        "manual_diagnosis",
        "manual_procedures",
        "comments",
    ]

    with Path(args.output_csv).open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in data:
            writer.writerow(
                {
                    "history": record.get("history"),
                    "parser_principal_diagnosis": record.get("parser_principal_diagnosis"),
                    "parser_consultations": ";".join(record.get("parser_consultations") or []),
                    "nlp_diagnoses": normalize_codes(record.get("nlp_diagnoses") or []),
                    "nlp_procedures": normalize_codes(record.get("nlp_procedures") or []),
                    "manual_diagnosis": "",
                    "manual_procedures": "",
                    "comments": "",
                }
            )

    print(f"[OK] CSV de anotación generado en {args.output_csv}")


if __name__ == "__main__":
    main()
