"""
Callbacks for the maintenance insights page.
This file should be imported and registered in main.py
"""

import pandas as pd
from dash import Dash, Input, Output
from typing import Any, Callable, cast


def register_insights_callbacks(app: Dash, get_data: Callable[[], pd.DataFrame]) -> None:
    """
    Register callbacks for the maintenance insights page.
    Call this function after creating the Dash app in main.py

    Args:
        app: Dash application
        get_data: Returns the current station data (refreshed by the "Actualiser" button)
    """
    
    @app.callback(
        Output('maintenance-table', 'data'),
        [
            Input('severity-filter', 'value'),
            Input('arrondissement-filter', 'value'),
            Input('problem-filter', 'value')
        ]
    )
    def update_maintenance_table(severity_val, zone_val, problem_val):
        """Filter the maintenance table based on dropdown selections."""
        # Import here to avoid circular imports
        from src.pages.insights import detect_maintenance_issues
        from src.utils.common_functions import filter_operational_stations
        
        # Re-create the filtered dataframe
        df_operational = filter_operational_stations(get_data())
        df_issues = detect_maintenance_issues(df_operational)
        df_issues = df_issues[df_issues['severity'].notna()].copy()
        
        if len(df_issues) == 0:
            return []
        
        # Sort by severity
        severity_order = {'CRITIQUE': 0, 'URGENT': 1}
        df_issues['severity_sort'] = df_issues['severity'].map(severity_order)
        df_issues = df_issues.sort_values('severity_sort').drop('severity_sort', axis=1)
        
        # Apply filters
        if severity_val != 'all':
            df_issues = df_issues[df_issues['severity'] == severity_val]
        
        if zone_val != 'all':
            df_issues = df_issues[df_issues['arrondissement'] == zone_val]
        
        if problem_val != 'all':
            df_issues = df_issues[df_issues['problem_type'] == problem_val]
        
        # Prepare data for table
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
        
        # Reorder columns sans 'Impact'
        table_data = table_data[['ID', 'Station', 'Probleme', 'Severite', 'Zone',
                                  'Velos', 'Places', 'Capacite', 'Statut']]
        
        return table_data.to_dict('records')