from flask import Flask, request, jsonify, send_file
from notes_manager import NotesManager
import os

app = Flask(__name__)
notes_manager = NotesManager()

@app.route('/')
def home():
    return send_file('glucose_report.html')

@app.route('/save_note', methods=['POST'])
def save_note():
    data = request.json
    timestamp = data.get('timestamp')
    note = data.get('note')
    
    if timestamp and note:
        notes_manager.set_note(timestamp, note)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Missing data'})

if __name__ == '__main__':
    print("Uruchamiam serwer na http://localhost:5000")
    print("Naciśnij Ctrl+C aby zatrzymać")
    app.run(debug=True)
