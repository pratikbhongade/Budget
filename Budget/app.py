from flask import Flask, render_template, request, redirect, url_for, session
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import json
import features

# Initialize Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize Dash with a light Bootstrap theme
dash_app = Dash(__name__, server=app, url_base_pathname='/dashboard/', external_stylesheets=[dbc.themes.LUX])

# Load merchant categorization rules from JSON file
with open('data/merchant_categories.json') as f:
    merchant_data = json.load(f)

currency_options = [
    {'label': 'USD', 'value': 'USD'},
    {'label': 'EUR', 'value': 'EUR'},
    {'label': 'INR', 'value': 'INR'},
    {'label': 'GBP', 'value': 'GBP'},
]

category_rules = {merchant['merchant']: merchant['category'] for merchant in merchant_data['merchants']}

# Sample transaction data
excel_file_path = 'data/sample_transaction_sheet.xlsx'

# Function to read the Excel file and return DataFrame
def load_excel_data(file_path):
    return pd.read_excel(file_path, engine='openpyxl')

# Function to categorize transactions based on merchant rules
def categorize_transactions(transaction_df):
    transaction_df['Category'] = transaction_df['Description'].apply(
        lambda x: next((category for merchant, category in category_rules.items() if merchant.lower() in x.lower()), 'Uncategorized'))
    return transaction_df

# Load the Excel data for the dashboard and categorize transactions
transaction_data = categorize_transactions(load_excel_data(excel_file_path))

# Function to calculate total income, expenses, and savings
def calculate_summary():
    income = transaction_data[transaction_data['Transaction Type'] == 'Credit']['Amount'].sum()
    expenses = transaction_data[transaction_data['Transaction Type'] == 'Debit']['Amount'].sum()
    savings = income - expenses
    budget_percentage = (expenses / 5000) * 100  # Assuming a fixed budget of 5000 for this example
    return income, expenses, savings, budget_percentage

# Protect dashboard with login
@app.before_request
def restrict_dashboard():
    if 'logged_in' not in session and request.path.startswith('/dashboard'):
        return redirect(url_for('login'))

# Function to dynamically change progress bar color based on budget usage
def get_progress_color(budget_percentage):
    if budget_percentage <= 50:
        return "success"  # Green
    elif 50 < budget_percentage <= 80:
        return "warning"  # Yellow
    else:
        return "danger"   # Red

# Function to fetch financial news from local JSON
def fetch_financial_news():
    try:
        with open('data/financial_news.json', 'r') as f:
            news_data = json.load(f)
            return news_data.get('articles', [])
    except Exception as e:
        return []

# Function to fetch currency conversion rates from local JSON
def fetch_currency_conversion_rates():
    try:
        with open('data/currency_rates.json', 'r') as f:
            rates_data = json.load(f)
            return rates_data.get('rates', {})
    except Exception as e:
        return {}

# Function to fetch the top 5 transactions by amount
def top_5_transactions():
    top_transactions = transaction_data.nlargest(5, 'Amount')
    return dbc.Card([
        dbc.CardBody([
            html.H5("Top 5 Transactions", className="card-title", style={"color": "black"}),
            html.Ul([html.Li(f"{row['Description']} - ${row['Amount']:,.2f}", style={"color": "black"}) for _, row in top_transactions.iterrows()])
        ])
    ], className="mb-4")

# Function to fetch the top 5 categories by total spending
def top_5_categories():
    category_totals = transaction_data[transaction_data['Transaction Type'] == 'Debit'].groupby('Category')['Amount'].sum()
    top_categories = category_totals.nlargest(5)
    return dbc.Card([
        dbc.CardBody([
            html.H5("Top 5 Categories", className="card-title", style={"color": "black"}),
            html.Ul([html.Li(f"{category} - ${amount:,.2f}", style={"color": "black"}) for category, amount in top_categories.items()])
        ])
    ], className="mb-4")

