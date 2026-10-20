from fastapi import FastAPI, HTTPException
import os
import pandas as pd
from sqlalchemy import create_engine, text
import json
import requests
from dotenv import load_dotenv

# Carga las variables del archivo .env si se ejecuta localmente
load_dotenv()

app = FastAPI(title="API C5i Sonora", description="API unificada de llamadas C5i")

# Leer variables estrictamente del entorno sin credenciales quemadas por seguridad
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Validación opcional pero recomendada para asegurar que existan las variables
if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
    faltantes = [k for k, v in {"DB_HOST": DB_HOST, "DB_USER": DB_USER, "DB_PASSWORD": DB_PASSWORD, "DB_NAME": DB_NAME}.items() if not v]
    raise ValueError(f"Faltan variables de entorno para la conexión a la base de datos: {', '.join(faltantes)}")

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL)

os.makedirs("datos", exist_ok=True)
geojson_path = "datos/sonora_municipios.geojson"
if not os.path.exists(geojson_path):
    url = "https://raw.githubusercontent.com/PhantomInsights/mexico-geojson/refs/heads/main/2023/states/Sonora.json"

    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            with open(geojson_path, "w", encoding="utf-8") as f:
                f.write(res.text)
        else:
            print(f"No se pudo descargar el GeoJSON. Código HTTP: {res.status_code}")
    except requests.RequestException as e:
        print(f"No se pudo descargar el GeoJSON: {e}")

# Caché del GeoJSON en memoria; se recarga solo si el archivo cambia en disco
_geojson_cache = {"mtime": None, "data": None}

def cargar_geojson():
    mtime = os.path.getmtime(geojson_path)
    if _geojson_cache["mtime"] != mtime:
        with open(geojson_path, "r", encoding="utf-8") as f:
            _geojson_cache["data"] = json.load(f)
        _geojson_cache["mtime"] = mtime
    return _geojson_cache["data"]

@app.get("/")
def home():
    return {"message": "API C5i Sonora Unificada en línea"}

@app.get("/api/clasificaciones")
def get_clasificaciones():
    try:
        query = "SELECT DISTINCT clasificacion FROM llamadas_c5i_procedentes WHERE clasificacion IS NOT NULL"
        params = {}

        query += " ORDER BY clasificacion ASC;"
        
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            clasificaciones = [row[0] for row in result if row[0]]
        return {"clasificaciones": clasificaciones}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/municipios")
