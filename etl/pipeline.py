try:
    from descargar_datos import descargar_archivos, descargar_geojson_sonora
    from carga_datos import procesar_y_cargar
except ImportError:
    from etl.descargar_datos import descargar_archivos, descargar_geojson_sonora
    from etl.carga_datos import procesar_y_cargar

def ejecutar_pipeline():
    # Los archivos existentes en datos/ actúan como caché local:
    # solo se descargan los que falten antes de cargar a PostgreSQL.
    print("=== Fase 1: Descarga de datos ===")
    descargar_archivos()
    descargar_geojson_sonora()

    print("\n=== Fase 2: Transformación y carga a PostgreSQL ===")
    procesar_y_cargar()

if __name__ == '__main__':
    ejecutar_pipeline()
