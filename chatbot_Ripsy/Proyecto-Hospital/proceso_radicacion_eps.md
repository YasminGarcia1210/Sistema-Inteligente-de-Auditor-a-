# Proceso Integral de Radicación de Facturación a EPS

## 1. Panorama Documental y Fuentes Analizadas
- **Normativa sector salud** (`normativa/*.pdf`): procedimientos vigentes de facturación y radicación (GF-FC-PR-001/003), resoluciones 2275-2023, 2284-2023, 463-2024, lineamientos de RIPS y estudio de mejoramiento del proceso de facturación.
- **Evidencias operativas** (`05_Entradas_Evidencia/`):
  - **Tablas SQL** (`SQL_TABLES/*.csv`): detalle de facturación (`Table DetaFact 2025.csv`), liquidaciones (`Table_DetaLiqu.csv`) y admisiones (`Table_Admision.csv`).
  - **Facturas fuente** (`Facturas/FACTURAS/*/FERO*.pdf`): soportes clínicos y financieros organizados por servicio.
  - **Radicación FEV** (`FEV_JSON/FERO*/`): paquetes por factura con RIPS, XML DIAN y resultados de validación CUV, incluyendo notificaciones de inconsistencias (ej. códigos RVC019, RVC033).
  - **Auditoría clínica** (`auditoria/Historias_Clinicas/*`): historias clínicas asociadas.
  - **Plantillas de gestión**: mapeo RIPS ↔ tablas internas (`facturacion.xlsx`) y tablero de métricas (`KPIS PROPUESTOS.xlsx`).

## 2. Requisitos y Condicionantes Clave
- **Reglamentación**: las resoluciones 2275 y 2284 de 2023 definen el estándar RIPS de factura electrónica; la 463 de 2024 adopta guías clínicas que influyen en codificación; el procedimiento interno GF-FC-PR-003 exige radicar en ≤2 días hábiles con checklist documental.
- **Validaciones CUV**: los JSON reportan alertas sobre compatibilidad CUPS-CIE, finalidad del servicio y autorizaciones, que deben resolverse previo a radicar para evitar glosas RIPS.
- **Trazabilidad DIAN**: cada factura cuenta con XML y CUV, requiriendo control de versiones y evidencias de envío/acuse.
- **Auditoría clínica**: los PDF y historias evidencian necesidad de vincular soportes escaneados a cada servicio facturado.

## 3. Flujo Integral del Proceso de Radicación

### 3.1 Planeación y Alistamiento (Día -2 a 0)
1. **Recepción de servicios**: consolidar atenciones desde HIS en tablas `Admision` y `DetaFact`.
2. **Cierre de facturación**: generar factura electrónica (XML + PDF) y preparar datos financieros.
3. **Generación automatizada de RIPS**: orquestar creación de archivos AF/US/AC/AT/AP/AM/AH a partir de la factura (`Facturas/FACTURAS/*/FERO*.pdf` y XML DIAN), la historia clínica (`auditoria/Historias_Clinicas/*`) y anexos (órdenes, autorizaciones). Este proceso debe normalizar campos conforme a `facturacion.xlsx` y catálogos oficiales.
4. **Alistamiento documental**: anexar historias clínicas, órdenes, autorizaciones y soportes de medicamentos/insumos (vinculados automáticamente a cada registro RIPS).

### 3.2 Pre-Radicación (Día 0)
5. **Validación automatizada RIPS**: ejecutar motor de reglas (ver sección 4) sobre los archivos generados en el paso anterior, usando diccionarios DIAN/CUPS/CIE y resultados históricos CUV.
6. **Auditoría financiera**: conciliar valores con `DetaLiqu` y contratos (capitado/PGP/Evento), revisar copagos y descuentos.
7. **Auditoría clínica**: IA + revisores clínicos verifican pertinencia vs guías (Res. 463/2024) y completitud de notas en `Historias_Clinicas`, contrastando contra los RIPS generados.
8. **Checklist documental**: certificar cumplimiento del procedimiento GF-FC-PR-003 (señalar soportes faltantes).

