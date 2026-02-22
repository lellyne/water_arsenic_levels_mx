########################################################################
# Script del cuadro de mandos de la aplicacion web
########################################################################

# load libraries

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# load data
df_s = pd.read_parquet('tlm_conagua_limpio.parquet')

########################################################################
# Crear contendio de la apli basada en Streamlit
########################################################################

########################################################################
# Crear un encabezado
########################################################################

st.header('Arsénico en los Principales Cuerpos de Agua de México de 2012-2024')
st.caption(
    'Con datos oficiales de la CONAGUA del 2025-05-06, ver: [*Resultados de la RENAMECA*](https://www.gob.mx/conagua/es/articulos/resultados-de-la-red-nacional-de-medicion-de-calidad-del-agua-renameca?idiom=es)')

########################################################################
# Crear casillas de verificacion
#######################################################################

st.subheader('Selecciona los gráficos que deseas visualizar:')

# Casilla 1 : hist as_tot
hist_As = st.checkbox('Construir un histograma de arsénico')

# Casilla 2 : scatter as_tot + fecha_realizacion_dt
scatter_As = st.checkbox(
    'Construir un gráfico de dispersión de arséncio en el tiempo')

# Casilla 3 : barras as_tot + ano + sub_o_sup
bar_As = st.checkbox(
    'Construir un gráfico de barras de los excessos de arséncio en el tiempo')

########################################################################
# Logica para mostrar graficos segun la casilla seleccionada
########################################################################

# grafico 1
if hist_As:
    # escribir un menasaje en la apli
    st.write('Creación de un histograma de los niveles de arsénico total de 2012-2024')

    # crear un hist con plotly.graph_objects
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=df_s['as_tot_float'],
            xbins=dict(
                start=0,
                end=1,
                size=0.005   # thinner bins
            ),
            name="Distribución",
            opacity=0.75
        )
    )
    # Línea vertical del límite NOM-127 (0.01 mg/L)
    fig.add_vline(
        x=0.01,
        line_dash="dash",
        line_color="red",
        line_width=3,
        annotation_text="Límite NOM-127 (0.01 mg/L)",
        annotation_position="top right"
    )
    # Layout mejorado
    fig.update_layout(
        title="Distribución de Arsénico Totales en Muestras de Agua (México)",
        xaxis_title="Arsénico Total en Muestra de Agua (mg/L)",
        yaxis_title="Frecuencia",
        bargap=0.05,
        # ← clave para limitar el rango del eje x a 0-0.2 mg/L
        xaxis=dict(range=[0, 0.2])
    )
    # mostrar el grafico interactivo en la apli streamlit
    st.plotly_chart(fig, use_container_width=True)


# grafico 2
if scatter_As:
    # escribir un mensaje
    st.write('Creación de un gráfico de dispersión de los mg/L de arsénico encontrados en las muestras de agua através del tiempo, según el tipo de agua')
    # filtrar datos válidos
    df_plot = df_s.dropna(
        subset=['as_tot_float', 'fecha_realizacion_dt', 'sub_o_sup'])
    # plot
    fig = px.scatter(
        df_plot,
        x='fecha_realizacion_dt',
        y='as_tot_float',
        color='sub_o_sup',
        facet_col='sub_o_sup',
        opacity=0.6,
        title='Dispersión de Arsénico en Agua por Tipo de Cuerpo de Agua (México)',
        labels={
            'fecha_realizacion_dt': 'Fecha de Realización de la Muestra',
            'as_tot_float': 'Arsénico Total (mg/L)',
            'sub_o_sup': 'Tipo de Cuerpo de Agua'
        }
    )
    # Limitar eje Y para mejor visibilidad
    fig.update_yaxes(range=[0, .2], title_text='Arsénico Total (mg/L)')
    # Línea NOM-127 en cada panel
    fig.add_hline(
        y=0.01,
        line_dash="dash",
        line_color="red",
        line_width=3,
        annotation_text="Límite NOM-127 (0.01 mg/L)"
    )
    fig.update_layout(legend_title_text='Tipo de Agua')
    # mostrar el grafico en la apli
    st.plotly_chart(fig, use_container_width=True)


# grafico 3

if bar_As:
    # escribir un mensaje
    st.write('Creación de un gráfico de barras de los excesos de arsénico encontrados anualmente en aguas subterráneas y superficiales')
    # 1) Crear tabla anual (numérica) si no la tienes ya
    tabla_excesos_anual = (
        df_s
        .dropna(subset=['as_tot_float'])
        .query("2012 <= ano <= 2024")
        .groupby(['ano', 'sub_o_sup'])
        .agg(
            total=('as_tot_float', 'count'),
            exceden=('supNOM127SSA12021_As', lambda x: (x == 1).sum())
        )
    )
    tabla_excesos_anual['proporcion_exceso'] = (
        tabla_excesos_anual['exceden'] / tabla_excesos_anual['total']
    )
    # 2) Pivot numérico (MultiIndex en columnas)
    pivot = (
        tabla_excesos_anual[['total', 'proporcion_exceso']]
        .unstack('sub_o_sup')
    )
    # 3) Helper para construir un subplot por tipo

    def add_bar(fig, col_idx, tipo, titulo_subplot):
        # Series por año
        y_prop = pivot[('proporcion_exceso', tipo)] * 100   # a %
        txt_tot = pivot[('total', tipo)].astype(
            'Int64')    # totales (puede tener <NA>)
        # limpiar NaNs para plot
        years = y_prop.index
        y_vals = y_prop.values
        txt_vals = [f"n={t}" if pd.notna(t) else "" for t in txt_tot.values]
        fig.add_trace(
            go.Bar(
                x=years,
                y=y_vals,
                name=tipo,
                text=txt_vals,          # texto arriba de la barra
                textposition="outside"
            ),
            row=1,
            col=col_idx
        )
        fig.update_xaxes(title_text="Año", row=1, col=col_idx)
        fig.update_yaxes(title_text="% que excede 0.01 mg/L",
                         row=1, col=col_idx, rangemode="tozero")
        # título del subplot
        fig.layout.annotations[col_idx-1].text = titulo_subplot
    # 4) Definir qué tipos existen en tus datos (ajusta si tus etiquetas son distintas)
    tipos_disponibles = list(pivot.columns.get_level_values(1).unique())
    tipo_sub = 'Subterránea'
    tipo_sup = 'Superficial'
    # 5) Crear figura con 2 subplots (uno por tipo)
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Agua subterránea", "Agua superficial"),
        shared_yaxes=False
    )
    # Agregar barras (si existen)
    if ('proporcion_exceso', tipo_sub) in pivot.columns:
        add_bar(fig, 1, tipo_sub, "Agua subterránea")
    else:
        print(
            f"⚠️ No encontré el tipo '{tipo_sub}' en sub_o_sup. Tipos disponibles: {tipos_disponibles}")

    if ('proporcion_exceso', tipo_sup) in pivot.columns:
        add_bar(fig, 2, tipo_sup, "Agua superficial")
    else:
        print(
            f"⚠️ No encontré el tipo '{tipo_sup}' en sub_o_sup. Tipos disponibles: {tipos_disponibles}")
    # 6) Layout general
    fig.update_layout(
        title="Porcentaje de muestras anuales de agua en México que exceden el límite de arsénico (NOM-127-SSA1-2021)",
        showlegend=False,
        bargap=0.15
    )
    # 7) mostrar el grafico en la apli
    st.plotly_chart(fig, use_container_width=True)
