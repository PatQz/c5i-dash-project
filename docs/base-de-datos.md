# Diseño de la Base de Datos y Normalización

[← Volver al README](../README.md)

* **Motor:** **PostgreSQL**, elegido por su robustez, rendimiento en consultas analíticas y capacidad probada para manejar grandes volúmenes de datos relacionales sin degradación.

## Tabla de llamadas procedentes (`llamadas_c5i_procedentes`)
* `id`: Clave primaria autoincremental (`SERIAL PRIMARY KEY`).
* `fecha`: Tipo `DATE` para permitir filtros cronológicos y agrupaciones temporales precisas día a día.
* `hora`: Tipo `INTEGER` para registrar el momento del incidente.
* `municipio`: Tipo `VARCHAR(100)` para la segmentación geográfica.
* `localidad` y `colonia`: Tipos `VARCHAR` para la ubicación detallada.
* `sexo_reportante`: Tipo `VARCHAR(50)` para análisis demográfico.
* `clasificacion`: Tipo `VARCHAR(150)` para agrupar el tipo de emergencia o motivo de la llamada.

## Tabla de llamadas improcedentes (`llamadas_c5i_improcedentes`)
* `id`: Clave primaria autoincremental (`SERIAL PRIMARY KEY`).
* `fecha`: Tipo `DATE` para permitir filtros cronológicos y agrupaciones temporales precisas día a día.
* `hora`: Tipo `INTEGER` para registrar el momento del incidente.
* `motivo_no_procedente`: Tipo `VARCHAR(250)` para agrupar el motivo de la llamada.

> **Nota:** El esquema anterior es el definido en `etl/carga_datos.py`. En cada ejecución, el ETL recrea las tablas desde cero a partir de los archivos descargados (`to_sql` con `if_exists='replace'`), por lo que los tipos almacenados se infieren de los datos y pueden diferir ligeramente del esquema documentado (por ejemplo, `fecha` puede almacenarse como `TIMESTAMP`).

## Normalización
* **Limpieza de texto en el ETL:** se eliminan espacios sobrantes y se estandarizan mayúsculas/minúsculas en municipio, localidad, colonia, clasificación, sexo del reportante y motivo de improcedencia.
* **Normalización demográfica:** Al consultar el campo de sexo, la API (`/api/analisis-sexo` y `/api/perfil-demografico`) unifica variantes como `"sin registros"`, espacios en blanco o valores nulos bajo una categoría estándar llamada **"Sin Especificar"** para mantener la consistencia en las gráficas demográficas. El valor *No Registrado* se conserva como categoría independiente.

### ¿Por qué existen "No Registrado" y "Sin Especificar"?
Estas categorías responden a la naturaleza operativa del 911 y a las limitaciones en la captura de datos bajo presión:

* La prioridad del operador es contener la crisis y enviar unidades de auxilio rápidamente, por lo que datos secundarios como el sexo de quien llama pasan a segundo plano si la llamada es breve, caótica o se corta.
* Muchas llamadas provienen de líneas anónimas, teléfonos públicos o terceros que reportan una situación ajena, lo que hace innecesario o imposible recabar el dato.
* **"Sin Especificar"** se usa cuando el operador omitió la pregunta por la urgencia o el campo opcional se dejó en blanco. Por ello, los valores vacíos o nulos se agrupan en esta categoría.
* **"No Registrado"** denota una falla de vinculación con los metadatos de la línea telefónica, común en números de prepago o registros de red sin un perfil de usuario asociado. Al tener un origen distinto, se mantiene como categoría independiente.

> Esta interpretación se basa en la operación típica de los sistemas de emergencia y no en una definición oficial publicada por el C5i.

**Distribución en los datos de llamadas procedentes (primer semestre 2026, 531,495 registros):**

| Valor original | Registros | % | Categoría en el dashboard |
|---|---|---|---|
| No Registrado | 277,824 | 52.3% | No Registrado |
| Vacío (`''`) | 69,935 | 13.2% | Sin Especificar |
| Nulo | 66,906 | 12.6% | Sin Especificar |
| Femenino | 62,224 | 11.7% | Femenino |
| Masculino | 53,312 | 10.0% | Masculino |
| Sin Especificar | 1,294 | 0.2% | Sin Especificar |

Más de la mitad de las llamadas carece de un registro de sexo asociado a la línea, y solo cerca del 22% cuenta con el dato capturado, por lo que el análisis demográfico debe interpretarse con cautela.
