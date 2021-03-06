import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import dash_table
import xlrd
import datetime
import xlsxwriter
import dash_core_components as dcc
import dash_html_components as html
import dash
import dash_bootstrap_components as dbc
import textwrap
from plotly.subplots import make_subplots
from datetime import datetime as dt
from fbprophet import Prophet
from fbprophet.plot import add_changepoints_to_plot
from fbprophet.plot import plot_plotly, plot_components_plotly
from collections import defaultdict
from jupyter_dash import JupyterDash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
pd.set_option("max_columns", None)
pd.set_option("max_rows", None)
pd.set_option("max_rows", None)
pd.set_option("display.max_columns", None)

df_paciente = pd.read_excel('./datasets/Pacientemockup5_pesoalterado.xlsx') 
df_eventos = pd.read_excel("./datasets/Eventos.xlsx")
df_enfermeira = pd.read_excel('./datasets/protocolo.xlsx') 
df_hist_cons = pd.read_excel('./datasets/Historico_consulta_mockup.xlsx')

df_paciente = round(df_paciente,2)
df_paciente['Temperatura'] = round(df_paciente['Temperatura'],1)
df_paciente3 = df_paciente
df_paciente3['Pressão Sistólica Normal'] = 120
df_paciente3['Pressão Diastólica Normal'] = 80
df_paciente2 = df_paciente3[['Pressão Diastólica',	'Pressão Sistólica',	'Frequência Cardíaca',	'Glicemia',	'Temperatura',	'Peso',	'IMC','Pressão Sistólica Normal','Pressão Diastólica Normal']]
last_values = df_paciente.tail(1)
p1 = ((last_values['Pressão Diastólica']-80)/(110-80))*5
p2 = ((last_values['Pressão Sistólica']-120)/(180-120))*5
f = ((last_values['Frequência Cardíaca']-56)/(100-56))*5
g = ((last_values['Glicemia']-99)/(200-99))*5
t = ((last_values['Temperatura']-35)/(39-35))*5
i = ((last_values['IMC']-19)/(33-19))*5
p1=round(p1+0.5)
p2=round(p2+0.5)
f=round(f+0.5)
g=round(g+0.5)
t=round(t+0.5)
i=round(i+0.5)
fig_radar2 = go.Figure()
fig_radar2.add_trace(go.Scatterpolar(
        r=[p1[363],i[363] , g[363], f[363], t[363],p2[363]],
        theta=['Pressão Dias.','IMC', 'Glicemia', 'Freq. Cardíaca','Temp.','Pressão Sis.'],
        line_color='rgb(43,140,190)',
        fillcolor='rgb(43,140,190)',
        hovertemplate= '<br> Risco do Indicador: %{r} <extra></extra>',
        r0=0,
        name=""
        ,
    ))
fig_radar2.update_traces(fill='toself', hovertext=['theta','r'])
fig_radar2.update_layout(
    polar = dict(
      radialaxis_range = [0, 5],
      angularaxis_thetaunit = "radians",
    ))
fig_radar2.update_layout(
    annotations = [
                  dict(
                       x=1.16,
                       y=1.23,
                       showarrow=False,
                       text=' 0 - Abaixo do normal<br> 1 - Normal porém baixo<br> 2 - Normal<br> 3 - Normal porém alto<br> 4 - Requer cuidados<br> 5 - Crítico',
                       xref='paper',
                       yref='paper',
                       align = 'left',
                       font=dict(
                           size=8
                       )                       
                  )
    ],

)
fig_radar2.update_layout(
    paper_bgcolor='rgba(255,255,255,255)',
    plot_bgcolor='rgba(255,255,255,255)',
)
df_paciente['contar']=1
temp = df_paciente.groupby(['Condições Descontroladas',
              "Hiperglicemia", 
              "Hipertensão", 
              "Fumante",
              "Medicamento",
              "Atividade física",
              "Estados Mentais",
              "Acontecimentos"])[df_paciente.columns[1]].count()
temp = pd.DataFrame(temp)
temp.reset_index(inplace=True)
temp_unpivot = pd.melt(
    temp,
    id_vars =['Condições Descontroladas',
              "Hiperglicemia", 
              "Hipertensão", 
              "Fumante",
              "Medicamento",
              "Atividade física",
              "Estados Mentais",
              "Acontecimentos"
              ], 
              value_vars=temp.columns[8]
              )
novo = temp_unpivot[temp_unpivot.value > 0].copy()
novo.reset_index(inplace=True)
novo.value_color_norm = (novo.value-novo.value.min())/(novo.value.max()-novo.value.min())
novo["raiz"] = np.power(novo.value, 0.02)
fig_sun = px.sunburst(
            novo, 
            path=['Condições Descontroladas',
              "Hiperglicemia", 
              "Hipertensão", 
              "Fumante",
              "Medicamento",
              "Atividade física",
              "Estados Mentais",
              "Acontecimentos"],
            values='value',
            maxdepth=2,
            color="raiz",
            color_continuous_scale="GnBu",
            hover_name="Condições Descontroladas",
          )
fig_sun.update_traces(
    hoverinfo='name',
    hovertemplate='<br> Quantidades de dias: %{value} <extra> </extra>',
    textfont=dict(
        color="#081c15",
        family="<b>Bold</b>",
        size=9,
    ),   
)
fig_sun.update_layout(
    coloraxis_showscale=False,
)
forecast_paciente = defaultdict(dict)
for parametro in df_paciente.columns[1:8]:
    print(parametro)
    dff = df_paciente.copy()
    dff = dff.groupby(["Data da Consulta"], as_index=False)[[parametro]].sum()
    dff.columns = ["ds", "y"]
    model = Prophet(mcmc_samples=300, interval_width=0.95)
    model.fit(dff, control={'max_treedepth': 20})
    forecast = model.predict(model.make_future_dataframe(periods=45))
    try:
      forecast_paciente[parametro]["Forecast"] = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
      forecast_paciente[parametro]["Trend"] = forecast[['ds', "trend", "trend_lower", "trend_upper"]]
      forecast_paciente[parametro]["Weekly"] = forecast[['ds', "weekly", "weekly_lower", "weekly_upper"]]
      forecast_paciente[parametro]["ChangePoints"] = model.changepoints.to_frame()
    except Exception as e:
      print(e)
def plotar_forecast(df_y, df_yhat, variavel):
        temp_y = df_y.copy()
        temp_y = temp_y.groupby(["Data da Consulta"], as_index=False)[[variavel]].sum()
        temp_y.columns = ["ds", "y"]
        temp_yhat = df_yhat.copy()
        previsao = go.Scatter(
            x=temp_yhat["ds"], y=temp_yhat["yhat"], mode="lines", name="Previsão"
        )
        superior = go.Scatter(
            x=temp_yhat["ds"],
            y=temp_yhat["yhat_upper"],
            mode="lines",
            fill="tonexty",
            line={"color": "#57b8ff"},
            name="Intervalo Superior",
        )
        inferior = go.Scatter(
            x=temp_yhat["ds"],
            y=temp_yhat["yhat_lower"],
            mode="lines",
            fill="tonexty",
            line={"color": "#57b8ff"},
            name="Intervalo Inferior",
        )
        pontos_y = go.Scatter(
            x=temp_y["ds"], y=temp_y["y"], name="Indicador", mode="markers"
        )
        data = [previsao, superior, inferior, pontos_y]
        layout = go.Layout(title=variavel, xaxis_rangeslider_visible=True)
        fig = go.Figure(data=data, layout=layout)

