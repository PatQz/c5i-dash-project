import os
import requests
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import unicodedata
import re
import logging

# Configurar logger básico si no lo tienes
logger = logging.getLogger(__name__)

API_HOST = os.getenv("API_HOST", "api-ubuntu")
BASE_API_URL = f"http://{API_HOST}:8000"

app = Dash(__name__)
app.title = "Dashboard C5i Sonora - Emergencias Avanzado"

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#f8f9fa'}, children=[
    html.H1("📊 Dashboard Analítico C5i Sonora", style={'color': '#2c3e50', 'textAlign': 'center'}),
    html.P("Centro de Control, Comando, Comunicación, Cómputo, Coordinación e Inteligencia", style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '10px'}),
    html.P("Análisis interactivo de más de 500,000 llamadas de emergencia al 9-1-1 en el estado de Sonora (primer semestre de 2026): evolución temporal, concentración horaria, perfil demográfico del reportante, distribución geográfica por municipio y detección de llamadas improcedentes.",
           style={'textAlign': 'center', 'color': '#95a5a6', 'fontSize': '14px', 'maxWidth': '900px', 'margin': '0 auto', 'marginBottom': '30px'}),
    
    # Barra de Filtros Globales
    html.Div(style={
        'display': 'flex', 
        'justifyContent': 'center',
        'alignItems': 'flex-start', 
        'gap': '20px', 
        'marginBottom': '35px', 
        'flexWrap': 'wrap', 
        'backgroundColor': 'white', 
        'padding': '20px', 
        'borderRadius': '10px', 
        'boxShadow': '0 2px 6px rgba(0,0,0,0.05)'
    }, children=[
        
        # 1. Tipo de Llamada
        html.Div(style={'width': '220px', 'minWidth': '220px'}, children=[
            html.Label("Tipo de Llamada:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='dropdown-tipo',
                options=[
                    {'label': 'PROCEDENTE', 'value': 'PROCEDENTE'},
                    {'label': 'IMPROCEDENTE', 'value': 'IMPROCEDENTE'}
                ],
                value='PROCEDENTE',
                style={'width': '100%'}
            )
        ]),

        # 2. Municipio
        html.Div(id='contenedor-dropdown-municipio', style={'width': '220px', 'minWidth': '200px'}, children=[
            html.Label("Municipio:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='dropdown-municipio',
                # tus opciones de municipio aquí...
                value='TODOS',
                clearable=False,
                style={'width': '100%'}
            )
        ]),

        # 3. Clasificación(es) - Ahora independiente
        html.Div(id='contenedor-dropdown-dinamico', style={'width': '280px', 'minWidth': '280px'}, children=[
            html.Label("Clasificación(es):", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='dropdown-clasificacion',
                # tus opciones de clasificación aquí...
                placeholder="Selecciona clasificación...",
                multi=True,
                style={'width': '100%'}
            )
        ]),

        # 4. Rango de Fechas
        html.Div(style={'width': '420px', 'minWidth': '280px'}, children=[
            html.Label("Rango de Fechas:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px', 'fontSize': '14px', 'color': '#2c3e50'}),
            dcc.DatePickerRange(
            id='date-picker-range',
            start_date='2026-01-01',
            end_date='2026-06-30',
            display_format='YYYY-MM-DD',
            start_date_placeholder_text="Fecha inicio",
            end_date_placeholder_text="Fecha fin",
            style={
                'border': 'none',
                'borderRadius': '4px',
                'fontSize': '14px',
                'padding': '0px'
            }
        )
        ])
    ]),
    html.Div(
        id='contenedor-analisis-avanzados',
        style={'display': 'none'},
        children=[
        # Sección 1: Gráficas de Evolución Temporal por Clasificación
        html.H3("📈 Evolución Temporal por Clasificación de Incidentes", style={'color': '#34495e', 'marginTop': '20px', 'marginBottom': '15px'}),
        html.Div(id='contenedor-graficas-temporales', children=[]),

        hr_style := html.Hr(style={'margin': '40px 0', 'borderColor': '#bdc3c7'}),

        # Sección 2: Panel de Análisis Avanzados (Grid ampliado)
        html.H3("🔍 Analítica Operativa, Demográfica y Territorial", style={'color': '#34495e', 'marginBottom': '20px'}),
        
        html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'justifyContent': 'space-between'}, children=[
            # 1. Mapa de Calor Horario
            html.Div(style={'width': '48%', 'minWidth': '450px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                dcc.Graph(id='grafico-heatmap')
            ]),
            # 4. Distribución por Sexo (Barras Horizontales)
            html.Div(style={'width': '48%', 'minWidth': '450px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                dcc.Graph(id='grafico-sexo')
            ]),
            # 5. Hotspots de Falsas Alarmas por Colonia
            html.Div(style={'width': '48%', 'minWidth': '450px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                dcc.Graph(id='grafico-colonias-mal-uso')
            ]),
            # 6. Estacionalidad Semanal
            html.Div(style={'width': '48%', 'minWidth': '450px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                dcc.Graph(id='grafico-estacionalidad')
            ]),
            # 7. Mapa Geográfico de Sonora por Municipio (Reemplazando al Treemap)
            html.Div(style={'width': '100%', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                dcc.Graph(id='grafico-mapa')
            ]),
        ]),
    ]),

    # Sección dedicada a Llamadas Improcedentes
    html.Div(
        #id='panel-improcedentes',
        id='contenedor-improcedentes',
        style={'display': 'none'}, # Se mostrará solo cuando elijas 'IMPROCEDENTE' en el filtro
        children=[
            html.H3("🚨 Análisis Detallado de Llamadas Improcedentes", style={'color': '#34495e', 'marginTop': '30px', 'marginBottom': '20px'}),
            
            html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'justifyContent': 'space-between'}, children=[
                # 1. Top Motivos
                html.Div(style={'width': '48%', 'minWidth': '450px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    dcc.Graph(id='grafico-improcedentes-top')
                ]),
                # 2. Evolución Temporal
                html.Div(style={'width': '48%', 'minWidth': '450px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    dcc.Graph(id='grafico-improcedentes-temporal')
                ]),
                # 3. Mapa de Calor Horario
                html.Div(style={'width': '48%', 'minWidth': '450px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    dcc.Graph(id='grafico-improcedentes-heatmap')
                ]),
                # 4. Distribución por Franja Horaria
                html.Div(style={'width': '48%', 'minWidth': '450px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[
                    dcc.Graph(id='grafico-improcedentes-franja')
                ]),
            ])
        ]
    )
])

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    
    # Manejar caracteres especiales específicos del español
    texto = texto.replace('ñ', 'n').replace('Ñ', 'N')
    
    # Convierte caracteres acentuados a su forma descompuesta y elimina las tildes
    nfkd_form = unicodedata.normalize('NFKD', texto)
    sin_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # Pasa a minúsculas y elimina espacios sobrantes
    return sin_acentos.title()

