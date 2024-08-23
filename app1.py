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
import mysql.connector

#from flask import send_from_directory
import logging



# Configurar la información de registro
logging.basicConfig(filename='app1.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

#USER_PASS_MAPPING = {"Admin_Opus":"Opus123", "admin123":"Opus456"}


os.environ['GH_TOKEN'] = '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'
deleted_rows = []
clientes_guardados = []
completados = 0
total = 0
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
                    'prioridad': row[6], ###agregar la prioridad desde la base de datos#########JESUS
                    'estado': row[7], ####agregar el estado desde la base de datos#######JESUS
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

# Importa otras bibliotecas según sea necesario

# Variables globales
total = 0
completados = 0
deleted_rows = []

# Tu función original
def delete_rows(df):
    global total
    global completados
    global deleted_rows
    global Likes_totales
    global Compartidos_totales
    global Comentarios_totales
    
    # Carga clientes y métricas totales
    clientes_guardados = cargar_clientes()
    cargar_metricas_totales()
    
    # Suma las métricas totales
    Likes_totales = sum([cliente["likes"] for cliente in clientes_guardados])
    Compartidos_totales = sum([cliente["compartidos"] for cliente in clientes_guardados])
    Comentarios_totales = sum([cliente["comentarios"] for cliente in clientes_guardados])
    
    # Consulta la tabla de la base de datos y suma las métricas de clientes detectados
    consulta_metricas_db()
    
    # Elimina filas según las métricas definidas
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
        
    # Actualiza las variables globales y retorna el DataFrame modificado
    completados = len(deleted_rows)
    total = len(df) + completados
    deleted_rows = []
    return df


# Función para cargar las métricas totales desde la tabla en la base de datos
def cargar_metricas_totales():
    global Likes_totales
    global Compartidos_totales
    global Comentarios_totales
    
    # Lógica para cargar Likes_totales, Compartidos_totales, Comentarios_totales desde la tabla de la base de datos
    # (reemplaza esto con tu lógica específica)
    Likes_totales = 0
    Compartidos_totales = 0
    Comentarios_totales = 0



def consulta_metricas_db():
    global Likes_totales
    global Compartidos_totales
    global Comentarios_totales
    
    # Configura la conexión a la base de datos
    connection = mysql.connector.connect(
       host='rimgsa.com',
            port=3306,
            user='Facebook_user',
            password='user_facebook123',
            database='practicas_facebook_scrapper'
    )

    # Crea un cursor para ejecutar consultas SQL
    cursor = connection.cursor()

    # Ejecuta una consulta para obtener las métricas por cliente
    consulta_sql = "SELECT cliente, SUM(likes) AS total_likes, SUM(compartidos) AS total_compartidos, SUM(comentarios) AS total_comentarios FROM clientes GROUP BY cliente"
    cursor.execute(consulta_sql)

    # Recorre los resultados y suma las métricas al total
    for (cliente, total_likes, total_compartidos, total_comentarios) in cursor:
        Likes_totales += total_likes
        Compartidos_totales += total_compartidos
        Comentarios_totales += total_comentarios

    # Cierra el cursor y la conexión
    cursor.close()
    connection.close()



def subir_cliente(cliente):
    try:
        mydb = mysql.connector.connect(
            host='rimgsa.com',
            port=3306,
            user='Facebook_user',
            password='user_facebook123',
            database='practicas_facebook_scrapper'
        )
        clientes_totales = cargar_clientes()
        nombres_clientes = [c['cliente'] for c in clientes_totales]
        if cliente not in nombres_clientes:
            cursor = mydb.cursor()
            query = "INSERT INTO clientes (cliente, likes, comentarios, compartidos, lugar) VALUES (%s, %s, %s, %s, %s)"
            values = (cliente['cliente'], cliente['likes'], cliente['comentarios'], cliente['compartidos'], cliente['lugar'])
            cursor.execute(query, values)
            mydb.commit()
            cursor.close()
            mydb.close()
        else:
            return 0  
    except mysql.connector.Error as e:
        print("Error while uploading the client:", e)
        return False
    return True
    
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

        df = df[["Pagina","URL","Compartidos","Likes","Comentarios","Contenido","Fecha","Hora"]]
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

        # Crear un diccionario que mapee el nombre del cliente con el valor de "lugar" correspondiente
        diccionario_cargo = {cliente['cliente']: cliente['cargo'] for cliente in clientes}
        diccionario_lugares = {cliente['cliente']: cliente['lugar'] for cliente in clientes}
        diccionario_nombre = {cliente['cliente']: cliente['nombre'] for cliente in clientes}
        diccionario_prioridad = {cliente['cliente']: cliente['prioridad'] for cliente in clientes}
        diccionario_meta = {cliente['cliente']: f"{cliente['likes']}/{cliente['comentarios']}/{cliente['compartidos']}" for cliente in clientes}

        # Aplicar el mapeo al DataFrame original
        df['Grupo_equipo'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_lugares)
        df['Cargo'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_cargo)
        df['Prioridad'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_prioridad) ###########agregamos la prioridad del cliente############JESUS
        df['Meta'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_meta) ###########agregamos la Meta del cliente############JESUS
        df['Pagina'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_nombre)

        #print("Original URLs:")
        #print(df["URL"])

        #for url in df["URL"]:
            #print(url)

        
        # Filtrar las publicaciones basadas en la columna "Contenido" y las publicaciones eliminadas
        deleted_contents = set()  # Almacenar los contenidos eliminados
        if clientes_guardados and not df.empty:
            df["URL"] = df["URL"].apply(lambda x: "[" + "Ver publicación" + "](" + x + ")")
            df = df.sort_values(["Tiempo_Transcurrido"], ascending=[False])
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
    {"name": "Meta", "id": "Meta"}, #########agregamos esto y eliminamos algunas de fechas que pidieron###########################JESUS
    {"name": "Grupo", "id": "Grupo_equipo"},
    {"name": "Prioridad", "id": "Prioridad"},
    {"name": "Cargo","id":"Cargo"}
   # Agrega más columnas si es necesario
]
# Crear una lista para almacenar los clientes agregados
clientes = []

