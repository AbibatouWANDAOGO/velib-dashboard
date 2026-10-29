"""
Map page of the dashboard.
Displays stations on an interactive map with geolocation.
"""

import unicodedata

from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.utils.common_functions import filter_operational_stations
from config import DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, LOW_AVAILABILITY_THRESHOLD

# État d'une station, du plus critique au plus confortable pour l'usager
STATUS_COLORS = {
    'Vide': '#dc2626',
    'Pleine': '#2563eb',
    'Presque vide': '#f59e0b',
    'Disponible': '#16a34a',
}


def station_status(df: pd.DataFrame) -> pd.Series:
    """
    Compute the user-facing status of each station.

    Args:
        df: DataFrame with num_bikes_available and num_docks_available columns

    Returns:
        Series of status labels (keys of STATUS_COLORS)
    """
    status = pd.Series('Disponible', index=df.index)
    status[df['num_bikes_available'] <= LOW_AVAILABILITY_THRESHOLD] = 'Presque vide'
    status[df['num_docks_available'] == 0] = 'Pleine'
    status[df['num_bikes_available'] == 0] = 'Vide'
    return status


def strip_accents(text: str) -> str:
    """
    Remove accents from a text (é -> e, â -> a).

    Args:
        text: Text to normalize

    Returns:
        Text without diacritics
    """
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def create_kpi_card(value_id: str, label: str, color: str) -> dbc.Col:
    """
    Create a small KPI card whose value is filled by a callback.

    Args:
        value_id: Id of the component holding the value
        label: Text displayed under the value
        color: Accent color of the value

    Returns:
        Dash Bootstrap column containing the card
    """
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.H3(id=value_id, className="mb-0", style={'color': color, 'fontWeight': 700}),
                html.Small(label, className="text-muted"),
            ]),
            className="text-center shadow-sm h-100",
        ),
        xs=6, md=3, className="mb-3",
    )


def create_map_layout(df: pd.DataFrame) -> html.Div:
    """
    Create the map page layout.

    Args:
        df: DataFrame with station data

    Returns:
        Dash HTML Div component
    """
    layout = html.Div([
        html.H2("Carte des Stations Vélib'", className="text-center mb-4"),

        # Key figures for the stations currently displayed
        dbc.Row([
            create_kpi_card('kpi-stations', 'stations affichées', '#0f172a'),
            create_kpi_card('kpi-bikes', 'vélos disponibles', '#16a34a'),
            create_kpi_card('kpi-ebikes', 'dont électriques', '#2563eb'),
            create_kpi_card('kpi-docks', 'places libres', '#7c3aed'),
        ]),

        # Map controls
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Rechercher une station", className="fw-semibold"),
                        # debounce: search runs on Enter (or when leaving the field), not on every key
                        dcc.Input(
                            id='map-station-search',
                            type='search',
                            placeholder="Ex. Châtelet, Opéra… puis Entrée",
                            debounce=True,
                            className="form-control"
                        ),
                        html.Small(id='map-search-result', className="text-muted")
                    ], xs=12, md=4, className="mb-2"),
                    dbc.Col([
                        html.Label("Afficher", className="fw-semibold"),
                        dcc.Dropdown(
                            id='map-display-dropdown',
                            options=[
                                {'label': 'Toutes les stations', 'value': 'all'},
                                {'label': 'Stations avec vélos disponibles', 'value': 'available'},
                                {'label': 'Stations avec vélos électriques', 'value': 'ebike'},
                                {'label': 'Stations vides ou presque vides', 'value': 'low'},
                                {'label': 'Stations pleines (aucune place libre)', 'value': 'full'}
                            ],
                            value='all',
                            clearable=False
                        )
                    ], xs=12, md=4, className="mb-2"),
                    dbc.Col([
                        html.Label("Colorer selon", className="fw-semibold"),
                        dcc.Dropdown(
                            id='color-by-radio',
                            options=[
                                {'label': 'État de la station', 'value': 'status'},
                                {'label': 'Vélos disponibles', 'value': 'availability'},
                                {'label': 'Places libres', 'value': 'docks'},
                                {'label': "Taux d'occupation", 'value': 'occupancy'},
                                {'label': 'Part de vélos électriques', 'value': 'bike_type'}
                            ],
                            value='status',
                            clearable=False
                        )
                    ], xs=12, md=4, className="mb-2"),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Label("Taille des marqueurs :", className="fw-semibold me-2"),
                        dcc.RadioItems(
                            id='marker-size-radio',
                            options=[
                                {'label': 'Petit', 'value': 'small'},
                                {'label': 'Moyen', 'value': 'medium'},
                                {'label': 'Grand', 'value': 'large'}
                            ],
                            value='medium',
                            inline=True,
                            inputClassName="me-1",
                            labelClassName="me-3"
                        )
                    ], className="d-flex align-items-center flex-wrap"),
                ]),
            ])
        ], className="mb-4 shadow-sm"),

        # Map
        dbc.Card([
            dbc.CardBody([
                dcc.Loading(
                    id="loading-map",
                    type="default",
                    children=dcc.Graph(
                        id='station-map',
                        style={'height': '72vh'},
                        config={'scrollZoom': True, 'displaylogo': False}
                    )
                )
            ])
        ], className="shadow-sm"),

        # Store the data
        dcc.Store(id='map-data', data=df.to_dict('records'))
    ])

    return layout


