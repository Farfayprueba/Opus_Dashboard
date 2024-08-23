import dash
import os
import dash_bootstrap_components as dbc


from flask import send_from_directory


app = dash.Dash(__name__,suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.QUARTZ])
server = app.server
#app.config.supress_callback_exceptions = True


@app.server.route('/static/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_folder, path)