### 3.3 Radicación (Día 0 a 1)
8. **Generación paquete EPS**: compilar factura XML/PDF, RIPS (AF, US, AC, AP, AH, AM, AT), soportes y acta de radicación.
9. **Entrega electrónica**: radicar por portal EPS o EDI; recolectar acuse y CUV; registrar en gestor documental.
10. **Registro en bitácora**: actualizar módulo de seguimiento con fecha/hora, usuario, EPS, número de radicado y SLA comprometido.

### 3.4 Post-Radicación y Seguimiento (Día 1 en adelante)
11. **Monitor de estados**: IA clasifica estatus (aceptada, glosa, devuelta) utilizando datos del portal EPS y correos.
12. **Gestión de glosas**: priorizar por severidad/valor; activar workflow clínico-financiero para respuesta dentro de plazos contractuales.
13. **Conciliación y cierre**: al aprobar EPS, conciliar giros vs `DetaLiqu`, emitir notas crédito/débito y actualizar contabilidad.

## 4. Controles, Responsables y Entregables

| Etapa | Responsable Primario | Control Clave | Evidencia |
| --- | --- | --- | --- |
| Recepción servicios | Coordinador HIS | Validación consistencia `Admision` ↔ `DetaFact` | Log ETL, reporte cruces |
| Validación RIPS | Analista facturación | Motor reglas (CUPS/CIE, autorizaciones) | Reporte inconsistencias, histórico CUV |
| Auditoría clínica | Enfermería auditoría | Checklist Res. 463/2024 | Acta revisión HC |
| Auditoría financiera | Líder contable | Conciliación vs contrato | Informe diferencia y ajustes |
| Radicación | Profesional cartera | Acuse EPS + CUV | Radicado digital |
| Seguimiento glosas | Gestor EPS | Matriz glosas (valor, causal, estado) | Tablero KPIs |
| Conciliación final | Tesorería | Cruce giros vs cuentas por cobrar | Estados financieros |

## 5. Solución Tecnológica Propuesta (con IA)

### 5.1 Arquitectura Conceptual
1. **Data Lake Operativo**: repositorio central (S3/Blob) con zonas *raw* (XML, PDF, JSON FEV, historias clínicas), *processed* (tablas `DetaFact`, `DetaLiqu`, `Admision` y RIPS generados) y *analytics* (mart para KPIs).
2. **Orquestación ETL**: flujos diarios (Apache Airflow / Prefect) que extraen del HIS/ERP y normalizan a esquema RIPS unificado; versionado en Parquet.
3. **Motor de Reglas y Calidad**:
   - Reglas determinísticas basadas en catálogo RIPS y contrato EPS.
   - Uso de resultados CUV (`ResultadosValidacion`) como retroalimentación para ajustar reglas.
4. **Generador automático de RIPS**:
   - Motor que combina datos financieros (XML/PDF factura) con clínicos (historias y anexos) usando mapeos de `facturacion.xlsx`.
   - Extracción de datos clínicos mediante OCR/NLP para poblar tablas AC/AT/AH, garantizando trazabilidad al soporte.
5. **Capa IA y Automatización**:
   - **LLM Jurídico-Operativo**: emplear modelo (ej. Llama 3 finetune local) con `normativa/*` embebida para responder consultas y validar cumplimiento documental paso a paso.
   - **IA de Auditoría Clínica**: modelo NLP que extrae diagnósticos, procedimientos y soportes de PDF `Historias_Clinicas`, comparando con RIPS para verificar coherencia (detección de faltantes).
   - **Clasificador de Glosas**: modelo supervisado que usa históricos de notificaciones CUV y respuestas EPS para predecir riesgo de glosa por factura y sugerir acciones preventivas.
   - **Agente RPA/Chatbot**: interfaz conversacional para el equipo de facturación, con capacidades de consultar estado, generar checklists y preparar respuestas a glosas.
