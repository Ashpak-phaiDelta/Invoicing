import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from _datetime import datetime as dt

def get_summary_data(filtered_df):
    fig = px.line(filtered_df, x="Date", y='Amount', color="Data_Type", text='Amount',
                  # labels=dict(Date="Dates ($)", tip="Tip ($)", sex="Payer Gender")
                  )
    df = filtered_df[filtered_df['Data_Type'] == 'Expense Amount']
    Expense_Amount=sum(df['Amount'])

    df = filtered_df[filtered_df['Data_Type'] == 'Profit']
    Profit_Amount=sum(df['Amount'])

    df = filtered_df[filtered_df['Data_Type'] == 'Payment Amount']
    Payment_Amount=sum(df['Amount'])

    df = filtered_df[filtered_df['Data_Type'] == 'Montly invoice Amount']
    invoice_Amount = sum(df['Amount'])

    df = filtered_df[filtered_df['Data_Type'] == 'Margin']
    Margin_per = f"{sum(df['Amount'])//len(df['Amount'])}%"


    return fig,Expense_Amount,Profit_Amount,Margin_per,Payment_Amount,invoice_Amount

def monthly_invoice(dates=None):
    invoice_file = pd.read_excel('./Invoice.xls', index_col='Sr.No.')
    df={}
    df['Date']=[]
    df['Montly invoice Amount']=[]
    if dates==None:
        dates=invoice_file['Date'].unique()
    for date in invoice_file.Date.unique():
        df['Date'].append(date)
        df['Montly invoice Amount'].append(sum(invoice_file[(invoice_file['Date']==date)]['Invoice Amount']))
    df=pd.DataFrame(df)
    return df

def montly_payment_details_for_project(project,dates=None):
    customer_payment_file = pd.read_excel('./customer payment.xls', index_col='Sr.No.')
    dfe={}
    dfe['Date']=[]
    dfe['Payment Amount']=[]
    dfe['Project']=[]
    if dates==None:
        df=customer_payment_file[(customer_payment_file['Project Name'].isin(project))]
    else:
        df=customer_payment_file[(customer_payment_file['Project Name'].isin(project))& (customer_payment_file['Date'].isin(dates))]

    for date in list(df['Date'].unique()):
        for project in df[df['Date']==date]['Project Name']:
            dfe['Payment Amount'].append(sum(df[(df['Date']==date)&(df['Project Name']==project)]['Payment amount']))
            dfe['Date'].append(date)
            dfe['Project'].append(project)
    return pd.DataFrame(dfe)

def montly_expense_details_for_project(project, dates=None):
    expense_file = pd.read_excel('./Expense.xls', index_col='Sr.No.')
    dfe = {}
    dfe['Date'] = []
    dfe['Expense Amount'] = []
    dfe['Project'] = []
    dfe['Expense Type'] = []
    if dates == None:
        df = expense_file[(expense_file['Project Name'].isin(project))]
    else:
        df = expense_file[(expense_file['Project Name'].isin(project)) & (expense_file['Date'].isin(dates))]

    for date in list(df.Date.unique()):
        for project in df[df['Date'] == date]['Project Name']:
            dfe['Date'].append(date)
            dfe['Expense Amount'].append(sum(df[(df['Date'] == date)&(df['Project Name'] == project)]['Expense Amount']))
            dfe['Project'].append(project)
            dfe['Expense Type'].append(df[(df['Date'] == date)&(df['Project Name'] == project)]['Expense Type'].unique())
    dfe = pd.DataFrame(dfe)
    return dfe

def merge_data_frames(df1,df2,key , how='inner'):
    df_result=pd.merge(df1, df2, on=key, how=how)
    df_result = df_result.sort_values(by=key)
    return df_result

def add_profit(df, Payments_col_name, Expense_col_name ):
    profit = []
    for index in range(len(df[Payments_col_name])):
        profit.append(df[Payments_col_name][index] - df[Expense_col_name][index])
    df['Profit'] = profit
    return df

