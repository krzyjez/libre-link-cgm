from datetime import datetime
from typing import List, Dict

def analyze_high_glucose(measurements: list, glucose_threshold: float) -> list:
    """Analyze periods of high glucose and calculate their severity"""
    high_periods = []
    current_period = None
    
    # Sort measurements by timestamp
    sorted_measurements = sorted(measurements, key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%dT%H:%M:00'))
    
    for i, measurement in enumerate(sorted_measurements):
        if measurement['glucose_value'] is None:
            continue
            
        is_high = measurement['glucose_value'] > glucose_threshold
        current_time = datetime.strptime(measurement['timestamp'], '%Y-%m-%dT%H:%M:00')
        
        if is_high:
            if current_period is None:
                # Start new period
                current_period = {
                    'start_time': current_time.strftime('%Y-%m-%dT%H:%M:00'),
                    'start_value': measurement['glucose_value'],
                    'measurements': [measurement],
                    'points': 0
                }
            else:
                # Continue current period
                current_period['measurements'].append(measurement)
        
        elif current_period is not None:
            # End current period
            current_period['end_time'] = current_time.strftime('%Y-%m-%dT%H:%M:00')
            current_period['end_value'] = sorted_measurements[i-1]['glucose_value']
            
            # Calculate points for the period
            points = 0
            for j in range(len(current_period['measurements'])):
                current_value = current_period['measurements'][j]['glucose_value']
                current_time = datetime.strptime(current_period['measurements'][j]['timestamp'], '%Y-%m-%dT%H:%M:00')
                
                # For the last measurement in period
                if j == len(current_period['measurements']) - 1:
                    next_time = datetime.strptime(measurement['timestamp'], '%Y-%m-%dT%H:%M:00')
                else:
                    next_time = datetime.strptime(current_period['measurements'][j+1]['timestamp'], '%Y-%m-%dT%H:%M:00')
                
                # Calculate minutes until next measurement
                duration_minutes = (next_time - current_time).total_seconds() / 60
                # Calculate points: excess glucose * duration
                points += (current_value - glucose_threshold) * duration_minutes
            
            current_period['points'] = round(points, 2)
            high_periods.append(current_period)
            current_period = None
    
    # Handle case where period extends to the end of the day
    if current_period is not None:
        current_period['end_time'] = current_time.strftime('%Y-%m-%dT%H:%M:00')
        current_period['end_value'] = measurement['glucose_value']
        
        # Calculate points for the last period
        points = 0
        for j in range(len(current_period['measurements'])):
            current_value = current_period['measurements'][j]['glucose_value']
            current_time = datetime.strptime(current_period['measurements'][j]['timestamp'], '%Y-%m-%dT%H:%M:00')
            
            if j < len(current_period['measurements']) - 1:
                next_time = datetime.strptime(current_period['measurements'][j+1]['timestamp'], '%Y-%m-%dT%H:%M:00')
                duration_minutes = (next_time - current_time).total_seconds() / 60
                points += (current_value - glucose_threshold) * duration_minutes
        
        current_period['points'] = round(points, 2)
        high_periods.append(current_period)
    
    return high_periods
