import os
import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_DIR = os.path.join(ROOT_DIR, 'datos')

def descargar_archivos():
    # Asegurar que la carpeta 'datos' exista en la raíz del proyecto
    os.makedirs(DATOS_DIR, exist_ok=True)
    
    # Diccionario con los enlaces de descarga directa hacia los archivos Excel o CSV del portal de Sonora
    # (Reemplaza los textos de ejemplo por las URLs directas que obtengas del portal)
    urls = {
        "Llamadas Procedentes 911 primer trimestre 2026.xlsx": "https://datos.sonora.gob.mx/dataset/923b485b-515e-4fb9-a4ac-cccbeb88cc92/resource/6ce17dd1-5716-44e9-bc5f-603c0925afe6/download/llamadas-procedentes-911-primer-trimestre-2026.xlsx",
        "Llamadas Procedentes 911 segundo trimestre 2026.xlsx": "https://datos.sonora.gob.mx/dataset/923b485b-515e-4fb9-a4ac-cccbeb88cc92/resource/943e2919-6a8b-4776-ac4f-c3d6b02bb94e/download/llamadas-procedentes-911-segundo-trimestre-2026.xlsx",
        #"Llamadas Improcedentes 911 primer trimestre 2026.xlsx": "https://datos.sonora.gob.mx/dataset/19e5036d-dbe3-4e1d-b021-df5d47b6fb1f/resource/54285a13-3a2a-4e47-b0af-e855861f5347/download/llamadas-improcedentes-911-primer-trimestre-2026.xlsx",
        "Llamadas Improcedentes 911 segundo trimestre 2026.xlsx": "https://datos.sonora.gob.mx/dataset/19e5036d-dbe3-4e1d-b021-df5d47b6fb1f/resource/0df8592f-bb3d-466c-aec3-6cbc91253be0/download/llamadas-improcedentes-911-segundo-trimestre-2026.xlsx"
    }
    
    for nombre_archivo, url in urls.items():
        ruta_destino = os.path.join(DATOS_DIR, nombre_archivo)
        
        # Evitar descargar si el archivo ya existe localmente
        if not os.path.exists(ruta_destino):
            print(f"📥 Descargando {nombre_archivo} desde el portal de Sonora...")
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    with open(ruta_destino, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ ¡Descargado exitosamente: {nombre_archivo}!")
                else:
                    print(f"❌ Error al descargar {nombre_archivo}. Código HTTP: {response.status_code}")
            except Exception as e:
                print(f"❌ Excepción durante la descarga de {nombre_archivo}: {e}")
        else:
            print(f"📂 El archivo {nombre_archivo} ya existe localmente en 'datos/'.")

def descargar_geojson_sonora():
    url = "https://raw.githubusercontent.com/PhantomInsights/mexico-geojson/refs/heads/main/2023/states/Sonora.json"

    output_dir = DATOS_DIR
    output_path = os.path.join(output_dir, "sonora_municipios.geojson")
    
    # Crear la carpeta data si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    print("Descargando archivo GeoJSON de Sonora...")
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"¡GeoJSON guardado exitosamente en {output_path}!")
        else:
            print(f"Error al descargar el GeoJSON. Código de estado: {response.status_code}")
    except Exception as e:
        print(f"Ocurrió un error al descargar el GeoJSON: {e}")
        
if __name__ == '__main__':
    descargar_archivos()
    descargar_geojson_sonora()