# Generador Automatizado de RIPS

Este módulo implementa el primer prototipo para obtener archivos RIPS a partir de la factura electrónica y la historia clínica disponibles en formato PDF. Forma parte del plan de radicación descrito en `proceso_radicacion_eps.md`.

## Estructura

- `src/rips_generator/`: lógica de extracción y construcción de registros.
  - `invoice_parser.py`: interpreta las facturas PDF generadas para radicación.
  - `history_parser.py`: obtiene datos clínicos relevantes desde la historia PDF.
  - `rips_builder.py`: combina ambos insumos en registros de procedimientos (AP).
- `scripts/generate_rips.py`: CLI para generar un JSON con los registros RIPS creados.
- `scripts/compare_history_nlp.py`: compara la extracción tradicional vs. el prototipo NLP sobre una historia.
- `scripts/evaluate_history_nlp.py`: evalúa varias historias y genera métricas básicas del piloto.
- `scripts/build_nlp_dataset.py`: construye un dataset preliminar (parser vs heurística) para anotación o futuros entrenamientos.
- `scripts/export_nlp_dataset_csv.py`: transforma el dataset JSON en un CSV con columnas para anotación manual.
- `scripts/batch_generate_rips.py`: procesa todas las facturas disponibles (FEV_JSON) y genera sus archivos RIPS, dejando un resumen de pendientes.
- `rips_exporter.py`: utilidades para emitir los archivos planos AF/US/AP/AC/AM/AT.
- `rips_validator.py`: reglas básicas de validación sobre los registros generados.
- `docs/ia_oportunidades.md`: propuestas de integración de IA sobre el flujo de radicación.

## Uso

```bash
python3 scripts/generate_rips.py \
  --invoice-pdf 05_Entradas_Evidencia/Facturas/FACTURAS/CONSULTAS/FERO866135/FERO.pdf \
  --history-pdf 05_Entradas_Evidencia/auditoria/Historias_Clinicas/RC1232835680/RC1232835680.pdf \
  --annex-rips-json 05_Entradas_Evidencia/FEV_JSON/FERO941607/FERO941607_Rips.json \
  --output-dir salidas/RIPS \
  --output-json salidas/FERO941607_rips.json \
  --include-nlp-details
```

> **Nota:**
> - El parámetro `--annex-rips-json` es opcional y permite utilizar los anexos RIPS del paquete FEV para completar datos faltantes (tipo y número de documento, nombre, sexo, municipio, etc.).
> - Si se suministra `--output-dir`, el script generará archivos planos `AF.txt`, `US.txt`, `AP.txt`, `AC.txt`, `AM.txt` y `AT.txt` listos para su carga en los portales EPS.
> - Cuando no se proporcione el anexo, el builder utilizará únicamente lo extraído de la historia clínica, dejando valores vacíos para enriquecerlos en pasos posteriores (ej. cruces con tablas HIS).
> - Con `--include-nlp-details` el JSON incluirá la extracción heurística/NLP de diagnósticos y procedimientos detectados en la historia.

### Validación automática

Durante la ejecución se evalúan reglas sencillas:

- Consistencia del tipo y número de documento entre todos los archivos RIPS.
- Conciliación de valores: si existen registros AP se usan como fuente del total (los demás archivos se consideran complementarios para evitar doble conteo).
- Presencia de diagnósticos principales y códigos CUPS.

Los resultados se incluyen en el JSON (`validation_messages`) y en la salida estándar, mostrando la cantidad de errores/advertencias detectadas.

## Integración con IA

Las líneas de trabajo sugeridas para incorporar IA (extracción NLP, predicción de glosas, copiloto normativo, detección de anomalías y chatbot interno) están documentadas en `docs/ia_oportunidades.md`.

### Piloto NLP

El módulo `history_nlp.py` incluye el extractor `ClinicalEntityExtractor`, que intenta usar un modelo HuggingFace (por defecto `PlanTL-GOB-ES/roberta-base-biomedical-es`) y, en caso de no estar disponible, recurre a heurísticas basadas en expresiones regulares. `HistoryParser` utiliza este extractor como **fallback** cuando la historia no trae diagnóstico principal.

Ejemplo de comparación contra el parser tradicional:

```bash
python3 scripts/compare_history_nlp.py \
  05_Entradas_Evidencia/auditoria/Historias_Clinicas/ASVEN12045033/ASVEN12045033.pdf \
  --output-json comparacion_nlp.json --local-files-only --disable-transformer
```

Evaluación heurística sobre un conjunto de historias:

```bash
python3 scripts/evaluate_history_nlp.py \
  05_Entradas_Evidencia/auditoria/Historias_Clinicas/ASVEN12045033/ASVEN12045033.pdf \
  05_Entradas_Evidencia/auditoria/Historias_Clinicas/TI1111689275/TI1111689275.pdf \
  --output-json piloto_nlp_evaluacion.json --disable-transformer
```

Generación de dataset para anotación/finetuning:

```bash
python3 scripts/build_nlp_dataset.py \
  '05_Entradas_Evidencia/auditoria/Historias_Clinicas/*/*.pdf' \
  --output-json nlp_dataset.json --disable-transformer

python3 scripts/export_nlp_dataset_csv.py \
  --input-json nlp_dataset.json --output-csv nlp_dataset.csv
```

Procesamiento masivo:

```bash
python3 scripts/batch_generate_rips.py \
  --fev-dir 05_Entradas_Evidencia/FEV_JSON \
  --histories-dir 05_Entradas_Evidencia/auditoria/Historias_Clinicas \
  --output-base salidas/lote \
  --include-nlp-details
```

El resumen queda en `salidas/lote/batch_summary.json`, incluyendo facturas procesadas y pendientes por falta de factura PDF, anexo RIPS o historia clínica.

## Próximos pasos

1. Ajustar los mapeos de códigos (vía de ingreso, finalidad, modalidades) según la normativa RIPS vigente.
2. Afinar las heurísticas de extracción sobre los distintos formatos de factura e historia PDF (urgencias, laboratorio, hospitalización).
3. Extender la exportación a los restantes archivos RIPS (AT/AM/AH) conforme a las especificaciones oficiales.
4. Integrar la validación automática frente a los catálogos DIAN y los hallazgos CUV.
