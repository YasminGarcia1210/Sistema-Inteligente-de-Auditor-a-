#!/usr/bin/env python3
"""Genera RIPS para todas las facturas disponibles (FEV_JSON) en un solo lote."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Procesa en lote las facturas del directorio FEV_JSON.")
    parser.add_argument(
        "--fev-dir",
        type=Path,
        default=Path("05_Entradas_Evidencia/FEV_JSON"),
        help="Directorio que contiene los subdirectorios FERO*/ con los insumos FEV.",
    )
    parser.add_argument(
        "--histories-dir",
        type=Path,
        default=Path("05_Entradas_Evidencia/auditoria/Historias_Clinicas"),
        help="Directorio raíz con las historias clínicas en PDF.",
    )
    parser.add_argument(
        "--output-base",
        type=Path,
        default=Path("salidas/lote"),
        help="Directorio raíz donde se almacenarán los resultados por factura.",
    )
    parser.add_argument(
        "--include-nlp-details",
        action="store_true",
        help="Incluye resultados NLP en los JSON generados.",
    )
    return parser.parse_args()


def find_file(directory: Path, pattern_priority: List[str]) -> Optional[Path]:
    for pattern in pattern_priority:
        matches = list(directory.glob(pattern))
        if matches:
            return matches[0]
    return None


def find_pdf_folder(facturas_dir: Path, factura_id: str) -> Optional[Path]:
    pattern = f"**/{factura_id}"
    matches = list(facturas_dir.glob(pattern))
    if matches:
        return matches[0]
    return None


def find_invoice_pdf(pdf_folder: Optional[Path], fev_subdir: Path) -> Optional[Path]:
    if pdf_folder:
        preferred = pdf_folder / "FERO.pdf"
        if preferred.exists():
            return preferred
        candidates = list(pdf_folder.glob("FERO*.pdf"))
        if candidates:
            return candidates[0]
        fallback = list(pdf_folder.glob("*.pdf"))
        if fallback:
            return fallback[0]

    # Fallback: buscar dentro del propio paquete FEV (FDE o factura firmada)
    internal_patterns = ["FDE*.pdf", "FERO*.pdf"]
    for pattern in internal_patterns:
        matches = list(fev_subdir.glob(pattern))
        if matches:
            return matches[0]
    return None


def find_history_pdf(histories_dir: Path, document_number: Optional[str], fev_subdir: Path) -> Optional[Path]:
    # Preferimos la historia incluida en el paquete FEV (HEV...)
    hev_matches = list(fev_subdir.glob("HEV*.pdf"))
    if hev_matches:
        return hev_matches[0]

    if not document_number:
        return None
    pattern = f"**/*{document_number}*.pdf"
    matches = list(histories_dir.glob(pattern))
    if matches:
        return matches[0]
    return None


def collect_batch_entries(args: argparse.Namespace) -> List[Dict[str, Optional[str]]]:
    entries: List[Dict[str, Optional[str]]] = []
    facturas_root = args.fev_dir.parent / "Facturas" / "FACTURAS"

    for fev_subdir in sorted(args.fev_dir.glob("FERO*/")):
        annex_json = find_file(fev_subdir, ["*_Rips.json"])
        pdf_folder = find_pdf_folder(facturas_root, fev_subdir.name) if facturas_root.exists() else None
        invoice_pdf = find_invoice_pdf(pdf_folder, fev_subdir)

        if not invoice_pdf:
            entries.append(
                {
                    "factura": fev_subdir.name,
                    "invoice_pdf": None,
                    "annex_json": str(annex_json) if annex_json else None,
                    "history_pdf": None,
                    "status": "invoice_pdf_missing",
                    "pdf_folder": str(pdf_folder) if pdf_folder else None,
                    "message": "No se encontró la factura PDF asociada.",
                }
            )
            continue

        if not annex_json:
            entries.append(
                {
                    "factura": fev_subdir.name,
                    "invoice_pdf": str(invoice_pdf),
                    "annex_json": None,
                    "history_pdf": None,
                    "status": "annex_missing",
                    "pdf_folder": str(pdf_folder) if pdf_folder else None,
                    "message": "No se encontró el anexo RIPS (JSON) necesario para identificar al usuario.",
                }
            )
            continue

        try:
            data = json.loads(annex_json.read_text())
            users = data.get("usuarios") or []
            doc_number = users[0].get("numDocumentoIdentificacion") if users else None
        except Exception as exc:  # pragma: no cover
            entries.append(
                {
                    "factura": fev_subdir.name,
                    "invoice_pdf": str(invoice_pdf),
                    "annex_json": str(annex_json),
                    "history_pdf": None,
                    "status": "annex_read_error",
                    "pdf_folder": str(pdf_folder) if pdf_folder else None,
                    "message": f"Error leyendo anexo: {exc}",
                }
            )
            continue

        history_pdf = find_history_pdf(args.histories_dir, doc_number, fev_subdir)
        if history_pdf is None:
            entries.append(
                {
                    "factura": fev_subdir.name,
                    "invoice_pdf": str(invoice_pdf),
                    "annex_json": str(annex_json),
                    "history_pdf": None,
                    "status": "history_not_found",
                    "pdf_folder": str(pdf_folder) if pdf_folder else None,
                    "message": f"No se encontró historia PDF que contenga {doc_number}.",
                }
            )
            continue

        entries.append(
            {
                "factura": fev_subdir.name,
                "invoice_pdf": str(invoice_pdf),
                "annex_json": str(annex_json),
                "history_pdf": str(history_pdf),
                "status": "pending",
                "pdf_folder": None,
                "message": "",
            }
        )
    return entries


def run_generation(entry: Dict[str, Optional[str]], args: argparse.Namespace) -> Dict[str, Optional[str]]:
    factura = entry["factura"]
    invoice_pdf = entry["invoice_pdf"]
    history_pdf = entry["history_pdf"]
    annex_json = entry["annex_json"]

    output_dir = args.output_base / factura
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / f"{factura}_rips.json"

    cmd = [
        sys.executable,
        str(Path(__file__).parent / "generate_rips.py"),
        "--invoice-pdf",
        invoice_pdf,
        "--history-pdf",
        history_pdf,
    ]
    if annex_json:
        cmd.extend(["--annex-rips-json", annex_json])
    cmd.extend(
        [
            "--output-json",
            str(output_json),
            "--output-dir",
            str(output_dir),
        ]
    )
    if args.include_nlp_details:
        cmd.append("--include-nlp-details")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        entry.update(
            {
                "status": "completed",
                "message": result.stdout.strip(),
                "output_json": str(output_json),
                "output_dir": str(output_dir),
                "pdf_folder": entry.get("pdf_folder"),
            }
        )
    except subprocess.CalledProcessError as exc:
        entry.update(
            {
                "status": "error",
                "message": exc.stderr or exc.stdout or str(exc),
                "pdf_folder": entry.get("pdf_folder"),
            }
        )
    return entry


def main() -> None:
    args = parse_args()
    args.output_base.mkdir(parents=True, exist_ok=True)

    entries = collect_batch_entries(args)
    processed: List[Dict[str, Optional[str]]] = []
    for entry in entries:
        if entry["status"] == "pending":
            processed.append(run_generation(entry, args))
        else:
            processed.append(entry)

    summary_path = args.output_base / "batch_summary.json"
    summary_path.write_text(json.dumps(processed, ensure_ascii=False, indent=2), encoding="utf-8")

    totals = {
        "total": len(processed),
        "completed": sum(1 for e in processed if e["status"] == "completed"),
        "skipped": sum(1 for e in processed if e["status"] not in {"completed", "error"}),
        "errors": sum(1 for e in processed if e["status"] == "error"),
    }
    print(json.dumps(totals, indent=2, ensure_ascii=False))
    print(f"[OK] Resumen guardado en {summary_path}")


if __name__ == "__main__":
    main()