df_enfermeira["Value"]=df_enfermeira.Pontos+11
def customwrap(s,width=20):
    return "<br>".join(textwrap.wrap(s,width=width))
g1 = df_enfermeira['Colesterol Total'].map(customwrap)
df_enfermeira['Colesterol Total'] = g1
df_enfermeira.head()
def customwrap(s,width=8):
    return "<br>".join(textwrap.wrap(s,width=width))
g2 = df_enfermeira['HDL'].map(customwrap)
df_enfermeira['HDL'] = g2
df_enfermeira.head()
def customwrap(s,width=20):
    return "<br>".join(textwrap.wrap(s,width=width))
g3 = df_enfermeira['PA sistólica'].map(customwrap)
df_enfermeira['PA sistólica'] = g3
df_enfermeira.head()
def customwrap(s,width=9):
    return "<br>".join(textwrap.wrap(s,width=width))
g4 = df_enfermeira['Risco'].map(customwrap)
df_enfermeira['Risco'] = g4
df_enfermeira.head()
def customwrap(s,width=8):
    return "<br>".join(textwrap.wrap(s,width=width))

g5 = df_enfermeira['Faz tratamentos da pressão?'].map(customwrap)
df_enfermeira['Faz tratamentos da pressão?'] = g5
df_enfermeira.head()
fig_sun_corona = px.sunburst(
                              df_enfermeira, 
                              path=["Gênero",
                                    "Idade",
                                    "Colesterol Total",
                                    "Fumante?",
                                    "HDL",
                                    "PA sistólica",
                                    "Faz tratamentos da pressão?",
                                    "Risco"],
                              values='Value',
                              maxdepth=2,
                              color="Pontos",
                              color_continuous_scale="GnBu",
                              hover_data=["Risco"],
                              width=700,
                              height=700
                            )
fig_sun_corona.update_traces(
    hoverinfo='name',
    hovertemplate='%{label}',
    textfont = dict(
                    color="White",
                    family="<b>Bold</b>",
                    size=12
                    ),  
)
fig_sun_corona.update_layout(
    coloraxis_showscale=False,
)
df_paciente5 = df_paciente[['Data da Consulta','Medicamento']].copy()
df_paciente5[['Medicamento A','Medicamento B']] = 0,0
df_paciente5.Medicamento = df_paciente5.Medicamento.replace(" + ","+")
df_paciente5[['Medicamento A','Medicamento B']] = df_paciente5.Medicamento.str.split("+",expand =True)
df_paciente5.drop(["Medicamento"], axis=1, inplace=True)
df_paciente5 = pd.melt(df_paciente5, id_vars =["Data da Consulta"], value_vars=df_paciente5.columns[1:])
df_paciente5.drop(["variable"], axis=1, inplace=True)
df_paciente5.value = df_paciente5.value.apply(lambda v: str(v).lstrip(" "))
df_paciente5.value.value_counts()
df_paciente5 = df_paciente5[df_paciente5.value != "None"].copy() 
df = pd.concat([df_paciente5,pd.get_dummies(df_paciente5['value'],dummy_na=False)],axis=1).drop(['value'],axis=1)
df["Insulina 20 UI"] = df["Insulina 20 UI"] + df["Insulina 20 UI "]
df.drop(["Insulina 20 UI "], axis=1, inplace=True)
mult = 1
for coluna in df.columns[1:]:
  df[coluna] = df[coluna].apply(lambda v: v*mult)
  mult += 1
fig_medicamento = go.Figure()
for coluna in df.columns[1:]:
  fig_medicamento.add_trace(
      go.Scatter(
          x=df["Data da Consulta"],
          y=df[coluna],
          mode="markers",
          name=coluna,
          showlegend=False
      )
  )
fig_medicamento.update_yaxes(
    ticktext=df.columns[1:],
    tickvals=[1, 2, 3, 4, 5],
    range=[0.2, 5.2]
)
fig_medicamento.update_layout(
          paper_bgcolor='rgba(255,255,255,255)',
          plot_bgcolor='rgba(255,255,255,255)',
          margin=dict(l=10, r=20, t=70, b=10),
  )
df_hist_cons['Data da consulta'] = df_hist_cons['Data da consulta'].dt.strftime("%d/%m/%Y")
df_new_table = df_paciente.tail(1)
df_new_table.reset_index(inplace=True,drop=True)
df_new_table = df_new_table.transpose(copy=True)
df_new_table = pd.DataFrame(df_new_table)
df_new_table.reset_index(inplace=True)
df_new_table.columns = ['variável','valor']
df_new_table = df_new_table.drop([0,8,9,10,11,12,13,14,15,18])
df_new_table.reset_index(inplace=True,drop=True)
df_unidades_medidas = df_new_table['variável']
df_unidades_medidas.reset_index(drop=True, inplace=True)
df_unidades_medidas=pd.DataFrame(df_unidades_medidas)
df_unidades_medidas.insert(0,"Unidades",['mmHg','mmHg','bpm','mg/dL','ºC','kg', 'kg/m2','mmHg','mmHg'])
df_unidades_medidas.columns = ['Unidades','var']
df_new_table = pd.concat([df_new_table, df_unidades_medidas], axis=1, join='inner')
df_new_table["valor"] = df_new_table["valor"].astype(str)
df_new_table["valor_final"] = df_new_table['valor'].str.cat(df_new_table['Unidades'],sep=" ")
df_new_table = df_new_table.drop(['var','Unidades','valor'], axis=1)
df_new_table = df_new_table.drop([7,8])

app = JupyterDash(__name__, title="PLENI")
server=app.server

NOME = "Olívia Oliveira"
NASCIMENTO = "01/01/1980"
BAIRRO = "Jardim Catarina"
Telefone = "(21) *****-1234"
Email = "oliviaoliveira@gmail.com"
Profissao = "Advogada"
Codigo_pleni = "******001"

app = JupyterDash(
    external_stylesheets=[dbc.themes.LUX],
    meta_tags=[
        {
            "name": "viewport", 
            "content": "width=device-width, initial-scale=1"
         }
    ],
     title="PLENI",
)

sidebar_header = dbc.Row(
    [
     html.A(
        dbc.Col(
            html.Img(
                        src="/assets/logo_pleni.png", 
                        height="60px", 
                        style={'marginRight': 18},
                        ),
        ),
        ),
        dbc.Col(
            [
                html.Button(
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    style={
                        "color": "#cdedf6",
                        "border-color": "#cdedf6",
                    },
                    id="navbar-toggle",
                ),
                html.Button(
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    style={
                        "color": "#cdedf6",
                        "border-color": "#cdedf6",
                    },
                    id="sidebar-toggle",
                ),
            ],
            width="auto",
            align="center",
        ),
    ]
)

