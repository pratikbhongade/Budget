import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

# Example data for initial budgets (could be fetched from a database or JSON)
def get_initial_budgets():
    return {
        'Housing': 1200,
        'Food': 500,
        'Transportation': 300,
        'Entertainment': 200,
        'Utilities': 400,
        'Other': 150
    }

# Function to calculate actual spending by category
def calculate_spending_by_category(transaction_data):
    spending_by_category = transaction_data[transaction_data['Transaction Type'] == 'Debit'].groupby('Category')['Amount'].sum()
    return spending_by_category.to_dict()

# Layout for budget setting input
def budget_setting_layout():
    initial_budgets = get_initial_budgets()
    return dbc.Card([
        dbc.CardBody([
            html.H5("Set Budget by Category", className="card-title", style={"color": "#2c3e50", "font-weight": "bold"}),
            *[
                dbc.Row([
                    dbc.Col(html.Label(f"{category} Budget:", style={"color": "#2c3e50"}), width=4),
                    dbc.Col(
                        dcc.Input(id=f'budget-{category}', value=initial_budgets[category], type='number', className="form-control", style={"color": "#34495e", "font-weight": "bold"}),
                        width=8
                    ),
                ], className="mb-2")
                for category in initial_budgets.keys()
            ],
            html.Button('Save Budgets', id='save-budgets-btn', className='btn btn-primary btn-block', style={"background-color": "#1abc9c", "border": "none"}),
        ])
    ], style={"box-shadow": "0 4px 8px rgba(0, 0, 0, 0.1)", "border-radius": "15px", "margin-top": "20px"})

# Function to track budget progress and generate alerts if needed
def track_budget_progress(spending_by_category, budgets):
    alerts = []
    progress_bars = []
    for category, budget in budgets.items():
        spent = spending_by_category.get(category, 0)
        progress = (spent / budget) * 100 if budget > 0 else 0
        
        # Ensure minimum progress visibility
        progress_display = max(progress, 1)
        
        color = "success" if progress < 80 else "warning" if progress < 100 else "danger"
        
        progress_bars.append(
            dbc.Progress(
                value=progress_display, color=color, className="mb-2", striped=True, animated=True,
                label=f"{category}: ${spent:.2f} / ${budget:.2f} ({progress:.1f}%)"
            )
        )

        if progress >= 100:
            alerts.append(dbc.Alert(f"Budget exceeded for {category}! You've spent ${spent:.2f} (Budget: ${budget:.2f})", color="danger"))

    return progress_bars, alerts

# Layout for budget progress tracking
def budget_progress_layout(transaction_data, income=5000):
    budgets = get_initial_budgets()
    spending_by_category = calculate_spending_by_category(transaction_data)
    progress_bars, alerts = track_budget_progress(spending_by_category, budgets)
    
    # Include both budget tracking and savings goals in this layout
    return dbc.Card([
        dbc.CardBody([
            html.H5("Budget Tracking", className="card-title", style={"color": "#2c3e50", "font-weight": "bold"}),
            *progress_bars,
            *alerts,
            html.Hr(),
            savings_goals_layout(income)  # Added the savings goals section here
        ])
    ], style={"box-shadow": "0 4px 8px rgba(0, 0, 0, 0.1)", "border-radius": "15px", "margin-top": "20px"})


# --- Savings Goals Section with Graph and Input Form ---

# Function to set initial savings goals (short-term and long-term)
def get_savings_goals():
    return {
        'Short Term': {'Vacation': 1000, 'Emergency Fund': 500},
        'Long Term': {'Home Purchase': 20000, 'Retirement': 50000}
    }

# Function to calculate savings progress based on allocated income
def calculate_savings_progress(income, allocated_percentages, savings_goals):
    savings_progress = {}
    for term, goals in savings_goals.items():
        savings_progress[term] = {}
        for goal, amount in goals.items():
            allocated_amount = (income * allocated_percentages.get(goal, 0)) / 100
            progress = (allocated_amount / amount) * 100
            savings_progress[term][goal] = {
                'allocated': allocated_amount,
                'goal': amount,
                'progress': progress
            }
    return savings_progress

# Layout for savings goals input and progress
def savings_goals_layout(income):
    savings_goals = get_savings_goals()

    # Define allocation percentages for savings goals
    allocated_percentages = {
        'Vacation': 10,  # Allocating 10% of income for vacation
        'Emergency Fund': 5,  # 5% for emergency fund
        'Home Purchase': 15,  # 15% for home purchase
        'Retirement': 20  # 20% for retirement
    }

    savings_progress = calculate_savings_progress(income, allocated_percentages, savings_goals)

    # Preparing data for the bar chart
    categories = []
    values = []
    for term, goals in savings_progress.items():
        for goal, data in goals.items():
            categories.append(f"{term}: {goal}")
            values.append(data['progress'])

    # Creating the bar chart using Plotly
    fig = go.Figure([go.Bar(x=categories, y=values, marker=dict(color='rgba(38, 166, 154, 0.8)'))])
    fig.update_layout(
        title="Savings Goals Progress",
        xaxis_title="Goals",
        yaxis_title="Progress (%)",
        template="plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=40)
    )

    # Create a section for users to set their own saving goals dynamically
    return dbc.Card([
        dbc.CardBody([
            html.H5("Set Savings Goals", className="card-title", style={"color": "#2c3e50", "font-weight": "bold"}),
            html.H6("Short Term Goals", className="card-subtitle mb-3", style={"color": "#2c3e50"}),
            *[
                dbc.Row([
                    dbc.Col(html.Label(f"{goal} Goal:", style={"color": "#2c3e50"}), width=4),
                    dbc.Col(
                        dcc.Input(id=f'short-term-{goal.lower().replace(" ", "-")}', value=savings_goals['Short Term'][goal], type='number', className="form-control", style={"color": "#34495e", "font-weight": "bold"}),
                        width=8
                    ),
                ], className="mb-2")
                for goal in savings_goals['Short Term']
            ],
            html.H6("Long Term Goals", className="card-subtitle mb-3", style={"color": "#2c3e50"}),
            *[
                dbc.Row([
                    dbc.Col(html.Label(f"{goal} Goal:", style={"color": "#2c3e50"}), width=4),
                    dbc.Col(
                        dcc.Input(id=f'long-term-{goal.lower().replace(" ", "-")}', value=savings_goals['Long Term'][goal], type='number', className="form-control", style={"color": "#34495e", "font-weight": "bold"}),
                        width=8
                    ),
                ], className="mb-2")
                for goal in savings_goals['Long Term']
            ],
            html.Button('Save Savings Goals', id='save-savings-goals-btn', className='btn btn-primary btn-block', style={"background-color": "#1abc9c", "border": "none"}),
            html.Hr(),
            dcc.Graph(figure=fig)
        ])
    ], style={"box-shadow": "0 4px 8px rgba(0, 0, 0, 0.1)", "border-radius": "15px", "margin-top": "20px"})