5. **Gestor Documental y Workflow**: implementación en plataforma BPM (Camunda/Power Automate) enlazando checklists, radicación y seguimiento; integra firma digital y actas.
6. **Capa Analítica y KPIs**: dashboards (Power BI / Superset) con métricas de `KPIS PROPUESTOS.xlsx` más indicadores de oportunidad, glosa recurrente por EPS, recuperaciones, SLA de respuesta y eficiencia del auditor IA.

### 5.2 Integraciones Clave
- **HIS/ERP actual**: mediante vistas SQL (`SQL_TABLES`) y APIs para captar datos en tiempo real.
- **DIAN e EPS**: conectores para ingestión automática de acuses (correo, SFTP, API).
- **Repositorio Normativo**: embeddings semánticos para consultas de reglamentación y procedimientos internos.

## 6. Ruta de Implementación Recomendada
1. **Fase 0 – Gobierno de datos (2 semanas)**: clasificar documentos, definir catálogo de datos y retención, elaborar matriz RACI, adecuar seguridad.
2. **Fase 1 – Fundamentos (6 semanas)**: construir pipelines ETL, data lake, motor reglas básico, dashboard KPI mínimo viable.
3. **Fase 2 – IA Asistida (8 semanas)**: entrenar modelos de auditoría (extracción de soporte clínico, predicción glosa), integrar copiloto normativo, probar en paralelo con proceso actual.
4. **Fase 3 – Automatización total (6 semanas)**: desplegar workflow BPM, integrar RPA para portales EPS, activar seguimiento automático de glosas.
5. **Fase 4 – Mejora continua**: monitoreo de modelos, realimentación con nuevas resoluciones e indicadores.

## 7. KPIs Operativos
- `Valor total facturado`, `Valor glosado`, `% de glosa sobre facturación`, `Número de facturas radicadas`, `Ciclo promedio de radicación (días)`, `Tiempo respuesta glosa`, `Recuperación de cartera (%)`, `Alertas IA resueltas`, `Cumplimiento documentación (checklist)`.

## 8. Recomendaciones Adicionales
- Formalizar un **manual de juego** del proceso tomando como base GF-FC-PR-003 y la propuesta aquí descrita.
- Establecer **campañas de capacitación** para el equipo en codificación CUPS/CIE conforme a lineamientos actualizados.
- Implementar **firmas digitales y control de versiones** sobre paquetes entregados a EPS para trazabilidad legal.
- Mantener **evaluación periódica de modelos IA** asegurando explicabilidad y adecuación a normativa de datos personales (Ley 1581 de 2012).

---

# Ejecución de Próximos Pasos

## A. Validación del Flujo y Matriz RACI

### A.1 Paquete para Socialización
- **Documento base**: `proceso_radicacion_eps.md` (versión 1.0).
- **Extractos normativos**: anexar resumen ejecutivo (1 página) con obligaciones de Res. 2275/2284/463 y procedimientos GF-FC-PR-001/003.
- **Anexos operativos**: diagramas de flujo (BPMN) generados desde la sección 3 y tabla de controles.

### A.2 Agenda de Taller (2 horas)
1. Presentación de objetivos y alcance (10 min).
2. Revisión colaborativa del flujo propuesto (40 min).
3. Validación de responsabilidades por etapa (30 min).
4. Identificación de riesgos y brechas actuales (20 min).
5. Priorización de quick wins y aprobaciones (15 min).
6. Definición de compromisos y próximos hitos (5 min).

**Participantes clave**: Coordinador HIS, líder de facturación, auditor jefe, tesorería, jurídico, TI, representante de EPS (opcional).

### A.3 Matriz RACI Propuesta

| Actividad | Responsable (R) | Aprobador (A) | Consultado (C) | Informado (I) |
| --- | --- | --- | --- | --- |
| Generar extractos HIS → pre facturación | Coordinador HIS | Jefe de Sistemas | Facturación, Auditoría clínica | Dirección médica |
| Validar reglas RIPS/DIAN | Analista facturación | Líder facturación | TI, Auditoría clínica | Jurídico |
| Auditoría clínica soportes | Enfermería auditoría | Coordinador auditoría | Facturación | EPS |
| Auditoría financiera contratos | Líder contable | Gerencia financiera | Facturación, Tesorería | Auditoría interna |
| Compilar paquete radicación | Profesional cartera | Jefe facturación | Auditorías | EPS |
| Registrar radicado y SLA | Profesional cartera | Líder facturación | TI (workflow) | Dirección financiera |
| Seguimiento glosas | Gestor EPS | Líder facturación | Auditoría clínica | Gerencia |
| Conciliación giros | Tesorería | Gerencia financiera | Contabilidad | Facturación |