# Callback para poblar municipios (y restablecer 'TODOS' al cambiar el tipo de llamada)
@callback(
    [Output('dropdown-municipio', 'options'),
     Output('dropdown-municipio', 'value')],
    Input('dropdown-tipo', 'value')
)
def load_municipios(tipo_seleccionado):
    options = [{'label': 'TODOS', 'value': 'TODOS'}]
    try:
        res_m = requests.get(f"{BASE_API_URL}/api/municipios", timeout=5)
        if res_m.status_code == 200:
            for m in res_m.json().get("municipios", []):
                options.append({'label': str(m), 'value': str(m)})
    except Exception as e:
        print(f"Error cargando municipios: {e}")
    return options, 'TODOS'

@callback(
    Output('dropdown-clasificacion', 'options'),
    [Input('dropdown-tipo', 'value'),
     Input('dropdown-municipio', 'value')]
)
def actualizar_opciones_clasificacion(selected_tipo, selected_municipio):
    params = {}
    if selected_tipo: # and selected_tipo != "TODOS":
        params["tipo_llamada"] = selected_tipo
    if selected_municipio and selected_municipio != "TODOS":
        params["municipio"] = selected_municipio
    try:
        res = requests.get(f"{BASE_API_URL}/api/clasificaciones", params=params, timeout=10)
        lista_clas = res.json().get("clasificaciones", [])
        return [{'label': c, 'value': c} for c in lista_clas]
    except:
        return []