#--------------------Modals ----------------------------------------------------------------------------------

modal_receita = html.Div(
    [
        dbc.Button("Inserir novo medicamento", id="open_receita", color="#64dfdf",size="sm", style={'Size':12}),
        dbc.Modal(
            [
                dbc.ModalHeader("Por favor, insira as informações do medicamento em uso:"),
                dbc.ModalBody(
                    dbc.Form(
                        [
                            dbc.FormGroup(
                                [
                                    dbc.Label("Nome do Medicamento", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Medicamento"),
                                ],
                                className="mr-3",
                            ),

                            dbc.FormGroup(
                                [
                                    dbc.Label("Data de Início", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Início do Tratamento"),
                                ],
                                className="mr-3",
                            ),
                         
                            dbc.FormGroup(
                                [
                                    dbc.Label("Duração prevista do Tratamento", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Duração prevista (dias)"),
                                ],
                                className="mr-3",
                            ),
                         
                            dbc.FormGroup(
                                [
                                    dbc.Label("Dosagem", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Insira a dosagem da medicação em uso (mg)"),
                                ],
                                className="mr-3",
                            ),
                         
                            dbc.FormGroup(
                                [
                                    dbc.Label("Observações", className="mr-2"),
                                    dbc.Textarea(
                                            bs_size="lg", 
                                    ),
                                ],
                                className="mr-3",
                            ),
                         
                            dbc.Button("Adicionar", color="#64dfdf"),
                        ],
                        inline=False,
                    )
                ),
                dbc.ModalFooter(
                    dbc.Button("Fechar", id="close_receita", className="ml-auto")
                ),
            ],
            id="modal_receita",
            is_open=False,
            size="x1",
            backdrop=True,
            scrollable=True,
            centered=True,
            fade=True
        ),
    ]
)
modal_anotacoes = html.Div(
    [
        dbc.Button("Anotações Pessoais", id="open_anotacoes", color="#64dfdf",size="sm", style={'Size':12}),
        dbc.Modal(
            [
                dbc.ModalHeader("Anotações"),
                dbc.ModalBody(
                    dbc.Form(
                        [
                            dbc.FormGroup(
                                [
                                    dbc.FormGroup(
                                [
                                    dbc.Label("Título", className="mr-2"),
                                    dbc.Input(type="text"),
                                ],
                                className="mr-3",
                            ),
                                    dbc.Textarea(
                                            bs_size="lg", 
                                            placeholder="Insira aqui suas anotações"
                                    ),
                                ],
                                className="mr-3",
                            ),

                            dbc.Button("Adicionar", color="#38a3a5"),
                        ],
                        inline=False,
                    )
                ),
                dbc.ModalFooter(
                    dbc.Button("Fechar", id="close_anotacoes", className="ml-auto")
                ),
            ],
            id="modal_anotacoes",
            is_open=False,
            size="x1",
            backdrop=True,
            scrollable=True,
            centered=True,
            fade=True
        ),
    ]
)
modal_alteracoes = html.Div(
    [
        dbc.Button("Alterações cadastrais", id="open_alteracoes", color="#64dfdf",size="sm", style={'Size':12}),
        dbc.Modal(
            [
                dbc.ModalHeader("Alterações cadastrais"),
                dbc.ModalBody(
                    dbc.Form(
                        [
                            dbc.FormGroup(
                                [
                                    dbc.Label("Nome completo", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Olívia Oliveira"),
                                ],
                                className="mr-3",
                            ),
                            dbc.FormGroup(
                                [
                                    dbc.Label("Data de nascimento", className="mr-2"),
                                    dbc.Input(type="text", placeholder="01/01/1970"),
                                ],
                                className="mr-3",
                            ),
                            dbc.FormGroup(
                                [
                                    dbc.Label("Bairro de residência", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Jardim Catarina"),
                                ],
                                className="mr-3",
                            ),
                            dbc.FormGroup(
                                [
                                    dbc.Label("Email", className="mr-2"),
                                    dbc.Input(type="text", placeholder="oliviaoliveira@gmail.com"),
                                ],
                                className="mr-3",
                            ),
                            dbc.FormGroup(
                                [
                                    dbc.Label("Profissão", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Advogada"),
                                ],
                                className="mr-3",
                            ),
                            dbc.FormGroup(
                                [
                                    dbc.Label("Data de nascimento", className="mr-2"),
                                    dbc.Input(type="text", placeholder="01/01/1970"),
                                ],
                                className="mr-3",
                            ),
                            dbc.FormGroup(
                                [
                                    dbc.Label("Gênero", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Feminino"),
                                ],
                                className="mr-3",
                            ),
                            dbc.FormGroup(
                                [
                                    dbc.Label("Etnia", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Branca"),
                                ],
                                className="mr-3",
                            ),

                            dbc.Button("Salvar", color="#38a3a5"),
                        ],
                        inline=False,
                    )
                ),
                dbc.ModalFooter(
                    dbc.Button("Fechar", id="close_alteracoes", className="ml-auto")
                ),
            ],
            id="modal_alteracoes",
            is_open=False,
            size="x1",
            backdrop=True,
            scrollable=True,
            centered=True,
            fade=True
        ),
    ]
)
modal_feedback = html.Div(
    [
        dbc.Button("Sugerir melhoria", id="open_feedback", color="#64dfdf",size="sm", style={'Size':12}),
        dbc.Modal(
            [
                dbc.ModalHeader("Conte-nos como poderíamos melhorar!"),
                dbc.ModalBody(
                    dbc.Form(
                        [
                            dbc.FormGroup(
                                [
                                    dbc.Label("Nome Completo", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Informe seu nome completo"),
                                ],
                                className="mr-3",
                            ),

                            dbc.FormGroup(
                                [
                                    dbc.Label("Email", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Informe seu email"),
                                ],
                                className="mr-3",
                            ),

                            dbc.FormGroup(
                                [
                                    dbc.Label("Melhoria protosta", className="mr-2"),
                                    dbc.Input(type="text", placeholder="Descreva"),
                                ],
                                className="mr-3",
                            ),

                            dbc.Button("Enviar", color="#38a3a5"),
                        ],
                        inline=False,
                    )
                ),
                dbc.ModalFooter(
                    dbc.Button("Fechar", id="close_feedback", className="ml-auto")
                ),
            ],
            id="modal_feedback",
            is_open=False,
            size="x1",
            backdrop=True,
            scrollable=True,
            centered=True,
            fade=True
        ),
    ]
)
#--------------------------------------SIDEBAR -----------------------------------------------------------------------------
sidebar = html.Div(
    [
        sidebar_header,
        html.Hr(),
        html.A(
            dbc.Row(
                [
                    dbc.Col(html.Img(
                        src="/assets/foto_olivia_oliveira.png", 
                        height="90px", 
                        className="rounded-circle"
                        )
                    ),
                ],
                align="center",
                no_gutters=True,
                justify="center",

            ),

        ),
        html.Div(
            [
                html.Hr(),
                html.P(
                    "Nome: "f"{NOME}",
                    className="lead",
                    style={'fontSize': 12},
                ),
                html.P(
                    "Código Pleni: "f"{Codigo_pleni}",
                    className="lead",
                    style={'fontSize': 12},
                ),
                html.P(
                    "Data de nascimento: "f"{NASCIMENTO}",
                    className="lead",
                    style={'fontSize': 12},
                ),
                html.P(
                    "Telefone: "f"{Telefone}",
                    className="lead",
                    style={'fontSize': 12},
                ),
                html.P(
                    "E-mail: "f"{Email}",
                    className="lead",
                    style={'fontSize': 12},
                ),
                html.P(
                    "Profissão: "f"{Profissao}",
                    className="lead",
                    style={'fontSize': 12, 'marginBottom': 0.1},
                ),
            ],
            id="blurb",
        ),
        dbc.Collapse(
            dbc.Nav(
                [
                    modal_receita,
                    modal_anotacoes,
                    modal_alteracoes,
                    modal_feedback,                   
                ],
                vertical=True,
                pills=True,       
                style={'marginBottom': 12},        
            ),
            id="collapse",
        ),
    ],
    id="sidebar",
    
)
#-----------------------------------------SEARCH BAR ------------------------------------------------------------------------
search_bar = dbc.Row(
    [
            
        dbc.Col(
            [
            html.Div(
               [
               
                   dbc.Button("VACINAS", id="abrirVacinas", outline=False, color="#cdedf6", size='sm'),
                       dbc.Modal(
                           [
                               dbc.ModalHeader("HISTÓRICO DE VACINAÇÃO"),
                               dbc.ModalBody("A small modal."),
                               dbc.ModalFooter(
                               dbc.Button("Fechar", id="fecharVacinas", className="ml-auto")
                               ),
                           ],
                           id="modalVacinas",
                           size="xl",
                       ),

               ]
               ),
            ],
            
            style={"marginLeft": -50,"marginBottom":-10,"marginTop":-10}
        ),
        dbc.Col(
          
            dcc.DatePickerRange(
                id='id_calendario_filtro',
                start_date_placeholder_text="       Início",
                end_date_placeholder_text="  Término",
                calendar_orientation='vertical',
            ),
            width=12,
            style={"marginRight": -60,"marginLeft":100,"marginBottom":-10,"marginTop":-10}
        ),
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)
barra_navegacao = dbc.Navbar(
    [
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(search_bar, id="navbar-collapse", navbar=True),
    ],
    color="#cdedf6",
    dark=True,
)

#-----------------------------------------CARDS --------------------------------------------------------------------------------
cards = html.Div(
    [
        dbc.Row(
            [
             dbc.Col(
              dbc.Card(
              dbc.CardBody(
                  [
                html.Div(
    [
        html.H6("Informações"),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("Perfil Clínico do Paciente",style={'fontSize': 11, 'width':300, 'marginBottom': 22}),
                dbc.ListGroupItem("Diabetes e Hipertensão",style={'fontSize': 11,'marginBottom':22,'width':400}),
            ],
            horizontal=True,
            className="mb-1000",
        ),
        html.H6("Medicamentos"),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("Medicamentos em uso",style={'fontSize': 11,'width':300}),
                dbc.ListGroupItem("Insulina 35 ui/dia",style={'fontSize': 11,'width':400}),
            ],
            horizontal="lg",
        ),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("Utilizou outro medicamento nos últimos 30 dias?",style={'fontSize': 11,'width':300}),
                dbc.ListGroupItem("Sim, Capitopril 150mg",style={'fontSize': 11,'width':400},className="list-group-item d-flex justify-content-between align-items-center"),
            ],
            horizontal="lg",
        ),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("Início da medicação",style={'fontSize': 11,'width':300, 'marginBottom': 22}),
                dbc.ListGroupItem("07/10/2020",style={'fontSize': 11,'width':400, 'marginBottom': 22}),
            ],
            horizontal="lg",
        ),
        html.H6("Consultas"),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("Última Consulta",style={'fontSize': 11,'width':300}),
                dbc.ListGroupItem("10/10/2020",style={'fontSize': 11,'width':400}),
            ],
            horizontal="lg",
        ),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("Próxima Consulta",style={'fontSize': 11,'width':300}),
                dbc.ListGroupItem("14/10/2020",style={'fontSize': 11,'width':400}),
            ],
            horizontal="lg",
        ),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("Médico",style={'fontSize': 11,'width':300}),
                dbc.ListGroupItem(html.Span("Dr. Paulo Roberto", id="tool_medico2"),style={'fontSize': 11,'width':400}),
                dbc.Tooltip(
                      "Doutor Paulo Roberto Carlos Magalhães, Médico da Família, atende de segunda, quarta e sexta das 08:00 as 15:00 na Santa Casa",
                      target="tool_medico2",
                      style={
                                        "background-color": "#ade8f4",
                                        "color": "#14213d",
                                    }
                ),
            ],
            horizontal="lg",
        ),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("Unidade de Saúde",style={'fontSize': 11,'width':300, 'marginBottom': 22}),
                dbc.ListGroupItem(html.Span("Santa Casa",id="tool_unidade_saude2"),style={'fontSize': 11,'width':400, 'marginBottom': 22}),
                                  dbc.Tooltip(
                                      "Rua das Laranjeiras, 1000, Centro",
                                      target="tool_unidade_saude2",
                                      style={
                                        "background-color": "#ade8f4",
                                        "color": "#14213d",
                                    }
                                      ),
            ],
            horizontal="lg",
        ),
     html.H6("Histórico Familiar"),
                  dbc.ListGroup(
                        [
                            dbc.ListGroupItem("Condições",style={'fontSize': 11, 'width':300, 'marginBottom': 22},className="list-group-item d-flex justify-content-between align-items-center"),
                            dbc.ListGroupItem("Pai (Diabetes), Mãe (Hipertensão) e Avó paterna (Câncer do pâncreas)",style={'fontSize': 11,'marginBottom':22, 'width':400}),
                        
                        ],
                   horizontal=True,
                   className="mb-1000",
                        ),
                   html.H6("Perfil"),
                   dbc.ListGroup(
                       [
                         dbc.ListGroupItem("Etnia",style={'fontSize': 11,'width':300}),
                         dbc.ListGroupItem("Branca",style={'fontSize': 11,'width':400}),
                        ],
                        horizontal="lg",
                        ),
                   dbc.ListGroup(
                       [
                         dbc.ListGroupItem("Gênero",style={'fontSize': 11,'width':300}),
                         dbc.ListGroupItem("Feminino",style={'fontSize': 11,'width':400}),
                        ],
                        horizontal="lg",
                        ),
                   dbc.ListGroup(
                       [
                         dbc.ListGroupItem("Idade",style={'fontSize': 11,'width':300}),
                         dbc.ListGroupItem("40 anos",style={'fontSize': 11,'width':400}),
                        ],
                        horizontal="lg",
                        ),
                   dbc.ListGroup(
                       [
                         dbc.ListGroupItem("Altura",style={'fontSize': 11,'width':300}),
                         dbc.ListGroupItem("1,69 m",style={'fontSize': 11,'width':400}),
                        ],
                        horizontal="lg",
                        ),
    ]
)
                ]
              ),
              style={'marginRight':-21, "marginLeft": 10},
             className="w-33 mb-2",
              )
            ),
            dbc.Col(   
              [
              dbc.Card(

               dbc.CardBody(
                 [
                  html.H5("Resultado atuais",  className="card-title"),
                  dash_table.DataTable(
                  id='table2',
                  columns=[
                             {'id': 'variável', 'name': 'Exame', 'presentation': 'dropdown'},
                             {'id': 'valor_final', 'name': 'Resultado'},
                         ],
                  data=df_new_table.to_dict('records'),
                  page_size=10,
                  filter_action='native',                                                    
                  style_data={
                             'width': '{}%'.format(100. / len(df_new_table.columns)),
                             'textOverflow': 'hidden',               
                                 },
                  page_action='native',
                  sort_action='native',
                  selected_rows=[],
                  style_filter={
                      'backgroundColor': 'rgb(237, 245, 253)',
                      'textColor': 'rgb(237, 245, 253)',
                      'text': "hidden",
                      'accentColor': '#3c3c3c',
                      "children": "Filtrar",      
                  },
                  style_cell_conditional=[
                          {
                              'if': {'column_id': c},
                              'textAlign': 'center'
                          } for c in df_new_table.columns
                      ],
                      style_data_conditional=[
                          {                            
                              'if': {'row_index': 'odd'},
                              'backgroundColor': 'rgb(237, 245, 253)',
                          },
                          { 
                              "if": {"state": "selected"},
                              "backgroundColor": "rgba(0, 116, 217, 0.3)",
                              "border": "1px solid blue",    
                          },
                      ],
                      style_header={
                          'backgroundColor': 'rgb(221, 239, 248)',
                          'fontWeight': 'bold'
                      },
                      export_format='xlsx',
                      export_headers='display',
                      row_selectable="multi",
                      css=[
                                { 'selector': 'button.export', 'rule': 'background-color: rgb(237, 245, 253); align-items: end); border-color: rgb(237, 245, 253);'},   
                            ],
              ),
                html.Hr(),
                html.H5("VISUALIZAÇÃO TEMPORAL",  className="card-title", ),
                                dcc.Graph(
                                          id='linechart',
                                          figure={},
                                          )
                    ],
                    className="w-95 mb-2",
            ),
            style={'marginBottom':10},
                  ), 
                ],
                className="w-95 mb-2",
            ),
            ],
            justify="round"
        ),
        dbc.Row(
            [
              dbc.Col(
               dbc.Card(
              dbc.CardBody(
                  [
                      dbc.ListGroup(
                        [
                            dbc.ListGroupItem("HÁBITOS",style={'fontSize': 14, 'width':550},className="list-group-item d-flex justify-items-center align-items-center list-group-items border-0"),
                            dbc.ListGroupItem("FREQUÊNCIA",style={'fontSize': 14, 'width':253},className="list-group-item d-flex justify-items-center align-items-center list-group-items border-0")
                        ],
                        horizontal ='lg',
                      ),
                      dbc.ListGroup(
                        [
                            dbc.ListGroupItem("Fumante?",style={'fontSize': 11, 'width':350},className="list-group-item d-flex justify-items-center align-items-center"),
                            dbc.ListGroupItem("Não",style={'fontSize': 11, 'width':173}),
                            dbc.ListGroupItem("0 vezes por dia",style={'fontSize': 11, 'width':250})
                        ],
                        horizontal="lg",
                      ),
                      dbc.ListGroup(
                        [
                            dbc.ListGroupItem("Consome bebida alcoólica?",style={'fontSize': 11, 'width':350},className="list-group-item d-flex justify-items-center align-items-center"),
                            dbc.ListGroupItem("Sim",style={'fontSize': 11, 'width':173}),
                            dbc.ListGroupItem("2 vezes por semana",style={'fontSize': 11, 'width':250})
                        ],
                        horizontal="lg",
                      ),
                            dbc.ListGroup(
                        [
                            dbc.ListGroupItem("Pratica exercícios físicos?",style={'fontSize': 11, 'width':350},className="list-group-item d-flex justify-items-center align-items-center"),
                            dbc.ListGroupItem("Não",style={'fontSize': 11, 'width':173}),
                            dbc.ListGroupItem("0 vezes por semana",style={'fontSize': 11, 'width':250})
                        ],
                        horizontal="lg",
                      ),
                            dbc.ListGroup(
                                [
                                    dbc.ListGroupItem("Observações: Procurar nutricionista e iniciar a prática de exercícios uma vez por semana",style={'fontSize': 11},className="list-group-item d-flex justify-items-center align-items-center"),          
                                  ] ,
                      )
                  ]
              ),
              style={'marginRight':-21, "marginLeft": 10},
              className="w-45 mb-2",
              )
            ),
            dbc.Col(
              dbc.Card(
              dbc.CardBody(
                  [
                      dbc.ListGroup(
                        [
                            dbc.ListGroupItem("HÁBITOS ALIMENTARES",style={'fontSize': 14},className="list-group-items border-0 align-items-stretch list-group-item text-center d-inline-block")
                        ],
                        horizontal ='lg',

                      ),
                      dbc.ListGroup(
                        [
                            dbc.ListGroupItem("Segue dieta?",style={'fontSize': 11, 'width':550},className="list-group-item d-flex justify-items-center align-items-center"),
                            dbc.ListGroupItem("Não",style={'fontSize': 11, 'width':250})
                        ],
                        horizontal="lg",
                      ),
                      dbc.ListGroup(
                        [
                            dbc.ListGroupItem("Consome diário de calorias?",style={'fontSize': 11, 'width':550},className="list-group-item d-flex justify-items-center align-items-center"),
                            dbc.ListGroupItem(
                                html.Span("2500 kcal", id= 'tool_cal'),style={'fontSize': 11, 'width':250}),
                                dbc.Tooltip(
                                    "Consumo diário ideal: 2000 kcal",
                                    target="tool_cal",
                                    style={
                                        "background-color": "#ade8f4",
                                        "color": "#14213d",
                                    }
                                ),      
                        ],
                        horizontal="lg",
                      ),
                            dbc.ListGroup(
                        [
                            dbc.ListGroupItem("Acompanhado por nutricionista? Qual?",style={'fontSize': 11, 'width':550},className="list-group-item d-flex justify-items-center align-items-center"),
                            dbc.ListGroupItem("Não",style={'fontSize': 11, 'width':250})
                        ],
                        horizontal="lg",
                      ),
                      dbc.ListGroupItem(
                          html.Span(
                              "Sugestão? Procurar acompanhamento especializado.",
                              id='tool_nutricionista',
                             
                              ),
                              style={'fontSize': 11},className="list-group-item d-flex justify-items-center align-items-center"),
                          dbc.Tooltip(
                                    "Sugestão: Nutricionista Michelle Cardoso, atendimentos de seg. à quar. na Santa Casa",
                                    target="tool_nutricionista",
                                     style={
                                        "background-color": "#ade8f4",
                                        "color": "#14213d",
                                    }),   
                  ]
              ),
              
             className="w-45 mb-2",
              )
            ),
            ],
            justify="round"
        ),
        dbc.Card(
            
             
             dbc.CardBody(
                 [
                  html.H5("Histórico de consultas",  className="card-title"),
                  dash_table.DataTable(
                  id='table',
                  columns=[{"name": i, "id": i} for i in df_hist_cons.columns],
                  data=df_hist_cons.to_dict('records'),
                  page_size=10,
                  filter_action='native',     
                  
                  style_data={
                             'width': '{}%'.format(100. / len(df_hist_cons.columns)),
                             'textOverflow': 'hidden',               
                                 },
                  page_action='native',
                  sort_action='native',
                  style_filter={
                      'backgroundColor': 'rgb(237, 245, 253)',              
                  },
                  style_cell_conditional=[
                          {
                              'if': {'column_id': c},
                              'textAlign': 'center'
                          } for c in df_hist_cons.columns
                      ],
                      style_data_conditional=[
                          {                            
                              'if': {'row_index': 'odd'},
                              'backgroundColor': 'rgb(237, 245, 253)',
                          },
                          { 
                              "if": {"state": "selected"},              
                              "backgroundColor": "rgba(0, 116, 217, 0.3)",
                              "border": "1px solid blue",    
                          },
                      ],
                      style_header={
                          'backgroundColor': 'rgb(221, 239, 248)',
                          'fontWeight': 'bold'
                      },
                      export_format='xlsx',
                      export_headers='display',
                      css=[
                                { 'selector': 'button.export', 'rule': 'background-color: rgb(237, 245, 253); align-items: end); border-color: rgb(237, 245, 253);'},
                            ],
              ),
                    ],
            ),
            style={"marginLeft": 10},
            className="w-95 mb-2",
        ),
        dbc.Row(
            [
              dbc.Col(
              dbc.Card(
              dbc.CardBody(
                  [
                      html.H5("Gráfico de atributos e riscos do paciente", className="card-title"),
                      
                      dcc.Graph(
                          id="radar_paciente",
                          figure=fig_radar2
                      ),
                      
                  ]
              ),
              style={'marginRight':-21, "marginLeft": 10,'marginBottom':15},
              className="mb-2, w-95",
              )
            ),
            dbc.Col(
              dbc.Card(
              dbc.CardBody(
                  [
                      html.H5("Análise das condições e atributos", className="card-title"),
                      dcc.Graph(
                          id="fig_sun",
                          figure=fig_sun
                      ),
                  ]
              ),
              style={'marginRight':0,'marginBottom':15},
              className="mb-2, w-95",
              )
            ),
            ],
            justify="around" ,  
        ),
        dbc.Card(
              dbc.CardBody(
                  [
                      html.H5("Série Histórica Indicadores | Paciente", className="card-title"),
                      dbc.Row(
                         [
                             dbc.Col(
                                dcc.Dropdown(
                                id="dropdown_indicador_paciente",
                                options=[
                                    {"label": indicador, "value": indicador}
                                    for indicador in df_paciente2.columns
                                ],
                                value=[],
                                multi=True,
                                placeholder="Selecione os indicadores que deseja visualizar",
                                ),
                              ),

                              dbc.Col(
                                dcc.Dropdown(
                                id="eventos_sentinelas",
                                options=[
                                    {"label": sentinela, "value": sentinela}
                                    for sentinela in df_eventos["Classe do Evento"].unique()
                                ],
                                value=None,
                                # multi=True,
                                placeholder="Selecione a classe de eventos sentinelas a visualizar"
                                ),
                              ),
                      
                         ],
                         no_gutters=True,  
                      ),
                    
                      dcc.Graph(
                          id="temporal_indicadores",
                          figure={},

                      ),
                  ]
              ),
            style={'marginBottom':10, "marginLeft": 10},
            className="w-95",
        ),
     dbc.Card(
            
        
              dbc.CardBody(
                  [
                    html.H5("MEDICAMENTOS  |  EM TRATAMENTO", className="card-title"),
                    dcc.Graph(
                        id="fig_medicamentos",
                        figure=fig_medicamento,
                    )
                  ]
              ),
        
            style={"marginLeft": 10},
            className="w-95, mb-2",
        ),
        dbc.Card(
            
        
              dbc.CardBody(
                  [
                    html.H5("Análise Preditiva", className="card-title"),
                    dcc.Dropdown(
                    id="dropdown_indicador",
                    options=[
                        {"label": indicador, "value": indicador}
                        for indicador in df_paciente.columns[1:8]
                    ],
                    value="Peso",
                    ),
                    
                    dcc.Graph(
                        id="forecast_normal",
                        figure={},
                    )
                  ]
              ),
        
            style={"marginLeft": 10},
            className="w-95, mb-2",
        ),
     dbc.Row(
            [
              dbc.Col(
              dbc.Card(
              dbc.CardBody(
                  [
                    html.H5("TENDÊNCIA", className="card-title"),
                
                    dcc.Graph(
                        id="viz_tendencia",
                        figure={},
                    )
                      
                  ]
              ),
              style={'marginRight':-21,'autoSize':True, "marginLeft": 10},
              className="mb-2",
              )
            ),
            dbc.Col(
              dbc.Card(
              dbc.CardBody(
                  [
                   
                    html.H5("SAZONALIDADE SEMANAL", className="card-title"),
                
                    dcc.Graph(
                        id="viz_sazonalidade",
                        figure={},
                    ),

                  ]
              ),
              style={'marginRight':0,'autoSize':True},
              className="mb-2",
              )
            ),
            ],
            justify="around" ,
            
            
        ),   
        dbc.Card(
            [
             html.H5("Projeção de risco de doenca arterial coronariana (Framingham)"),
             html.H5("Determinação de Risco em 10 anos"),
            
              dbc.CardBody(
                  [
                    dcc.Graph(
                          id="id_treemap_card",
                          figure=fig_sun_corona,
                          style={"marginTop":-20, "marginBottom":-30}
                      ),
                  ],
              ),
            ],
            style={"marginLeft": 10, "align": "center", "justify": "center"},
            className="w-95, mb-2, list-group-item d-flex align-items-center",
        ),     
    ]
)
content = html.Div(id="page-content")