**Acciones inmediatas**:
- Recopilar feedback del taller y actualizar RACI en ≤3 días.
- Formalizar acta firmada y versionar el documento en gestor documental.

## B. Piloto de Validación RIPS + IA (Subconjunto FEV_JSON)

### B.1 Alcance
- **Factura universo piloto**: seleccionar 50 facturas recientes con notificaciones RVC (ej. `FEV_JSON/FERO941607`, `FERO941761`, `FERO948230`).
- **Objetivo**: reducir en ≥60% las notificaciones RVC antes de radicar y medir tiempo de revisión.

### B.2 Preparación de Datos
- Automatizar generación de RIPS piloto desde las facturas (XML/PDF), historias clínicas y anexos para construir archivos AF/US/AC/AT/AP/AM/AH con la estructura oficial.
- Extraer de los RIPS generados y de `FEV_JSON/*_Rips.json` / `*_CUV.json` campos clave: diagnósticos, CUPS, notificaciones, fechas de radicación.
- Vincular con `SQL_TABLES/Table DetaFact 2025.csv` y `Table_Admision.csv` para obtener contexto de paciente/procedimiento.
- Etiquetar estado actual (glosada/no glosada) si existe en registros históricos.

### B.3 Componentes del Piloto
1. **Motor reglas básico**: script Python con diccionarios CUPS-CIE-Finalidad y validaciones de autorización.
2. **IA auditoría clínica**: modelo NLP (ej. spaCy/transformer base) que compara texto de historias clínicas con códigos RIPS para detectar inconsistencias (se puede iniciar con 10 historias).
3. **Panel seguimiento**: dashboard simple (Power BI/Streamlit) mostrando notificaciones detectadas vs corregidas.
4. **Retroalimentación humana**: checklists digitales para capturar decisiones del auditor y alimentar dataset de entrenamiento.

### B.4 Métricas de Evaluación
- `# Notificaciones RVC iniciales` vs `post-corrección`.
- `Tiempo medio revisión` por factura.
- `Porcentaje facturas radicadas sin glosa inicial`.
- `Precisión sugerencias IA` (recomendaciones aceptadas / totales).

### B.5 Cronograma Piloto (4 semanas)
1. Semana 1: preparación datos y configuración entorno (repos Git, pipelines básicos).
2. Semana 2: desarrollo motor reglas + integración panel.
3. Semana 3: pruebas con equipo auditor y ajustes.
4. Semana 4: evaluación resultados, decisión de escalamiento.

## C. Requerimientos Técnicos Data Lake y Orquestación

### C.1 Infraestructura
- **Almacenamiento**: bucket cloud segregado por zonas (`raw/processed/analytics`), cifrado en reposo (AES-256) y tránsito (TLS 1.2).
- **Compute**: clúster de orquestación (Airflow/Prefect) con workers escalables; servidores para ejecución de modelos IA (GPU opcional para NLP).
- **Base de datos analítica**: warehouse (BigQuery/Snowflake/Redshift) o Lakehouse (Delta/Iceberg) según disponibilidad tecnológica.

### C.2 Seguridad y Cumplimiento
- Autenticación con SSO corporativo, roles por capas (mínimo privilegio).
- Cumplimiento Ley 1581/2012 y lineamientos de datos sensibles de salud (enmascaramiento, tokenización para ambientes de prueba).
- Auditoría y logging centralizados (SIEM) para accesos y cambios.

