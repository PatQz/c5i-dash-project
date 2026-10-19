import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

load_dotenv(os.path.join(ROOT_DIR, ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password123")
DB_NAME = os.getenv("POSTGRES_DB", "c5i_db")

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL)

def procesar_y_cargar():
    # NOTA: Los bloques CREATE TABLE documentan el esquema esperado, pero las tablas
    # se recrean desde cero con to_sql(if_exists='replace') en cada ejecución. Esto
    # es intencional: el ETL siempre recarga los archivos recién descargados para
    # evitar registros duplicados al repetir el proceso.

    # Rutas de archivos procedentes
    proc_1 = os.path.join(ROOT_DIR, 'datos', 'Llamadas Procedentes 911 primer trimestre 2026.xlsx')
    proc_2 = os.path.join(ROOT_DIR, 'datos', 'Llamadas Procedentes 911 segundo trimestre 2026.xlsx')
    
    # Rutas de archivos improcedentes
    #improc_1 = os.path.join(ROOT_DIR, 'datos', 'Llamadas Improcedentes 911 primer trimestre 2026.xlsx')
    improc_2 = os.path.join(ROOT_DIR, 'datos', 'Llamadas Improcedentes 911 segundo trimestre 2026.xlsx')
    
    # ==========================================
    # 1. PROCESAR LLAMADAS PROCEDENTES
    # ==========================================
    if os.path.exists(proc_1) and os.path.exists(proc_2):
        print("Leyendo archivos de llamadas procedentes...")
        df_p1 = pd.read_excel(proc_1)
        df_p2 = pd.read_excel(proc_2)
        df_proc = pd.concat([df_p1, df_p2], ignore_index=True)
        
        # Limpieza de columnas y datos procedentes
        df_proc.columns = df_proc.columns.str.strip()
        df_proc['MUNICIPIO'] = df_proc['MUNICIPIO'].astype(str).str.strip().str.upper()
        df_proc['LOCALIDAD'] = df_proc['LOCALIDAD'].astype(str).str.strip().str.title()
        df_proc['COLONIA'] = df_proc['COLONIA'].astype(str).str.strip().str.title()
        df_proc['CLASIFICACION'] = df_proc['CLASIFICACION'].astype(str).str.strip().str.title()
        df_proc['SEXO REPORTANTE'] = df_proc['SEXO REPORTANTE'].astype(str).str.strip().str.title()
        
        df_proc = df_proc.rename(columns={
            'FECHA': 'fecha',
            'HORA': 'hora',
            'MUNICIPIO': 'municipio',
            'LOCALIDAD': 'localidad',
            'COLONIA': 'colonia',
            'SEXO REPORTANTE': 'sexo_reportante',
            'CLASIFICACION': 'clasificacion'
        })

        print("Creando tabla 'llamadas_c5i_procedentes' en PostgreSQL...")
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llamadas_c5i_procedentes (
                    id SERIAL PRIMARY KEY,
                    fecha DATE,
                    hora INT,
                    municipio VARCHAR(100),
                    localidad VARCHAR(150),
                    colonia VARCHAR(200),
                    sexo_reportante VARCHAR(50),
                    clasificacion VARCHAR(150)
                );
            """ ))

        print(f"Cargando {len(df_proc)} registros procedentes a PostgreSQL...")
        df_proc.to_sql('llamadas_c5i_procedentes', engine, if_exists='replace', index=False, chunksize=10000)
        print("¡Tabla 'llamadas_c5i_procedentes' cargada con éxito!")
    else:
        print("⚠️ Faltan archivos de llamadas procedentes en la carpeta 'datos/'.")

    # ==========================================
    # 2. PROCESAR LLAMADAS IMPROCEDENTES
    # ==========================================
    #if os.path.exists(improc_1) and os.path.exists(improc_2):
    if os.path.exists(improc_2):
        print("Leyendo archivos de llamadas improcedentes...")
        #df_i1 = pd.read_excel(improc_1)
        df_i2 = pd.read_excel(improc_2)
        #df_improc = pd.concat([df_i1, df_i2], ignore_index=True)
        df_improc = pd.concat([df_i2], ignore_index=True)
        
        # Limpieza de columnas y datos improcedentes (según la estructura que mostraste)
        df_improc.columns = df_improc.columns.str.strip()
        df_improc['MOTIVO NO PROCEDENTE'] = df_improc['MOTIVO NO PROCEDENTE'].astype(str).str.strip().str.title()
        
        df_improc = df_improc.rename(columns={
            'FECHA': 'fecha',
            'HORA': 'hora',
            'MOTIVO NO PROCEDENTE': 'motivo_no_procedente'
        })

        print("Creando tabla 'llamadas_c5i_improcedentes' en PostgreSQL...")
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llamadas_c5i_improcedentes (
                    id SERIAL PRIMARY KEY,
                    fecha DATE,
                    hora INT,
                    motivo_no_procedente VARCHAR(250)
                );
            """ ))

        print(f"Cargando {len(df_improc)} registros improcedentes a PostgreSQL...")
        df_improc.to_sql('llamadas_c5i_improcedentes', engine, if_exists='replace', index=False, chunksize=10000)
        print("¡Tabla 'llamadas_c5i_improcedentes' cargada con éxito!")
    else:
        print("⚠️ No se encontraron archivos de llamadas improcedentes (o falta alguno).")

if __name__ == '__main__':
    procesar_y_cargar()