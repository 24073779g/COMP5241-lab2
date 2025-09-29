from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add the parent directory to the path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_database_adapter

app = Flask(__name__)
CORS(app)

# Initialize database adapter
db = get_database_adapter()

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all notes"""
    try:
        notes = db.get_notes()
        return jsonify(notes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        note = db.create_note(data['title'].strip(), data['content'].strip())
        return jsonify(note), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note"""
    try:
        # Convert to int for file/postgres, keep as string for MongoDB
        if os.getenv('DATABASE_TYPE', 'file').lower() != 'mongodb':
            note_id = int(note_id)
            
        success = db.delete_note(note_id)
        
        if success:
            return jsonify({'message': 'Note deleted successfully'}), 200
        else:
            return jsonify({'error': 'Note not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a note"""
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        # Convert to int for file/postgres, keep as string for MongoDB
        if os.getenv('DATABASE_TYPE', 'file').lower() != 'mongodb':
            note_id = int(note_id)
            
        note = db.update_note(note_id, data['title'].strip(), data['content'].strip())
        
        if note:
            return jsonify(note), 200
        else:
            return jsonify({'error': 'Note not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Vercel expects a handler function
def handler(request):
    return app(request.environ, lambda status, headers: None)