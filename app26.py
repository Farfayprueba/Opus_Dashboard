import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import csv
import threading
import re
import os
from sqlalchemy import create_engine
import mysql.connector
import os 
import time
from datetime import datetime, timedelta
from app import app
import logging


os.environ['GH_TOKEN'] = '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'
deleted_rows = []
clientes_guardados = []
completados = 0
total = 0

def get_colaboradores_data():
    query = """
    SELECT usuario
    FROM colaboradores
    WHERE statusData = 1 AND lugar = 'ejecutivo-K'
    """
    mydbs = mysql.connector.connect(
        host='rimgsa.com',
        port=3306,
        user='facebook_admin',
        password='practicas123',
        database='Facebook_mngmnt'
    )
    
    # Ejecutar la consulta y devolver los resultados como un DataFrame
    df = pd.read_sql_query(query, mydbs)
    
    # Cerrar la conexión
    mydbs.close()

    return df

def clientes_inaccesibles():
    query = """
    SELECT nombre
    FROM clientes
    WHERE Opus = 3 AND enlace = 'Enlace_Kenia'
    """
    mydbs = mysql.connector.connect(
            host='rimgsa.com',
            port=3306,
            user='Facebook_user',
            password='user_facebook123',
            database='practicas_facebook_scrapper'
        )
    df = pd.read_sql_query(query, mydbs)
    mydbs.close()
    return df

def post_exists_in_deleted_posts(url):
    try:
        mydb = mysql.connector.connect(
            host='rimgsa.com',
            port=3306,
            user='Facebook_user',
            password='user_facebook123',
            database='practicas_facebook_scrapper'
        )

        cursor = mydb.cursor()
        query = "SELECT * FROM deleted_posts WHERE URL = %s"
        cursor.execute(query, (url,))
        result = cursor.fetchone()
        mydb.close()

        if result:
            return True
        else:
            return False

    except Exception as e:
        print("Error:", str(e))
        return False
    
def obtener_nombre_usuario(link):
    try:
        match = re.search(r'facebook\.com/([^/?]+)', link)
        if match:
            nombre_usuario = match.group(1)
            return nombre_usuario
        else:
            return None
    except:
        return None

def cargar_clientes():
    clientes_guardados = []
    try:
        mydb = mysql.connector.connect(
            host='rimgsa.com',
            port=3306,
            user='Facebook_user',
            password='user_facebook123',
            database='practicas_facebook_scrapper'
        )
        cursor = mydb.cursor()
        query = "SELECT * FROM clientes WHERE estatus = 'Activo'" 
        cursor.execute(query)
        reader = cursor.fetchall()
        mydb.close()
        for row in reader:
            if len(row) >= 5:
                cliente = {
                    'cliente': row[0].lower(),
                    'likes': int(row[1]),
                    'comentarios': int(row[2]),
                    'compartidos': int(row[3]),
                    'lugar': row[4],
                    'prioridad': row[6],
                    'estado': row[7],
                    "nombre":row[9],
                    "cargo": row[11],
                    "partido": row[12],
                    "enlace": row[13]
                }
                nombres_clientes = [c['cliente'] for c in clientes_guardados]
                if cliente['cliente'] not in nombres_clientes:
                    clientes_guardados.append(cliente)
        return clientes_guardados
        
    except FileNotFoundError:
        return [] 
    except Exception as e:
        print("Error:", str(e))
        return []    
    
def delete_rows(df):
    global total
    global completados
    global deleted_rows
    clientes_guardados = cargar_clientes()
    
    for cliente in clientes_guardados:
        likes_goal = cliente["likes"]
        compartidos_goal = cliente["compartidos"]
        comentarios_goal = cliente["comentarios"]
        rows_to_delete = df[(df["Pagina"].str.lower() == cliente["nombre"].lower()) 
                            & ((df["Compartidos"] >= compartidos_goal) &
                                (df["Comentarios"] >= comentarios_goal))]
        if len(rows_to_delete.index) > 0:
            for row_index in rows_to_delete.index.values:
                if row_index not in deleted_rows:
                    deleted_rows.append(row_index)
        df = df.drop(rows_to_delete.index)
    completados = len(deleted_rows)
    total = (len(df)+completados)
    deleted_rows = []
    return df

def asignar_grupo_equipo(row):
    nombre_pagina = row['Pagina']
    for cliente in clientes:
        if cliente['cliente'] == nombre_pagina:
            return cliente['lugar']
    return None

    