def get_municipios():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DISTINCT municipio FROM llamadas_c5i_procedentes WHERE municipio IS NOT NULL ORDER BY municipio ASC;"))
            municipios = [row[0] for row in result if row[0]]
        return {"municipios": municipios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumen-diario")
def get_resumen_diario(municipio: str = None, fecha_inicio: str = None, fecha_fin: str = None):
    try:
        query = """
            SELECT CAST(fecha AS VARCHAR) as fecha, municipio, clasificacion, COUNT(*) as cantidad
            FROM llamadas_c5i_procedentes
            WHERE 1=1
        """
        params = {}

        if municipio and municipio != "TODOS":
            query += " AND municipio = :municipio"
            params["municipio"] = municipio
            
        if fecha_inicio:
            query += " AND fecha >= :fecha_inicio"
            params["fecha_inicio"] = fecha_inicio
            
        if fecha_fin:
            query += " AND fecha <= :fecha_fin"
            params["fecha_fin"] = fecha_fin
            
        # Agrupamos por todos los campos seleccionados para que coincida con el SELECT
        query += " GROUP BY fecha, municipio, clasificacion ORDER BY fecha ASC;"
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return {"total_registros": len(df), "data": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NUEVOS ENDPOINTS ANALÍTICOS

@app.get("/api/analisis-horario")
def get_analisis_horario(municipio: str = None, fecha_inicio: str = None, fecha_fin: str = None):
    try:
        query = """
            SELECT hora, EXTRACT(DOW FROM fecha) as dia_semana, COUNT(*) as cantidad
            FROM llamadas_c5i_procedentes
            WHERE hora IS NOT NULL
        """
        params = {}

        if municipio and municipio != "TODOS":
            query += " AND municipio = :municipio"
            params["municipio"] = municipio
        
        if fecha_inicio:
            query += " AND fecha >= :fecha_inicio"
            params["fecha_inicio"] = fecha_inicio
            
        if fecha_fin:
            query += " AND fecha <= :fecha_fin"
            params["fecha_fin"] = fecha_fin
            
        query += " GROUP BY hora, dia_semana ORDER BY dia_semana, hora;"
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return {"data": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/top-clasificaciones")
def get_top_clasificaciones(municipio: str = None, fecha_inicio: str = None, fecha_fin: str = None):
    try:
        query = """
            SELECT clasificacion, COUNT(*) as cantidad
            FROM llamadas_c5i_procedentes
            WHERE clasificacion IS NOT NULL
        """
        params = {}

        if municipio and municipio != "TODOS":
            query += " AND municipio = :municipio"
            params["municipio"] = municipio
        
        if fecha_inicio:
            query += " AND fecha >= :fecha_inicio"
            params["fecha_inicio"] = fecha_inicio
            
        if fecha_fin:
            query += " AND fecha <= :fecha_fin"
            params["fecha_fin"] = fecha_fin
            
        query += " GROUP BY clasificacion ORDER BY cantidad DESC LIMIT 10;"
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return {"data": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analisis-sexo")
def get_analisis_sexo(municipio: str = None, fecha_inicio: str = None, fecha_fin: str = None):
    try:
        query = """
            SELECT COALESCE(NULLIF(TRIM(sexo_reportante), ''), 'Sin Especificar') as sexo_reportante, COUNT(*) as cantidad
            FROM llamadas_c5i_procedentes
            WHERE 1=1
        """
        params = {}

        if municipio and municipio != "TODOS":
            query += " AND municipio = :municipio"
            params["municipio"] = municipio

        if fecha_inicio:
            query += " AND fecha >= :fecha_inicio"
            params["fecha_inicio"] = fecha_inicio
            
        if fecha_fin:
            query += " AND fecha <= :fecha_fin"
            params["fecha_fin"] = fecha_fin
            
        query += " GROUP BY 1 ORDER BY cantidad DESC;"
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
            
        if not df.empty and 'sexo_reportante' in df.columns:
            # 1. Limpieza estándar de texto (eliminar espacios y estandarizar mayúsculas/minúsculas)
            df['sexo_reportante'] = df['sexo_reportante'].astype(str).str.strip().str.title()
            
            # 2. Mapeo para unificar todas las variantes indeseadas en una sola
            mapeo_sexo = {
                '': 'Sin Especificar',
                'Nan': 'Sin Especificar',
                'Sin Registros': 'Sin Especificar',
                'Sin Especificar': 'Sin Especificar'
            }
            df['sexo_reportante'] = df['sexo_reportante'].replace(mapeo_sexo)
            
            # 3. Re-agrupar por si existían registros separados con el mismo nombre normalizado y sumar sus cantidades
            df = df.groupby('sexo_reportante', as_index=False)['cantidad'].sum()
            
            # 4. Volver a ordenar de mayor a menor por cantidad
            df = df.sort_values(by='cantidad', ascending=False)

        return {"data": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/analisis-colonias-mal-uso")
def get_analisis_colonias_mal_uso(municipio: str = None, fecha_inicio: str = None, fecha_fin: str = None):
    try:
        query = """
            SELECT 
                INITCAP(TRIM(colonia)) as colonia, 
                SUM(1) as cantidad
            FROM llamadas_c5i_procedentes
            WHERE colonia IS NOT NULL 
              AND TRIM(colonia) != '' 
              AND UPPER(TRIM(colonia)) NOT IN ('SIN COLONIA', 'S/C', 'NA', 'N/A')
        """
        params = {}

        # Filtro dinámico de municipio
        if municipio and municipio != "TODOS":
            query += " AND municipio = :municipio"
            params["municipio"] = municipio
        
        if fecha_inicio:
            query += " AND fecha >= :fecha_inicio"
            params["fecha_inicio"] = fecha_inicio
            
        if fecha_fin:
            query += " AND fecha <= :fecha_fin"
            params["fecha_fin"] = fecha_fin
            
        # Nota: quitamos 'tipo_llamada' del GROUP BY a menos que lo selecciones en el SELECT
        query += " GROUP BY INITCAP(TRIM(colonia)) ORDER BY cantidad DESC LIMIT 10;"
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
            
        return {"data": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/estacionalidad-semanal")
def get_estacionalidad_semanal(municipio: str = None, fecha_inicio: str = None, fecha_fin: str = None):
    try:
        query = """
            SELECT 
                CASE EXTRACT(DOW FROM fecha)
                    when 0 then 'Domingo'
                    when 1 then 'Lunes'
                    when 2 then 'Martes'
                    when 3 then 'Miércoles'
                    when 4 then 'Jueves'
                    when 5 then 'Viernes'
                    when 6 then 'Sábado'
                END as dia_semana_nombre,
                EXTRACT(DOW FROM fecha) as dow,
                COUNT(*) as cantidad
            FROM llamadas_c5i_procedentes
            WHERE fecha IS NOT NULL
        """
        params = {}

        if municipio and municipio != "TODOS":
            query += " AND municipio = :municipio"
            params["municipio"] = municipio
        
        if fecha_inicio:
            query += " AND fecha >= :fecha_inicio"
            params["fecha_inicio"] = fecha_inicio
            
        if fecha_fin:
            query += " AND fecha <= :fecha_fin"
            params["fecha_fin"] = fecha_fin
            
        query += " GROUP BY dow, dia_semana_nombre ORDER BY dow;"
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return {"data": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/perfil-demografico")
def get_perfil_demografico(municipio: str = None, fecha_inicio: str = None, fecha_fin: str = None):
    try:
        query = """
            SELECT COALESCE(NULLIF(TRIM(sexo_reportante), ''), 'Sin Especificar') as sexo_reportante, clasificacion, COUNT(*) as cantidad
            FROM llamadas_c5i_procedentes
            WHERE clasificacion IS NOT NULL
        """
        params = {}

        if municipio and municipio != "TODOS":
            query += " AND municipio = :municipio"
            params["municipio"] = municipio
        
        if fecha_inicio:
            query += " AND fecha >= :fecha_inicio"
            params["fecha_inicio"] = fecha_inicio
            
        if fecha_fin:
            query += " AND fecha <= :fecha_fin"
            params["fecha_fin"] = fecha_fin
            
        query += " GROUP BY 1, clasificacion ORDER BY cantidad DESC LIMIT 15;"
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return {"data": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/api/mapa-municipios")
def get_mapa_municipios(fecha_inicio: str = None, fecha_fin: str = None):
    try:
        # Usamos INITCAP para que coincida con el formato de nombres del GeoJSON (ej. 'Hermosillo')
        query = """
            SELECT INITCAP(TRIM(municipio)) as municipio, COUNT(*) as cantidad
            FROM llamadas_c5i_procedentes
            WHERE municipio IS NOT NULL
        """
        params = {}
        
        if fecha_inicio:
            query += " AND fecha >= :fecha_inicio"
            params["fecha_inicio"] = fecha_inicio
            
        if fecha_fin:
            query += " AND fecha <= :fecha_fin"
            params["fecha_fin"] = fecha_fin
        
        query += " GROUP BY INITCAP(TRIM(municipio));"
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)

        return {
            "data": df.to_dict(orient='records'),
            "geojson": cargar_geojson()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/improcedentes")
def get_llamadas_c5i_improcedentes(fecha_inicio: str = None, fecha_fin: str = None):
    try:
        query = """
            SELECT CAST(fecha AS DATE) AS fecha, hora, motivo_no_procedente, COUNT(*) AS cantidad
            FROM llamadas_c5i_improcedentes
            WHERE 1=1
        """
        params = {}
        
        # Filtro dinámico opcional por rango de fechas
        if fecha_inicio:
            query += " AND fecha >= :fecha_inicio"
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            query += " AND fecha <= :fecha_fin"
            params["fecha_fin"] = fecha_fin
            
        query += " GROUP BY CAST(fecha AS DATE), hora, motivo_no_procedente ORDER BY fecha;"
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
            
        # Convertir la columna fecha a string para evitar problemas de serialización JSON
        if not df.empty and 'fecha' in df.columns:
            df['fecha'] = df['fecha'].astype(str)
            
        return {"data": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))