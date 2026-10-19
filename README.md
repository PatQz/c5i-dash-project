# 📊 Dashboard de Llamadas de Emergencia (C5i Sonora)

Prototipo analítico y arquitectura basada en microservicios contenerizados para el procesamiento, almacenamiento masivo y visualización interactiva de más de 500,000 registros unificados de llamadas de emergencia (tanto **procedentes** como **improcedentes**) del 9-1-1 correspondientes al primer semestre de 2026.

---

## 1. Problemática o Necesidad del Proyecto
El C5i (Centro de Control, Comando, Comunicación, Cómputo, Coordinación e Inteligencia) de Sonora centraliza un volumen masivo de llamadas operativas. El proyecto busca procesar, almacenar y analizar más de **500,000 registros** del primer semestre de 2026 —incluyendo llamadas procedentes y de mal uso o improcedentes— para identificar tendencias de incidentes, evaluar el nivel de saturación de las líneas y facilitar la toma de decisiones estratégicas y de concientización ciudadana.

---

## 2. API Seleccionada y Tipo de Información
* **Selección:** Una **Mock API personalizada** desarrollada a la medida utilizando **FastAPI**.
* **Información Proporcionada:** Actúa como una capa intermedia desacoplada que expone endpoints RESTful orientados a consultar la base de datos central en tiempo real. Proporciona catálogos dinámicos (`/api/clasificaciones`, `/api/municipios`) y un endpoint analítico (`/api/resumen-diario`) que filtra y agrupa los incidentes por fecha, municipio y clasificación para alimentar de forma dinámica el frontend.

---

## 3. Arquitectura de la Solución y Función de los Contenedores
El proyecto está completamente containerizado utilizando **Docker Compose**, implementando una arquitectura de microservicios distribuida en 3 contenedores interconectados:
1. **Contenedor Base de Datos (`postgres_db` - PostgreSQL 15):** Es el corazón del almacenamiento. Contiene la tabla relacional unificada con los más de 500,000 registros respaldados mediante un volumen persistente (`pgdata`), garantizando integridad y alta velocidad de consulta.
2. **Contenedor API (`container_api_ubuntu` - FastAPI):** Aloja la lógica de negocio y se conecta en tiempo real a PostgreSQL mediante SQLAlchemy para procesar las peticiones y entregar los datos en formato JSON optimizado.
3. **Contenedor Frontend (`container_python_dash` - Python Dash & Plotly):** La aplicación web interactiva que se comunica mediante peticiones HTTP con la API para renderizar dinámicamente los menús desplegables, el selector de tipo de llamada, el rango de fechas y las visualizaciones especializadas interactivas.

### Diagrama de Funcionamiento

```mermaid
flowchart LR
    subgraph Fuentes["Fuentes externas"]
        PORTAL["Portal de Datos Abiertos<br/>de Sonora (Excel)"]
        GEO["PhantomInsights<br/>GeoJSON de municipios"]
    end

    subgraph ETL["ETL local: make etl"]
        DESC["descargar_datos.py<br/>Extracción"]
        DATOS[("datos/<br/>caché local")]
        CARGA["carga_datos.py<br/>Transformación y carga"]
    end

    subgraph Docker["Docker Compose"]
        DB[("PostgreSQL 15<br/>postgres_db :5432")]
        API["API FastAPI<br/>container_api_ubuntu :8000"]
        DASH["Dashboard Dash / Plotly<br/>container_python_dash :8050"]
    end

    USER(["Usuario<br/>navegador web"])

    PORTAL --> DESC
    GEO --> DESC
    DESC --> DATOS
    DATOS --> CARGA
    CARGA -->|"SQL - localhost:5432"| DB
    DB -->|"Consultas SQL"| API
    DATOS -.->|"Volumen ./datos<br/>GeoJSON"| API
    API -->|"JSON vía HTTP"| DASH
    USER -->|"localhost:8050"| DASH
```