def load_data():
    global completados
    global total
    texto = f"{completados}/{total}"
    print(texto)
    clientes = cargar_clientes()
    try:

        mydb = mysql.connector.connect(
            host='rimgsa.com',
            port=3306,
            user='Facebook_user',
            password='user_facebook123',
            database='practicas_facebook_scrapper'
        )

        cursor = mydb.cursor()

        query = "SELECT * FROM clientes_facebook"
        cursor.execute(query)
        results = cursor.fetchall()

        df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
        df = df.drop_duplicates(subset=["Contenido"], keep="last")
        df = df.rename(columns={"Nombre_pagina": "Pagina", "URL_post": "URL", 
                        "Recuento_compartidos": "Compartidos", "Reacciones_totales": "Likes",
                        "Recuento_comentarios": "Comentarios", "Fecha":"Fecha","Hora": "Hora"})

        df = df[["Pagina","URL","Compartidos","Likes","Comentarios","Contenido","Fecha","Hora"]]
        df['Hora'] = pd.to_datetime(df['Hora'], format='%I:%M %p')
        df = df.sort_values(by='Hora', ascending=False)
        df['Hora'] = df['Hora'].dt.strftime('%I:%M %p')
        
        df['Hora'] = pd.to_datetime(df['Hora'], format='%I:%M %p')
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
        df['Fecha_Hora'] = pd.to_datetime(df['Fecha'].dt.strftime('%Y-%m-%d') + ' ' + df['Hora'].dt.strftime('%H:%M:%S'))

        current_time = datetime.now().time()
        current_datetime = datetime.now()
        df['TimeElapsed'] = current_datetime - df['Fecha_Hora']
        df['HoursElapsed'] = df['TimeElapsed'] // timedelta(hours=1) - 6
        df['MinutesElapsed'] = (df['TimeElapsed'] % timedelta(hours=1)) // timedelta(minutes=1)

        df['Tiempo_Transcurrido'] = df['HoursElapsed'].astype(str) + 'h ' + df['MinutesElapsed'].astype(str) + 'm'
        df['Hora'] = df['Hora'].dt.strftime('%I:%M %p')

        df = df[df['Pagina'].apply(lambda x: x.lower()).isin([cliente['cliente'].lower() for cliente in clientes if cliente['enlace'] == "Enlace_Kenia"])]
        
        diccionario_lugares = {cliente['cliente']: cliente['lugar'] for cliente in clientes}
        diccionario_cargo = {cliente['cliente']: cliente['cargo'] for cliente in clientes}
        diccionario_nombre = {cliente['cliente']: cliente['nombre'] for cliente in clientes}
        diccionario_prioridad = {cliente['cliente']: cliente['prioridad'] for cliente in clientes}
        diccionario_meta = {cliente['cliente']: f"{cliente['likes']}/{cliente['comentarios']}/{cliente['compartidos']}" for cliente in clientes}

        df['Grupo_equipo'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_lugares)
        df['Cargo'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_cargo)
        df['Prioridad'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_prioridad) 
        df['Meta'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_meta) 
        df['Pagina'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_nombre)
        
        deleted_contents = set() 
        if clientes and not df.empty:
            df["URL"] = df["URL"].apply(lambda x: "[" + "Ver publicación" + "](" + x + ")")
            df = delete_rows(df)
            consulta_contenidos_borrados = "SELECT Contenido FROM deleted_posts"
            cursor.execute(consulta_contenidos_borrados)
            contenidos_borrados = [contenido[0] for contenido in cursor.fetchall()]
            #print("Contenidos Eliminados:")
            #print(contenidos_borrados)

            # Filtrar el DataFrame df en función de si el contenido está en la lista de contenidos borrados
            df_excluded = df[~df["Contenido"].str.strip().isin(contenidos_borrados) & (df["Contenido"] != "")]

            #print("Publicaciones Excluidas:")
            #print(df_excluded)

            return df_excluded.to_dict("records")

        if not df.empty:
            df["URL"] = df["URL"].apply(lambda x: "[" + "Ver publicación" + "](" + x + ")")
            return df.to_dict("records")
        
        mydb.close()
    except pd.errors.EmptyDataError:
        pass
    return []


table_style = {
    "border": "thin lightgrey solid",
    "position": "absolute",
    "display": "inline-block",
    "width": "100%",
    "tableLayout": "auto",
    "overflowY": "auto"
}

