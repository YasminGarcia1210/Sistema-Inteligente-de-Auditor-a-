"""Parsers para anexos que complementan la información del paciente y servicios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from .models import (
    AnnexData,
    AnnexMedicationEntry,
    AnnexOtherServiceEntry,
    AnnexPatientInfo,
)


@dataclass
class RipsJsonAnnexParser:
    """Extrae datos del paciente desde el JSON de RIPS generado por FEV."""

    path: Path

    def parse(self) -> AnnexData:
        data = json.loads(self.path.read_text(encoding="utf-8"))

        usuarios = data.get("usuarios") or []
        if not usuarios:
            empty_patient = AnnexPatientInfo(document_type=None, document_number=None, full_name=None)
            return AnnexData(patient=empty_patient)

        # Para este MVP tomamos el primer usuario. Se podría cruzar por factura si viene.
        usuario = usuarios[0]
        doc_type = usuario.get("tipoDocumentoIdentificacion")
        doc_number = usuario.get("numDocumentoIdentificacion")
        full_name = usuario.get("nombreUsuario")
        gender = usuario.get("codSexo")
        birth_date = self._parse_date(usuario.get("fechaNacimiento"))
        municipality_code = usuario.get("codMunicipioResidencia")
        residence_zone = usuario.get("codZonaTerritorialResidencia")

        # Normalizar si vienen cadenas vacías.
        doc_type = doc_type or None
        doc_number = doc_number or None
        full_name = full_name or None
        gender = gender or None
        municipality_code = municipality_code or None
        residence_zone = residence_zone or None

        patient = AnnexPatientInfo(
            document_type=doc_type,
            document_number=doc_number,
            full_name=full_name,
            gender=gender,
            birth_date=birth_date,
            municipality_code=municipality_code,
            residence_zone=residence_zone,
        )

        servicios = usuario.get("servicios", {})
        medications = [self._parse_medication(item) for item in servicios.get("medicamentos", [])]
        other_services = [self._parse_other_service(item) for item in servicios.get("otrosServicios", [])]

        return AnnexData(patient=patient, medications=medications, other_services=other_services)

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        value = value.replace("/", "-")
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ"):
            try:
                return datetime.strptime(value[: len(fmt)], fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        value_str = str(value).replace(",", "")
        try:
            return Decimal(value_str)
        except Exception:
            return Decimal("0")

    def _parse_medication(self, item: dict) -> AnnexMedicationEntry:
        return AnnexMedicationEntry(
            provider_code=item.get("codPrestador", ""),
            document_type=item.get("tipoDocumentoIdentificacion"),
            document_number=item.get("numDocumentoIdentificacion"),
            authorization_number=item.get("numAutorizacion"),
            medication_code=item.get("codTecnologiaSalud", ""),
            medication_name=item.get("nomTecnologiaSalud"),
            medication_type=item.get("tipoMedicamento"),
            unit_value=self._parse_decimal(item.get("vrUnitMedicamento")),
            total_value=self._parse_decimal(item.get("vrServicio")),
            quantity=self._parse_decimal(item.get("cantidadMedicamento")),
            unit_measure=str(item.get("unidadMinDispensa")) if item.get("unidadMinDispensa") is not None else None,
            treatment_days=item.get("diasTratamiento"),
            diagnosis_code=item.get("codDiagnosticoPrincipal"),
            related_diagnosis=item.get("codDiagnosticoRelacionado"),
            mipres_id=item.get("idMIPRES"),
            administration_date=self._parse_date(item.get("fechaDispensAdmon")),
            pharmaceutical_form=item.get("formaFarmaceutica"),
            concentration=str(item.get("concentracionMedicamento")) if item.get("concentracionMedicamento") is not None else None,
        )

    def _parse_other_service(self, item: dict) -> AnnexOtherServiceEntry:
        return AnnexOtherServiceEntry(
            provider_code=item.get("codPrestador", ""),
            document_type=item.get("tipoDocumentoIdentificacion"),
            document_number=item.get("numDocumentoIdentificacion"),
            authorization_number=item.get("numAutorizacion"),
            service_code=item.get("codTecnologiaSalud", ""),
            service_name=item.get("nomTecnologiaSalud"),
            service_type=item.get("tipoOS"),
            service_date=self._parse_date(item.get("fechaSuministroTecnologia")),
            unit_value=self._parse_decimal(item.get("vrUnitOS")),
            total_value=self._parse_decimal(item.get("vrServicio")),
            quantity=self._parse_decimal(item.get("cantidadOS")),
            diagnosis_code=item.get("codDiagnosticoPrincipal"),
            related_diagnosis=item.get("codDiagnosticoRelacionado"),
            mipres_id=item.get("idMIPRES"),
        )