#---------------------------LAYOUT ------------------------------------------------------------------------------------------
app.layout = html.Div(
                  [
                    dbc.Row(
                        [dbc.Col(barra_navegacao, width=12)]
                      ),
                    dbc.Col(
                        [
                          dcc.Location(id="url"), 
                          sidebar, 
                          content
                        ],
                        width=2,
                      ),
                      html.Div(
                        [
                         dbc.Col(
                            cards,
                            width={"offset": 1},
                            align="start"),
                        ],
                        style={'marginLeft': 190, 'marginTop': -60, 'marginRight': 10},
                        id="margin_style",
                        ),   
                  ],
              )

# ****************Callbacks **************************************************************************************************
# Grafico + tabela

@app.callback(
     Output('linechart', 'figure'),
     Input('table2', 'selected_rows'),
)
def update_data(chosen_rows):
    if len(chosen_rows)==0:
        df_filterd = df_paciente[['Data da Consulta','Peso']]
        fig = go.Figure()
        fig.add_trace(
              go.Scatter(
                x=df_filterd['Data da Consulta'],
                y=df_filterd['Peso'],
                name="Peso",
                showlegend=True
          ))
        
    else:
        print(chosen_rows)
        temp = df_new_table.loc[df_new_table.index.isin(chosen_rows), 'variável'].to_list()
        df_filterd = df_paciente[['Data da Consulta',*temp]]
        fig = go.Figure()
        for variavel in temp: 
          fig.add_trace(
              go.Scatter(
                x=df_filterd['Data da Consulta'],
                y=df_filterd[variavel],
                name=variavel,
                showlegend=True
          ))

    fig.update_layout(
            xaxis_rangeslider_visible=True,
            paper_bgcolor='rgba(255,255,255,255)',
            plot_bgcolor='rgba(255,255,255,255)',
            legend = dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="right",
                x=0.93,         
            ),
            margin=dict(l=10, r=20, t=70, b=10),
        )


    return fig