cell_style = {
    "whiteSpace": "normal",
    "textAlign": "left",
    "verticalAlign": "top",
    "maxWidth": "100px",
    "wordBreak": "break-all"
}
columns = [
    {"name": "Fecha", "id": "Fecha"},
    {"name": "Hora", "id": "Hora"},
    {"name": "Pagina", "id": "Pagina"},
    {"name": "URL", "id": "URL", "type": "text", "presentation": "markdown"},
    {"name": "Likes", "id": "Likes"},
    {"name": "Comentarios", "id": "Comentarios"},
    {"name": "Compartidos", "id": "Compartidos"},
    {"name": "Meta", "id": "Meta"},
    {"name": "Grupo", "id": "Grupo_equipo"},
    {"name": "Prioridad", "id": "Prioridad"},
    {"name": "Cargo","id":"Cargo"}
]

# Crear una lista para almacenar los clientes agregados
clientes = []

layout = html.Div(
    children=[
        html.H1("Proyecto Opus Ejecutivo Kenia"),
        html.Div(id='output-container'),
        html.Div(style={'position': 'fixed', 'top': '0', 'left': '990px', 'width': '100%', 'height': '220px', 'overflowY': 'scroll', 'font-size': '40px', "font-weight": "bold",},
                children=[
                    dcc.Interval(
                    id='interval-component-ejecutivo-K',
                    interval=60*1000,  # Actualizar cada minuto
                    n_intervals=0
                ),
                dcc.Graph(id='colaboradores-data-ejecutivo-K', 
                           config={'displayModeBar': False},
                           style={'width': '10%', "font-weight": "bold", 'font-size': '40px'} ),
            ]),
        html.Div(
                    #style={'display':'inline-block', 'flex-direction': 'row-reverse', 'flex-grow': '1', "width": "100%"},
                    style={'display': 'inlne-block', 'justify-content': 'flex-start', "width": "100%", 'flex-direction': 'row-reverse', 'flex-grow': '1'},
                    children=[
                        html.Div(
                            id='contador-ejecutivo-K',
                            style={
                                "text-align": "left",
                                "margin-left": "25px",
                                "font-size": "28px",
                                "font-weight": "bold",
                                "white-space": "pre-line", # Agrega esta línea para hacer que el texto sea más grueso
                                
                            }
                        ),
                    html.Div(
                            style={'display': 'inlne-block', 'justify-content': 'flex-start', "width": "100%", 'flex-direction': 'row-reverse', 'flex-grow': '1'},
                            children=[
                                dcc.Interval(
                                    id='interval',
                                    interval=1000,  # 1 segundo
                                    n_intervals=0
                                ),
                                html.H1(id='countdown-ejecutivo-K', style={'font-size': '48px', 'margin-left': '30px', 'display': 'inlne-block',}),
                                html.P(id='message-ejecutivo-K', style={'font-size': '20px', 'margin-left': '30px'}),
                            ]
                        ),
        html.Div(id="clientes_inaccesibles_kenia"),
        html.H2(""),
        # Agregar las selecciones de opción múltiple
        html.Div(
            children=[
                html.H2("Pool"),
                html.Div(
                    dash_table.DataTable(
                        id="data-table2-ejecutivo-K",
                        columns=columns,
                        data=load_data(),  # Llama a load_data() para cargar los datos iniciales en el pool
                        style_table=table_style,
                        style_cell=cell_style,
                        style_data={'color': 'black'},
                        style_header={'color':'black'},
                        style_data_conditional=[
                            {
                                 'if': {'filter_query': '{Cargo} eq "PRE. MUNICIPAL"'},
                                 'backgroundColor': '#ea9999'
                            },
                            {
                                'if': {'filter_query': '{Cargo} eq "DIP. LOCAL"'},
                                'backgroundColor': '#674ea7',
                                "color": "white"
                            },
                            {
                                'if': {'filter_query': '{Cargo} eq "DIP. FEDERAL"'},
                                'backgroundColor': '#fffd94'
                            },
                            {
                                'if': {'filter_query': '{Cargo} eq SENADOR'},
                                'backgroundColor': 'lightgreen'
                            },
                            {   'if': {'filter_query': '{Cargo} eq VIP'},
                                'backgroundColor': 'lightblue'
                            }
                        ]
                    )
                ),
            ],
            style={"width": "100%", "display": "inline-block","vertical-align": "top"}
        ),
        dcc.Interval(
            id='interval-component',
            interval=180 * 1000,  # 30 segundos en milisegundos
            n_intervals=0
        ),
            ]
        )
        
    ],
    style={"margin": "10px"}
    
)

