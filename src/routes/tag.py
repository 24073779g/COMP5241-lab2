from flask import Blueprint, jsonify, request
from src.models.tag import Tag
from src.lib.supabase_client import supabase

tag_bp = Blueprint('tag', __name__)

@tag_bp.route('/tags', methods=['GET'])
def get_tags():
    """Get all tags"""
    try:
        response = supabase.table('tags').select('*').order('name').execute()
        tags = [Tag.from_dict(tag) for tag in response.data]
        return jsonify([tag.to_dict() for tag in tags])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tag_bp.route('/tags', methods=['POST'])
def create_tag():
    """Create a new tag"""
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
        
        tag_data = {
            'name': data['name'],
            'color': data.get('color', '#6B73FF')
        }
        
        response = supabase.table('tags').insert(tag_data).execute()
        if response.data:
            tag = Tag.from_dict(response.data[0])
            return jsonify(tag.to_dict()), 201
        return jsonify({'error': 'Failed to create tag'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tag_bp.route('/tags/<tag_id>', methods=['PUT'])
def update_tag(tag_id):
    """Update a specific tag"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'color' in data:
            update_data['color'] = data['color']
        
        response = supabase.table('tags').update(update_data).eq('id', tag_id).execute()
        if not response.data:
            return jsonify({'error': 'Tag not found'}), 404
        
        tag = Tag.from_dict(response.data[0])
        return jsonify(tag.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tag_bp.route('/tags/<tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """Delete a specific tag"""
    try:
        response = supabase.table('tags').delete().eq('id', tag_id).execute()
        if not response.data:
            return jsonify({'error': 'Tag not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tag_bp.route('/notes/<note_id>/tags', methods=['POST'])
def add_tag_to_note(note_id):
    """Add a tag to a note"""
    try:
        data = request.json
        if not data or 'tag_id' not in data:
            return jsonify({'error': 'Tag ID is required'}), 400
        
        tag_id = data['tag_id']
        
        # Check if note exists
        note = supabase.table('notes').select('*').eq('id', note_id).execute()
        if not note.data:
            return jsonify({'error': 'Note not found'}), 404
        
        # Check if tag exists
        tag = supabase.table('tags').select('*').eq('id', tag_id).execute()
        if not tag.data:
            return jsonify({'error': 'Tag not found'}), 404
        
        # Add the relationship
        response = supabase.table('note_tags').insert({
            'note_id': note_id,
            'tag_id': tag_id
        }).execute()
        
        if response.data:
            return jsonify({'message': 'Tag added to note successfully'}), 201
        return jsonify({'error': 'Failed to add tag to note'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tag_bp.route('/notes/<note_id>/tags/<tag_id>', methods=['DELETE'])
def remove_tag_from_note(note_id, tag_id):
    """Remove a tag from a note"""
    try:
        response = supabase.table('note_tags').delete().eq('note_id', note_id).eq('tag_id', tag_id).execute()
        if not response.data:
            return jsonify({'error': 'Tag not found on note'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500