"""
import dependencies 
"""
import numpy as np
import pandas as pd
from os import listdir

import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, dash_table, State 
from dash.dependencies import Input, Output

import plotly.graph_objects as go
import plotly.express as px

import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.append('./functions/')
import correlation_coefficient

"""
Read in datafiles, will change to read directly from S3
"""
path = r'../data/'
filenames = listdir(path)
files=[path+'/'+f for f in filenames if f.endswith('.csv') ]

df=pd.concat([pd.read_csv(f) for f in files]).reset_index(drop=True)
# print(np.shape(df)

df_nobool=df[[col for col in df.columns if 'bool' not in col]]
# print(np.shape(df_nobool))

columns_to_change=[
    'context_block_code','context_participant','modality','context_accession_number',
    'act_seq_acc','act_seq_bc']
for c in columns_to_change:
    df_nobool[c]=df_nobool[c].astype('category')

df_nobool_hist= df_nobool[['context_block_code', 'modality']]

df_nobool_scatter = df_nobool.select_dtypes(include=np.number)
# print(np.shape(df_nobool_scatter))
threshold=0.3
df_corr=correlation_coefficient.get_top_correlations_blog(df_nobool_scatter, threshold=threshold)
df_corr["feature_pairs"] = df_corr["Feature1"] +" & "+ df_corr["Feature2"]

corr_range=[0.3,0.5,0.8,1.0]  
corr_range_str=['('+str(corr_range[i])+','+str(corr_range[i+1])+']'
                for i in range(len(corr_range)-1)]

df_corr['correlation_range']=pd.cut(df_corr.iloc[:,2], bins=corr_range, labels=corr_range_str)
df_corr=df_corr.sort_values(df_corr.columns[2],ascending=False)


"""
Start plotting 
"""
app = Dash(__name__,title="Naep2024FeatureDevelopment", 
           external_stylesheets=['./assets/style.css',dbc.themes.SANDSTONE])
server = app.server

app.layout = html.Div(
    children=[
        html.H1(
        children="NAEP Feature Developments - 2024",
        className='title',
        ),
        
        html.Div([
            ### Left Histogram Graph container
            html.Div([
                dcc.Dropdown(
                    id='histogram',
                    options=df_nobool_hist.columns,
                    value=None,
                    placeholder='Select Feature',
                    style ={
                            'font-size':'20px',
                            'height':'40px'},
                    ),
                    dcc.Graph(id='histogram-plot',
                              style={'width':'100%',
                                  'margin-top':'20px',
                                  'display':'inline-block',})
                    ], style ={'width':'48%',
                               'display':'inline-block',
                               'margin-left':'10px',
                               'margin-right':'10px',
                               'margin-top':'20px',}
                    ),           
        
            ### Right Scatter Graph container
            html.Div([
                
                dbc.Container([
                dbc.Row([
                    dbc.Col(    
                    dcc.Dropdown(
                    id='correlation-range-dropdown',
                    options=[{'label': i, 'value': i} for i in df_corr.iloc[:,4].unique()],
                    value=None, 
                    placeholder='Select Correlation Range',
                    style ={
                        'font-size':'20px',
                        'height':'40px',
                        'margin-right':'-20px',
                        }, 
                    ), width=4,
                ),
                
                    dbc.Col(  
                    dcc.Dropdown(
                    id='feature-pairs-dropdown',
                    placeholder='Select Feature Pairs',
                    optionHeight=60,
                    style ={
                        'font-size':'20px',
                        'height':'40px',
                        'margin-right':'-20px',
                        },
                    ), width=8,
                )
                ])
                ]),
                
                   
                dcc.Graph(
                    id='graph',
                    style={
                        'width':'100%',
                        'margin-left':'10px',
                        'margin-right':'10px',
                        'margin-top':'20px',
                        'display':'inline-block',
                        }
                    ),
                ],
                     style ={'width':'48%',
                             'display':'inline-block',
                             'margin-left':'10px',
                             'margin-right':'10px',
                             'margin-top':'20px',
                             }
                     ) 
            ],
                 style={'display': 'flex'},
        ),
    ],)
   
    
"""
Call back histogram
"""
@app.callback(
    Output('histogram-plot', 'figure'),
    [Input('histogram', 'value')]
)

def update_graph(col):
    if col is None:
        # fig = px.histogram(df_nobool_hist, x="context_block_code")
        # title="context_block_code"
        fig = go.Figure(
            go.Histogram(x=pd.Series(dtype=object), y=pd.Series(dtype=object))
            )
        fig.update_layout(
        title={'text':"Select Feature for Histogram",'x':0.5,},
        font=dict(size=14),
        paper_bgcolor="LightSteelBlue",
        ) 
        
    else:
        fig = px.histogram(df_nobool_hist, x=col)  
        title=col

    fig.update_layout(
        bargap=0.2,
        xaxis_title="",
        font=dict(size=16),
        paper_bgcolor="LightSteelBlue",
        ) 
    return fig


"""
Call back scatter
"""

@app.callback(
    Output('feature-pairs-dropdown', 'options'),
    Input('correlation-range-dropdown', 'value')
)

def update_correlation_range_dropdown(selected_range):
    filtered_df = df_corr[df_corr.iloc[:,4] == selected_range]
    return [{'label': i, 'value': i} for i in filtered_df.iloc[:,3].tolist()]

@app.callback(
    Output('graph', 'figure'),
    [Input('correlation-range-dropdown', 'value'),
     Input('feature-pairs-dropdown', 'value')]
)

def update_graph(selected_range, selected_feature_pairs):
    if selected_range is None or selected_feature_pairs is None:
        fig = go.Figure(
            go.Scatter(x=pd.Series(dtype=object), y=pd.Series(dtype=object), mode="markers")
            )
        fig.update_layout(
        title={'text':"Select Correlation Coefficient Range and Feature Pairs",'x':0.5,},
        font=dict(size=14),
        paper_bgcolor="LightSteelBlue",
        )     
    elif selected_feature_pairs is not None:  
        feature1= selected_feature_pairs.replace(' ','').split('&')[0]
        feature2= selected_feature_pairs.replace(' ','').split('&')[1]
        
        fig = px.scatter(df_nobool_scatter, 
                     x=feature1, y=feature2, trendline="ols",)  
        corr_coef = np.round(df_nobool_scatter[feature1].corr(df_nobool_scatter[feature2]), 3)
        fig.update_traces(marker=dict(size=8),selector=dict(mode='markers'))
        fig.update_layout(
        title={'text':" Pearson Correlation Coefficient ="+str(corr_coef),'x':0.5,},
        font=dict(size=14),
        paper_bgcolor="LightSteelBlue",
        )       
    return fig        
    

if __name__ == '__main__':
    app.run_server(debug=True)