@app.callback(
    Output('colaboradores-data-ejecutivo-K', 'figure'),
    Input('interval-component-ejecutivo-K', 'n_intervals')
)
def update_colaboradores_data(n):
    df = get_colaboradores_data()
    figure = {
        'data': [
            {
                'type': 'table',
                'header': {
                    'values': ["Usuarios activos"]  # Cabeceras de las columnas
                },
                'cells': {
                    'values': [df['usuario']],
                    'line': {'color': 'black', 'width': 1},  # Línea de separación de las celdas
                    'fill': {'color': 'white'} 
                }
            }
        ],
            'layout': {
            'margin': {'t': 10, 'l': 10, 'r': 10, 'b': 10},
            'font': {
            'family': 'Arial, sans-serif',  # Tipo de fuente
            'size': 12,  # Tamaño de fuente
            'color': 'black',  # Color del texto
            'weight': 'bold'  # Negrita
        }
            
        },
        

    }
    
    return figure

@app.callback(
    Output('clientes_inaccesibles_kenia', 'children'),
    Input('interval-component-ejecutivo-K', 'n_intervals')
)
def clientes(n):    
    df = clientes_inaccesibles()
    
    if df.empty:
        return ""
    num_columns = 10  
    names = df['nombre'].tolist()
    rows = [names[i:i+num_columns] for i in range(0, len(names), num_columns)]
    table_rows = [html.Tr([html.Td(nombre) for nombre in row]) for row in rows]
    table = html.Table([
        html.Thead(html.Tr([html.Th("Clientes Inaccesibles")])),  
        html.Tbody(table_rows) 
    ])
    return table
    
@app.callback(
    Output('contador-ejecutivo-K', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_counter(n):    
    total_post = f"Total de posts: {total} \n"
    post_sin_metricas = f"Posts que aún no llegan a sus métricas: {total - completados} \n"
    post_con_metricas = f"Post que han llegado a sus métricas: {completados} \n"
    
    return total_post, post_sin_metricas, post_con_metricas


@app.callback(
    Output('button-agregar-ejecutivo-K', 'disabled'),  # Habilitar/deshabilitar el botón de agregar
    [Input('input-cliente-ejecutivo-K', 'value'),
     Input('input-likes-ejecutivo-K', 'value'),
     Input('input-comentarios-ejecutivo-K', 'value'),
     Input('input-compartidos-ejecutivo-K', 'value'),
     Input('input-ubicacion-ejecutivo-K','value')]
)
def update_button_disabled(cliente, likes, comentarios, compartidos,lugar):
    if cliente and likes is not None and comentarios is not None and compartidos is not None and lugar is not None:
        return False
    return True

@app.callback(
    Output('clear-button-ejecutivo-K', 'disabled'),  # Disable the delete button if no row is selected
    [Input('data-table', 'selected_rows')]
)
def update_button_disabled2(selected_rows):
    return len(selected_rows) == 0


@app.callback(Output('data-table2-ejecutivo-K', 'data'),
              Input('interval-component', 'n_intervals'))
def update_data_table2(n_intervals):
    updated_data = load_data()
    return updated_data

@app.callback(
    Output('input-cliente-ejecutivo-K', 'value'),  # Limpiar el campo de entrada
    Output('input-likes-ejecutivo-K', 'value'),  # Limpiar la selección de likes
    Output('input-comentarios-ejecutivo-K', 'value'),  # Limpiar la selección de comentarios
    Output('input-compartidos-ejecutivo-K', 'value'),
    Output('input-ubicacion-ejecutivo-K', 'value'),  # Limpiar la selección de compartidos
    [Input('button-agregar-ejecutivo-K', 'n_clicks'),
     Input('clear-button-ejecutivo-K', 'n_clicks')],  # Include clear-button-ejecutivo-K as input trigger
    prevent_initial_call=True
)
def clear_inputs(n_clicks_agregar, n_clicks):
    return '', None, None, None,None

@app.callback(
    Output('countdown-ejecutivo-K', 'children'),
    Output('message-ejecutivo-K', 'children'),
    Input('interval', 'n_intervals'),
    State('countdown-ejecutivo-K', 'children')
)
def update_countdown(n_intervals, countdown):
    remaining_time = 600 - (n_intervals % 600) - 1
    if remaining_time <= 0:
        remaining_time = 600
        message = 'Actualizando datos'
    else:
        message = ''
    return f'{remaining_time // 60:02}:{remaining_time % 60:02}', message
