"""Parser de historias clínicas en PDF."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .models import ConsultationInfo, PatientInfo
from .pdf_utils import extract_pdf_text


DATE_FORMATS = ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%d/%m/%y %H:%M:%S")
JUST_DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d")
DOCUMENT_TYPES = ("CC", "TI", "RC", "CE", "PA", "NUIP", "MS")


@dataclass
class HistoryParser:
    """Extrae información clínica para construir registros RIPS desde un PDF."""

    path: Path

    def parse(self) -> PatientInfo:
        raw_text = extract_pdf_text(self.path)
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        normalized_text = "\n".join(lines)

        document_type, document_number = self._extract_document_info(normalized_text)
        full_name = self._extract_full_name(lines, normalized_text)

        admission_id = self._first_match(normalized_text, r"Atención:\s*([0-9A-Za-z-]+)")
        admission_datetime = self._extract_datetime(normalized_text, r"Fecha y Hora de Ingreso:\s*([0-9/: -]+)")
        discharge_datetime = self._extract_datetime(normalized_text, r"Cierre Historia\s*Fecha y Hora:\s*([0-9/: -]+)")
        service_type = self._first_match(normalized_text, r"Servicio de ingreso:\s*([A-Za-zÁÉÍÓÚÑ/ ]+)")
        entry_service = self._extract_entry_service(lines, service_type)

        diagnosis_code, diagnosis_text = self._extract_diagnosis(normalized_text)
        service_purpose = self._first_match(normalized_text, r"Finalidad:\s*([A-Za-zÁÉÍÓÚÑ ]+)")

        consultations = self._extract_consultations(normalized_text)

        return PatientInfo(
            document_type=document_type,
            document_number=document_number,
            full_name=full_name,
            admission_id=admission_id,
            admission_datetime=admission_datetime,
            discharge_datetime=discharge_datetime,
            service_type=service_type,
            entry_service=entry_service,
            principal_diagnosis=diagnosis_text,
            principal_diagnosis_code=diagnosis_code,
            service_purpose=service_purpose,
            triage_level=self._first_match(normalized_text, r"Triage\s*(I{1,3}|IV|V)"),
            consultations=consultations,
        )

    def _extract_document_info(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        match = re.search(r"Identificación:\s*([A-Z]{1,4})\s*-?\s*([0-9A-Za-z-]+)", text)
        if match:
            return match.group(1), match.group(2)
        top_match = re.search(r"\b(CC|TI|RC|CE|PA|NUIP|MS)\s*-?\s*([0-9A-Za-z-]{4,})\s*-\s*[A-Z]", text)
        if top_match:
            return top_match.group(1), top_match.group(2)
        generic = re.search(r"\b(CC|TI|RC|CE|PA|NUIP|MS)\s*-?\s*([0-9A-Za-z-]{4,})\b", text)
        if generic:
            return generic.group(1), generic.group(2)
        return None, None

    @staticmethod
    def _extract_full_name(lines: List[str], text: str) -> Optional[str]:
        match = re.search(r"Nombre:\s*([A-ZÁÉÍÓÚÑ0-9 .,'?-]+)", text)
        if match:
            return match.group(1).strip()
        for line in lines:
            for doc_type in DOCUMENT_TYPES:
                marker = f"{doc_type} "
                if line.startswith(marker) and " - " in line:
                    return line.split(" - ", 1)[1].strip()
        return None

    @staticmethod
    def _extract_entry_service(lines: List[str], fallback: Optional[str]) -> Optional[str]:
        for idx, line in enumerate(lines):
            if line.lower().startswith("cierre historia"):
                for candidate in lines[idx + 1 : idx + 5]:
                    if candidate and candidate.isupper():
                        return candidate
                break
        return fallback

    def _extract_diagnosis(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        code_match = re.search(r"DXP:\s*([A-Z0-9]{3,6})", text)
        diagnosis_code = code_match.group(1) if code_match else None

        diag_line = self._first_match(text, r"DX DIAGNOSTICOS:\s*([A-ZÁÉÍÓÚÑ0-9 ,./-]+)")
        if not diag_line:
            diag_line = self._first_match(text, r"Diagn[oó]stico(?: Principal)?:\s*([A-ZÁÉÍÓÚÑ0-9 ,./-]+)")

        return diagnosis_code, diag_line

    def _extract_consultations(self, text: str) -> List[ConsultationInfo]:
        consultations: List[ConsultationInfo] = []
        seen_keys = set()

        sections = re.split(r"•\s*", text)
        for raw_section in sections:
            section = raw_section.strip()
            if not section:
                continue
            section_datetime = self._extract_datetime(section, r"Fecha y Hora:\s*([0-9/: -]+)")
            purpose_text = self._first_match(section, r"Finalidad:\s*([A-Za-zÁÉÍÓÚÑ ]+)")
            authorization = self._first_match(section, r"Autorizaci[oó]n:\s*([A-Za-z0-9-]+)")

            for match in re.finditer(r"Tipo de Consulta:\s*\(([0-9A-Za-z]+)\)\s*([^\n]+)", section):
                code = match.group(1)
                description = match.group(2).strip()
                key = (code, section_datetime)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                consultations.append(
                    ConsultationInfo(
                        code=code,
                        description=description,
                        datetime=section_datetime,
                        purpose_text=purpose_text,
                        authorization_number=authorization,
                        diagnosis_type=None,
                    )
                )

            for match in re.finditer(r"Cod:\s*([A-Z0-9]+)\s+Nomb:\s*(.+?)(?:\s+Cant:|\s+DXP:|\s+DXR:|\s+Descripción:)", section, flags=re.DOTALL):
                code = match.group(1)
                description = " ".join(match.group(2).split())
                key = (code, section_datetime)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                consultations.append(
                    ConsultationInfo(
                        code=code,
                        description=description,
                        datetime=section_datetime,
                        purpose_text=purpose_text,
                        authorization_number=authorization,
                        diagnosis_type=None,
                    )
                )
        return consultations

    @staticmethod
    def _first_match(text: str, pattern: str) -> Optional[str]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return None
        group_index = 1 if match.lastindex else 0
        value = match.group(group_index).strip()
        return value or None

    @staticmethod
    def _extract_datetime(text: str, pattern: str) -> Optional[datetime]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return None
        candidate = match.group(1).strip()
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
        for fmt in JUST_DATE_FORMATS:
            try:
                date_obj = datetime.strptime(candidate.split()[0], fmt)
                return datetime.combine(date_obj.date(), datetime.min.time())
            except ValueError:
                continue
        return None
