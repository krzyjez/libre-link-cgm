import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional
from glucose_analyzer import analyze_high_glucose

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)
    GLUCOSE_THRESHOLD = config['glucose_threshold']

def process_csv_file(csv_path: str) -> Dict[str, List[dict]]:
    """Process CSV file and return measurements grouped by date"""
    measurements_by_date = {}
    
    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row with column names
        
        for row in reader:
            # Skip empty rows or rows without enough columns
            if not row or len(row) < 14:
                continue
                
            # Skip if timestamp column is empty or contains header
            if not row[2] or row[2] == 'Znacznik czasu w urządzeniu':
                continue
                
            try:
                timestamp_str = row[2]  # Column C contains timestamp
                timestamp = datetime.strptime(timestamp_str, '%d-%m-%Y %H:%M')
                date_str = timestamp.strftime('%Y-%m-%d')
                
                # Get glucose value and note
                glucose_value = float(row[4]) if row[4] else None
                note = row[13] if row[13] else None
                
                # Skip empty records (no glucose value and no note)
                if glucose_value is None and not note:
                    continue
                
                measurement = {
                    "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:00'),
                    "glucose_value": glucose_value,
                    "note": note
                }
                
                if date_str not in measurements_by_date:
                    measurements_by_date[date_str] = {
                        "date": date_str,
                        "measurements": [],
                        "high_glucose_periods": []
                    }
                
                measurements_by_date[date_str]["measurements"].append(measurement)
                
            except (ValueError, IndexError) as e:
                print(f"Error processing row: {e}")
                continue
    
    # Analyze high glucose periods for each day
    for date, data in measurements_by_date.items():
        if data["measurements"]:
            data["high_glucose_periods"] = analyze_high_glucose(data["measurements"], GLUCOSE_THRESHOLD)
    
    return measurements_by_date

def save_json_files(measurements_by_date: Dict[str, List[dict]], output_dir: str):
    """Save measurements to separate JSON files by date, only for days with measurements"""
    os.makedirs(output_dir, exist_ok=True)
    
    for date, data in measurements_by_date.items():
        # Save only if there are any measurements for this day
        if data["measurements"]:
            output_path = os.path.join(output_dir, f"{date}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
def process_csv_files():
    """Process all CSV files in the source directory"""
    source_dir = 'data/source'
    processed_dir = 'data/processed'
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # Process each CSV file
    for filename in os.listdir(source_dir):
        if filename.endswith('.csv'):
            print(f"Processing {filename}...")
            csv_path = os.path.join(source_dir, filename)
            measurements = process_csv_file(csv_path)
            save_json_files(measurements, processed_dir)

    # Generate HTML report
    from report_generator import generate_html_report
    generate_html_report(processed_dir, 'glucose_report.html')
    print("Generated HTML report: glucose_report.html")

def main():
    process_csv_files()

if __name__ == "__main__":
    main()