### C.3 Integraciones de Datos
- Conectores ETL a HIS/ERP (SQL Server/Oracle) vía vistas dedicadas y API REST donde aplique.
- Ingesta automatizada de archivos FEV (watcher sobre carpeta `FEV_JSON` y buzón DIAN/EPS).
- OCR/ingesta de soportes PDF con metadatos (historia clínica, laboratorio).
- Conector de correo/portal EPS para capturar glosas y estados.

### C.4 Pipeline de Datos Principales
1. **Landing**: copiar datos crudos (XML, JSON, CSV, PDF) y registrar metadatos.
2. **Normalización**: convertir RIPS a tablas Parquet estandarizadas (AF, US, AC, AP, AT, AM, AH).
3. **Generación RIPS**: construir archivos AF/US/AC/AT/AP/AM/AH desde factura + historia clínica + anexos, con diccionarios de mapeo y trazabilidad al soporte.
4. **Validación**: ejecutar reglas de calidad (campos obligatorios, dominios, consistencia cross-tablas) sobre los RIPS generados.
5. **Curación**: enriquecer con catálogos (EPS, contratos, códigos RIPS).
6. **Publicación**: exponer vistas en warehouse y API para dashboards y motor IA.

### C.5 Requerimientos de IA
- Repositorio de embeddings normativos (vector DB tipo FAISS/PGVector).
- Pipeline de entrenamiento con versionamiento de modelos (MLflow/DVC).
- Herramientas de evaluación continua (drift, bias) integradas al monitoreo.
- Integración con BPM/chatbot vía API segura.

### C.6 Gestión y DevOps
- IaC (Terraform/Ansible) para reproducibilidad.
- CI/CD con pruebas automatizadas de pipelines y validaciones de datos.
- Observabilidad: métricas de tareas ETL, latencia, SLAs, alertas on-call.

## D. Implementación Inicial Levantada

- Se creó el paquete `src/rips_generator/` con parsers para la factura UBL (`invoice_parser.py`) y la historia clínica HTML (`history_parser.py`), además del `RipsBuilder` que integra ambos insumos.
- El script `scripts/generate_rips.py` genera un JSON con registros RIPS (procedimientos) a partir de rutas de factura e historia, como primer MVP de la automatización solicitada.
- Se añadió `annex_parser.py` para aprovechar anexos FEV (`*_Rips.json`) y completar datos de identificación del paciente cuando no estén presentes en la historia; la CLI acepta `--annex-rips-json` para habilitar este cruce.
- Se extendió el builder para crear registros AF (factura), US (usuarios), AC (consultas), AM (medicamentos) y AT (otros servicios), y se incorporó `rips_exporter.py`, permitiendo producir archivos planos `AF.txt`, `US.txt`, `AP.txt`, `AC.txt`, `AM.txt` y `AT.txt` mediante la bandera `--output-dir` de la CLI.
- Se añadió `rips_validator.py` y se integró la evaluación automática de reglas (consistencia de documentos, conciliación de totales y diagnósticos) con reporte en consola y en el JSON resultante.
- Se documentaron oportunidades de IA para el flujo (extracción NLP, predictor de glosas, copiloto normativo, detección de anomalías y chatbot interno) en `docs/ia_oportunidades.md`.
- Se implementó el piloto `history_nlp.py` (extractor NLP + fallback heurístico) y los scripts `scripts/compare_history_nlp.py`, `scripts/evaluate_history_nlp.py` y `scripts/build_nlp_dataset.py` para comparar, evaluar y construir datasets de entrenamiento; además `scripts/generate_rips.py` permite incluir los hallazgos NLP en el JSON con `--include-nlp-details`.
- `README.md` documenta la ejecución y próximos pasos técnicos: mejorar mapeos normativos, soportar PDF/OCR y ampliar la salida a archivos AF/US/AC/AT/AP/AM/AH.
- Primera prueba (`FERO941607` + `ASVEN12045033`) produce dos registros AP con códigos CUPS 993520 y 993510; el tipo/número de documento se completa al suministrar el anexo RIPS, y se deja preparado para futuras integraciones con tablas HIS cuando no haya anexos disponibles.

---

<small>Última actualización: 2025-10-18</small>