def find_stations(df: pd.DataFrame, query: str | None) -> pd.DataFrame:
    """
    Find stations whose name contains the query, ignoring accents and case
    (so "Châtelet" finds "Place du Chatelet").

    Args:
        df: Station data
        query: Text typed by the user

    Returns:
        Matching stations, names starting with the query first
    """
    needle = strip_accents(query or '').lower().strip()
    if not needle:
        return df.iloc[0:0]
    names = df['name'].astype(str).map(lambda n: strip_accents(n).lower())
    matches = df[names.str.contains(needle, regex=False)].copy()
    matches['_starts'] = names[matches.index].str.startswith(needle)
    return matches.sort_values(['_starts', 'name'], ascending=[False, True]).drop(columns='_starts')


@callback(
    [Output('station-map', 'figure'),
     Output('kpi-stations', 'children'),
     Output('kpi-bikes', 'children'),
     Output('kpi-ebikes', 'children'),
     Output('kpi-docks', 'children'),
     Output('map-search-result', 'children')],
    [Input('map-display-dropdown', 'value'),
     Input('marker-size-radio', 'value'),
     Input('color-by-radio', 'value'),
     Input('map-station-search', 'value'),
     Input('map-data', 'data')]
)
def update_map(
    display_filter: str,
    marker_size: str,
    color_by: str,
    search_query: str | None,
    data: list
) -> tuple:
    """
    Update the map and the key figures based on filters.

    Args:
        display_filter: Filter for which stations to display
        marker_size: Size of map markers
        color_by: How to color the markers
        search_query: Station name typed in the search box (or None)
        data: Station data

    Returns:
        Plotly scatter_map figure, the four KPI values and the search result message
    """
    df = pd.DataFrame(data)
    df_filtered = filter_operational_stations(df)
    df_filtered['status'] = station_status(df_filtered)

    # Apply display filter
    if display_filter == 'available':
        df_filtered = df_filtered[df_filtered['num_bikes_available'] > 0]
    elif display_filter == 'ebike':
        df_filtered = df_filtered[df_filtered['ebikes'] > 0]
    elif display_filter == 'low':
        df_filtered = df_filtered[df_filtered['num_bikes_available'] <= LOW_AVAILABILITY_THRESHOLD]
    elif display_filter == 'full':
        df_filtered = df_filtered[df_filtered['num_docks_available'] == 0]

    # Set marker size
    size_map = {'small': 8, 'medium': 12, 'large': 16}
    marker_size_value = size_map.get(marker_size, 12)

    # Occupancy rate (0 when capacity is unknown)
    df_filtered = df_filtered.copy()
    capacity = df_filtered['capacity'].where(df_filtered['capacity'] > 0)
    df_filtered['occupancy_pct'] = (df_filtered['num_bikes_available'] / capacity * 100).fillna(0).round(1)

    # Create hover text (FRANÇAIS uniquement)
    df_filtered['hover_text'] = (
        '<b>' + df_filtered['name'] + '</b><br>' +
        'État : ' + df_filtered['status'] + '<br>' +
        'Vélos disponibles : ' + df_filtered['num_bikes_available'].astype(int).astype(str) +
        ' (' + df_filtered['mechanical_bikes'].astype(int).astype(str) + ' mécaniques, ' +
        df_filtered['ebikes'].astype(int).astype(str) + ' électriques)<br>' +
        'Places libres : ' + df_filtered['num_docks_available'].astype(int).astype(str) +
        ' / ' + df_filtered['capacity'].astype(int).astype(str) + '<br>' +
        'Taux d\'occupation : ' + df_filtered['occupancy_pct'].astype(str) + ' %'
    )

    # Center on the searched station, otherwise on Paris
    center = {'lat': DEFAULT_MAP_CENTER[0], 'lon': DEFAULT_MAP_CENTER[1]}
    zoom = DEFAULT_MAP_ZOOM
    matches = find_stations(df, search_query)
    selected = matches.head(1)
    if not (search_query or '').strip():
        search_message = ""
    elif len(matches) == 0:
        search_message = f"Aucune station ne correspond à « {search_query.strip()} »."
    elif len(matches) == 1:
        search_message = f"→ {selected['name'].iloc[0]}"
    else:
        search_message = (f"→ {selected['name'].iloc[0]} ({len(matches)} stations correspondent, "
                          f"précisez pour en choisir une autre)")
    if len(selected) > 0:
        center = {'lat': float(selected['lat'].iloc[0]), 'lon': float(selected['lon'].iloc[0])}
        zoom = 15

    common = dict(
        lat='lat',
        lon='lon',
        size='capacity',
        custom_data=['hover_text'],
        size_max=marker_size_value,
        zoom=zoom,
        center=center,
        map_style='carto-voyager',
    )
    if color_by == 'status':
        fig = px.scatter_map(
            df_filtered,
            color='status',
            color_discrete_map=STATUS_COLORS,
            category_orders={'status': list(STATUS_COLORS)},
            **common
        )
    else:
        color_column, color_scale, color_label = {
            'occupancy': ('occupancy_pct', 'RdYlGn', 'Taux d\'occupation (%)'),
            'availability': ('num_bikes_available', 'RdYlGn', 'Vélos disponibles'),
            'docks': ('num_docks_available', 'RdYlGn', 'Places libres'),
            'bike_type': ('ebike_percentage', 'Viridis', '% vélos électriques'),
        }[color_by]
        fig = px.scatter_map(
            df_filtered,
            color=color_column,
            color_continuous_scale=color_scale,
            labels={color_column: color_label},
            **common
        )

    # Utiliser SEULEMENT le hover_text personnalisé (pas de doublon)
    fig.update_traces(hovertemplate='%{customdata[0]}<extra></extra>')

    # Highlight the searched station
    if len(selected) > 0:
        fig.add_trace(go.Scattermap(
            lat=selected['lat'], lon=selected['lon'], mode='markers+text',
            marker=dict(size=26, color='rgba(15, 23, 42, 0.35)'),
            text=selected['name'], textposition='top center',
            textfont=dict(size=14, color='#0f172a'),
            hoverinfo='skip', showlegend=False
        ))

    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(title='État', orientation='h', yanchor='bottom', y=0.01, xanchor='left', x=0.01,
                    bgcolor='rgba(255,255,255,0.85)'),
        coloraxis_colorbar=dict(thickness=15, len=0.7),
        # Keep the user's zoom when filters change, but recenter on a new search
        uirevision=str(selected['station_id'].iloc[0]) if len(selected) > 0 else 'paris',
    )

    def fmt(value: float) -> str:
        return f"{int(value):,}".replace(',', ' ')

    return (
        fig,
        fmt(len(df_filtered)),
        fmt(df_filtered['num_bikes_available'].sum()),
        fmt(df_filtered['ebikes'].sum()),
        fmt(df_filtered['num_docks_available'].sum()),
        search_message,
    )


if __name__ == "__main__":
    print("Map page layout created successfully")