def add_margin(df, Payments_col_name, Profit_col_name ):
    Margin = []
    for index in range(len(df[Payments_col_name])):
        Margin.append(df[Profit_col_name][index]//(df[Payments_col_name][index]*0.01))
    df['Margin'] = Margin
    return df

def combine_df(df, column_list):
    new_df = {}
    new_df['Date'] = []
    new_df['Data_Type'] = []
    new_df['Amount'] = []
    new_df['Project'] = []

    for date in df['Date']:
        for column in column_list:
#             print(column,date)
            new_df['Date'].append(date)
            new_df['Data_Type'].append(column)
            new_df['Amount'].append(sum(df[df['Date'] == date][column]))
            new_df['Project'].append(df[df['Date'] == date]['Project_x'].values[0])
    return pd.DataFrame(new_df)

def get_data_frame(selection_):
    if type(selection_)!=list:
        selection_=list(selection_)
    monthly_invoice_details = monthly_invoice()
    montly_payment = montly_payment_details_for_project(selection_)
    montly_expense = montly_expense_details_for_project(selection_)
    df_result=merge_data_frames(montly_expense,monthly_invoice_details, 'Date')
    df_result=merge_data_frames(df_result,montly_payment, 'Date')
    df_result.drop(columns='Project_y', inplace=True)
    df_total= add_profit(df_result,'Payment Amount', 'Expense Amount')
    df_total=add_margin(df_result,'Payment Amount', 'Profit')
    return combine_df(df_total,['Expense Amount', 'Montly invoice Amount', 'Payment Amount', 'Profit','Margin'])




external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}


new_df=get_data_frame(['ABCD','DJFC','INTERNAL'])

available_Project=new_df['Project'].unique()
print(available_Project)
available_years=new_df['Date'].dt.year.unique()
print(available_years)
available_Dates=[]
for year in available_years:
    available_Dates.extend(list(new_df[new_df['Date'].dt.year==year]['Date'].unique()))
    # available_Dates
# available_Dates=new_df['Date'].unique()
print(available_Dates)


