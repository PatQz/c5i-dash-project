# Dashboard Interactivo

[← Volver al README](../README.md)

El dashboard está construido con **Dash** y **Plotly**, se ejecuta en el contenedor `container_python_dash` y obtiene todos sus datos de la API.

* **Dirección:** [http://localhost:8050](http://localhost:8050)

## Barra de Filtros Globales
Incorpora un selector de tipo de llamada de dos modos exclusivos (`PROCEDENTE` / `IMPROCEDENTE`), selector de municipio, filtro de clasificación(es) y un rango de fechas sincronizado.

* **Municipio:** inicia en `TODOS` y vuelve a `TODOS` cada vez que cambia el tipo de llamada.
* **Clasificación(es):** permite seleccionar varias clasificaciones a la vez.
* Los filtros de **municipio** y **clasificación** solo se muestran en la vista `PROCEDENTE`, ya que los datos de llamadas improcedentes no incluyen esa información.

## Vista de Llamadas Procedentes
* *Evolución Temporal por Clasificación:* Gráfica de líneas superior que desglosa la tendencia temporal de los incidentes según su clasificación específica.
* *Concentración Horaria de Llamadas:* Mapa de calor (`imshow`) que cruza los días de la semana con las horas del día para identificar patrones de alta saturación.
* *Distribución por Sexo del Reportante:* Gráfica de anillos con la proporción demográfica normalizada (*No Registrado*, *Sin Especificar*, *Femenino*, *Masculino*).
* *Top 10 Colonias con Mayor Incidencia:* Gráfica de barras horizontales que destaca las zonas con mayor número de reportes.
* *Estacionalidad Semanal de Llamadas:* Gráfica de barras con el comportamiento operativo agrupado de Domingo a Sábado.
* *Distribución Geográfica por Municipio:* Mapa coroplético interactivo de Sonora basado en GeoJSON que representa volumétricamente la incidencia municipal.

## Vista de Llamadas Improcedentes (Módulo Especializado)
* *Top Motivos de Improcedencia:* Gráfica de barras horizontales que detalla las causas principales de llamadas falsas o de mal uso (ej. "No Contesta O Cuelga", "Llamada Incompleta", "Bromas", etc.).
* *Evolución Diaria de Llamadas Improcedentes:* Gráfica de líneas en tono azul oscuro con marcadores para el seguimiento temporal de incidencias.
* *Concentración Horaria de Llamadas Improcedentes (Heatmap):* Mapa de calor optimizado con escala de color continua y desglose exacto de las 24 horas del día (0 a 23 hrs) frente a los días de la semana.
* *Distribución por Franja Horaria:* Gráfica de barras con orden cronológico estricto (*Madrugada*, *Mañana*, *Tarde* y *Noche*).
