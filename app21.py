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
        query = "SELECT * FROM clientes"
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
                    'lugar': row[4]
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
    global total
    global completados
    global deleted_rows
    clientes_guardados = cargar_clientes()
    # Drop rows that exceed the goals for each metric
    for cliente in clientes_guardados:
        likes_goal = cliente["likes"]
        compartidos_goal = cliente["compartidos"]
        comentarios_goal = cliente["comentarios"]
        # Store the rows to be deleted in deleted_rows before dropping them
        rows_to_delete = df[(df["Pagina"].str.lower() == cliente["cliente"].lower()) 
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
        df['Tiempo_Transcurrido'] = df['HoursElapsed'].astype(str) + 'h ' + df['MinutesElapsed'].astype(str) + 'm'
        df['Hora'] = df['Hora'].dt.strftime('%I:%M %p')

        df = df[df['Pagina'].apply(lambda x: x.lower()).isin([cliente['cliente'].lower() for cliente in clientes if cliente['lugar'] == "C"])]
        # Crear un diccionario que mapee el nombre del cliente con el valor de "lugar" correspondiente
        diccionario_lugares = {cliente['cliente']: cliente['lugar'] for cliente in clientes}

        # Aplicar el mapeo al DataFrame original
        df['Grupo_equipo'] = df['Pagina'].apply(lambda x: x.lower()).map(diccionario_lugares)

        diccionario_vip = {"DHCAGUAKAN":"VIP", "AliGamboaM":"VIP","soyanapaty":"VIP", "audelurbinamx":"VIP", "horacioduarteolivares":"VIP","BenjaminRicoM":"VIP", "cuauhochoa":"VIP", "diegotorresitagui":"VIP", "DuniaLudlowD":"VIP", "00092238522976":"VIP","LupitaMurguiaG":"VIP", "boyconlaciudad":"VIP", "mariodelgadocarrillo":"VIP","MARIOFMUNDO":"VIP", "oscargtzcamacho":"VIP",  "rabinsalazar":"VIP", "frenteinformativo.com.mx":"VIP", "InformeDiarioMx":"VIP", "InformeDiarioMx":"VIP", "enlaloteria":"VIP","AuditorDeMorelos":"VIP","cuautlacanal2":"VIP", "solonoticiasdemorelos":"VIP", "RS24PorMorelos":"VIP", "reflexionesparamorelos":"VIP","RaRaRaRabin":"VIP","ElMomorelos":"VIP", "SheffieldGto":"VIP","RicardoVelazco2022":"VIP","RodolfoCorreaV":"VIP","SandraTorresGua":"VIP", "MaraLezamaOficial":"VIP"}
        df['Prioridad'] = df['Pagina'].apply(lambda x: x).map(diccionario_vip)

        
        # Filtrar las publicaciones basadas en la columna "Contenido" y las publicaciones eliminadas
        deleted_contents = set()  # Almacenar los contenidos eliminados
        if clientes_guardados and not df.empty:
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
    {"name": "Prioridad", "id": "Prioridad"},
    {"name": "Pagina", "id": "Pagina"},
    {"name": "URL", "id": "URL", "type": "text", "presentation": "markdown"},
    {"name": "Likes", "id": "Likes"},
    {"name": "Comentarios", "id": "Comentarios"},
    {"name": "Compartidos", "id": "Compartidos"},
    {"name": "Fecha", "id": "Fecha"},
    {"name": "Hora", "id": "Hora"},
    {"name": "HoursElapsed", "id": "HoursElapsed"},
    {"name": "Tiempo_Transcurrido", "id": "Tiempo_Transcurrido"},
   # Agrega más columnas si es necesario
]

# Crear una lista para almacenar los clientes agregados
clientes = []

