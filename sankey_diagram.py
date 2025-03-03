import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import webbrowser
from threading import Timer
import dash_bootstrap_components as dbc

# Load Data
file_path = "Cleaned_Package_Data_County.csv"  # Ensure this file is present in the working directory
df = pd.read_csv(file_path)

# Convert DateTime columns with explicit format
date_columns = ["Routed Date Time", "Stored Date Time", "Delivered Date Time"]
for col in date_columns:
    df[col] = pd.to_datetime(df[col], format="%m/%d/%Y %H:%M", errors='coerce')

# Drop rows with missing critical timestamps
df.dropna(subset=["Routed Date Time", "Delivered Date Time"], inplace=True)

# Compute Processing Stages
df['Routed → Stored'] = (df['Stored Date Time'] - df['Routed Date Time']).dt.total_seconds() / 3600
df['Stored → Delivered'] = (df['Delivered Date Time'] - df['Stored Date Time']).dt.total_seconds() / 3600
df['Total Processing Time'] = (df['Delivered Date Time'] - df['Routed Date Time']).dt.total_seconds() / 3600

# Ensure all values are properly handled
df.fillna(0, inplace=True)

# Initialize Dash App with a Modern Theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "🚀 Ultimate Package Analytics Dashboard"

# Layout
app.layout = dbc.Container([
    html.Div([
        html.H1("📦 Ultimate Package Tracking Dashboard 🚀", 
                style={'textAlign': 'center', 'color': '#FFD700', 'padding': '20px'}),
        html.Hr(),
    ], className="app-header"),
    
    dbc.Row([
        dbc.Col(html.Div([html.H4(f"📦 Total Packages: {len(df)}", 
                                  style={'color': '#FF4500', 'fontSize': '24px'})]), width=4),
        dbc.Col(html.Div([html.H4(f"🚚 Top Carrier: {df['Carrier'].mode()[0]}", 
                                  style={'color': '#32CD32', 'fontSize': '24px'})]), width=4),
        dbc.Col(html.Div([html.H4(f"⏳ Avg. Processing Time: {df['Total Processing Time'].mean():.2f} Hours", 
                                  style={'color': '#1E90FF', 'fontSize': '24px'})]), width=4)
    ], className="mb-4 text-center dashboard-stats"),
    
    dbc.Tabs([
        dbc.Tab(label='📦 Package Flow', children=[
            dbc.Card(
                dbc.CardBody([
                    html.H3("📊 Real-time Package Flow", className='card-title', style={'textAlign': 'center'}),
                    dcc.Graph(id='sankey-graph')
                ]),
                className="mt-3 shadow-lg"
            )
        ]),
        
        dbc.Tab(label='📈 Statistical Insights', children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H3("📊 Carrier Distribution", className='card-title', style={'textAlign': 'center'}),
                            dcc.Graph(id='carrier-bar')
                        ]),
                        className="mt-3 shadow-lg"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H3("📦 Package Processing Histogram", className='card-title', style={'textAlign': 'center'}),
                            dcc.Graph(id='histogram')
                        ]),
                        className="mt-3 shadow-lg"
                    )
                ], width=6)
            ])
        ]),
        
        dbc.Tab(label='📊 Additional Insights', children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H3("📊 Processing Time Over Time", className='card-title', style={'textAlign': 'center'}),
                            dcc.Graph(id='line-chart')
                        ]),
                        className="mt-3 shadow-lg"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H3("📦 Package Volume by Carrier", className='card-title', style={'textAlign': 'center'}),
                            dcc.Graph(id='pie-chart')
                        ]),
                        className="mt-3 shadow-lg"
                    )
                ], width=6)
            ])
        ]),
        
        dbc.Tab(label='🔥 Heatmap & Trends', children=[
            dbc.Card(
                dbc.CardBody([
                    html.H3("⏰ Package Pickup Heatmap", className='card-title', style={'textAlign': 'center'}),
                    dcc.Graph(id='heatmap')
                ]),
                className="mt-3 shadow-lg"
            )
        ])
    ])
], fluid=True, className="app-container")

# Callbacks
@app.callback(Output('sankey-graph', 'figure'), Input('sankey-graph', 'id'))
def update_sankey(_):
    sources = [0, 1, 1, 2, 2]
    targets = [1, 2, 3, 3, 4]
    values = [df['Routed → Stored'].mean(), df['Stored → Delivered'].mean(), 4000, 3200, 1200]
    labels = ["📦 Arrived", "📍 Sorting", "📦 Storage", "🚀 Out for Delivery", "🏡 Delivered"]
    
    fig = go.Figure(go.Sankey(
        node=dict(pad=15, thickness=40, line=dict(color="black", width=1), label=labels),
        link=dict(source=sources, target=targets, value=values)
    ))
    return fig

@app.callback(Output('carrier-bar', 'figure'), Input('carrier-bar', 'id'))
def update_carrier_bar(_):
    carrier_counts = df['Carrier'].value_counts().reset_index()
    carrier_counts.columns = ['Carrier', 'Count']
    fig = px.bar(carrier_counts, x='Carrier', y='Count', title="📊 Carrier Distribution", color='Carrier')
    return fig

@app.callback(Output('histogram', 'figure'), Input('histogram', 'id'))
def update_histogram(_):
    fig = px.histogram(df, x="Total Processing Time", nbins=50, title="⏳ Processing Time Distribution")
    return fig

@app.callback(Output('line-chart', 'figure'), Input('line-chart', 'id'))
def update_line_chart(_):
    df_sorted = df.dropna(subset=['Routed Date Time']).sort_values(by='Routed Date Time')
    fig = px.line(df_sorted, x="Routed Date Time", y="Total Processing Time", title="📊 Processing Time Over Time")
    return fig

@app.callback(Output('pie-chart', 'figure'), Input('pie-chart', 'id'))
def update_pie_chart(_):
    carrier_counts = df['Carrier'].value_counts().reset_index()
    carrier_counts.columns = ['Carrier', 'Count']
    fig = px.pie(carrier_counts, names='Carrier', values='Count', title="📦 Package Volume by Carrier")
    return fig

@app.callback(Output('heatmap', 'figure'), Input('heatmap', 'id'))
def update_heatmap(_):
    df['Hour of Day'] = df['Delivered Date Time'].dt.hour.fillna(0).astype(int)
    df['Day of Week'] = df['Delivered Date Time'].dt.day_name().fillna("Unknown")
    heatmap_data = df.groupby(['Day of Week', 'Hour of Day']).size().reset_index(name='Count')
    fig = px.density_heatmap(heatmap_data, x='Hour of Day', y='Day of Week', z='Count', title="🔥 Pickup Trends")
    return fig

# Auto-open browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server(debug=True)
