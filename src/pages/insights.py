"""
Maintenance Operations Page - Dashboard for field maintenance crews.
Real-time actionable insights for maintaining the network efficiently.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable
import plotly.graph_objects as go
import pandas as pd
from typing import Any, cast

from src.utils.common_functions import filter_operational_stations


def detect_maintenance_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Detect stations requiring maintenance intervention."""
    df = df.copy()
    
    # CRITICAL: Empty stations
    df['is_critical_empty'] = (df['num_bikes_available'] == 0) & (df['is_renting'] == 1)
    
    # CRITICAL: Full stations
    df['is_critical_full'] = (df['num_docks_available'] == 0) & (df['is_returning'] == 1)
    
    # URGENT: Severe imbalance (>90%)
    total = df['num_bikes_available'] + df['num_docks_available']
    df['is_imbalanced'] = ((df['num_bikes_available'] / total > 0.9) | 
                           (df['num_docks_available'] / total > 0.9))
    
    # URGENT: No electric bikes
    df['no_ebikes'] = (df['ebikes'] == 0) & (df['capacity'] > 0)
    
    # Assign severity level
    def assign_severity(row):
        if row['is_critical_empty'] or row['is_critical_full']:
            return 'CRITIQUE'
        elif row['is_imbalanced'] or row['no_ebikes']:
            return 'URGENT'
        else:
            return None
    
    df['severity'] = df.apply(assign_severity, axis=1)
    
    # Determine problem type
    def get_problem_type(row):
        if row['is_critical_empty']:
            return 'Vide'
        elif row['is_critical_full']:
            return 'Pleine'
        elif row['is_imbalanced']:
            return 'Déséquilibrée'
        elif row['no_ebikes']:
            return 'Pas d\'e-bikes'
        else:
            return None
    
    df['problem_type'] = df.apply(get_problem_type, axis=1)
    
    # Calculate impact (Gardé uniquement pour le Hover de la carte si besoin)
    df['impact'] = df.apply(
        lambda row: row['num_docks_available'] if row['is_critical_full'] 
                    else row['num_bikes_available'] if row['is_critical_empty']
                    else 0,
        axis=1
    )
    
    # Estimate arrondissement
    df['arrondissement'] = df.apply(estimate_arrondissement, axis=1)
    
    return df


def estimate_arrondissement(row) -> str:
    """Estimate Paris arrondissement based on lat/lon."""
    lat, lon = row['lat'], row['lon']
    if lat >= 48.8585 and lat < 48.8652 and lon >= 2.3368 and lon < 2.3456: return '1er'
    elif lat >= 48.8596 and lat < 48.8683 and lon >= 2.3463 and lon < 2.3536: return '2e'
    elif lat >= 48.8625 and lat < 48.8741 and lon >= 2.3495 and lon < 2.3652: return '3e'
    elif lat >= 48.8458 and lat < 48.8595 and lon >= 2.3431 and lon < 2.3652: return '4e'
    elif lat >= 48.8356 and lat < 48.8506 and lon >= 2.3368 and lon < 2.3590: return '5e'
    elif lat >= 48.8356 and lat < 48.8488 and lon >= 2.3221 and lon < 2.3368: return '6e'
    elif lat >= 48.8324 and lat < 48.8575 and lon >= 2.2869 and lon < 2.3221: return '7e'
    elif lat >= 48.8644 and lat < 48.8838 and lon >= 2.2869 and lon < 2.3229: return '8e'
    elif lat >= 48.8709 and lat < 48.8833 and lon >= 2.3229 and lon < 2.3467: return '9e'
    elif lat >= 48.8709 and lat < 48.8864 and lon >= 2.3467 and lon < 2.3725: return '10e'
    elif lat >= 48.8507 and lat < 48.8704 and lon >= 2.3652 and lon < 2.3880: return '11e'
    elif lat >= 48.8270 and lat < 48.8507 and lon >= 2.3652 and lon < 2.4023: return '12e'
    elif lat >= 48.8130 and lat < 48.8356 and lon >= 2.3368 and lon < 2.3778: return '13e'
    elif lat >= 48.8230 and lat < 48.8379 and lon >= 2.3068 and lon < 2.3368: return '14e'
    elif lat >= 48.8230 and lat < 48.8500 and lon >= 2.2745 and lon < 2.3068: return '15e'
    elif lat >= 48.8445 and lat < 48.8644 and lon >= 2.2476 and lon < 2.2869: return '16e'
    elif lat >= 48.8838 and lat < 48.8970 and lon >= 2.2845 and lon < 2.3229: return '17e'
    elif lat >= 48.8838 and lat < 48.9044 and lon >= 2.3229 and lon < 2.3600: return '18e'
    elif lat >= 48.8801 and lat < 48.9044 and lon >= 2.3600 and lon < 2.3976: return '19e'
    elif lat >= 48.8507 and lat < 48.8801 and lon >= 2.3880 and lon < 2.4154: return '20e'
    else: return 'Autre/Banlieue'