layout = html.Div(
    children=[
        html.H1("Dashboard de Facebook Scraper"),
        html.Div(
            children=[
                html.Div(id='output-container'),
                html.Div(
                    style={'display': 'flex', 'flex-direction': 'row-reverse', 'flex-grow': '1'},
                    children=[
                        html.Div(
                            id='contador',
                            style={
                                "text-align": "left",
                                "margin-left": "240px",
                                "font-size": "28px",
                                "font-weight": "bold", # Agrega esta línea para hacer que el texto sea más grueso
                                "white-space": "pre-line", 
                                "margin-right":"21%",
                                "margin-bottom":"3%"
                            }
                        ),
                        html.Div(
                            style={'display': 'inlne-block','align-items':'center'},
                            children=[
                                dcc.Interval(
                                    id='interval',
                                    interval=1000,  # 1 segundo
                                    n_intervals=0
                                ),
                                html.H1(id='countdown', style={'font-size': '48px', 'margin-left': '30px', 'display': 'inlne-block',}),
                                html.P(id='message', style={'font-size': '20px', 'margin-left': '30px'}),
                            ]
                        ),
                html.Div(
                    children=[
                        html.Div(
                            dcc.Input(id='input-cliente', type='text', placeholder='Agregar cliente'),
                            style={"margin-right": "10px"}  # Aplicar un margen derecho al campo de entrada
                        ),
                        dcc.Input(
                            id='input-likes',
                            type='number',
                            placeholder="Numero de likes",
                            min=0
                        ),
                        dcc.Input(
                            id='input-comentarios',
                            type='number',
                            placeholder="Numero de comentarios",
                            min=0
                        ),
                        dcc.Input(
                            id='input-compartidos',
                            type='number',
                            placeholder="Numero de compartidos",
                            min=0
                        ),
                        dcc.Dropdown(
                            id='input-ubicacion',
                            options=[
                                {'label': 'Team Hercules', 'value': 'HERC'},
                                {'label': 'Team Masarik', 'value': 'MASA'},
                                {'label': 'Team C', 'value': 'C'}
                            ],
                            placeholder='Seleccionar grupo',
                           style={
                                'backgroundColor': 'white',  # Cambiar el color de fondo a blanco
                                'color': 'black',  # Mantener el color de texto en negro
                                'width': "210px"
                            },
                        ),
                        html.Button('Agregar', id='button-agregar', disabled=True),  # Agrega el atributo 'disabled'
                    ],
                    style={"width": "15%", "display": "inline-block","height": "10px","margin-right":"10px"}
                ),
                
                    ]
                )
            ],
            style={"margin-bottom": "10px"}
        ),
        
        html.H2(""),
        html.Div(
            children=[
                html.H2("Clientes"),
                dash_table.DataTable(
                    id="data-table",
                    columns=[{"name": "Cliente", "id": "cliente"}],
                    data=cargar_clientes(),  # Cargar los clientes al inicio
                    row_selectable='single',
                    selected_rows=[],
                    style_table={'overflowY': 'scroll','backgroundColor': 'transparent'},
                    style_cell={'height': '30px', 'minWidth': '0px', 'maxWidth': '180px'},
                    style_filter={'backgroundColor': '#D9D9D9', 'border': '1px solid #d3d3d3', 'padding': '5px'},
                    style_data={'color': 'black'},
                    style_header={'color':'black'},
                    filter_action='native',  # Habilitar la funcionalidad de filtrado nativo
                    sort_action='native'  # Habilitar la funcionalidad de ordenar nativo
                ),
                dbc.Button('Borrar cliente', id='clear-button', color='primary',size='sm', disabled=True,  n_clicks=0)
            ],
            style={"width": "15%", "display": "inline-block","vertical-align": "top"}
        ),
        # Agregar las selecciones de opción múltiple
         html.Div(
            children=[
                html.H2("Pool"),
                html.Div(
                    dash_table.DataTable(
                        id="data-table2",
                        columns=columns,
                        data=load_data(),  # Llama a load_data() para cargar los datos iniciales en el pool
                        style_table=table_style,
                        style_cell=cell_style,
                        style_data={'color': 'black'},
                        style_header={'color':'black'},
                        row_selectable='single',
                        selected_rows=[],
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
            style={"width": "77%", "margin-left": "3%", "display": "inline-block","vertical-align": "top"}
        ),
        html.Div(
            dbc.Button('Borrar post', id='clear-post', color='primary', size='sm', disabled=True, n_clicks=0),
            style={"margin-top": "10px", "text-align": "left"}  # Add a margin at the top and center-align the button
        ),
        dcc.Interval(
            id='interval-component',
            interval=20 * 1000,  # 30 segundos en milisegundos
            n_intervals=0
        ),
    ],
    style={"margin": "10px"}
)
@app.callback(
    Output('contador', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_counter(n):    
    total_post = f"Total de posts: {total} \n"
    post_sin_metricas = f"Posts que aún no llegan a sus métricas: {total - completados} \n"
    post_con_metricas = f"Post que han llegado a sus métricas: {completados} \n"
    
    return total_post, post_sin_metricas, post_con_metricas

@app.callback(
    Output('button-agregar', 'disabled'),  # Habilitar/deshabilitar el botón de agregar
    [Input('input-cliente', 'value'),
     Input('input-likes', 'value'),
     Input('input-comentarios', 'value'),
     Input('input-compartidos', 'value'),
     Input('input-ubicacion','value')]
)
def update_button_disabled(cliente, likes, comentarios, compartidos,lugar):
    if cliente and likes is not None and comentarios is not None and compartidos is not None and lugar is not None:
        return False
    return True


@app.callback(
    Output('clear-button', 'disabled'),  # Disable the delete button if no row is selected
    [Input('data-table', 'selected_rows')]
)
def update_button_disabled2(selected_rows):
    return len(selected_rows) == 0

@app.callback(
    Output('data-table', 'data'),
    [Input('button-agregar', 'n_clicks'),
     Input('clear-button', 'n_clicks'),
     Input('data-table', 'selected_rows')],  # Add selected_rows as an Input
    [State('input-cliente', 'value'),
     State('input-likes', 'value'),
     State('input-comentarios', 'value'),
     State('input-compartidos', 'value'),
     State('input-ubicacion','value')],
    prevent_initial_call=True
)
def update_clientes_table(n_clicks_agregar, n_clicks, selected_rows, cliente, likes, comentarios, compartidos,lugar):

    global clientes_guardados

    if not clientes_guardados:
        clientes_guardados = cargar_clientes()

    ctx = dash.callback_context

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'button-agregar' and cliente and likes is not None and comentarios is not None and compartidos is not None:
            cliente = obtener_nombre_usuario(cliente)
            nuevo_cliente = {
                'cliente': cliente,
                'likes': int(likes),
                'comentarios': int(comentarios),
                'compartidos': int(compartidos),
                'lugar': lugar
            }
            nombres_clientes = [c['cliente'] for c in clientes_guardados]
            if cliente not in nombres_clientes:
                clientes_guardados.append(nuevo_cliente)
                #guardar_clientes(clientes_guardados)
                subir_cliente(nuevo_cliente)
        elif button_id == 'clear-button':
            selected_rows = dash.callback_context.inputs['data-table.selected_rows']
            if selected_rows:
                cliente = clientes_guardados[selected_rows[0]]['cliente']
                clientes_guardados = [c for c in clientes_guardados if c['cliente'] != cliente]
                guardar_clientes(clientes_guardados)
                return clientes_guardados


    return cargar_clientes()


@app.callback(Output('data-table2', 'data'),
              Input('interval-component', 'n_intervals'), prevent_initial_call=True)

def update_data_table2(n_intervals):
    updated_data = load_data()
    return updated_data

@app.callback(
    [Output('input-cliente', 'value'),  # Limpiar el campo de entrada
     Output('input-likes', 'value'),  # Limpiar la selección de likes
     Output('input-comentarios', 'value'),  # Limpiar la selección de comentarios
     Output('input-compartidos', 'value'),
     Output('input-ubicacion', 'value')],  # Limpiar la selección de compartidos
    [Input('button-agregar', 'n_clicks'),
     Input('clear-button', 'n_clicks'),
     Input('clear-post', 'n_clicks')],  # Include clear-button as input trigger
    prevent_initial_call=True
)
def clear_inputs(n_clicks_agregar, n_clicks_clear_button, n_clicks_clear_post):
    return '', None, None, None, None


@app.callback(
    Output('clear-post', 'disabled'),
    [Input('data-table2', 'selected_rows'),
     Input('clear-post', 'n_clicks')]
)
def delete_post(selected_rows, n_clicks):
    mydb = mysql.connector.connect(
        host='rimgsa.com',
        port=3306,
        user='Facebook_user',
        password='user_facebook123',
        database='practicas_facebook_scrapper'
    )
    data = load_data()
    data = pd.DataFrame.from_dict(data)
    cursor = mydb.cursor()
    #print("DATAFRAMEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
    #print(data.columns)

    if selected_rows and n_clicks:
        deleted_posts = []  # Store the deleted posts for insertion into the "deleted_posts" table
        deleted_urls = []  # Store the deleted URLs for insertion into the "deleted_posts" table
        # Filter selected rows that are within the DataFrame index range
        valid_rows = [row for row in selected_rows if row < len(data)]

        for i in valid_rows:
            post = data.iloc[i].to_dict()
            deleted_posts.append(post)
            # Delete the row from the SQL database
            url = post["URL"]
            url_value = re.search(r'\((.*?)\)', url).group(1) if re.search(r'\((.*?)\)', url) else ""
            deleted_urls.append(url_value)  # Add the URL to the list

            cursor.execute(f"DELETE FROM clientes_facebook WHERE URL_post = '{url_value}'")

        mydb.commit()
        # Insert the deleted URLs into the "deleted_posts" table
        insert_query = "INSERT INTO deleted_posts (Pagina, URL, Compartidos, Likes, Comentarios,Contenido ,Fecha, Hora) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.executemany(insert_query, [(post["Pagina"], url, post["Compartidos"], post["Likes"], post["Comentarios"], post["Contenido"],post["Fecha"].strftime('%Y-%m-%d'), post["Hora"]) for post, url in zip(deleted_posts, deleted_urls)])
        mydb.commit()
        # Upload the deleted posts DataFrame to the "deleted_posts" table in the database
        #upload_deleted_posts(pd.DataFrame(deleted_posts))
        update_data_table2(0)

        return len(selected_rows) == 0




@app.callback(
    Output('countdown', 'children'),
    Output('message', 'children'),
    Input('interval', 'n_intervals'),
    State('countdown', 'children')
)
def update_countdown(n_intervals, countdown):
    remaining_time = 600 - (n_intervals % 600) - 1
    if remaining_time <= 0:
        remaining_time = 600
        message = 'Actualizando datos'
    else:
        message = ''
    return f'{remaining_time // 60:02}:{remaining_time % 60:02}', message
