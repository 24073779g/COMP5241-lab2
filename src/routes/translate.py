from flask import Blueprint, request, jsonify
import os
import json
import httpx
from src.lib.supabase_client import supabase
from dotenv import load_dotenv

translate_bp = Blueprint('translate', __name__)

# Environment configuration
# Load environment variables from .env file if present
load_dotenv()

TRANSLATE_URL = os.getenv('TRANSLATE_URL', 'https://libretranslate.de')
TRANSLATE_API_KEY = os.getenv('TRANSLATE_API_KEY')  # optional
USE_GITHUB_MODELS = os.getenv('USE_GITHUB_MODELS', 'false').lower() in ('1', 'true', 'yes')
GITHUB_MODELS_ENDPOINT = os.getenv('GITHUB_MODELS_ENDPOINT', 'https://models.github.ai/inference/chat/completions')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
def call_translate_api(text: str, target: str, source: str | None = None) -> dict:
    """Call the configured translation service and return a dict with translated text.

    Uses LibreTranslate-compatible API by default. Environment variables:
      TRANSLATE_URL - base URL (default: https://libretranslate.de)
      TRANSLATE_API_KEY - optional API key
    """
    payload = {
        'q': text,
        'target': target,
        'format': 'text'
    }
    if source:
        payload['source'] = source
    if TRANSLATE_API_KEY:
        payload['api_key'] = TRANSLATE_API_KEY

    # If configured to use GitHub Models (or token provided and env requests it), use that API
    if USE_GITHUB_MODELS or GITHUB_TOKEN:
        # Build a chat-completions style payload compatible with the GitHub Models endpoint
        gh_payload = {
            'model': 'openai/gpt-4o-mini',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a professional translator. Translate the given text into the target language provided. Only return the translated text.'
                },
                {
                    'role': 'user',
                    'content': f'Translate the following text to {target}: {text}'
                }
            ],
            'temperature': 0.2
        }

        headers = {
            'Authorization': f'Bearer {GITHUB_TOKEN}' if GITHUB_TOKEN else '',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(GITHUB_MODELS_ENDPOINT, json=gh_payload, headers=headers, follow_redirects=True)
                resp.raise_for_status()
                data = resp.json()
                # Expecting GitHub Models response in chat/completions format
                # Try common shapes: {'choices': [{'message': {'content': '...'}}]} or {'choices': [{'text': '...'}]}
                if isinstance(data, dict) and 'choices' in data and len(data['choices']) > 0:
                    choice = data['choices'][0]
                    if isinstance(choice, dict):
                        if 'message' in choice and isinstance(choice['message'], dict) and 'content' in choice['message']:
                            return {'translatedText': choice['message']['content'].strip()}
                        if 'text' in choice:
                            return {'translatedText': choice['text'].strip()}
                # Fallback: return entire response as text
                return {'translatedText': json.dumps(data)}
        except httpx.HTTPStatusError as e:
            msg = f"HTTP error: {str(e)}"
            if e.response is not None:
                try:
                    msg += f" - {e.response.text}"
                except Exception:
                    pass
            return {'error': msg}
        except Exception as e:
            return {'error': str(e)}

    # Fallback: use LibreTranslate-compatible API
    url = TRANSLATE_URL.rstrip('/') + '/translate'
    try:
        headers = {'Accept': 'application/json'}
        with httpx.Client(timeout=15.0) as client:
            # follow_redirects=True ensures POST redirects (301) are followed
            resp = client.post(url, data=payload, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            # Try parsing JSON response first
            try:
                data = resp.json()
            except Exception:
                # Fallback: return raw text
                return {'translatedText': resp.text}
            # LibreTranslate returns {'translatedText': '...'}
            if isinstance(data, dict) and 'translatedText' in data:
                return {'translatedText': data['translatedText']}
            # Some providers may return text directly
            if isinstance(data, str):
                return {'translatedText': data}
            return {'translatedText': data}
    except httpx.HTTPStatusError as e:
        # Include response body when available
        msg = f"HTTP error: {str(e)}"
        if e.response is not None:
            try:
                msg += f" - {e.response.text}"
            except Exception:
                pass
        return {'error': msg}
    except Exception as e:
        return {'error': str(e)}


@translate_bp.route('/translate', methods=['POST'])
def translate_text():
    """Translate arbitrary text.

    Request JSON: { "text": "...", "target": "en", "source": "auto" (optional) }
    Response JSON: { "translatedText": "..." }
    """
    try:
        data = request.json or {}
        text = data.get('text')
        target = data.get('target')
        source = data.get('source')

        if not text or not target:
            return jsonify({'error': 'Both "text" and "target" are required'}), 400

        result = call_translate_api(text, target, source)
        if 'error' in result:
            return jsonify({'error': result['error']}), 502
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@translate_bp.route('/notes/<note_id>/translate', methods=['POST'])
def translate_note(note_id):
    """Translate the content of a note by ID and return translated text.

    Request JSON: { "target": "en", "source": "auto" (optional) }
    Response JSON: { "id": note_id, "original": "...", "translatedText": "..." }
    """
    try:
        data = request.json or {}
        target = data.get('target')
        source = data.get('source')

        if not target:
            return jsonify({'error': 'Target language is required'}), 400

        # Fetch the note
        resp = supabase.from_('notes').select('*').eq('id', note_id).execute()
        if not resp.data:
            return jsonify({'error': 'Note not found'}), 404

        note = resp.data[0]
        text = note.get('content', '')

        result = call_translate_api(text, target, source)
        if 'error' in result:
            return jsonify({'error': result['error']}), 502

        return jsonify({'id': note_id, 'original': text, 'translatedText': result.get('translatedText')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
