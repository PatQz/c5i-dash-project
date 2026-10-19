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
* **Normalización demográfica:** Al consultar el campo de sexo, la API (`/api/analisis-sexo`) unifica variantes como `"sin registros"`, espacios en blanco o valores nulos bajo una categoría estándar llamada **"Sin Especificar"** para mantener la consistencia en las gráficas demográficas. El valor *No Registrado* se conserva como categoría independiente.