@callback(
    [Output('contenedor-dropdown-dinamico', 'style'),
     Output('contenedor-dropdown-municipio', 'style')],
    Input('dropdown-tipo', 'value')
)
def alternar_visibilidad(tipo_seleccionado):
    # Los filtros de municipio y clasificación solo aplican a llamadas procedentes;
    # se devuelve el estilo completo para no perder el ancho del contenedor.
    if tipo_seleccionado == 'PROCEDENTE':
        return (
            {'display': 'block', 'width': '280px', 'minWidth': '280px'},
            {'display': 'block', 'width': '220px', 'minWidth': '200px'}
        )

    # De lo contrario, se ocultan ambos por completo
    return {'display': 'none'}, {'display': 'none'}

@callback(
    Output('contenedor-analisis-avanzados', 'style'),
    Input('dropdown-tipo', 'value')
)
def alternar_panel_avanzado(tipo_seleccionado):
    # Si está en 'TODOS' o no hay selección, mantenemos el panel oculto
    if tipo_seleccionado == 'PROCEDENTE':
        return {'display': 'block'}  # Muestra tanto el label como el dropdown
        
    # De lo contrario, se ocultan ambos por completo
    return {'display': 'none'}


@callback(
    Output('contenedor-improcedentes', 'style'),
    Input('dropdown-tipo', 'value')
)
def alternar_panel_improcedentes(tipo_seleccionado):
    # Si está en 'TODOS' o no hay selección, mantenemos el panel oculto
    if tipo_seleccionado == 'IMPROCEDENTE':
        return {'display': 'block'}  # Muestra tanto el label como el dropdown
        
    # De lo contrario, se ocultan ambos por completo
    return {'display': 'none'}

