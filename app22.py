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
#from flask import send_from_directory
import logging


os.environ['GH_TOKEN'] = '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'
deleted_rows = []
clientes_guardados = []
completados = 0
total = 0

def clientes_inaccesibles():
    query = """
    SELECT nombre
    FROM clientes
    WHERE Opus = 3 AND lugar = 'HERCULES5' AND estatus = 'Activo'
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

def get_colaboradores_data():
    query = """
    SELECT usuario
    FROM colaboradores
    WHERE statusData = 1 AND lugar = 'hercules5'
    """
    mydbs = mysql.connector.connect(
        host='rimgsa.com',
        port=3306,
        user='facebook_admin',
        password='practicas123',
        database='Facebook_mngmnt'
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
        # Utilizar expresiÃ³n regular para encontrar el nombre de usuario
        match = re.search(r'facebook\.com/([^/?]+)', link)
        if match:
            nombre_usuario = match.group(1)
            return nombre_usuario
        else:
            return None
    except:
        return None

def guardar_clientes(clientes):
        global clientes_guardados
        if len(clientes) > 0:
            keys = list(clientes[0].keys())
            df = pd.DataFrame(clientes)
            df = df[keys]  # Rearrange the columns to match the keys order
            df.columns = keys
        else:
            df = pd.DataFrame(columns=["cliente","likes","comentarios","compartidos","lugar"])
            clientes_guardados = []
            database_type = 'mysql'  # Tipo de base de datos (puedes cambiarlo según tu base de datos)
            user = 'Facebook_user'  # Usuario de la base de datos
            password = 'user_facebook123'  # Contraseña de la base de datos
            host = "rimgsa.com"
            database_name = 'practicas_facebook_scrapper'  # Nombre de la base de datos

            db_connection_str = f'{database_type}://{user}:{password}@{host}/{database_name}'

            engine = create_engine(db_connection_str)

        # Subir el DataFrame a la tabla de la base de datos reemplazando los registros existentes
        df.to_sql(name='clientes', con=engine, if_exists='replace', index=False)
        engine.dispose()

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
        query = "SELECT * FROM clientes WHERE estatus = 'Activo'" ####modificar esta consulta#########JESUS
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
                    'prioridad': row[6],####agregar la prioridad desde la base de datos#########JESUS
                    'estado': row[7],####agregar el estado desde la base de datos#######JESUS
                    "nombre":row[9],
                    "cargo": row[11]
                }
                nombres_clientes = [c['cliente'] for c in clientes_guardados]
                if cliente['cliente'] not in nombres_clientes:
                    clientes_guardados.append(cliente)
        return clientes_guardados
        
    except FileNotFoundError:
        return []  # Devuelve una lista vacía si el archivo no existe

    except Exception as e:
        print("Error:", str(e))
        return []  # Devuelve una lista vacía en caso de cualquier otro error
    

def delete_rows(df):
    global deleted_rows
    global total
    global completados
    global likes_totales
    global comentarios_totales
    global compartidos_totales
    total = 0
    completados = 0
    likes_totales = 0
    comentarios_totales = 0
    compartidos_totales = 0
    clientes_guardados = cargar_clientes()
    for cliente in clientes_guardados:
        likes_goal = cliente["likes"]
        compartidos_goal = cliente["compartidos"]
        comentarios_goal = cliente["comentarios"]
        rows_to_delete = df[df.apply(lambda row: (row["Pagina"].lower() == cliente["nombre"].lower()) and
                                         ((row["Reshare"] == "0" and row["Compartidos"] >= compartidos_goal and
                                           row["Comentarios"] >= comentarios_goal) or
                                          (row["Reshare"] == "1" and row["Comentarios"] >= 10 and
                                           row["Compartidos"] >= 20)),axis=1)]
        if len(rows_to_delete.index) > 0:
            for row_index in rows_to_delete.index.values:
                if row_index not in deleted_rows:
                    deleted_rows.append(row_index)
        df = df.drop(rows_to_delete.index)
    completados = len(deleted_rows)
    total = (len(df)+completados)
    deleted_rows = []

    clientes_presentes = df['Pagina'].str.lower().tolist()
    print(clientes_presentes)
    resultados_db = consultar_base_de_datos()
    print(f"Métricas totales antes: Likes {likes_totales}, Comentarios {comentarios_totales}, Compartidos {compartidos_totales}")
    for cliente in clientes_presentes:
        cliente = cliente.lower()
        cliente_rows = [row for row in resultados_db if row['cliente'].lower() == cliente]

        if cliente_rows:
            total_likes = sum(row['total_likes'] for row in cliente_rows)
            total_comentarios = sum(row['total_comentarios'] for row in cliente_rows)
            total_compartidos = sum(row['total_compartidos'] for row in cliente_rows)
            print(f"Procesando cliente: {cliente}, Likes: {total_likes}, Comentarios: {total_comentarios}, Compartidos: {total_compartidos}")

            # Actualizar métricas en el DataFrame
            mask = df['Pagina'].str.lower() == cliente
            df.loc[mask, 'Likes'] += total_likes
            df.loc[mask, 'Comentarios'] += total_comentarios
            df.loc[mask, 'Compartidos'] += total_compartidos

            # Actualizar variables locales
            likes_totales += total_likes
            comentarios_totales += total_comentarios
            compartidos_totales += total_compartidos

    # Imprimir métricas totales después de la actualización
    print(f"Métricas totales después: Likes {likes_totales}, Comentarios {comentarios_totales}, Compartidos {compartidos_totales}")

    return df

def consultar_base_de_datos():
    # Conexión a la base de datos MySQL
    mydb = mysql.connector.connect(
        host='rimgsa.com',
        port=3306,
        user='Facebook_user',
        password='user_facebook123',
        database='practicas_facebook_scrapper'
    )

    cursor = mydb.cursor(dictionary=True)

    try:
        sql = "SELECT cliente, SUM(likes) AS total_likes, SUM(comentarios) AS total_comentarios, SUM(compartidos) AS total_compartidos FROM clientes GROUP BY cliente"
        cursor.execute(sql)
        results = cursor.fetchall()

    finally:
        mydb.close()

    return results

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
    clientes_guardados = cargar_clientes()
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

        # Query to fetch data from clientes_facebook table
        query = "SELECT * FROM clientes_facebook"
        cursor.execute(query)
        results = cursor.fetchall()

        # Convert the results to a pandas DataFrame
        df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
        df = df.drop_duplicates(subset=["Contenido"], keep="last")
        df = df.rename(columns={"Nombre_pagina": "Pagina", "URL_post": "URL", 
                        "Recuento_compartidos": "Compartidos", "Reacciones_totales": "Likes",
                        "Recuento_comentarios": "Comentarios", "Fecha":"Fecha","Hora": "Hora"})

        df = df[["Pagina","URL","Compartidos","Likes","Comentarios","Contenido","Fecha","Hora","Reshare"]]
        df['Hora'] = pd.to_datetime(df['Hora'], format='%I:%M %p')
        df = df.sort_values(by='Hora', ascending=False)
        df['Hora'] = df['Hora'].dt.strftime('%I:%M %p')
        
        ###Cálculo para saber el tiempo transcurrido desde la hora del post
        df['Hora'] = pd.to_datetime(df['Hora'], format='%I:%M %p')
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
        df['Fecha_Hora'] = pd.to_datetime(df['Fecha'].dt.strftime('%Y-%m-%d') + ' ' + df['Hora'].dt.strftime('%H:%M:%S'))

        # Calculate the time difference in hours and minutes
        current_time = datetime.now().time()
        current_datetime = datetime.now()
        df['TimeElapsed'] = current_datetime - df['Fecha_Hora']
        df['HoursElapsed'] = df['TimeElapsed'] // timedelta(hours=1) - 6
        df['MinutesElapsed'] = (df['TimeElapsed'] % timedelta(hours=1)) // timedelta(minutes=1)

        # Format the elapsed time as a string
        df['Tiempo_Transcurrido'] = df['HoursElapsed'].astype(int)
        df['Hora'] = df['Hora'].dt.strftime('%I:%M %p')

        df = df[df['Pagina'].apply(lambda x: x.lower()).isin([cliente['cliente'].lower() for cliente in clientes if cliente['lugar'] == "HERCULES5"])]
        # Crear un diccionario que mapee el nombre del cliente con el valor de "lugar" correspondiente
        diccionario_lugares = {cliente['cliente']: cliente['lugar'] for cliente in clientes}
        diccionario_cargo = {cliente['cliente']: cliente['cargo'] for cliente in clientes}
        diccionario_nombre = {cliente['cliente']: cliente['nombre'] for cliente in clientes}
        diccionario_prioridad = {cliente['cliente']: cliente['prioridad'] for cliente in clientes}
        diccionario_meta = {cliente['cliente']: f"{cliente['likes']}/{cliente['comentarios']}/{cliente['compartidos']}" for cliente in clientes}

        # Aplicar el mapeo al DataFrame original
        df['Grupo_equipo'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_lugares)
        df['Cargo'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_cargo)
        df['Prioridad'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_prioridad) ###########agregamos la prioridad del cliente############JESUS
        df['Meta'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_meta) ###########agregamos la Meta del cliente############JESUS
        df['Pagina'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_nombre)

        
        # Filtrar las publicaciones basadas en la columna "Contenido" y las publicaciones eliminadas
        deleted_contents = set()  # Almacenar los contenidos eliminados
        if clientes_guardados and not df.empty:
            df["URL"] = df["URL"].apply(lambda x: "[" + "Ver publicación" + "](" + x + ")")
            df = df.sort_values(["Tiempo_Transcurrido"], ascending=[False])
            df = delete_rows(df)
            #df = actualizar_dashboard(df)

            
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
    {"name": "Meta", "id": "Meta"}, #########agregamos esto y eliminamos algunas de fechas que pidieron###########################JESUS
    {"name": "Grupo", "id": "Grupo_equipo"},
    #{"name": "Prioridad", "id": "Prioridad"},
    {"name": "Cargo","id":"Cargo"}
]

# Crear una lista para almacenar los clientes agregados
clientes = []

layout = html.Div(
    children=[
        html.H1("Proyecto Opus Team Hercules (5)"),
        html.H1(id="total_clientes-hercules5", #cambiar id
                style={'float': 'right',
                    "margin-right":"50px",
                    "font-size": "28px",
                    "font-weight": "bold",
                    "white-space": "pre-line", 
                }),
        html.Div(id='output-container'),
        html.Div(style={'position': 'fixed', 'top': '0', 'left': '990px', 'width': '100%', 'height': '220px', 'overflowY': 'scroll', 'font-size': '40px', "font-weight": "bold",},
                children=[
                    dcc.Interval(
                    id='interval-component-hercules5',
                    interval=60*1000,  # Actualizar cada minuto
                    n_intervals=0
                ),
                dcc.Graph(id='colaboradores-data-hercules5', 
                          config={'displayModeBar': False},
                          style={'width': '10%', "font-weight": "bold", 'font-size': '40px'} ),
            ]),
        html.Div(style={'position': 'fixed', 'top': '0', 'left': '800px', 'width': '100%', 'height': '220px', 'overflowY': 'scroll', 'font-size': '40px', "font-weight": "bold",},
                children=[
                dcc.Graph(id='clientes-data-hercules5', 
                          config={'displayModeBar': False},
                          style={'width': '10%', "font-weight": "bold", 'font-size': '40px'} ),
            ]),
        html.Div(
                    #style={'display':'inline-block', 'flex-direction': 'row-reverse', 'flex-grow': '1', "width": "100%"},
                    style={'display': 'inlne-block', 'justify-content': 'flex-start', "width": "100%", 'flex-direction': 'row-reverse', 'flex-grow': '1'},
                    children=[
                        html.Div(
                            id='contador-hercules-(5)',
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
                                html.H1(id='countdown-hercules-(5)', style={'font-size': '48px', 'margin-left': '30px', 'display': 'inlne-block',}),
                                html.P(id='message-hercules-(5)', style={'font-size': '20px', 'margin-left': '30px'}),
                            ]
                        ),
        html.Div(id="clientes_inaccesibles_hercules5"),
        html.H2(""),
        html.Div(
            children=[
                html.H2("Pool"),
                html.Div(
                    dash_table.DataTable(
                        id="data-table2-hercules-(5)",
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
    Output('total_clientes-hercules5', 'children'),
    Input('interval-component-hercules5', 'n_intervals')
)
def update_colaboradores_data(n):
    df = cargar_clientes()
    df = pd.DataFrame(df)
    df = df[df["lugar"] == "HERCULES5"]
    return html.Div(f"Total de clientes: {len(df)} \n")

@app.callback(
    Output('clientes_inaccesibles_hercules5', 'children'),
    Input('interval-component-hercules5', 'n_intervals')
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
    Output('colaboradores-data-hercules5', 'figure'),
    Input('interval-component-hercules5', 'n_intervals')
)
def update_colaboradores_data(n):
    df = get_colaboradores_data()
    figure = {
        'data': [
            {
                'type': 'table',
                'header': {
                    'values': ["Usuarios Activos"],
                    'font': {'size': 16, 'color': 'white'},  # Tamaño y color de la fuente del encabezado
                    'fill': {'color': 'orange'}  
                },
                'cells': {
                    'values': [df['usuario']],
                    'line': {'color': 'black', 'width': 1}, 
                    'fill': {'color': 'white'},
                    'font': {'size': 12, 'color': 'black'},  # Tamaño y color de la fuente de las celdas
                    'align': ['center'] 
                }
            }
        ],
            'layout': {
            'margin': {'t': 10, 'l': 10, 'r': 10, 'b': 10},
            'font': {
            'family': 'Arial, sans-serif', 
            'size': 12, 
            'color': 'black', 
            'weight': 'bold'  
        }
        },
    }
    return figure

@app.callback(
    Output('clientes-data-hercules5', 'figure'),
    Input('interval-component-hercules5', 'n_intervals')
)
def update_colaboradores_data(n):
    df = cargar_clientes()
    df = pd.DataFrame(df)
    df = df[df["lugar"] == "HERCULES5"]
    figure = {
        'data': [
            {
                'type': 'table',
                'header': {
                    'values': ["Clientes activos"],
                    'align': ['center'],
                    'font': {'size': 16, 'color': 'white'},  
                    'fill': {'color': '#007BFF'},  
                },
                'cells': {
                    'values': [df['nombre']],
                    'line': {'color': 'black', 'width': 1},  
                    'fill': {'color': ['#f7f7f7', 'white']}, 
                    'font': {'size': 12, 'color': 'black'},  
                    'align': ['center']  
                }
            }
        ],
        'layout': {
            'margin': {'t': 10, 'l': 10, 'r': 10, 'b': 10},
            'font': {
                'family': 'Arial, sans-serif',
                'size': 12,
            }
        },
    }
    return figure


@app.callback(
    Output('contador-hercules-(5)', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_counter(n):    
    total_post = f"Total de posts: {total} \n"
    post_sin_metricas = f"Posts que aún no llegan a sus métricas: {total - completados} \n"
    post_con_metricas = f"Post que han llegado a sus métricas: {completados} \n"
    return total_post, post_sin_metricas, post_con_metricas




@app.callback(
    Output('button-agregar-hercules-(5)', 'disabled'),  # Habilitar/deshabilitar el botón de agregar
    [Input('input-cliente-hercules-(5)', 'value'),
     Input('input-likes-hercules-(5)', 'value'),
     Input('input-comentarios-hercules-(5)', 'value'),
     Input('input-compartidos-hercules-(5)', 'value'),
     Input('input-ubicacion-hercules-(5)','value')]
)
def update_button_disabled(cliente, likes, comentarios, compartidos,lugar):
    if cliente and likes is not None and comentarios is not None and compartidos is not None and lugar is not None:
        return False
    return True

@app.callback(
    Output('clear-button-hercules-(5)', 'disabled'),  # Disable the delete button if no row is selected
    [Input('data-table', 'selected_rows')]
)
def update_button_disabled2(selected_rows):
    return len(selected_rows) == 0

@app.callback(Output('data-table2-hercules-(5)', 'data'),
              Input('interval-component', 'n_intervals'))
def update_data_table2(n_intervals):
    updated_data = load_data()
    return updated_data

@app.callback(
    Output('input-cliente-hercules-(5)', 'value'),  # Limpiar el campo de entrada
    Output('input-likes-hercules-(5)', 'value'),  # Limpiar la selección de likes
    Output('input-comentarios-hercules-(5)', 'value'),  # Limpiar la selección de comentarios
    Output('input-compartidos-hercules-(5)', 'value'),
    Output('input-ubicacion-hercules-(5)', 'value'),  # Limpiar la selección de compartidos
    [Input('button-agregar-hercules-(5)', 'n_clicks'),
     Input('clear-button-hercules-(5)', 'n_clicks')],  # Include clear-button-hercules-(5) as input trigger
    prevent_initial_call=True
)
def clear_inputs(n_clicks_agregar, n_clicks):
    return '', None, None, None,None

@app.callback(
    Output('countdown-hercules-(5)', 'children'),
    Output('message-hercules-(5)', 'children'),
    Input('interval', 'n_intervals'),
    State('countdown-hercules-(5)', 'children')
)
def update_countdown(n_intervals, countdown):
    remaining_time = 600 - (n_intervals % 600) - 1
    if remaining_time <= 0:
        remaining_time = 600
        message = 'Actualizando datos'
    else:
        message = ''
    return f'{remaining_time // 60:02}:{remaining_time % 60:02}', message