############################################

@app.callback(
    Output("sidebar", "className"),
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar", "className")],
)
def toggle_classname(n, classname):
    if n and classname == "":
        return "collapsed"
    return ""
import time
# ajustar margens

@app.callback(
    Output("margin_style", "style"),
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar", "className")],
)
def toggle_open(n, classname):
    if n and classname == "":
        time.sleep(0.18)
        return {'marginLeft': -62, 'marginTop': -60, 'marginRight': 0} 
    time.sleep(0.1)
    return {'marginLeft': 220, 'marginTop': -60, 'marginRight': 0} 

@app.callback(
    [Output("collapse", "is_open")],
    [Input("navbar-toggle", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open,

# modal_receita
@app.callback(
    Output("modal_receita", "is_open"),
    [
        Input("open_receita", "n_clicks"),
        Input("close_receita", "n_clicks")
    ], 
    [State("modal_receita", "is_open")]
)
def toggle_modal(n1, n2, is_open):
    """
    Watches over the State of the open and close buttons
    and decides wether to open or close the the modal 
    """
    if n1 or n2: 
        return not is_open 
    return is_open 

# modal_anotacoes
@app.callback(
    Output("modal_anotacoes", "is_open"),
    [
        Input("open_anotacoes", "n_clicks"),
        Input("close_anotacoes", "n_clicks")
    ], 
    [State("modal_anotacoes", "is_open")]
)
def toggle_modal(n1, n2, is_open):
    """
    Watches over the State of the open and close buttons
    and decides wether to open or close the the modal 
    """
    if n1 or n2: # if there's an n1 or an n2, equivalent to saying any button is clicked
        return not is_open # makes is_open equals to True, since it is False by default
    return is_open # no button is clicked, nothing happens (is_open remains False)

# modal_alteracoes
@app.callback(
    Output("modal_alteracoes", "is_open"),
    [
        Input("open_alteracoes", "n_clicks"),
        Input("close_alteracoes", "n_clicks")
    ], 
    [State("modal_alteracoes", "is_open")]
)
def toggle_modal(n1, n2, is_open):
    """
    Watches over the State of the open and close buttons
    and decides wether to open or close the the modal 
    """
    if n1 or n2: # if there's an n1 or an n2, equivalent to saying any button is clicked
        return not is_open # makes is_open equals to True, since it is False by default
    return is_open # no button is clicked, nothing happens (is_open remains False)

# modal_feedback
@app.callback(
    Output("modal_feedback", "is_open"),
    [
        Input("open_feedback", "n_clicks"),
        Input("close_feedback", "n_clicks")
    ], 
    [State("modal_feedback", "is_open")]
)
def toggle_modal(n1, n2, is_open):
    """
    Watches over the State of the open and close buttons
    and decides wether to open or close the the modal 
    """
    if n1 or n2: # if there's an n1 or an n2, equivalent to saying any button is clicked
        return not is_open # makes is_open equals to True, since it is False by default
    return is_open # no button is clicked, nothing happens (is_open remains False)

#---------------------------MODALS GRÁFICOS ----------------------------------------------------------------
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# vacinas
app.callback(
    Output("modalVacinas", "is_open"),
    [Input("abrirVacinas", "n_clicks"), Input("fecharVacinas", "n_clicks")],
    [State("modalVacinas", "is_open")],
)(toggle_modal)

#------------------------GRÁFICOS ---------------------------------------------------------------------------
@app.callback(
    Output("temporal_indicadores", "figure"),
    [
        Input("dropdown_indicador_paciente", "value"),
        Input("eventos_sentinelas", "value")
    ]
)
def atualizar_ambos(indicador, eventos_sentinela):

  if eventos_sentinela == None:
    temp_figuras = df_paciente2[indicador].copy()

    colors=['#56A3A6','#538890','#E3B505','#DF8328','#084C61','#724E56','#DB504A','#6c757d','#343a40']
    fig = go.Figure()
    for indicador in temp_figuras.columns:
      fig.add_trace(
          go.Scatter(
              x = df_paciente['Data da Consulta'],
              y = temp_figuras[indicador],
              name = indicador,
              showlegend=True,
          )
      )

    fig.update_layout(
            xaxis_rangeslider_visible=True,
            paper_bgcolor='rgba(255,255,255,255)',
            plot_bgcolor='rgba(255,255,255,255)',
            legend = dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="right",
                x=0.93,         
            ),
            margin=dict(l=10, r=20, t=70, b=10),
        )


    return fig

  elif (indicador == []) & (eventos_sentinela != None):
    fig = go.Figure()
    fig.update_layout(
            paper_bgcolor='rgba(255,255,255,255)',
            plot_bgcolor='rgba(255,255,255,255)',
            legend = dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="right",
                x=0.93,         
            ),
            margin=dict(l=10, r=20, t=70, b=10),
        )
    return fig

  else:
    indicadores_y = df_paciente2[indicador].copy()
    df_sentinelas = df_eventos[df_eventos["Classe do Evento"] == eventos_sentinela].copy()

    max_y = []
    min_y = []

    colors=['#56A3A6','#538890','#E3B505','#DF8328','#084C61','#724E56','#DB504A','#6c757d','#343a40']
    fig = go.Figure()
    for indicador in indicadores_y.columns:
      fig.add_trace(
          go.Scatter(
              x = df_paciente['Data da Consulta'],
              y = indicadores_y[indicador],
              name = indicador,
              showlegend=True,
          )
      )
      max_y.append(indicadores_y[indicador].max())
      min_y.append(indicadores_y[indicador].min())


    for evento_sentinela in df_sentinelas["Classe do Evento"].unique():
        df_sentinelas_filtrado = df_sentinelas[df_sentinelas["Classe do Evento"] == evento_sentinela]
        for data in df_sentinelas_filtrado.Data:
          fig.add_trace(
              go.Scatter(
                  x=[data, data],
                  y=[min(min_y) - 1, max(max_y) + 1],
                  line=dict(color='#263c41', width=2, dash='dot'),
                  showlegend=False,
                  hovertext=[
                             (dt.strftime(data, "%Y-%m-%d")+" | "+str(df_sentinelas_filtrado.loc[df_sentinelas_filtrado.Data == data, "Evento"].values[0])),
                             (dt.strftime(data, "%Y-%m-%d")+" | "+str(df_sentinelas_filtrado.loc[df_sentinelas_filtrado.Data == data, "Evento"].values[0])),
                  ],
                  hoverinfo="text"
              )
          )

          fig.update_layout(
            paper_bgcolor='rgba(255,255,255,255)',
            plot_bgcolor='rgba(255,255,255,255)',
            legend = dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="right",
                x=0.93,         
            ),
            margin=dict(l=10, r=20, t=120, b=10),
        )
          
        return fig