# Callbacks para actualizar todas las visualizaciones dinámicamente
@callback(
    [
        Output('contenedor-graficas-temporales', 'children'),
        Output('grafico-heatmap', 'figure'),
        Output('grafico-sexo', 'figure'),
        Output('grafico-colonias-mal-uso', 'figure'),
        Output('grafico-estacionalidad', 'figure'),
        Output('grafico-mapa', 'figure'),
        Output('grafico-improcedentes-top', 'figure'),
        Output('grafico-improcedentes-temporal', 'figure'),
        Output('grafico-improcedentes-heatmap', 'figure'),
        Output('grafico-improcedentes-franja', 'figure')
    ],
    [
        Input('dropdown-tipo', 'value'),
        Input('dropdown-municipio', 'value'),
        Input('dropdown-clasificacion', 'value'),  
        Input('date-picker-range', 'start_date'),
        Input('date-picker-range', 'end_date')
    ]
)
def update_all_analytics(selected_tipo, selected_municipio, selected_clasificaciones, start_date, end_date):
    params = {}
    if selected_tipo:
        params["tipo_llamada"] = selected_tipo
    if selected_municipio and selected_municipio != "TODOS":
        params["municipio"] = selected_municipio

    params['fecha_inicio'] = start_date
    params['fecha_fin'] = end_date

    # Inicializamos todas las figuras vacías por defecto
    temporal_cards = []
    fig_heat = fig_sexo = fig_colonias = fig_est = fig_mapa = px.bar()
    fig_top_imp = fig_temp_imp = fig_heat_imp = fig_franja_imp = px.bar()

    # =========================================================================
    # CASO 1: SI ES PROCEDENTE (Carga todas las analíticas operativas y territoriales)
    # =========================================================================
    if selected_tipo == 'PROCEDENTE':
        
        # 1. Series Temporales (Procedentes)
        try:
            res_temp = requests.get(f"{BASE_API_URL}/api/resumen-diario", params=params, timeout=10)
            df_temp = pd.DataFrame(res_temp.json().get("data", []))
        except:
            df_temp = pd.DataFrame()

        if not df_temp.empty:
            df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
            mask = (df_temp['fecha'] >= start_date) & (df_temp['fecha'] <= end_date)
            df_temp = df_temp.loc[mask]

        if df_temp.empty:
            temporal_cards = [html.Div("⚠️ No hay registros temporales para los filtros seleccionados.", style={'textAlign': 'center', 'color': '#e74c3c', 'padding': '20px'})]
        else:
            df_filtrado = df_temp.copy()
            if selected_clasificaciones:
                df_filtrado = df_filtrado[df_filtrado['clasificacion'].isin(selected_clasificaciones)]
            
            df_grouped_clasif = df_filtrado.groupby(['fecha', 'clasificacion'])['cantidad'].sum().reset_index()
            fig = px.line(
                df_grouped_clasif, x='fecha', y='cantidad', color='clasificacion', markers=True,
                title=f"Evolución Temporal por Clasificación ({selected_tipo})", 
                labels={'fecha': 'Fecha', 'cantidad': 'Llamadas', 'clasificacion': 'Clasificación'}
            )
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', hovermode='x unified', margin=dict(t=40, b=20, l=40, r=20), legend_title_text='Clasificación')
            temporal_cards = [html.Div(style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}, children=[dcc.Graph(figure=fig)])]

        # 2. Mapa de Calor Horario
        try:
            res_heat = requests.get(f"{BASE_API_URL}/api/analisis-horario", params=params, timeout=10)
            df_heat = pd.DataFrame(res_heat.json().get("data", []))
        except:
            df_heat = pd.DataFrame()

        if not df_heat.empty:
            dias_map = {0.0: 'Domingo', 1.0: 'Lunes', 2.0: 'Martes', 3.0: 'Miércoles', 4.0: 'Jueves', 5.0: 'Viernes', 6.0: 'Sábado'}
            df_heat['dia_nombre'] = df_heat['dia_semana'].map(dias_map)
            pivot_heat = df_heat.pivot(index='dia_nombre', columns='hora', values='cantidad').fillna(0)
            fig_heat = px.imshow(pivot_heat, labels=dict(x="Hora del Día", y="Día de la Semana", color="Llamadas"), title="Concentración Horaria de Llamadas")
            fig_heat.update_layout(plot_bgcolor='white', paper_bgcolor='white')


        # 5. Análisis Demográfico por Sexo
        try:
            res_sexo = requests.get(f"{BASE_API_URL}/api/analisis-sexo", params=params, timeout=10)
            df_sexo = pd.DataFrame(res_sexo.json().get("data", []))
        except:
            df_sexo = pd.DataFrame()

        if not df_sexo.empty:
            fig_sexo = px.pie(df_sexo, names='sexo_reportante', values='cantidad', title="Distribución por Sexo del Reportante", hole=0.4)
            fig_sexo.update_layout(plot_bgcolor='white', paper_bgcolor='white')

        # 6. Gráfico de Top Colonias
        try:
            res_colonias = requests.get(f"{BASE_API_URL}/api/analisis-colonias-mal-uso", params=params, timeout=10)
            df_colonias = pd.DataFrame(res_colonias.json().get("data", []))
        except:
            df_colonias = pd.DataFrame()

        if not df_colonias.empty:
            df_colonias = df_colonias.sort_values(by='cantidad', ascending=False)
            fig_colonias = px.bar(
                df_colonias, x='cantidad', y='colonia', orientation='h', title=f"Top 10 Colonias con Mayor Incidencia de Llamadas",
                labels={'cantidad': 'Total de Llamadas', 'colonia': 'Colonia'}, color_discrete_sequence=["#fd9438"]
            )
            fig_colonias.update_layout(plot_bgcolor='white', paper_bgcolor='white', yaxis=dict(autorange='reversed'), margin={"r":10,"t":40,"l":10,"b":10})

        # 7. Estacionalidad Semanal
        try:
            res_est = requests.get(f"{BASE_API_URL}/api/estacionalidad-semanal", params=params, timeout=10)
            df_est = pd.DataFrame(res_est.json().get("data", []))
        except:
            df_est = pd.DataFrame()

        if not df_est.empty:
            fig_est = px.bar(df_est, x='dia_semana_nombre', y='cantidad', title="Estacionalidad Semanal de Llamadas", labels={'dia_semana_nombre': 'Día de la Semana', 'cantidad': 'Volumen'})
            fig_est.update_layout(plot_bgcolor='white', paper_bgcolor='white')

        # 8. Mapa Geográfico (vista estatal: no aplica el filtro de municipio a propósito)
        try:
            params_mapa = {k: v for k, v in params.items() if k != 'municipio'}
            res_mapa = requests.get(f"{BASE_API_URL}/api/mapa-municipios", params=params_mapa, timeout=10)
            mapa_json = res_mapa.json()
            df_mapa = pd.DataFrame(mapa_json.get("data", []))
            geojson_sonora = mapa_json.get("geojson", {})
        except:
            df_mapa = pd.DataFrame()
            geojson_sonora = {}

        if not df_mapa.empty and geojson_sonora:
            df_mapa['municipio_norm'] = df_mapa['municipio'].apply(normalizar_texto)
            for feature in geojson_sonora.get('features', []):
                nombre_original = feature['properties'].get('NOMGEO', '')
                feature['properties']['NOMGEO_2_norm'] = normalizar_texto(nombre_original)
                
            fig_mapa = px.choropleth(
                df_mapa, geojson=geojson_sonora, locations='municipio_norm', featureidkey="properties.NOMGEO_2_norm",
                color='cantidad', color_continuous_scale="Reds", title="Distribución Geográfica por Municipio — Vista Estatal (no se filtra por municipio)", labels={'cantidad': 'Total de Llamadas'}
            )
            fig_mapa.update_geos(fitbounds="locations", visible=False)
            fig_mapa.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, paper_bgcolor='white')

    # =========================================================================
    # CASO 2: SI ES IMPROCEDENTE (Carga las 4 gráficas exclusivas de improcedentes)
    # =========================================================================
    elif selected_tipo == 'IMPROCEDENTE':
        try:
            res_improc = requests.get(f"{BASE_API_URL}/api/improcedentes", params=params, timeout=10)
            df_improc = pd.DataFrame(res_improc.json().get("data", []))
        except Exception as e:
            print(f"Error cargando improcedentes: {e}")
            df_improc = pd.DataFrame()

        if not df_improc.empty:
            df_improc['fecha'] = pd.to_datetime(df_improc['fecha'])
            
            # 1. Top Motivos
            df_top_imp = df_improc.groupby('motivo_no_procedente')['cantidad'].sum().reset_index()
            df_top_imp = df_top_imp.sort_values(by='cantidad', ascending=True).tail(10)
            fig_top_imp = px.bar(df_top_imp, x='cantidad', y='motivo_no_procedente', orientation='h', title="Top Motivos de Improcedencia", labels={'cantidad': 'Total', 'motivo_no_procedente': 'Motivo'})
            fig_top_imp.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin={"r":10,"t":40,"l":10,"b":10})

            # --- 2. Evolución Temporal (Corregido para agrupar solo por fecha YYYY-MM-DD) ---
            df_improc['solo_fecha'] = pd.to_datetime(df_improc['fecha']).dt.date
            df_temp_imp = df_improc.groupby('solo_fecha')['cantidad'].sum().reset_index()
            
            fig_temp_imp = px.line(
                df_temp_imp, x='solo_fecha', y='cantidad', markers=True, 
                title="Evolución Diaria de Llamadas Improcedentes", 
                labels={'solo_fecha': 'Fecha', 'cantidad': 'Cantidad de Llamadas'}
            )
            fig_temp_imp.update_traces(line_color="#242989")
            fig_temp_imp.update_layout(
                plot_bgcolor='white', paper_bgcolor='white', 
                margin={"r":10,"t":40,"l":10,"b":10},
                xaxis=dict(type='date')
            )

            # --- 3. Mapa de Calor Horario (Corregido para mostrar todos los días ordenados y horas de 0 a 23) ---
            df_improc['dia_semana'] = pd.to_datetime(df_improc['fecha']).dt.dayofweek
            dias_orden = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
            df_improc['dia_nombre'] = df_improc['dia_semana'].map(dias_orden)
            
            # 1. Creamos la tabla pivote con todos los días y aseguramos las 24 horas (0 a 23) en las columnas
            pivot_imp = df_improc.pivot_table(
                index='dia_nombre', 
                columns='hora', 
                values='cantidad', 
                aggfunc='sum', 
                fill_value=0
            )
            
            # Asegurarnos de que existan las columnas de la hora 0 a la 23 completas
            horas_completas = list(range(24))
            pivot_imp = pivot_imp.reindex(columns=horas_completas, fill_value=0)
            
            # Reordenar los días de la semana de Lunes a Domingo
            dias_lista = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            pivot_imp = pivot_imp.reindex([d for d in dias_lista if d in pivot_imp.index])
            
            # 2. Generar el Heatmap con Plotly Express
            fig_heat_imp = px.imshow(
                pivot_imp,
                labels=dict(x="Hora del Día (0 - 23 hrs)", y="Día de la Semana", color="Total de Llamadas"),
                x=horas_completas,
                y=pivot_imp.index,
                color_continuous_scale="viridis_r",
                aspect="auto",
                title="Concentración Horaria de Llamadas Improcedentes (Heatmap)"
            )
            
            fig_heat_imp.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='white', 
                margin={"r":20,"t":40,"l":20,"b":20},
                xaxis=dict(dtick=1) # Muestra cada hora de forma exacta en el eje X
            )
        
            # --- 4. Franja Horaria (Ordenada cronológicamente) ---
            def asignar_franja(h):
                if 0 <= h < 6: return 'Madrugada (00-06h)'
                elif 6 <= h < 12: return 'Mañana (06-12h)'
                elif 12 <= h < 18: return 'Tarde (12-18h)'
                else: return 'Noche (18-24h)'
            
            df_improc['franja'] = df_improc['hora'].apply(asignar_franja)
            df_franja = df_improc.groupby('franja')['cantidad'].sum().reset_index()

            # Forzar el orden cronológico exacto de las franjas
            orden_franjas = ['Madrugada (00-06h)', 'Mañana (06-12h)', 'Tarde (12-18h)', 'Noche (18-24h)']
            df_franja['franja'] = pd.Categorical(df_franja['franja'], categories=orden_franjas, ordered=True)
            df_franja = df_franja.sort_values('franja')

            fig_franja_imp = px.bar(
                df_franja, 
                x='franja', 
                y='cantidad', 
                title="Distribución por Franja Horaria", 
                labels={'franja': 'Franja Horaria', 'cantidad': 'Total de Llamadas'},
                #color_discrete_sequence=['#1e3d59'] # Usando el mismo azul oscuro elegante
            )
            fig_franja_imp.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='white', 
                margin={"r":10,"t":40,"l":10,"b":10}
            )

    # Retorno unificado de todas las figuras en el orden exacto del Output
    return (
        temporal_cards, fig_heat, fig_sexo, 
        fig_colonias, fig_est, fig_mapa, 
        fig_top_imp, fig_temp_imp, fig_heat_imp, fig_franja_imp
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)