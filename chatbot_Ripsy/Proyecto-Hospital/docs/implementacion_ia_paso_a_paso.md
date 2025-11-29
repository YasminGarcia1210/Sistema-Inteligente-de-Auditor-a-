# Plan Paso a Paso para la Implementación de IA en el Generador de RIPS

Este documento detalla el flujo actual del proyecto, identifica los puntos de integración con inteligencia artificial y propone un plan iterativo para desplegar las capacidades de IA que acompañan al pipeline de radicación.

## 1. Flujo Operativo Actual

1. **Insumos principales**
   - Facturas en PDF (`FERO*.pdf`) almacenadas en `05_Entradas_Evidencia/Facturas/FACTURAS/...`.
   - Historias clínicas en PDF (`<documento>.pdf`) dentro de `05_Entradas_Evidencia/auditoria/Historias_Clinicas/...`.
   - Anexos RIPS en JSON (`*_Rips.json`) provistos por FEV.

2. **Extracción de factura (`src/rips_generator/invoice_parser.py`)**
   - Utiliza `pdfplumber` para leer texto y tablas.
   - Reconstruye identificadores, totales y líneas con códigos CUPS/costos.

3. **Extracción de historia (`src/rips_generator/history_parser.py`)**
   - Convierte el PDF en texto plano y obtiene documento, fechas de ingreso/egreso, diagnósticos y consultas.
   - Genera una lista de `ConsultationInfo` asociando códigos con fechas y propósitos.

4. **Anexos y enriquecimiento (`src/rips_generator/annex_parser.py`)**
   - Normaliza datos de usuario (tipo/numero de documento, sexo, municipio) y medicamentos/otros servicios.

5. **Construcción de RIPS (`src/rips_generator/rips_builder.py`)**
   - Combina factura + historia + anexo para producir registros AP, AC, AM, AT, AF y US.

6. **Validación y exportación**
   - `validate_rips` aplica reglas de consistencia (documentos, totales, diagnósticos).
   - `rips_exporter` escribe archivos planos si se solicita `--output-dir`.

7. **Automatización en scripts**
   - `scripts/generate_rips.py` orquesta el flujo para un caso.
   - `scripts/batch_generate_rips.py` procesa todas las facturas detectadas y crea `batch_summary.json`.

## 2. Componentes de IA ya disponibles

| Componente | Ubicación | Propósito |
|------------|-----------|-----------|
| Extractor híbrido de entidades clínicas | `src/rips_generator/history_nlp.py` | Detectar diagnósticos y procedimientos desde texto clínico con heurísticas y/o transformer. |
| Comparador parser vs NLP | `scripts/compare_history_nlp.py` | Analizar un caso y contrastar resultados determinísticos vs IA. |
| Evaluación masiva | `scripts/evaluate_history_nlp.py` | Medir métricas básicas sobre varias historias en PDF. |
| Generación de dataset | `scripts/build_nlp_dataset.py` + `scripts/export_nlp_dataset_csv.py` | Crear insumos anotables para finetuning. |
| Documentación estratégica | `docs/ia_oportunidades.md` | Visión de líneas IA (validación inteligente, copiloto normativo, etc.). |

## 3. Plan Paso a Paso

### Etapa 0 – Preparación de Datos
1. Consolidar los insumos PDF y JSON en las rutas estándar del proyecto.
2. Ejecutar `scripts/build_nlp_dataset.py '.../*.pdf'` para producir `nlp_dataset.json`.
3. Exportar a CSV (`scripts/export_nlp_dataset_csv.py`) y coordinar anotación manual (diagnóstico y procedimiento verdaderos).

### Etapa 1 – Piloto NLP
1. Ajustar anotaciones y validar consistencia (mínimo 50 historias).
2. Entrenar un modelo específico (ej. `PlanTL-GOB-ES/roberta-base-biomedical-es`) con el dataset anotado.
3. Integrar el modelo entrenado en `history_nlp.py` configurando `TransformerConfig(model_path_local, enabled=True)`.
4. Medir desempeño frente al parser determinístico con `scripts/evaluate_history_nlp.py`.