@app.callback(
    Output("forecast_normal", "figure"),
    Input("dropdown_indicador", "value"),
)
def plotar_forecast(variavel):

      temp_y = df_paciente.copy()
      temp_y = temp_y.groupby(["Data da Consulta"], as_index=False)[[variavel]].sum()
      temp_y.columns = ["ds", "y"]
      temp_yhat = forecast_paciente[variavel]["Forecast"].copy()
      previsao = go.Scatter(
          x=temp_yhat["ds"], y=temp_yhat["yhat"], mode="lines", name="Previsão", line={"color": "#03045e"}
      )
      superior = go.Scatter(
          x=temp_yhat["ds"],
          y=temp_yhat["yhat_upper"],
          mode="lines",
          fill="tonexty",
          fillcolor= "rgba(144, 224, 239, 0.2)",
          line={"color": "#ade8f4", "width": 0},
          name="Intervalo Superior",
      )
      inferior = go.Scatter(
          x=temp_yhat["ds"],
          y=temp_yhat["yhat_lower"],
          mode="lines",
          fill="tonexty",
          fillcolor= "rgba(144, 224, 239, 0.2)",
          line={
              "color": "#ade8f4",
              "width": 0
          },
          name="Intervalo Inferior",
      )
      pontos_y = go.Scatter(
          x=temp_y["ds"], y=temp_y["y"], name="Indicador", mode="markers",
              marker=dict(
                  size=3,
                  color="#000000",
              )
      )
      data = [previsao, superior, inferior, pontos_y]
      layout = go.Layout(
          xaxis_rangeslider_visible=True,
          paper_bgcolor='rgba(255,255,255,255)',
          plot_bgcolor='rgba(255,255,255,255)',
          legend = dict(
              orientation="h",
              yanchor="bottom",
              y=1.03,
              xanchor="right",
              x=0.93,         
          ),
          margin=dict(l=10, r=20, t=70, b=10),
      )
      fig = go.Figure(data=data, layout=layout)
      
      # figuras.append(fig)
      return fig
    

