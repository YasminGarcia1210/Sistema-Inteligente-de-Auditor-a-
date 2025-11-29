"""Utilidades comunes para trabajar con documentos PDF."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pdfplumber


def extract_pdf_text(path: Path) -> str:
    """Devuelve el contenido textual del PDF concatenando todas las páginas."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    texts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            texts.append(page_text)
    return "\n".join(texts)


def extract_pdf_tables(path: Path) -> List[List[List[Optional[str]]]]:
    """Extrae las tablas identificadas por pdfplumber en cada página."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    tables: List[List[List[Optional[str]]]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                tables.append(table)
    return tables