layout = html.Div(
    children=[
        # Agregar las selecciones de opción múltiple
        html.Div(
            children=[
                html.Div(
                    dash_table.DataTable(
                        id="data-table2-mini-c-equipo",
                        columns=columns,
                        data=load_data(),  # Llama a load_data() para cargar los datos iniciales en el pool
                        style_table=table_style,
                        style_cell=cell_style,
                        style_data={'color': 'black'},
                        style_header={'color':'black'},
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{HoursElapsed} >= 1 < 3'},
                                'backgroundColor': '#FDE541'
                            },
                            {
                                'if': {'filter_query': '{HoursElapsed} >= 3'},
                                'backgroundColor': 'lightcoral'
                            },
                            {
                                'if': {'filter_query': '{HoursElapsed} < 1'},
                                'backgroundColor': 'lightgreen'
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
@app.callback(
    Output('contador-mini-c-equipo', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_counter(n):    
    total_post = f"Total de posts: {total} \n"
    post_sin_metricas = f"Posts que aún no llegan a sus métricas: {total - completados} \n"
    post_con_metricas = f"Post que han llegado a sus métricas: {completados} \n"
    
    return total_post, post_sin_metricas, post_con_metricas


@app.callback(
    Output('button-agregar-mini-c-equipo', 'disabled'),  # Habilitar/deshabilitar el botón de agregar
    [Input('input-cliente-mini-c-equipo', 'value'),
     Input('input-likes-mini-c-equipo', 'value'),
     Input('input-comentarios-mini-c-equipo', 'value'),
     Input('input-compartidos-mini-c-equipo', 'value'),
     Input('input-ubicacion-mini-c-equipo','value')]
)
def update_button_disabled(cliente, likes, comentarios, compartidos,lugar):
    if cliente and likes is not None and comentarios is not None and compartidos is not None and lugar is not None:
        return False
    return True

@app.callback(
    Output('clear-button-mini-c-equipo', 'disabled'),  # Disable the delete button if no row is selected
    [Input('data-table', 'selected_rows')]
)
def update_button_disabled2(selected_rows):
    return len(selected_rows) == 0

@app.callback(Output('data-table2-mini-c-equipo', 'data'),
              Input('interval-component', 'n_intervals'))
def update_data_table2(n_intervals):
    updated_data = load_data()
    #guardar_clientes(clientes_guardados)
    '''threads = []

    for i in clientes_guardados:
        lista = [i["cliente"]]
        print("Accediendo a", str(i))
        perfil = threading.Thread(target=buscar_dia_v3.extractprofiles, args=(lista,))
        threads.append(perfil)
        perfil.start()

    for thread in threads:
        thread.join()'''

    return updated_data
@app.callback(
    Output('input-cliente-mini-c-equipo', 'value'),  # Limpiar el campo de entrada
    Output('input-likes-mini-c-equipo', 'value'),  # Limpiar la selección de likes
    Output('input-comentarios-mini-c-equipo', 'value'),  # Limpiar la selección de comentarios
    Output('input-compartidos-mini-c-equipo', 'value'),
    Output('input-ubicacion-mini-c-equipo', 'value'),  # Limpiar la selección de compartidos
    [Input('button-agregar-mini-c-equipo', 'n_clicks'),
     Input('clear-button-mini-c-equipo', 'n_clicks')],  # Include clear-button-mini-c-equipo as input trigger
    prevent_initial_call=True
)
def clear_inputs(n_clicks_agregar, n_clicks):
    return '', None, None, None,None

@app.callback(
    Output('countdown-mini-c-equipo', 'children'),
    Output('message-mini-c-equipo', 'children'),
    Input('interval', 'n_intervals'),
    State('countdown-mini-c-equipo', 'children')
)
def update_countdown(n_intervals, countdown):
    remaining_time = 600 - (n_intervals % 600) - 1
    if remaining_time <= 0:
        remaining_time = 600
        message = 'Actualizando datos'
    else:
        message = ''
    return f'{remaining_time // 60:02}:{remaining_time % 60:02}', message