@app.callback(
    Output("viz_tendencia", "figure"),
    Input("dropdown_indicador", "value")
)
def plotar_tendencia(variavel):

        temp_y = df_paciente.copy()
        temp_y = temp_y.groupby(["Data da Consulta"], as_index=False)[[variavel]].sum()
        temp_y.columns = ["ds", "y"]

        temp_yhat = forecast_paciente[variavel]["Trend"].copy()

        previsao = go.Scatter(
            x=temp_yhat["ds"], y=temp_yhat["trend"], mode="lines", name="Previsão", line={"color": "#03045e"}
        )

        superior = go.Scatter(
            x=temp_yhat["ds"],
            y=temp_yhat["trend_upper"],
            mode="lines",
            fill="tonexty",
            fillcolor= "rgba(144, 224, 239, 0.2)",
            line={"color": "rgba(144, 224, 239, 0.1)", "width": 0},
            name="Intervalo Superior",
        )

        inferior = go.Scatter(
            x=temp_yhat["ds"],
            y=temp_yhat["trend_lower"],
            mode="lines",
            fill="tonexty",
            fillcolor= "rgba(144, 224, 239, 0.2)",
            line={"color": "rgba(144, 224, 239, 0.1)", "width": 0},
            name="Intervalo Inferior",
        )

        data = [previsao, superior, inferior]

        layout = go.Layout(
            xaxis_rangeslider_visible=True,
            paper_bgcolor='rgba(255,255,255,255)',
            plot_bgcolor='rgba(255,255,255,255)',
            legend = dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="right",
                x=0.93,         
            ),
            margin=dict(l=10, r=20, t=70, b=10),
        )

        fig = go.Figure(data=data, layout=layout)
        # figuras.append(fig)
        return fig