def create_maintenance_kpi_cards(df: pd.DataFrame) -> dbc.Row:
    critical_count = len(df[df['severity'] == 'CRITIQUE'])
    urgent_count = len(df[df['severity'] == 'URGENT'])
    total_issues = critical_count + urgent_count
    total_stations = len(df)
    health_percent = (1 - total_issues / total_stations) * 100 if total_stations > 0 else 100
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H4("🔴 CRITIQUE", style={'color': '#DC2626', 'marginBottom': '8px', 'fontSize': '14px'}),
                        html.H2(f"{critical_count}", style={'color': '#DC2626', 'marginBottom': '0'})
                    ])
                ])
            ], style={'border': '2px solid #FCA5A5', 'borderRadius': '12px', 'backgroundColor': '#FEF2F2'})
        ], xs=4, className="mb-3"),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H4("🟠 URGENT", style={'color': '#EA580C', 'marginBottom': '8px', 'fontSize': '14px'}),
                        html.H2(f"{urgent_count}", style={'color': '#EA580C', 'marginBottom': '0'})
                    ])
                ])
            ], style={'border': '2px solid #FDBA74', 'borderRadius': '12px', 'backgroundColor': '#FFFBEB'})
        ], xs=4, className="mb-3"),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H4("✅ Sain", style={'color': '#16A34A', 'marginBottom': '8px', 'fontSize': '14px'}),
                        html.H2(f"{health_percent:.0f}%", style={'color': '#16A34A', 'marginBottom': '0'})
                    ])
                ])
            ], style={'border': '2px solid #86EFAC', 'borderRadius': '12px', 'backgroundColor': '#F0FDF4'})
        ], xs=4, className="mb-3"),
    ], style={'marginBottom': '32px'})