**Flujo general:**
1. **Extracción:** `descargar_datos.py` descarga los archivos Excel del portal de Sonora y el GeoJSON de municipios hacia `datos/` (solo los que falten).
2. **Transformación y carga:** `carga_datos.py` limpia los datos y los carga en PostgreSQL. `pipeline.py` ejecuta ambos pasos en orden (`make etl`).
3. **Servicio:** La API (FastAPI) consulta PostgreSQL y lee el GeoJSON desde el volumen compartido `./datos`.
4. **Visualización:** El dashboard (Dash) consume la API por HTTP y el usuario lo abre en `http://localhost:8050`.

---

## 4. Fuentes de Datos y Consideraciones Temporales
Los conjuntos de datos utilizados para alimentar este prototipo provienen de fuentes oficiales abiertas y repositorios geoespaciales normalizados:
* **Llamadas Procedentes 911:** [Portal de Datos Abiertos de Sonora (Llamadas Procedentes 911)](https://datos.sonora.gob.mx/dataset/Llamadas%20Procedentes%20911)
* **Llamadas Improcedentes 911:** [Portal de Datos Abiertos de Sonora (Llamadas Improcedentes 911)](https://datos.sonora.gob.mx/dataset/Llamadas%20Improcedentes%20911)
* **Geometría de Municipios:** [Repositorio PhantomInsights México GeoJSON (Sonora)](https://github.com/PhantomInsights/mexico-geojson/blob/main/2023/states/Sonora.json)

> **Nota importante sobre los datos:** Actualmente, el sistema cuenta únicamente con información de **llamadas improcedentes correspondientes al segundo trimestre de 2026**, debido a que los registros del primer trimestre de dicho rubro presentaron inconsistencias en su estructura. Quedan pendientes de integración los trimestres restantes del 2026 conforme se valide la integridad oficial de los mismos.

---

## 5. Diseño de la Base de Datos y Normalización
* **Motor:** **PostgreSQL**, elegido por su robustez, rendimiento en consultas analíticas y capacidad probada para manejar grandes volúmenes de datos relacionales sin degradación.
* **Estructura de la tabla de llamadas procedentes (`llamadas_c5i_procedentes`):**
  * `id`: Clave primaria autoincremental (`SERIAL PRIMARY KEY`).
  * `fecha`: Tipo `DATE` para permitir filtros cronológicos y agrupaciones temporales precisas día a día.
  * `hora`: Tipo `INTEGER` para registrar el momento del incidente.
  * `municipio`: Tipo `VARCHAR(100)` para la segmentación geográfica.
  * `localidad` y `colonia`: Tipos `VARCHAR` para la ubicación detallada.
  * `sexo_reportante`: Tipo `VARCHAR(50)` para análisis demográfico.
  * `clasificacion`: Tipo `VARCHAR(150)` para agrupar el tipo de emergencia o motivo de la llamada.
* **Estructura de la tabla de llamadas improcedentes (`llamadas_c5i_improcedentes`):**
  * `id`: Clave primaria autoincremental (`SERIAL PRIMARY KEY`).
  * `fecha`: Tipo `DATE` para permitir filtros cronológicos y agrupaciones temporales precisas día a día.
  * `hora`: Tipo `INTEGER` para registrar el momento del incidente.
  * `MOTIVO NO PROCEDENTE`: Tipo `VARCHAR(150)` para agrupar motivo de la llamada.
* **Normalización:**
  * **Normalización demográfica:** En el procesamiento de datos del campo de sexo se unifican variantes operativas históricas (como `"sin registros"`, `"no registrado"`, espacios en blanco o valores nulos) bajo una categoría estándar unificada llamada **"Sin Especificar"** para mantener la consistencia en las gráficas demográficas.

---

## 6. How-To: Instrucciones de Ejecución y Uso

### Prerrequisitos
* Tener instalado **Docker** y **Docker Compose** en tu sistema operativo.
* Tener instalado **Python 3.10+** (para la ejecución local de los scripts ETL).
* Tener instalado **GNU Make** (incluido por defecto en WSL y en la mayoría de distribuciones Linux).
* Crear un archivo `.env` en la raíz del proyecto con las credenciales de PostgreSQL (usa `.env.example` como plantilla):
  ```bash
  cp .env.example .env
  ```

> **Nota:** Todos los comandos `make` deben ejecutarse desde la raíz del proyecto.

### Paso 1: Instalar Dependencias del ETL
Instala las dependencias de Python necesarias para los scripts ETL en tu entorno local:

```bash
make install
# o manualmente: pip install -r requirements.txt
```

### Paso 2: Levantar la Base de Datos
El script de carga se conecta a PostgreSQL en `localhost:5432`, por lo que el contenedor de la base de datos **debe estar en ejecución antes de cargar los datos**:

```bash
make db
# equivale a: docker compose up -d db
```

### Paso 3: Obtención y Carga de Datos (ETL)
Descarga los archivos Excel del portal de datos abiertos de Sonora junto con el GeoJSON de municipios, y cárgalos en PostgreSQL con un solo comando:

```bash
make etl
# descarga automáticamente los archivos que falten y carga los datos
```

*(Opcional)* Si prefieres ejecutar los scripts manualmente:

```bash
python etl/descargar_datos.py   # Solo descarga los archivos hacia datos/
python etl/carga_datos.py       # Solo transforma y carga los registros a PostgreSQL
python etl/pipeline.py          # Ejecuta el pipeline completo (descarga + carga)
```

> **Importante:** `make cargar` (o `python etl/carga_datos.py`) **solo funciona si el contenedor de PostgreSQL está en ejecución** (Paso 2). También puedes colocar los archivos Excel manualmente en `datos/`; el descargador omite los archivos que ya existan localmente.
>
> **Nota sobre la carga:** Cada ejecución del ETL **reemplaza las tablas por completo** (`if_exists='replace'`), recargando los datos desde cero a partir de los archivos descargados. Esto es deliberado para evitar registros duplicados al re-ejecutar el proceso.

### Paso 4: Levantar la Arquitectura Completa
Una vez que los datos se encuentren cargados en PostgreSQL, construye y pon en marcha todos los microservicios:

```bash
make up
# equivale a: docker compose up --build -d
```

### Comandos Make Disponibles
| Comando | Descripción |
|---|---|
| `make help` | Muestra la lista de comandos disponibles |
| `make install` | Instala las dependencias de Python (`requirements.txt`) |
| `make descargar` | Descarga los datos del portal de Sonora a `datos/` (sin cargar) |
| `make cargar` | Transforma y carga los datos a PostgreSQL (requiere la BD activa y los archivos en `datos/`) |
| `make etl` | Pipeline completo de ETL (`etl/pipeline.py`: descarga lo que falte + carga) |
| `make db` | Levanta únicamente el contenedor de PostgreSQL |
| `make up` | Levanta toda la arquitectura con Docker Compose |
| `make down` | Detiene todos los contenedores |

---

## 7. Demostración y Endpoints del Prototipo

* **Documentación Interactiva de la API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
* `GET /`: Estado de salud de la API.
  * `GET /api/clasificaciones`: Catálogo de clasificaciones de incidentes procedentes ordenadas alfabéticamente.
  * `GET /api/municipios`: Catálogo geográfico de municipios disponibles.
  * `GET /api/resumen-diario`: Endpoint analítico de llamadas procedentes con filtrado cruzado por municipio y rango de fechas (`fecha_inicio`, `fecha_fin`).
  * `GET /api/analisis-horario`: Concentrado de llamadas procedentes por hora del día y día de la semana (`EXTRACT(DOW)`), con filtros opcionales de municipio y fechas.
  * `GET /api/top-clasificaciones`: Top 10 de motivos de emergencia procedentes más frecuentes bajo los filtros seleccionados.
  * `GET /api/analisis-sexo`: Distribución demográfica por sexo del reportante (con normalización automática de valores nulos o variantes a "Sin Especificar"), filtrable por municipio y fechas.
  * `GET /api/analisis-colonias-mal-uso`: Top 10 de colonias con mayor incidencia, excluyendo valores nulos o genéricos.
  * `GET /api/estacionalidad-semanal`: Distribución de volumen de llamadas procedentes agrupadas por día de la semana.
  * `GET /api/perfil-demografico`: Relación cruzada entre el sexo del reportante y la clasificación de los incidentes (Top 15).
  * `GET /api/mapa-municipios`: Consulta de volumen agrupado por municipio optimizada para la integración con mapas GeoJSON.
  * `GET /api/improcedentes`: Endpoint especializado para la consulta de registros de la tabla `llamadas_c5i_improcedentes` con soporte de filtrado temporal por rango de fechas.

* **Dashboard Interactivo (Dash):** [http://localhost:8050](http://localhost:8050)
  * **Barra de Filtros Globales:** Incorpora un selector de tipo de llamada de dos modos exclusivos (`PROCEDENTE` / `IMPROCEDENTE`), selector de municipio, filtro de clasificación(es) y un rango de fechas sincronizado.
  * **Vista de Llamadas Procedentes:**
    * *Evolución Temporal por Clasificación:* Gráfica de líneas superior que desglosa la tendencia temporal de los incidentes según su clasificación específica.
    * *Concentración Horaria de Llamadas:* Mapa de calor (`imshow`) que cruza los días de la semana con las horas del día para identificar patrones de alta saturación.
    * *Distribución por Sexo del Reportante:* Gráfica de anillos con la proporción demográfica normalizada (*No Registrado*, *Sin Especificar*, *Femenino*, *Masculino*).
    * *Top 10 Colonias con Mayor Incidencia:* Gráfica de barras horizontales que destaca las zonas con mayor número de reportes.
    * *Estacionalidad Semanal de Llamadas:* Gráfica de barras con el comportamiento operativo agrupado de Domingo a Sábado.
    * *Distribución Geográfica por Municipio:* Mapa coroplético interactivo de Sonora basado en GeoJSON que representa volumétricamente la incidencia municipal.
  * **Vista de Llamadas Improcedentes (Módulo Especializado):**
    * *Top Motivos de Improcedencia:* Gráfica de barras horizontales que detalla las causas principales de llamadas falsas o de mal uso (ej. "No Contesta O Cuelga", "Llamada Incompleta", "Bromas", etc.).
    * *Evolución Diaria de Llamadas Improcedentes:* Gráfica de líneas en tono azul oscuro con marcadores para el seguimiento temporal de incidencias.
    * *Concentración Horaria de Llamadas Improcedentes (Heatmap):* Mapa de calor optimizado con escala de color continua y desglose exacto de las 24 horas del día (0 a 23 hrs) frente a los días de la semana.
    * *Distribución por Franja Horaria:* Gráfica de barras con orden cronológico estricto (*Madrugada*, *Mañana*, *Tarde* y *Noche*).
---

## 8. Estructura del Proyecto
```text
proyecto-c5i/
├── datos/                  # Generado por `make etl` (excluido de git)
│   ├── sonora_municipios.geojson
│   ├── Llamadas Procedentes 911 primer trimestre 2026.xlsx
│   ├── Llamadas Procedentes 911 segundo trimestre 2026.xlsx
│   └── Llamadas Improcedentes 911 segundo trimestre 2026.xlsx
├── api/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── dashboard/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── etl/
│   ├── descargar_datos.py
│   ├── carga_datos.py
│   └── pipeline.py
├── .env.example
├── Makefile
├── requirements.txt
└── docker-compose.yml
```