@app.callback(
    Output("viz_sazonalidade", "figure"),
    Input("dropdown_indicador", "value")
)
def plotar_sazonalidade(variavel):

        temp_yhat = forecast_paciente[variavel]["Weekly"].copy()
        temp_yhat = temp_yhat[("2019-10-14" <= temp_yhat.ds) & (temp_yhat.ds <= "2019-10-20")]


        previsao = go.Scatter(
            x=temp_yhat["ds"], y=temp_yhat["weekly"], mode="lines", name="Previsão", line={"color": "#03045e"}
        )

        superior = go.Scatter(
            x=temp_yhat["ds"],
            y=temp_yhat["weekly_upper"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(144, 224, 239, 0.1)",
            line={"color": "#CAF0F8", "width": 0},
            name="Intervalo Superior",
        )

        inferior = go.Scatter(
            x=temp_yhat["ds"],
            y=temp_yhat["weekly_lower"],
            mode="lines",
            fill="tonexty",
            fillcolor= "rgba(144, 224, 239, 0.2)",
            line={"color": "#CAF0F8", "width": 0},
            name="Intervalo Inferior",
        )

        data = [previsao, superior, inferior]

        layout = go.Layout(
            xaxis_rangeslider_visible=True,
            paper_bgcolor='rgba(255,255,255,255)',
            plot_bgcolor='rgba(255,255,255,255)',
            legend = dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="right",
                x=0.93,         
            ),
            xaxis = dict(
                    tickmode = 'array',
                    tickvals = temp_yhat.ds,
                    ticktext = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
                  ),
            margin=dict(l=10, r=20, t=70, b=10),
        )


        fig = go.Figure(data=data, layout=layout)

        fig.add_shape(type='line',
                x0="2019-10-14",
                y0=0,
                x1="2019-10-20",
                y1=0,
                line=dict(color='#adb5bd', dash='dot'),
                xref='x',
                yref='y'
        )

        return fig


if __name__ == "__main__":
  app.run_server(debug=True)