### Etapa 2 – Integración en el Pipeline
1. Activar la bandera `--include-nlp-details` en `scripts/generate_rips.py` para incluir resultados IA en el JSON.
2. Crear un módulo `history_ai_enricher` (propuesto en `docs/ia_oportunidades.md`) que:
   - Rellene diagnóstico principal cuando falte.
   - Marque discrepancias entre parser e IA para revisión.
3. Incorporar la verificación IA como paso opcional en `scripts/batch_generate_rips.py` (marcar en `batch_summary.json`).

### Etapa 3 – Validación Inteligente y Decisiones
1. Recolectar histórico de glosas/aceptaciones y etiquetar por causal.
2. Diseñar un pipeline `glosa_predictor`:
   - Features: diagnósticos/procedimientos, totales, alertas IA.
   - Modelo inicial: árbol de decisión o gradient boosting.
3. Integrar el predictor previo al envío:
   - Registrar riesgo y recomendaciones (`validation_messages`).
   - Automatizar tareas correctivas (ej. solicitar anexos faltantes).

### Etapa 4 – Copiloto Normativo y Automatizaciones
1. Indexar normativa (PDFs en `normativa/`) usando embeddings.
2. Construir servicio QA interno (puede ser un microservicio o script) para responder preguntas sobre normas.
3. Conectar métricas de radicación, glosas y predictor de recuperación de cartera para dashboards operativos.

## 4. Cómo Ejecutar las Herramientas IA

1. **Comparar extracción determinística vs IA**
   ```bash
   python3 scripts/compare_history_nlp.py \
     05_Entradas_Evidencia/auditoria/Historias_Clinicas/RC1232835680/RC1232835680.pdf \
     --output-json comparacion_nlp.json --disable-transformer
   ```
2. **Evaluar un conjunto**
   ```bash
   python3 scripts/evaluate_history_nlp.py \
     05_Entradas_Evidencia/auditoria/Historias_Clinicas/*/*.pdf \
     --output-json piloto_nlp_evaluacion.json --disable-transformer
   ```
3. **Generar dataset para anotación**
   ```bash
   python3 scripts/build_nlp_dataset.py \
     '05_Entradas_Evidencia/auditoria/Historias_Clinicas/*/*.pdf' \
     --output-json nlp_dataset.json --disable-transformer
   python3 scripts/export_nlp_dataset_csv.py \
     --input-json nlp_dataset.json --output-csv nlp_dataset.csv
   ```
4. **Pipeline completo con resultados IA**
   ```bash
   python3 scripts/generate_rips.py \
     --invoice-pdf 05_Entradas_Evidencia/Facturas/FACTURAS/CONSULTAS/FERO866135/FERO.pdf \
     --history-pdf 05_Entradas_Evidencia/auditoria/Historias_Clinicas/RC1232835680/RC1232835680.pdf \
     --annex-rips-json 05_Entradas_Evidencia/FEV_JSON/FERO866135/FERO866135_Rips.json \
     --output-json salidas/FERO866135_rips.json \
     --include-nlp-details
   ```

## 5. Buenas Prácticas y Gobernanza

- **Versionado de modelos:** etiquetar cada versión de modelo IA y documentar el dataset usado para entrenamiento.
- **Trazabilidad:** conservar los reportes JSON (`comparacion_nlp.json`, `piloto_nlp_evaluacion.json`) como evidencia.
- **Comité de revisión:** evaluar alertas IA antes de automatizar correcciones; mantener bitácora en `salidas/lote/batch_summary.json`.
- **Protección de datos:** cumplir Ley 1581/2012 asegurando que datasets anotados se anonimicen si se comparten externamente.
- **Métricas clave:** precisión/recall de diagnósticos IA, reducción de glosas, tiempo de radicación, monto recuperado.

## 6. Próximos Pasos Inmediatos

1. Recolectar y anotar historias adicionales para robustecer el dataset.
2. Documentar casos donde la IA mejora o contradice al parser para priorizar reglas que deben ajustarse.
3. Prototipar el `glosa_predictor` con datos históricos (cuando estén disponibles).
4. Diseñar panel de indicadores que combine métricas de IA y del pipeline determinístico.

Con esta ruta, la organización contará con un flujo completamente automatizado y enriquecido por IA, manteniendo trazabilidad y control en cada etapa del proceso de radicación a EPS.
