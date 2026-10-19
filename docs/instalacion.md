# Instalación y Ejecución

[← Volver al README](../README.md)

## Prerrequisitos
* Tener instalado **Docker** y **Docker Compose** en tu sistema operativo.
* Tener instalado **Python 3.10+** (para la ejecución local de los scripts ETL).
* Tener instalado **GNU Make** (incluido por defecto en WSL y en la mayoría de distribuciones Linux).
* Crear un archivo `.env` en la raíz del proyecto con las credenciales de PostgreSQL (usa `.env.example` como plantilla):
  ```bash
  cp .env.example .env
  ```

> **Nota:** Todos los comandos `make` deben ejecutarse desde la raíz del proyecto.

## Paso 1: Instalar Dependencias del ETL
Instala las dependencias de Python necesarias para los scripts ETL en tu entorno local:

```bash
make install
# o manualmente: pip install -r requirements.txt
```

## Paso 2: Levantar la Base de Datos
El script de carga se conecta a PostgreSQL en `localhost:5432`, por lo que el contenedor de la base de datos **debe estar en ejecución antes de cargar los datos**:

```bash
make db
# equivale a: docker compose up -d db
```

## Paso 3: Obtención y Carga de Datos (ETL)
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

## Paso 4: Levantar la Arquitectura Completa
Una vez que los datos se encuentren cargados en PostgreSQL, construye y pon en marcha todos los microservicios:

```bash
make up
# equivale a: docker compose up --build -d
```

Después abre:
* **Dashboard:** [http://localhost:8050](http://localhost:8050)
* **Documentación de la API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

Para detener todos los contenedores: `make down`.

## Comandos Make Disponibles
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

## Solución de Problemas
* **`make cargar` / `make etl` no puede conectarse a la base de datos:** verifica que el contenedor esté activo con `make db` y que tu `.env` no contenga una línea `DB_HOST=db` (ese nombre solo existe dentro de la red de Docker; el ETL usa `localhost` por defecto).
* **Cambiaste las credenciales en `.env` y PostgreSQL las rechaza:** PostgreSQL solo aplica las credenciales al crear el volumen por primera vez. Ejecuta `docker compose down -v` (**esto borra los datos cargados**), luego `make db` y `make etl`.
* **`error getting credentials` al ejecutar `make up`:** suele ser un fallo temporal de Docker Desktop mientras inicia. Espera unos segundos y vuelve a intentarlo.
* **`make: getcwd: No such file or directory`:** la terminal quedó en un directorio inválido. Vuelve a entrar a la carpeta del proyecto con `cd`.