# Function to fetch the top 5 merchants by total spending
def top_5_merchants():
    merchant_totals = transaction_data[transaction_data['Transaction Type'] == 'Debit'].groupby('Description')['Amount'].sum()
    top_merchants = merchant_totals.nlargest(5)
    return dbc.Card([
        dbc.CardBody([
            html.H5("Top 5 Merchants", className="card-title", style={"color": "black"}),
            html.Ul([html.Li(f"{merchant} - ${amount:,.2f}", style={"color": "black"}) for merchant, amount in top_merchants.items()])
        ])
    ], className="mb-4")

# Layout for the dashboard with tabs
dash_app.layout = html.Div(
    style={
        'background-image': 'url("https://www.toptal.com/designers/subtlepatterns/patterns/dot-grid.png")',
        'background-size': 'cover',
        'min-height': '100vh',
        'padding': '20px',
        'color': '#212529',  # Dark font color for the entire dashboard
        'transition': 'opacity 1s ease-in-out'
    },
    children=[
        html.Link(rel="stylesheet", href="https://fonts.googleapis.com/icon?family=Material+Icons"),
        dbc.Container([
            dbc.Tabs([
                dbc.Tab(label="Dashboard", tab_id="dashboard"),
                dbc.Tab(label="Budget Tracker", tab_id="budget-tracker")  # Budget Tracker tab
            ], id="tabs", active_tab="dashboard"),

            html.Div(id="tab-content", className="p-4")
        ], fluid=True)
    ]
)

