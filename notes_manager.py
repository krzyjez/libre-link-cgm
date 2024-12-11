import json
import os
from typing import Dict, Optional

class NotesManager:
    def __init__(self, data_dir: str = 'data/user'):
        self.data_dir = data_dir
        self.notes_file = os.path.join(data_dir, 'notes_override.json')
        self.notes: Dict[str, str] = {}
        # Upewnij się, że katalog istnieje
        os.makedirs(data_dir, exist_ok=True)
        self.load_notes()
    
    def load_notes(self):
        """Load notes from override file if it exists"""
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading {self.notes_file}, starting with empty notes")
                self.notes = {}
        else:
            self.notes = {}
    
    def save_notes(self):
        """Save notes to override file"""
        with open(self.notes_file, 'w', encoding='utf-8') as f:
            json.dump(self.notes, f, indent=2, ensure_ascii=False)
    
    def get_note(self, timestamp: str) -> Optional[str]:
        """Get note for timestamp, return None if not found"""
        return self.notes.get(timestamp)
    
    def set_note(self, timestamp: str, note: str):
        """Set or update note for timestamp"""
        self.notes[timestamp] = note
        self.save_notes()
    
    def delete_note(self, timestamp: str):
        """Delete note for timestamp if it exists"""
        if timestamp in self.notes:
            del self.notes[timestamp]
            self.save_notes()

    def apply_overrides(self, measurements: list) -> list:
        """Apply note overrides to measurements list"""
        for measurement in measurements:
            override = self.get_note(measurement['timestamp'])
            if override is not None:
                measurement['note'] = override
        return measurements
