# Integración de IA en el Proceso de Radicación a EPS

Este documento resume las líneas de trabajo recomendadas para incorporar capacidades de inteligencia artificial sobre la solución actual de generación y validación de RIPS.

## 1. Enriquecimiento de Historias Clínicas
- **Extracción NLP**: Entrenar un modelo basado en spaCy/transformers para extraer diagnósticos, procedimientos, triage, autorizaciones y signos vitales desde historias HTML o PDF (con OCR). Complementa la lógica determinística de `HistoryParser`.
- **Pertinencia clínica**: Clasificador supervisado (glosa vs aceptado) usando decisiones históricas de auditoría para anticipar riesgos por falta de soporte clínico.

## 2. Validación Inteligente Previa a Radicación
- **Motor híbrido Reglas + ML**: Mantener reglas determinísticas (CUPS, totales, documentos) e incorporar un modelo predictivo de glosas por EPS que sugiere acciones preventivas.
- **Copiloto normativo**: Construir un buscador semántico sobre resoluciones y procedimientos internos (GF-FC-PR-001/003) usando embeddings y un LLM corporativo para responder consultas y explicar la base normativa.

## 3. Reconciliación de Identidades y Anexos
- **Record linkage automático**: Modelos de similitud (TF-IDF + clasificación o embeddings) para resolver discrepancias entre documento de historia, anexo FEV y tablas HIS, marcando casos que requieren revisión manual.
- **Detección de anomalías**: Isolation Forest/Autoencoders sobre RIPS consolidados para identificar valores atípicos (dx-procedimiento, fechas, montos) antes del envío.

## 4. Gestión de Glosas y Seguimiento Post-Radicación
- **Análisis de respuestas EPS**: Clasificador NLP que agrupe causales de glosa y genere borradores de respuesta aprovechando casos resueltos.
- **Chatbot interno**: Asistente conversacional alimentado con normativa, métricas y RIPS generados, capaz de guiar al equipo (“¿Qué registros se generaron para FERO943963?”) y destacar alertas.

## 5. KPIs y Mejora Continua
- **Predicción de recuperación de cartera**: Modelos de series de tiempo para anticipar flujos de caja con base en radicaciones, glosas y tiempos de respuesta.
- **Explainable AI**: Registrar métricas y explicaciones (SHAP/LIME) para cada recomendación IA, manteniendo cumplimiento con la Ley 1581 de 2012 y lineamientos de Superintendencia.

## Ruta Recomendada
1. **Piloto NLP** (extracción de diagnósticos/procedimientos) comparando modelo vs parser actual.
2. **Modelo predictor de glosa** usando históricos etiquetados por causal-EPS.
3. **Copiloto normativo** sobre normativa vigente para consultas del equipo.
4. **Integración en el pipeline**: añadir pasos opcionales `history_ai_enricher`, `compliance_ai_checker`, `glosa_predictor` tras la generación y validación de RIPS.

## Avances del Piloto NLP (2025-10-18)
- Se implementó `history_nlp.py` con un extractor híbrido (transformer opcional + heurísticas).
- Las utilidades `scripts/compare_history_nlp.py` y `scripts/evaluate_history_nlp.py` permiten comparar y medir la extracción vs. parser; el reporte de ejemplo (`piloto_nlp_evaluacion.json`) muestra que, sin modelo transformer, el heurístico detecta procedimientos pero solo identifica diagnósticos en 1 de 2 casos.
- `scripts/build_nlp_dataset.py` genera un dataset base (`nlp_dataset.json`) para anotación/finetuning, y `scripts/export_nlp_dataset_csv.py` facilita convertirlo en CSV para etiquetado manual.
- Próximos pasos recomendados:
  1. Anotar un conjunto mayor (≥50 historias) con diagnósticos/procedimientos correctos.
  2. Finetunear un modelo clínico en español (ClinicalBETO o variante local) usando ese dataset.
  3. Integrar el modelo ajustado al extractor y medir precisión/recall contra el parser determinístico.