# Callback to switch between tabs
@dash_app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "dashboard":
        # Layout for the main dashboard
        return html.Div([
            # Main dashboard content like summary cards, graphs, etc.
            dbc.Row([
                dbc.Col(html.H1("Bank Customer Budgeting Tool", className="text-center mb-4 text-dark"), width=12)
            ]),

            # Modern Summary Cards for Income, Expenses, Savings, and Budget Used
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.I(className="material-icons", style={"float": "right", "color": "#ffffff99", "font-size": "36px"}, children="attach_money"),
                                html.H4("Total Income", className="card-title text-white"),
                                html.H2(f"${calculate_summary()[0]:,.2f}", className="card-text text-white")
                            ])
                        ]),
                        style={"background": "linear-gradient(135deg, #6A82FB, #FC5C7D)"}, 
                        className="card"
                    ), 
                    width=3, className="mb-4"
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.I(className="material-icons", style={"float": "right", "color": "#ffffff99", "font-size": "36px"}, children="money_off"),
                                html.H4("Expenses", className="card-title text-white"),
                                html.H2(f"${calculate_summary()[1]:,.2f}", className="card-text text-white")
                            ])
                        ]),
                        style={"background": "linear-gradient(135deg, #ff5f6d, #ffc371)"},  # Reddish gradient
                        className="card"
                    ), 
                    width=3, className="mb-4"
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.I(className="material-icons", style={"float": "right", "color": "#ffffff99", "font-size": "36px"}, children="savings"),
                                html.H4("Savings", className="card-title text-white"),
                                html.H2(f"${calculate_summary()[2]:,.2f}", className="card-text text-white")
                            ])
                        ]),
                        style={"background": "linear-gradient(135deg, #11998E, #38EF7D)"}, 
                        className="card"
                    ), 
                    width=3, className="mb-4"
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.I(className="material-icons", style={"float": "right", "color": "#ffffff99", "font-size": "36px"}, children="pie_chart"),
                                html.H4("Budget Used", className="card-title text-white"),
                                dbc.Progress(value=calculate_summary()[3], color=get_progress_color(calculate_summary()[3]), className="mt-2"),
                                html.P(f"{calculate_summary()[3]:.2f}%", className="text-white")
                            ])
                        ]),
                        style={"background": "linear-gradient(135deg, #F7971E, #FFD200)"}, 
                        className="card"
                    ), 
                    width=3, className="mb-4"
                )
            ], className="mb-4"),

            # Graphs for income-expense comparison and category breakdown
            dbc.Row([
                dbc.Col(html.Div(
                    dcc.Loading(
                        id="loading-1",
                        type="circle",
                        children=dcc.Graph(id='income-expense-comparison', config={
                            'displayModeBar': True,
                            'scrollZoom': True  # Enable zoom and pan
                        })
                    ), className="graph-container"
                ), width=6),

                dbc.Col(html.Div(
                    dcc.Loading(
                        id="loading-2",
                        type="circle",
                        children=dcc.Graph(id='category-breakdown', config={
                            'displayModeBar': True,
                            'scrollZoom': True  # Enable zoom and pan
                        })
                    ), className="graph-container"
                ), width=6),
            ], className="mb-4"),

            # Row for Top 5 Transactions, Categories, and Merchants
            dbc.Row([
                dbc.Col(top_5_transactions(), width=4),
                dbc.Col(top_5_categories(), width=4),
                dbc.Col(top_5_merchants(), width=4)
            ], className="mb-4"),

            # Savings trend graph
            dbc.Row([
                dbc.Col(html.Div(
                    dcc.Loading(
                        id="loading-3",
                        type="circle",
                        children=dcc.Graph(id='savings-trend', config={
                            'displayModeBar': True,
                            'scrollZoom': True  # Enable zoom and pan
                        })
                    ), className="graph-container"
                ), width=6),

                # Financial News and Currency Conversion Widget
                dbc.Col([
                    html.H4("Financial News", className="text-dark"),
                    dcc.Loading(
                        id="loading-4",
                        type="circle",
                        children=html.Div(id='financial-news', style={
                            "background-color": "#ffffff",
                            "border-radius": "15px",
                            "box-shadow": "0 4px 16px rgba(0, 0, 0, 0.2)",
                            "padding": "20px",
                            "height": "250px",
                            "overflow-y": "scroll",
                            "border-left": "5px solid #F7971E",
                            "transition": "box-shadow 0.3s ease-in-out"
                        })
                    ),
                    # Currency Conversion Widget
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Currency Converter", className="card-title", style={"color": "black"}),

                            # First row: Base and Target Currency with switch arrow in between
                            dbc.Row([
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='base-currency',
                                        options=currency_options,
                                        placeholder="Base Currency",
                                        style={'margin-bottom': '10px', 'color': 'black'}
                                    ), width=5
                                ),
                                dbc.Col(
                                    html.I(className="material-icons", children="swap_horiz", style={"font-size": "36px", "cursor": "pointer", "color": "black"}, id="switch-arrow"),
                                    width=2,
                                    style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='target-currency',
                                        options=currency_options,
                                        placeholder="Target Currency",
                                        style={'margin-bottom': '10px', 'color': 'black'}
                                    ), width=5
                                ),
                            ]),

                            # Second row: Amount and Convert Button
                            dbc.Row([
                                dbc.Col(
                                    dcc.Input(id='amount', type='number', placeholder='Amount', className="form-control", style={'color': 'black'}),
                                    width=6
                                ),
                                dbc.Col(
                                    html.Button('Convert', id='convert-btn', className='btn btn-primary btn-block'),
                                    width=6
                                ),
                            ]),
                            html.Div(id='conversion-result', style={'margin-top': '10px', 'color': 'black'}),
                        ])
                    ], className="mt-4", style={"height": "220px"})  # Reduced height for the card
                ], width=6),
            ]),

            # Transaction Details Table
            dbc.Row([
                dbc.Col(html.Div([
                    html.H4("Transaction Details", className="mt-4 text-dark"),
                    html.Table([
                        html.Thead(html.Tr([html.Th(col, style={"border-bottom": "2px solid #dee2e6", "padding": "10px", "text-align": "center", "color": "#212529"}) for col in transaction_data.columns], className="text-dark")),
                        html.Tbody([
                            html.Tr([html.Td(transaction_data.iloc[i][col], style={"border-bottom": "1px solid #dee2e6", "padding": "10px", "text-align": "center", "background-color": "#f8f9fa", "color": "#212529"}) for col in transaction_data.columns])
                            for i in range(len(transaction_data))
                        ])
                    ], className="table table-bordered table-hover", style={
                        "border-radius": "15px",
                        "box-shadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
                        "border": "2px solid #dee2e6"
                    })
                ]))
            ])
        ])

    elif active_tab == "budget-tracker":
        # Content for Budget Tracker tab
        return html.Div([
            dbc.Row([
                dbc.Col(features.budget_setting_layout(), width=4),  # Budget settings from features.py
                dbc.Col(features.budget_progress_layout(transaction_data), width=8)  # Progress tracking from features.py
            ])
        ])
    return html.P("No tab selected")

