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
import correlation_coefficient, titlerenderer

"""
Read in datafiles, will change to read directly from S3
"""
path = r'C:\Users\SZHANG\OneDrive - Educational Testing Service\Desktop\FeatureDev_2024'
filenames = listdir(path)
files=[path+'/'+f for f in filenames if f.endswith('.csv') ]

df_ori=pd.concat([pd.read_csv(f) for f in files]).reset_index(drop=True)
# print(np.shape(df_ori))

df=df_ori.drop([
    'subject','grade','blockContent','language','accommodation','context_accession_number.1',
    'n_enter_screen','n_exit_screen','n_enter_block','n_exit_block','n_enter_item','n_exit_item',
    'n_enter_assessment',
    ],axis=1,errors='ignore')
# print(np.shape(df))
df_nobool=df[[col for col in df.columns if 'bool' not in col]]
# print(np.shape(df_nobool))

columns_to_change=[
    'context_block_code','context_participant','modality','context_accession_number',
    'act_seq_acc','act_seq_bc']
for c in columns_to_change:
    df_nobool[c]=df_nobool[c].astype('category')
    
df_nobool_numerics = df_nobool.select_dtypes(include=np.number)
# print(np.shape(df_nobool_numerics))
threshold=0.8
threshold_column='Correlation Coefficient>'+str(threshold)
df_top_corr=correlation_coefficient.get_top_correlations_blog(df_nobool_numerics, threshold=threshold)
# print(df_top_corr.head())

"""
Start plotting 
"""
subject_list=['Select a Profile Report for Subject: All','Reading','Math','Science']


app = Dash(__name__,title="Naep2024FeatureDevelopment", external_stylesheets=['./assets/style.css'])
server = app.server

app.layout = html.Div(
    children=[
        html.H1(
        children="2024 NAEP Feature Developments",
        style ={'color':'#000000','font-family':'Arial',
                'font-size':'36px','font-weight':'bold',
                'text-align':'center'},
        ),

        html.Div([
            
            ### Graph container
            html.Div([
                dcc.Dropdown(
                    id='profile',
                    options=subject_list,
                    value=subject_list[0],
                    clearable=False,
                    style ={'background-color':'#d1d1d9','font-size':'20px','font-weight':'bold','height':'40px'},
                    ),
                    html.Div(id='profile_input'),
                    ],   
                    style ={'width':'50%','display':'inline-block',
                            'margin-left':'20px','margin-top': 10,}
                    ),
            
            ### Table container
            html.Div([
                dash_table.DataTable(
                    id='correlation_table',
                    columns= [{"name": i, "id": i} for i in df_top_corr.columns],
                    data=df_top_corr.to_dict('records'),
                    ### Table Styling
                    style_table={'margin-top': 10},
                    style_header={'backgroundColor': 'rgb(30, 30, 30)','color':'white','whiteSpace':'normal'},
                    style_data={'backgroundColor': '#d1d1d9',},        
                    style_cell={'font-size':'18px','textAlign': 'center'},
                    style_cell_conditional=[{'if':{'column_id':threshold_column},'width':'25%'},],
                    ### DataTable Interactivity
                    row_selectable='single',
                    editable=False,
                    ),
                    ], style ={'width':'44%','display':'inline-block',
                               'margin-left':'30px'}
                    ),
            html.Div(id='display_selected_row'),
        
        ], style={'display': 'flex'},
        ) ,     
        ],)


@app.callback(
    Output('profile_input', 'children'), 
    [Input('profile', 'value')]
    )

def update_profile(value):
    if not value: return []
    subjects= {'Select a Profile Report for Subject: All':'All',
               'Reading':'RE','Math':'MA','Science':'SC'}
    return html.Iframe(
        src="assets/Profile_Report_"+subjects[value]+"_NoBoolean.html",
        style={"height":"600px",'width':'100%','border':'2px solid grey'}
            )

@app.callback(
    output=Output('display_selected_row', "children"),
    inputs=[Input('correlation_table', "selected_rows")],
    state=[State('correlation_table', "data")],
    prevent_initial_call=True)

def update_graph(selected_rows, rows):
    
    if len(selected_rows)!=0:
        dff=pd.DataFrame(rows)
        ftr1=dff.iloc[selected_rows,0].values[0]
        ftr2=dff.iloc[selected_rows,1].values[0]
        r2=dff.iloc[selected_rows,2].values[0]
        fig = px.scatter(df_nobool_numerics, x=ftr1, y=ftr2,trendline="ols")
        fig.update_traces(marker=dict(size=8,line=dict(width=1,color='DarkSlateGrey')),
                  selector=dict(mode='markers'))
        fig.update_layout(
            title={
                'text':"Pearson Correlation Coefficient ="+str(r2),
                'x':0.5,},
            font=dict(size=16),autosize=False, width=650, height=600,paper_bgcolor="LightSteelBlue",)
        return fig.show(renderer="titleBrowser", browser_tab_title=ftr1+' vs '+ftr2)
    

if __name__ == "__main__":
    app.run_server(debug=True)
    ### Open terminal and run python app.py
    


