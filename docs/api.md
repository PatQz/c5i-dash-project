# Endpoints de la API

[← Volver al README](../README.md)

La API está construida con **FastAPI** y se ejecuta en el contenedor `container_api_ubuntu`.

* **Documentación Interactiva (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

## Parámetros de Filtrado
La mayoría de los endpoints aceptan los siguientes parámetros opcionales (query string):

| Parámetro | Formato | Descripción |
|---|---|---|
| `municipio` | Texto | Filtra por municipio. El valor `TODOS` (o no enviarlo) incluye todos. |
| `fecha_inicio` | `YYYY-MM-DD` | Fecha inicial del rango (inclusive). |
| `fecha_fin` | `YYYY-MM-DD` | Fecha final del rango (inclusive). |

Ejemplo: `GET /api/analisis-horario?municipio=HERMOSILLO&fecha_inicio=2026-01-01&fecha_fin=2026-03-31`

## Endpoints

| Endpoint | Filtros | Descripción |
|---|---|---|
| `GET /` | — | Estado de salud de la API. |
| `GET /api/clasificaciones` | — | Catálogo de clasificaciones de incidentes procedentes ordenadas alfabéticamente. |
| `GET /api/municipios` | — | Catálogo geográfico de municipios disponibles. |
| `GET /api/resumen-diario` | municipio, fechas | Endpoint analítico de llamadas procedentes agrupadas por fecha, municipio y clasificación. |
| `GET /api/analisis-horario` | municipio, fechas | Concentrado de llamadas procedentes por hora del día y día de la semana (`EXTRACT(DOW)`, 0 = Domingo). |
| `GET /api/top-clasificaciones` | municipio, fechas | Top 10 de motivos de emergencia procedentes más frecuentes. |
| `GET /api/analisis-sexo` | municipio, fechas | Distribución demográfica por sexo del reportante (con normalización automática de valores nulos o variantes a "Sin Especificar"). |
| `GET /api/analisis-colonias-mal-uso` | municipio, fechas | Top 10 de colonias con mayor incidencia, excluyendo valores nulos o genéricos. |
| `GET /api/estacionalidad-semanal` | municipio, fechas | Distribución de volumen de llamadas procedentes agrupadas por día de la semana. |
| `GET /api/perfil-demografico` | municipio, fechas | Relación cruzada entre el sexo del reportante y la clasificación de los incidentes (Top 15). |
| `GET /api/mapa-municipios` | fechas | Volumen agrupado por municipio junto con el GeoJSON de Sonora para el mapa coroplético. |
| `GET /api/improcedentes` | fechas | Registros de la tabla `llamadas_c5i_improcedentes` con soporte de filtrado temporal por rango de fechas. |

## Notas
* El GeoJSON de municipios se lee desde `datos/sonora_municipios.geojson` (volumen compartido con el host) y se mantiene en memoria; se recarga automáticamente si el archivo cambia. Si no existe al iniciar, la API intenta descargarlo.
* Las credenciales de la base de datos se reciben por variables de entorno (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) definidas en `docker-compose.yml` a partir del archivo `.env`.
