"""Extractor clínico basado en NLP para historias clínicas."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

from .models import ClinicalEntity, ClinicalExtractionResult

LOGGER = logging.getLogger(__name__)

_TRANSFORMERS_AVAILABLE = importlib.util.find_spec("transformers") is not None

# Patrones básicos de respaldo
CIE_PATTERN = re.compile(r"\b([A-TV-Z][0-9]{2}(?:\.[0-9A-Z])?)\b")
CUPS_PATTERN = re.compile(r"\b([0-9]{4,7}(?:-[0-9])?)\b")
PROCEDURE_KEYWORDS = [
    "procedimiento",
    "sutura",
    "curación",
    "infiltración",
    "aplicación",
    "vacunación",
    "consulta",
    "terapia",
]


@dataclass
class TransformerConfig:
    """Configura el modelo HuggingFace a utilizar."""

    model_name: str = "PlanTL-GOB-ES/roberta-base-biomedical-es"
    aggregation_strategy: str = "simple"
    local_files_only: bool = False
    enabled: bool = True


class ClinicalEntityExtractor:
    """Realiza la extracción de diagnósticos/procedimientos usando un modelo base."""

    def __init__(self, config: Optional[TransformerConfig] = None) -> None:
        self.config = config or TransformerConfig()
        self.enabled = False
        self._pipeline = None

        if self.config.enabled and _TRANSFORMERS_AVAILABLE:
            try:
                transformers = importlib.import_module("transformers")
                AutoTokenizer = getattr(transformers, "AutoTokenizer")
                AutoModelForTokenClassification = getattr(transformers, "AutoModelForTokenClassification")
                pipeline_fn = getattr(transformers, "pipeline")

                tokenizer = AutoTokenizer.from_pretrained(
                    self.config.model_name,
                    local_files_only=self.config.local_files_only,
                )
                model = AutoModelForTokenClassification.from_pretrained(
                    self.config.model_name,
                    local_files_only=self.config.local_files_only,
                )
                self._pipeline = pipeline_fn(
                    "token-classification",
                    model=model,
                    tokenizer=tokenizer,
                    aggregation_strategy=self.config.aggregation_strategy,
                )
                self.enabled = True
                LOGGER.info("Extractor NLP inicializado con modelo %s", self.config.model_name)
            except Exception as exc:  # pragma: no cover - dependencias opcionales
                LOGGER.warning(
                    "No fue posible inicializar el modelo transformers (%s). "
                    "Se usará el extractor heurístico.",
                    exc,
                )

    def extract(self, text: str) -> ClinicalExtractionResult:
        if self.enabled and self._pipeline is not None:
            return self._extract_with_transformer(text)
        return self._extract_with_heuristics(text)

    # --------------------------------------------------------------------- #
    # Implementaciones
    # --------------------------------------------------------------------- #
    def _extract_with_transformer(self, text: str) -> ClinicalExtractionResult:
        """Utiliza el modelo HuggingFace para identificar entidades."""
        entities = self._pipeline(text)
        diagnoses: List[ClinicalEntity] = []
        procedures: List[ClinicalEntity] = []

        for ent in entities:
            label = ent.get("entity_group") or ent.get("entity") or ""
            value = ent.get("word") or ent.get("text") or ""
            score = float(ent.get("score", 0))

            if label.upper().startswith("DIAG"):
                diagnoses.append(ClinicalEntity(label=label, text=value, score=score, code=self._match_cie(value)))
            elif label.upper().startswith(("PRO", "PROC", "ACT")):
                procedures.append(ClinicalEntity(label=label, text=value, score=score, code=self._match_cups(value)))
            else:
                # Intentar clasificar por contenido si el modelo no distingue
                if self._match_cie(value):
                    diagnoses.append(ClinicalEntity(label=label or "DIAG", text=value, score=score, code=self._match_cie(value)))
                elif self._looks_like_procedure(value):
                    procedures.append(ClinicalEntity(label=label or "PROC", text=value, score=score, code=self._match_cups(value)))

        return ClinicalExtractionResult(diagnoses=diagnoses, procedures=procedures)

    def _extract_with_heuristics(self, text: str) -> ClinicalExtractionResult:
        """Fallback simple basado en expresiones regulares y palabras clave."""
        diagnoses: List[ClinicalEntity] = []
        procedures: List[ClinicalEntity] = []

        for code in set(CIE_PATTERN.findall(text)):
            diagnoses.append(ClinicalEntity(label="DIAG_HEURISTIC", text=code, code=code, score=None))

        for match in CUPS_PATTERN.finditer(text):
            code = match.group(1)
            context_window = text[max(0, match.start() - 80) : match.end() + 80]
            if self._looks_like_procedure(context_window):
                procedures.append(
                    ClinicalEntity(label="PROC_HEURISTIC", text=context_window.strip(), code=code, score=None)
                )

        return ClinicalExtractionResult(diagnoses=diagnoses, procedures=procedures)

    @staticmethod
    def _match_cie(text: str) -> Optional[str]:
        match = CIE_PATTERN.search(text)
        return match.group(1) if match else None

    @staticmethod
    def _match_cups(text: str) -> Optional[str]:
        match = CUPS_PATTERN.search(text)
        return match.group(1) if match else None

    @staticmethod
    def _looks_like_procedure(text: str) -> bool:
        lower_text = text.lower()
        return any(keyword in lower_text for keyword in PROCEDURE_KEYWORDS)
