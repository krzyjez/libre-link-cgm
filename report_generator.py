import os
import json
from datetime import datetime
import plotly.graph_objects as go
from typing import List, Dict
from notes_manager import NotesManager

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)
    POINTS_MEDIUM = config['points_thresholds']['medium']
    POINTS_HIGH = config['points_thresholds']['high']

def get_severity_class(points: float) -> str:
    """Return Bootstrap class based on points severity"""
    if points >= POINTS_HIGH:
        return "bg-danger bg-opacity-25"  # Light red
    elif points >= POINTS_MEDIUM:
        return "bg-warning bg-opacity-25"  # Light yellow
    else:
        return "bg-success bg-opacity-25"  # Light green

def create_glucose_plot(data: dict) -> go.Figure:
    """Create a glucose plot for a single day"""
    # Regular glucose measurements
    timestamps = []
    glucose_values = []
    
    # Notes data
    note_timestamps = []
    note_texts = []
    
    # Prepare annotations for peaks
    annotations = []
    for period in data['high_glucose_periods']:
        # Find the highest glucose value in this period
        period_start = datetime.strptime(period['start_time'], '%Y-%m-%dT%H:%M:00')
        period_end = datetime.strptime(period['end_time'], '%Y-%m-%dT%H:%M:00')
        
        peak_value = 0
        peak_time = None
        
        for measurement in data['measurements']:
            m_time = datetime.strptime(measurement['timestamp'], '%Y-%m-%dT%H:%M:00')
            if period_start <= m_time <= period_end and measurement['glucose_value'] is not None:
                if measurement['glucose_value'] > peak_value:
                    peak_value = measurement['glucose_value']
                    peak_time = m_time
        
        if peak_time:
            annotations.append(dict(
                x=peak_time,
                y=peak_value,
                text=str(int(period['points'])),
                showarrow=True,
                arrowhead=0,
                yshift=10,
                font=dict(size=10, color='red'),
                arrowcolor='red',
                arrowsize=0.3,
                arrowwidth=1
            ))
    
    for measurement in data['measurements']:
        timestamp = datetime.strptime(measurement['timestamp'], '%Y-%m-%dT%H:%M:00')
        glucose = measurement['glucose_value']
        note = measurement['note']
        
        # Always add glucose measurement if exists
        if glucose is not None:
            timestamps.append(timestamp)
            glucose_values.append(glucose)
        
        # If there's a note, add to notes series
        if note:
            note_timestamps.append(timestamp)
            note_texts.append(note)
    
    # Calculate y-axis range
    if glucose_values:
        y_min = min(v for v in glucose_values if v is not None)
        y_max = max(v for v in glucose_values if v is not None)
        
        # Set default range [80, 180] unless data requires wider range
        y_range = [
            min(80, y_min) if y_min < 80 else 80,
            max(180, y_max + 20) if y_max > 180 else 180  # Added +20 for annotations
        ]
    else:
        y_range = [80, 180]  # Default range if no valid values
    
    fig = go.Figure()
    
    # Add main glucose line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=glucose_values,
        mode='lines+markers',
        name='Glucose',
        line=dict(color='blue'),
        marker=dict(size=8),
        hovertemplate='%{x}<br>Glucose: %{y}<extra></extra>'
    ))
    
    # Add notes markers
    if note_timestamps:
        # Calculate y-position for note markers (at the bottom of the plot)
        note_y = [y_range[0]] * len(note_timestamps)
        
        fig.add_trace(go.Scatter(
            x=note_timestamps,
            y=note_y,
            mode='markers',
            name='Notes',
            marker=dict(
                size=12,
                color='red',
                symbol='star-triangle-up'
            ),
            hovertemplate='%{x}<br>Note: %{text}<extra></extra>',
            text=note_texts
        ))
    
    # Add threshold line
    fig.add_hline(y=140, line_dash="dash", line_color="red")
    
    # Add baseline
    fig.add_hline(y=100, line_color="black")
    
    # Highlight high glucose periods
    for period in data['high_glucose_periods']:
        start = datetime.strptime(period['start_time'], '%Y-%m-%dT%H:%M:00')
        end = datetime.strptime(period['end_time'], '%Y-%m-%dT%H:%M:00')
        
        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor="red",
            opacity=0.1,
            layer="below",
            line_width=0,
        )
    
    # Add annotations for peaks
    for annotation in annotations:
        fig.add_annotation(annotation)
    
    # Update layout with fixed y-axis range
    fig.update_layout(
        title="",  # Removed title from plot
        xaxis=dict(
            title="",
            tickformat="%H:%M",
            type='date'
        ),
        yaxis=dict(
            title="",
            range=y_range
        ),
        height=300,
        margin=dict(l=50, r=50, t=20, b=50),  # Reduced top margin since we removed title
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig

def generate_notes_html(measurements: list) -> str:
    """Generate HTML for notes list"""
    notes_html = []
    for m in measurements:
        if m['note']:
            time = datetime.strptime(m['timestamp'], '%Y-%m-%dT%H:%M:00').strftime('%H:%M')
            notes_html.append(f'''
                <li>
                    <strong>{time}</strong>: <span class="note-text" id="note-text-{m['timestamp']}" 
                        onclick="toggleNoteEdit('{m['timestamp']}')">{m['note']}</span>
                    <div id="note-edit-{m['timestamp']}" class="note-edit">
                        <textarea id="note-textarea-{m['timestamp']}" class="form-control">{m['note']}</textarea>
                        <button class="btn btn-sm btn-primary" onclick="saveNote('{m['timestamp']}')">Zapisz</button>
                        <button class="btn btn-sm btn-secondary" onclick="toggleNoteEdit('{m['timestamp']}')">Anuluj</button>
                    </div>
                </li>
            ''')
    
    if not notes_html:
        return ""  # Return empty string if no notes
        
    return f'''
    <div class="card mt-3">
        <div class="card-body">
            <h6>Notatki:</h6>
            <ul class="mb-0">
                {"".join(notes_html)}
            </ul>
        </div>
    </div>
    '''

def generate_periods_html(periods: list) -> str:
    """Generate HTML for high glucose periods details"""
    if not periods:
        return "<p class='card-text'>Brak przekroczeń</p>"
    
    html = ["<ul class='list-unstyled mb-2'>"]
    for period in periods:
        start_time = datetime.strptime(period['start_time'], '%Y-%m-%dT%H:%M:00').strftime('%H:%M')
        html.append(
            f"<li>{start_time}: <strong>{int(period['points'])}</strong></li>"
        )
    html.append("</ul>")
    return "\n".join(html)

def has_valid_measurements(data: dict) -> bool:
    """Check if the day has any valid glucose measurements"""
    return any(m['glucose_value'] is not None for m in data['measurements'])

def generate_html_report(processed_data_dir: str, output_file: str):
    """Generate HTML report with all glucose plots"""
    # Initialize notes manager
    notes_manager = NotesManager()
    
    # Read all JSON files and sort by date (newest first)
    days_data = []
    for filename in os.listdir(processed_data_dir):
        if filename.endswith('.json') and filename != 'notes_override.json':
            with open(os.path.join(processed_data_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Apply note overrides
                data['measurements'] = notes_manager.apply_overrides(data['measurements'])
                if data['measurements']:  # Include all days with measurements
                    days_data.append(data)
    
    days_data.sort(key=lambda x: x['date'], reverse=True)
    
    # Generate plots and calculate statistics
    plots_html = []
    for data in days_data:
        fig = create_glucose_plot(data)
        
        # Calculate total points for the day
        total_points = sum(period['points'] for period in data['high_glucose_periods'])
        num_periods = len(data['high_glucose_periods'])
        
        # Get severity class for card background
        severity_class = get_severity_class(total_points)
        
        # Create HTML for this day's plot and stats
        plot_html = f'''
        <div class="row mb-5">
            <div class="col-12">
                <h4 class="bg-light p-3 mb-4 rounded">{data['date']}</h4>
            </div>
            <div class="col-md-9">
                {fig.to_html(full_html=False, include_plotlyjs=False)}
                {generate_notes_html(data['measurements'])}
            </div>
            <div class="col-md-3">
                <div class="card {severity_class}">
                    <div class="card-body">
                        <h5 class="card-title">Przekroczenia glukozy: {num_periods}</h5>
                        {generate_periods_html(data['high_glucose_periods'])}
                        <p class="card-text mt-2"><strong>Razem: {int(total_points)}</strong></p>
                    </div>
                </div>
            </div>
        </div>
        '''
        plots_html.append(plot_html)
    
    # Create full HTML document with interactive notes editing
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Raport analizy glukozy</title>
        <meta charset="utf-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <style>
            body {{ padding: 20px; }}
            .plotly-graph-div {{ width: 100% !important; }}
            .note-edit {{ display: none; padding: 10px; margin-top: 5px; }}
            .note-edit textarea {{ width: 100%; margin-bottom: 10px; }}
            .note-text {{ 
                cursor: pointer;
                padding: 2px 5px;
                border-radius: 3px;
            }}
            .note-text:hover {{
                background-color: #f8f9fa;
            }}
        </style>
        <script>
            function toggleNoteEdit(timestamp) {{
                const editDiv = document.getElementById(`note-edit-${{timestamp}}`);
                editDiv.style.display = editDiv.style.display === 'none' ? 'block' : 'none';
            }}
            
            function saveNote(timestamp) {{
                const note = document.getElementById(`note-textarea-${{timestamp}}`).value;
                fetch('/save_note', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ timestamp, note }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        document.getElementById(`note-text-${{timestamp}}`).textContent = note;
                        document.getElementById(`note-edit-${{timestamp}}`).style.display = 'none';
                    }}
                }});
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1 class="mb-4">Raport analizy glukozy</h1>
            <div class="plots-container">
                {"".join(plots_html)}
            </div>
        </div>
    </body>
    </html>
    '''
    
    # Save HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