# Callback to update income-expense comparison and category breakdown graphs
@dash_app.callback(
    [Output('income-expense-comparison', 'figure'),
     Output('category-breakdown', 'figure'),
     Output('savings-trend', 'figure')],
    [Input('tabs', 'active_tab')]
)
def update_graphs(active_tab):
    if active_tab == "dashboard":
        # Filter and prepare data for the graphs
        filtered_data = transaction_data.copy()

        # Income vs. Expense comparison graph
        income_expense_fig = px.bar(
            filtered_data,
            x='Date',
            y='Amount',
            color='Transaction Type',
            title='Income vs Expenses Over Time',
            barmode='group',
            template='plotly_white'
        )

        # Category breakdown pie chart
        category_labels = filtered_data[filtered_data['Transaction Type'] == 'Debit']['Category'].unique()
        category_values = filtered_data[filtered_data['Transaction Type'] == 'Debit'].groupby('Category')['Amount'].sum().values

        category_fig = go.Figure(
            go.Pie(
                labels=category_labels,
                values=category_values,
                hoverinfo='label+percent',
                textinfo='value',
                pull=[0 for _ in category_labels]
            )
        )
        category_fig.update_layout(title="Expense Breakdown by Category", template="plotly_white")

        # Savings trend graph
        savings_data = filtered_data.groupby('Date').apply(
            lambda x: x[x['Transaction Type'] == 'Credit']['Amount'].sum() - x[x['Transaction Type'] == 'Debit']['Amount'].sum()
        ).cumsum().reset_index()

        savings_fig = px.line(savings_data, x='Date', y=0, title="Cumulative Savings Over Time", template="plotly_white")

        return income_expense_fig, category_fig, savings_fig

    return {}, {}, {}

# Callback for currency conversion
@dash_app.callback(
    Output('conversion-result', 'children'),
    [Input('convert-btn', 'n_clicks')],
    [State('base-currency', 'value'),
     State('target-currency', 'value'),
     State('amount', 'value')]
)
def convert_currency(n_clicks, base, target, amount):
    if n_clicks and base and target and amount:
        rates = fetch_currency_conversion_rates()

        # Ensure both base and target currencies are available in the rates
        if base in rates and target in rates:
            conversion_rate = rates[target] / rates[base]  # Calculate the conversion rate
            converted_amount = amount * conversion_rate
            return f"{amount} {base} = {converted_amount:.2f} {target}"
        else:
            return "Conversion failed. Try again."
    return ""

# Callback to handle currency switch
@dash_app.callback(
    [Output('base-currency', 'value'), Output('target-currency', 'value')],
    [Input('switch-arrow', 'n_clicks')],
    [State('base-currency', 'value'), State('target-currency', 'value')]
)
def switch_currency(n_clicks, base, target):
    if n_clicks:
        return target, base
    return base, target

# Callback to update financial news
@dash_app.callback(
    Output('financial-news', 'children'),
    Input('loading-4', 'children')
)
def update_financial_news(_):
    articles = fetch_financial_news()
    if articles:
        news_items = []
        for article in articles:
            news_items.append(
                html.Div([
                    html.A(article['title'], href=article['url'], target="_blank", style={"font-weight": "bold", "color": "black"}),
                    html.P(article['description'], style={"font-size": "12px", "color": "black"}),
                    html.Hr()
                ])
            )
        return news_items
    else:
        return html.P("No news available at the moment.", style={"color": "black"})

# Flask route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Simple email and password check (replace with a database or a more secure approach)
        if email == 'admin@example.com' and password == 'password':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))

    return render_template('login.html')

# Flask route for the dashboard redirect
@app.route('/dashboard')
def dashboard():
    return dash_app.index()

# Flask route for logging out
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Main route
@app.route('/')
def home():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


