# 🏥 Generador Automatizado de RIPS

## Mg Yasmin Johanna Garcia 
## Javier Ricardo Muñoz 

> **Transforma facturas y registros clínicos en archivos RIPS listos para radicación.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Prototipo-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## 📋 Descripción

Este proyecto es una solución integral diseñada para **automatizar la generación de Registros Individuales de Prestación de Servicios de Salud (RIPS)**. Utilizando técnicas avanzadas de procesamiento de documentos y **Procesamiento de Lenguaje Natural (NLP)**, el sistema extrae, valida y estructura información clave a partir de:

- 📄 **Facturas Electrónicas** (PDF/XML)
- 🩺 **Historias Clínicas** (PDF)

El objetivo principal es optimizar el flujo de radicación ante las EPS, minimizando errores manuales, reduciendo tiempos operativos y mitigando el riesgo de glosas.

---

## ✨ Características Principales

| Característica | Descripción |
| :--- | :--- |
| **🔄 Extracción Inteligente** | Parsea y estructura datos desde PDFs de facturas e historias clínicas no estructuradas. |
| **🤖 Potenciado por IA** | Integra modelos de NLP y heurísticas para identificar diagnósticos (CIE-10) y procedimientos (CUPS). |
| **✅ Validación Automática** | Verifica consistencia documental, reglas de negocio y cruces de valores antes de la radicación. |
| **📂 Generación RIPS** | Produce automáticamente los archivos planos requeridos: `AF`, `US`, `AP`, `AC`, `AM`, `AT`. |
| **📊 Auditoría y Logs** | Genera reportes detallados en JSON para trazabilidad y corrección de errores. |

---

## 🚀 Instalación

Sigue estos pasos para configurar el entorno de desarrollo:

### 1. Clonar el repositorio
```bash
git clone https://github.com/jarimso/Proyecto-Hospital.git
cd Proyecto-Hospital
```

### 2. Configurar entorno virtual
Se recomienda usar un entorno virtual para aislar las dependencias.

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
El proyecto utiliza `pyproject.toml` para la gestión de paquetes.
```bash
pip install -e .
# Para instalar dependencias de desarrollo (como pytest):
pip install -e .[dev]
```

---

## 🛠️ Uso

### 1. Generación de RIPS
Ejecuta el script principal para procesar una factura y su historia clínica asociada:

```bash
python scripts/generate_rips.py \
  --invoice-pdf "ruta/a/factura.pdf" \
  --history-pdf "ruta/a/historia.pdf" \
  --annex-rips-json "ruta/a/anexo.json" \
  --output-dir "salidas/RIPS" \
  --include-nlp-details
```

> **💡 Nota:** El argumento `--annex-rips-json` es opcional pero muy útil para enriquecer los datos demográficos del paciente que no siempre están en la historia clínica.

### 2. Herramientas de NLP
El proyecto incluye scripts para experimentar con la extracción de entidades clínicas:

- **Comparar extracción (Tradicional vs NLP):**
  ```bash
  python scripts/compare_history_nlp.py "ruta/historia.pdf" --local-files-only
  ```

- **Construir Dataset para entrenamiento:**
  ```bash
  python scripts/build_nlp_dataset.py "ruta/historias/*.pdf" --output-json dataset.json
  ```

---

## 🤖 Ripsy: Asistente Inteligente de Auditoría

> **Ubicación:** `chatbot_Ripsy/`

**Ripsy** es un chatbot especializado integrado en el proyecto para apoyar el proceso de auditoría y validación de facturas. Actúa como un copiloto inteligente que permite:

- **💬 Consultas Interactivas:** Resolver dudas sobre normatividad y procesos de facturación mediante un chat natural.
- **🔮 Predicción de Glosas:** Analizar la probabilidad de rechazo de una factura basándose en históricos y reglas de negocio (RVC033, RVC019, etc.).
- **📄 Análisis Documental:** Cruzar información entre la factura y la historia clínica para detectar inconsistencias.

### Tecnologías de Ripsy
- **Frontend:** Streamlit
- **Backend:** FastAPI + PostgreSQL
- **IA:** OpenAI GPT-4o / Llama 3 (Ollama)

Para más detalles sobre su configuración y uso, consulta su [documentación oficial](chatbot_Ripsy/README.md).

---

## 📂 Estructura del Proyecto

```plaintext
Proyecto-Hospital/
├── 📂 chatbot_Ripsy/         # 🤖 Sub-proyecto Ripsy (Chatbot de Auditoría)
├── 📂 docs/                  # Documentación técnica y oportunidades de IA
├── 📂 normativa/             # Base de conocimiento legal (Resoluciones RIPS)
├── 📂 scripts/               # Herramientas CLI y scripts de procesamiento
│   ├── generate_rips.py      # Script principal de generación
│   └── ... (scripts NLP)
├── 📂 src/                   # Código fuente del núcleo
│   ├── rips_generator/       # Módulos de lógica de negocio
│   │   ├── invoice_parser.py # Lector de facturas
│   │   ├── history_parser.py # Lector de historias clínicas
│   │   └── rips_builder.py   # Constructor de archivos RIPS
│   └── ...
├── 📂 salidas/               # Directorio de salida para archivos generados
└── 📄 proceso_radicacion_eps.md  # 📖 Guía detallada del flujo de negocio
```

---

## 🗺️ Hoja de Ruta (Roadmap)

- [ ] **Mejora de Mapeos**: Actualizar tablas de códigos según la normativa vigente más reciente.
- [ ] **Soporte Multiformato**: Afinar heurísticas para soportar más variaciones de diseños de historias clínicas.
- [ ] **Validación DIAN**: Integrar validaciones directas contra catálogos oficiales de la DIAN.
- [ ] **Predicción de Glosas**: Implementar modelos de ML para predecir probabilidad de rechazo.
- [ ] **Integración Total Ripsy**: Unificar el flujo de generación de RIPS con el asistente Ripsy.

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**. Consulta el archivo `LICENSE` para más información.

---

<div align="center">
  <sub>Construido con 💻 y ☕ para transformar la salud digital.</sub>
</div>