app.layout = html.Div([
    #Dropdowns
    html.Div([
    #Projects
    html.Div([
        html.Label('Project'),
        dcc.Dropdown(
        id='crossfilter-Project-column',
        options=[{'label': i, 'value': i} for i in available_Project],
        value=available_Project,
        multi=True
    )
],
    style = {'width': '30%', 'display': 'inline-block'}),
    #Dates
    html.Div([
        html.Label('From Date'),
        dcc.Dropdown(
            id='crossfilter-Date-column',
            options=[{'label': dt.fromtimestamp(int(i)//10**9).strftime('%m-%y'), 'value': dt.fromtimestamp(int(i)//10**9).strftime('%Y-%m')} for i in available_Dates],
            value= [dt.fromtimestamp(int(i)//10**9).strftime('%Y-%m') for i in available_Dates],
            multi=True
        )
],style = {'width': '69%', 'display': 'inline-block'}),

]),
    html.Div([
    #Year
#     html.Div([
#         html.Label('From Date'),
#         dcc.Dropdown(
#             id='crossfilter-Year-column',
#             options=[{'label': i, 'value': i} for i in available_years],
#             value=available_years,
#             # options=[{'label': dt.fromtimestamp(int(i)//10**9).strftime('%y'), 'value': dt.fromtimestamp(int(i)//10**9).strftime('%Y')} for i in available_Dates],
#             # value= [dt.fromtimestamp(int(i)//10**9).strftime('%Y') for i in available_Dates],
#             multi=True
#         )
# ],style = {'width': '69%', 'display': 'inline-block'})
    ]),
    #Summary
    html.Div([
        html.Div([
            html.Label('Summary: ')
        ]),
       html.Div(
        [
            html.Div(                    html.Label('Total Invoice amount:')),
            html.Div(children=[html.H2(''), html.H2(id='Invoice-Amount')],
                     style={'width': '20%', 'display': 'inline-block', 'text-align': 'center', 'font-family': 'Century Gothic'})
            ]
        ,    style = {'width': '20%', 'display': 'inline-block'}),
        html.Div([
            # Output('Payment-Amount', 'children'),    # Payment_Amount
            html.Div([html.Label('Total Payment amount:')]),
            html.Div(children=[html.H2(''), html.H2(id='Payment-Amount')],
                     style={'width': '20%', 'display': 'inline-block', 'text-align': 'center',
                            'font-family': 'Century Gothic'}),

       ],    style = {'width': '20%', 'display': 'inline-block'}),
        html.Div([
            # Output('Expense-Amount', 'children'), #Expense_Amount
            html.Div([            html.Label('Total Expense amount')]),
            html.Div(children=[html.H2(''), html.H2(id='Expense-Amount')],
                     style={'width': '20%', 'display': 'inline-block', 'text-align': 'center',
                            'font-family': 'Century Gothic'})
       ],    style = {'width': '20%', 'display': 'inline-block'}),
        html.Div([
            # Output('Profit-Amount', 'children'),
            # #Profit_Amount
            html.Div([            html.Label('Total Profit Earned')]),
            html.Div(children=[html.H2(''), html.H2(id='Profit-Amount')],
                     style={'width': '20%', 'display': 'inline-block', 'text-align': 'center',
                            'font-family': 'Century Gothic'})
       ],    style = {'width': '20%', 'display': 'inline-block'}),
        html.Div([
            html.Div([            html.Label('Total Profit Margin')]),
            html.Div(children=[html.H2(''), html.H2(id='Margin-Amount')],
                     style={'width': '20%', 'display': 'inline-block', 'text-align': 'center',
                            'font-family': 'Century Gothic'})
       ],    style = {'width': '20%','float': 'right', 'display': 'inline-block'})
]),
    #Main graph
   html.Div([
            dcc.Graph(id='graph-with-slider'),
            ]),
    # subplots
    html.Div([
            dcc.Graph(id='sub-graph'),
    ]),
    # Profit-Plot
    html.Div([
        dcc.Graph(id='Profit-Plot'),
    ]),
    ])


@app.callback(
[Output('graph-with-slider', 'figure'), #fig
Output('Expense-Amount', 'children'), #Expense_Amount
Output('Profit-Amount', 'children'),    #Profit_Amount
Output('Margin-Amount', 'children'),    #Margin%
Output('Payment-Amount', 'children'),    # Payment_Amount
Output('Invoice-Amount', 'children')],    # invoice_Amount
Output('sub-graph','figure'), #Subplot
Output('Profit-Plot','figure'), #Profitplot

Input('crossfilter-Project-column','value'),
Input('crossfilter-Date-column','value'),
# Input('crossfilter-Year-column','value')
              )
def update_figure(selection_,from_date ): #, year
    # if type(year)!=list:
    #     year=[year]

    # to convert i/p in list
    if type(from_date)!=list:
        from_date=[from_date]

    if type(selection_)!=list:
        selection_=[selection_]

    filtered_df=get_data_frame(selection_)
    filtered_df=filtered_df[(filtered_df['Date'].isin(from_date))]
    print(filtered_df)
    sub_graph=px.bar(filtered_df[filtered_df['Data_Type'].isin(['Expense Amount','Montly invoice Amount','Payment Amount'])],x='Date',y='Amount',facet_col='Data_Type', text='Amount')
    profit_plot=px.line(filtered_df[filtered_df['Data_Type'].isin(['Profit','Margin'])],x='Date',y='Amount',facet_col='Data_Type', text='Amount')
    fig,Expense_Amount,Profit_Amount,Margin_per,Payment_Amount,invoice_Amount = get_summary_data(filtered_df)
    return fig,Expense_Amount,Profit_Amount,Margin_per,Payment_Amount,invoice_Amount, sub_graph, profit_plot



if __name__ == '__main__':
    app.run_server(debug=True)

