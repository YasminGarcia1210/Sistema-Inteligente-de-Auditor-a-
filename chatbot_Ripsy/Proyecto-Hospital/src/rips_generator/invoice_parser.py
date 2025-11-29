"""Parser de facturas PDF emitidas a EPS."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, List, Optional

from .models import InvoiceData, InvoiceLine
from .pdf_utils import extract_pdf_tables, extract_pdf_text


INVOICE_ID_PATTERN = re.compile(r"\bNo[.: ]+([A-Za-z0-9-]+)", flags=re.IGNORECASE)
DATE_PATTERNS = [
    ("%d/%m/%Y", re.compile(r"(\d{2}/\d{2}/\d{4})")),
    ("%d-%m-%Y", re.compile(r"(\d{2}-\d{2}-\d{4})")),
    ("%Y-%m-%d", re.compile(r"(\d{4}-\d{2}-\d{2})")),
    ("%d/%m/%y", re.compile(r"(\d{1,2}/\d{1,2}/\d{2})")),
]


@dataclass
class InvoiceParser:
    """Extrae datos relevantes de una factura PDF (formato FERO)."""

    path: Path

    def parse(self) -> InvoiceData:
        raw_text = extract_pdf_text(self.path)
        tables = extract_pdf_tables(self.path)
        text_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        invoice_id = self._extract_invoice_id(text_lines, raw_text)
        issue_date = self._extract_issue_date(raw_text)
        supplier_name = text_lines[0] if text_lines else None
        supplier_tax_id = self._extract_supplier_tax_id(text_lines)
        customer_name = self._extract_customer_name(text_lines)
        customer_tax_id = self._extract_customer_tax_id(text_lines)

        invoice_lines = self._extract_lines_from_tables(tables)
        total_amount = self._extract_total_amount(text_lines)
        if total_amount is None and invoice_lines:
            total_amount = sum((line.line_extension_amount or Decimal("0")) for line in invoice_lines)
        if total_amount is None:
            total_amount = Decimal("0")

        return InvoiceData(
            invoice_id=invoice_id or "",
            issue_date=issue_date,
            supplier_tax_id=supplier_tax_id,
            supplier_name=supplier_name,
            customer_tax_id=customer_tax_id,
            customer_name=customer_name,
            total_amount=total_amount,
            currency="COP",
            lines=invoice_lines,
        )

    def _extract_invoice_id(self, lines: List[str], full_text: str) -> Optional[str]:
        for line in lines:
            match = INVOICE_ID_PATTERN.search(line)
            if match:
                return match.group(1).strip()
        # Fallback: buscar códigos con prefijo FERO en todo el texto.
        fallback = re.search(r"\b(FE[A-Z]{1,3}[0-9]{3,})\b", full_text)
        if fallback:
            return fallback.group(1)
        return None

    def _extract_issue_date(self, text: str) -> datetime:
        for fmt, pattern in DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    return datetime.strptime(match.group(1), fmt)
                except ValueError:
                    continue
        raise ValueError(f"No se pudo determinar la fecha de la factura en {self.path}")

    @staticmethod
    def _extract_supplier_tax_id(lines: Iterable[str]) -> Optional[str]:
        for line in lines:
            if re.search(r"(?i)^nit[.: ]", line):
                match = re.search(r"([0-9]{3,}-[0-9])", line)
                if match:
                    return match.group(1)
        return None

    @staticmethod
    def _extract_customer_name(lines: List[str]) -> Optional[str]:
        for idx, line in enumerate(lines):
            if line.lower() == "cliente":
                for candidate in lines[idx + 1 : idx + 5]:
                    if candidate and candidate.lower() != "cliente":
                        return candidate
        return None

    @staticmethod
    def _extract_customer_tax_id(lines: List[str]) -> Optional[str]:
        for idx, line in enumerate(lines):
            if line.lower() == "cliente":
                for candidate in lines[idx + 1 : idx + 10]:
                    match = re.search(r"\bNIT[:. ]+([0-9-]+)", candidate, flags=re.IGNORECASE)
                    if match:
                        return match.group(1)
                break
        # Fallback al primer NIT en mayúsculas.
        for line in lines:
            match = re.search(r"\bNIT[:. ]+([0-9-]+)", line, flags=re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_lines_from_tables(self, tables: List[List[List[Optional[str]]]]) -> List[InvoiceLine]:
        invoice_lines: List[InvoiceLine] = []
        for table in tables:
            if not table or len(table) < 2:
                continue
            header = [cell.strip().lower() if cell else "" for cell in table[0]]
            if "codigo" not in header or "nombre" not in header:
                continue
            for row in table[1:]:
                if not row:
                    continue
                first_cell = (row[0] or "").strip()
                if not first_cell or first_cell.upper().startswith("SUBTOTAL"):
                    continue
                code = (row[1] or "").strip() or None
                description = self._clean_description(row[2])
                quantity = self._parse_decimal(row[5])
                unit_amount = self._parse_decimal(row[6])
                line_total = self._parse_decimal(row[7])
                if line_total == Decimal("0") and unit_amount and quantity:
                    line_total = unit_amount * quantity
                invoice_lines.append(
                    InvoiceLine(
                        line_id=first_cell,
                        cups_code=code,
                        description=description,
                        quantity=quantity or Decimal("0"),
                        price_amount=unit_amount,
                        line_extension_amount=line_total,
                    )
                )
        return invoice_lines

    def _extract_total_amount(self, lines: List[str]) -> Optional[Decimal]:
        total = self._extract_amount_after_label(lines, "Total")
        if total:
            return total
        total = self._extract_amount_after_label(lines, "Subtotal")
        return total

    def _extract_amount_after_label(self, lines: List[str], label: str) -> Optional[Decimal]:
        label_lower = label.lower()
        for idx, line in enumerate(lines):
            if not line.lower().startswith(label_lower):
                continue
            amount = self._find_amount_in_line(line)
            if amount is not None:
                return amount
            for candidate in lines[idx + 1 : idx + 4]:
                amount = self._find_amount_in_line(candidate)
                if amount is not None:
                    return amount
        return None

    def _find_amount_in_line(self, line: str) -> Optional[Decimal]:
        if not line:
            return None
        matches = re.findall(r"\$\s*[0-9.,]+", line)
        if not matches:
            return None
        last_match = matches[-1]
        return self._parse_decimal(last_match)

    @staticmethod
    def _clean_description(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return " ".join(value.split())

    @staticmethod
    def _parse_decimal(raw_value: Optional[str]) -> Decimal:
        if raw_value is None:
            return Decimal("0")
        value = raw_value.strip()
        if not value:
            return Decimal("0")
        value = value.replace("$", "").replace("COP", "").replace(" ", "")
        value = value.replace(",", ".")
        if value.count(".") > 1:
            parts = value.split(".")
            value = "".join(parts[:-1]) + "." + parts[-1]
        try:
            return Decimal(value)
        except InvalidOperation:
            digits = re.sub(r"[^0-9]", "", value)
            if not digits:
                return Decimal("0")
            if len(digits) <= 2:
                return Decimal(digits) / Decimal("100")
            return Decimal(digits[:-2] + "." + digits[-2:])