def create_maintenance_map(df: pd.DataFrame) -> dcc.Graph:
    df_issues = df[df['severity'].notna()].copy()
    
    if len(df_issues) == 0:
        fig = go.Figure(
            data=[],
            layout=go.Layout(
                map=dict(style='open-street-map', center=dict(lat=48.8566, lon=2.3522), zoom=11),
                title='<b>Aucun problème détecté ! 🎉</b>', height=500, margin=dict(l=0, r=0, b=0, t=40), font=dict(family='Inter')
            )
        )
        return dcc.Graph(figure=fig, config={'displayModeBar': False})
    
    severity_colors = {'CRITIQUE': '#DC2626', 'URGENT': '#F59E0B'}
    df_issues['color'] = df_issues['severity'].map(severity_colors)
    df_issues['size'] = df_issues['severity'].map({'CRITIQUE': 15, 'URGENT': 10})
    
    # Note : L'impact reste affiché sur la carte dans l'infobulle (Utile pour le terrain)
    df_issues['hover_text'] = df_issues.apply(
        lambda row: f"<b>{row['name']}</b><br>Problème: {row['problem_type']}<br>Sévérité: {row['severity']}<br>Impact: {row['impact']} unités<br>Zone: {row['arrondissement']}",
        axis=1
    )
    
    fig = go.Figure()
    for severity in ['CRITIQUE', 'URGENT']:
        df_severity = df_issues[df_issues['severity'] == severity]
        if len(df_severity) > 0:
            fig.add_trace(go.Scattermap(
                lat=df_severity['lat'], lon=df_severity['lon'], mode='markers',
                marker=dict(size=df_severity['size'], color=severity_colors[severity], opacity=0.8),
                text=df_severity['hover_text'], hovertemplate='%{text}<extra></extra>', name=severity
            ))
    
    fig.update_layout(
        map=dict(style='open-street-map', center=dict(lat=48.8566, lon=2.3522), zoom=11),
        height=500, margin=dict(l=0, r=0, b=0, t=40), hovermode='closest',
        title='<b>Carte de Maintenance - Stations à Intervenir</b>', font=dict(family='Inter'), title_x=0.5
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': True})


def create_maintenance_table(df: pd.DataFrame) -> html.Div:
    df_issues = df[df['severity'].notna()].copy()
    
    if len(df_issues) == 0:
        return html.Div([
            html.P("Aucune station à intervenir - réseau en bon état ! ✅", style={'textAlign': 'center', 'padding': '20px', 'color': '#16A34A'})
        ])
    
    severity_order = {'CRITIQUE': 0, 'URGENT': 1}
    df_issues['severity_sort'] = df_issues['severity'].map(severity_order)
    df_issues = df_issues.sort_values('severity_sort').drop('severity_sort', axis=1)
    
    table_data = df_issues[[
        'name', 'problem_type', 'severity', 'arrondissement', 
        'num_bikes_available', 'num_docks_available', 'capacity'
    ]].copy()
    
    table_data.columns = [
        'Station', 'Probleme', 'Severite', 'Zone',
        'Velos', 'Places', 'Capacite'
    ]
    
    table_data['ID'] = range(len(table_data))
    table_data['Statut'] = 'A FAIRE'
    
    # Nettoyage ici aussi : suppression de 'Impact'
    table_data = table_data[['ID', 'Station', 'Probleme', 'Severite', 'Zone', 
                             'Velos', 'Places', 'Capacite', 'Statut']]
    
    unique_zones = sorted([z for z in df_issues['arrondissement'].dropna().unique() if z != 'Unknown'])
    unique_problems = sorted(df_issues['problem_type'].dropna().unique().tolist())
    
    return html.Div([
        html.Div([
            html.H3("📋 Stations à Intervenir", style={'marginBottom': '16px', 'color': '#0F172A', 'fontSize': '18px', 'fontWeight': '600'}),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Sévérité:", style={'fontWeight': '600', 'marginBottom': '4px', 'fontSize': '13px'}),
                    dcc.Dropdown(
                        id='severity-filter',
                        options=[
                            {'label': 'Tous', 'value': 'all'},
                            {'label': '🔴 CRITIQUE', 'value': 'CRITIQUE'},
                            {'label': '🟠 URGENT', 'value': 'URGENT'}
                        ],
                        value='all',
                        clearable=False
                    )
                ], xs=12, sm=4, className="mb-3"),
                
                dbc.Col([
                    html.Label("Zone:", style={'fontWeight': '600', 'marginBottom': '4px', 'fontSize': '13px'}),
                    dcc.Dropdown(
                        id='arrondissement-filter',
                        options=[{'label': 'Tous', 'value': 'all'}] + 
                                [{'label': arr, 'value': arr} for arr in unique_zones],
                        value='all',
                        clearable=False
                    )
                ], xs=12, sm=4, className="mb-3"),
                
                dbc.Col([
                    html.Label("Type:", style={'fontWeight': '600', 'marginBottom': '4px', 'fontSize': '13px'}),
                    dcc.Dropdown(
                        id='problem-filter',
                        options=[{'label': 'Tous', 'value': 'all'}] +
                                [{'label': pt, 'value': pt} for pt in unique_problems],
                        value='all',
                        clearable=False
                    )
                ], xs=12, sm=4, className="mb-3"),
            ], style={'marginBottom': '20px'}),
            
            DataTable(
                id='maintenance-table',
                columns=[
                    {'name': col, 'id': col, 'editable': False} 
                    for col in table_data.columns
                ],
                data=cast(Any, table_data.to_dict('records')),
                style_cell={
                    'textAlign': 'left', 'padding': '12px', 'fontFamily': 'Inter', 'fontSize': '13px', 'borderBottom': '1px solid #E2E8F0'
                },
                style_header={
                    'backgroundColor': '#F1F5F9', 'fontWeight': '600', 'color': '#0F172A', 'borderBottom': '2px solid #CBD5E1', 'fontSize': '13px', 'padding': '12px'
                },
                style_data_conditional=cast(
                    Any,
                    [
                        {
                            'if': {'column_id': 'Severite', 'filter_query': "{Severite} = 'CRITIQUE'"},
                            'backgroundColor': '#FEF2F2', 'color': '#DC2626', 'fontWeight': '600'
                        },
                        {
                            'if': {'column_id': 'Severite', 'filter_query': "{Severite} = 'URGENT'"},
                            'backgroundColor': '#FFFBEB', 'color': '#EA580C', 'fontWeight': '600'
                        }
                    ]
                ),
                style_as_list_view=True,
                fixed_rows={'headers': True}
            )
        ], style={
            'padding': '24px', 'backgroundColor': 'white', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.1)', 'overflowX': 'auto'
        })
    ])


def create_maintenance_layout(df: pd.DataFrame) -> html.Div:
    df_operational = filter_operational_stations(df)
    df_maintenance = detect_maintenance_issues(df_operational)
    
    layout = html.Div([
        html.Div([
            html.Div([
                html.H1("🔧 Maintenance & Operations", style={'fontSize': '2rem', 'fontWeight': '700', 'color': '#0F172A', 'marginBottom': '8px'}),
                html.P("Dashboard temps réel pour les opérateurs de maintenance", style={'fontSize': '1rem', 'color': '#64748B', 'marginBottom': '0'})
            ], style={'marginBottom': '32px'}),
            
            create_maintenance_kpi_cards(df_maintenance),
            
            html.Div([
                html.H2("Localisation des Problèmes", style={'fontSize': '1.25rem', 'fontWeight': '700', 'color': '#0F172A', 'marginBottom': '16px'}),
                dbc.Card([
                    dbc.CardBody([create_maintenance_map(df_maintenance)])
                ], style={'border': '1px solid #E2E8F0', 'borderRadius': '12px', 'backgroundColor': 'white', 'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.1)', 'marginBottom': '32px', 'padding': '0'})
            ]),
            
            create_maintenance_table(df_maintenance)
        ], style={'padding': '32px', 'maxWidth': '1400px', 'margin': '0 auto'})
    ], style={'backgroundColor': '#F8FAFC', 'minHeight': '100vh', 'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'})
    
    return layout


if __name__ == "__main__":
    print("Maintenance operations page created successfully")