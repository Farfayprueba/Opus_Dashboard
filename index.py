from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from app import app
import app1,app2,app3,app4,app5,app6,app7,app8,app9,app10,app11,app13,app14,app15,app16,app17,app18,app19,app20,app21,app22,app24,app25,app26,app27,app28,app29,app33,app38,app43,app44,app101,app23,app30,app31,app32,app37,app39,app40,app41,app42,app34,app35,app36,app45

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])

def login(pathname):
        if pathname == '/app/Admin_Opus':
                return app1.layout
        elif pathname == '/app/Team_Masarik':
                return app2.layout
        elif pathname == '/app/Team_C':
                return app3.layout
        elif pathname == '/app/Team_Cancun':
                return app4.layout
        elif pathname == '/app/Team_Hercules':
                return app5.layout
        elif pathname == '/app/Mini_Masarik':
                return app6.layout
        elif pathname == '/app/Mini_Hercules':
                return app7.layout
        elif pathname == '/app/Mini_Cancun':
                return app8.layout
        elif pathname == '/app/Team_Honduras':
                return app9.layout
        elif pathname == '/app/Mini_Honduras':
                return app10.layout
        elif pathname == '/app/Mini_Hercules(1)':
                return app11.layout
        elif pathname == '/app/Mini_Hercules(3)':
                return app13.layout
        elif pathname == '/app/Mini_Hercules(4)':
                return app14.layout
        elif pathname == '/app/Team_Hercules(1)':
                return app15.layout
        elif pathname == '/app/Team_Hercules(2)':
                return app16.layout
        elif pathname == '/app/Team_Hercules(3)':
                return app17.layout
        elif pathname == '/app/Team_Hercules(4)':
                return app18.layout
        elif pathname == '/app/Team_Hercules_Global':
                return app19.layout
        elif pathname == '/app/Mini_Hercules_Global':
                return app20.layout
        elif pathname == '/app/Mini_C':
                return app21.layout
        elif pathname == '/app/Team_Hercules(5)':
                return app22.layout
        elif pathname == '/app/Team_D':
                return app23.layout
        elif pathname == '/app/Mini_D':
                return app24.layout
        elif pathname == '/app/chetumal2_vespertino':
                return app25.layout
        elif pathname == '/app/ejecutivo-Kenia':
                return app26.layout
        elif pathname == '/app/ejecutivo-Alizbeth':
                return app27.layout
        elif pathname == '/app/ejecutivo-Raquel':
                return app28.layout
        elif pathname == '/app/ejecutivo-Adriana':
                return app29.layout
        elif pathname == '/app/ejecutivo-Erick':
                return app34.layout
        elif pathname == '/app/ejecutivo-D1':
                return app30.layout
        elif pathname == '/app/ejecutivo-D2':
                return app31.layout
        elif pathname == '/app/ejecutivo-D3':
                return app32.layout
        elif pathname == '/app/ejecutivo-C2':
               return app33.layout
        elif pathname == '/app/ejecutivo-C3':
               return app35.layout
        elif pathname == '/app/ejecutivo-C1':
               return app36.layout
        elif pathname == '/app/ejecutivo-D4':
                return app37.layout
        elif pathname == '/app/Cancun-2':
                return app38.layout
        elif pathname == '/app/Team_D5':
                return app39.layout
        elif pathname == '/app/Team_D6':
                return app40.layout
        elif pathname == '/app/Team_D7':
                return app41.layout
        elif pathname == '/app/Team_D8':
                return app42.layout
        elif pathname == '/app/Team_yucatan':
                return app43.layout
        elif pathname == '/app/Morelos_morena':
                return app45.layout
        elif pathname == '/app/OcultoD1j5tr4':
                return app101.layout
        elif pathname == '/app/ejecutivo-Amilcar':
                return app44.layout
        else:
            return 'Error'

if __name__ == '__main__':
    app.run_server(debug=True)
