import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from db.user import db
from routes.user import user_bp
from routes.note import note_bp
from db.note import Note
from dotenv import load_dotenv

app = Flask(__name__, pages_folder=os.path.join(os.path.dirname(__file__), 'pages'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

CORS(app)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(note_bp, url_prefix='/api')

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(ROOT_DIR, 'database', 'app.db')

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

load_dotenv()
POSTGRES_URL = os.getenv("supabaseURL")
POSTGRES_KEY = os.getenv("supabaseKey")

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    pages_folder_path = app.pages_folder
    if pages_folder_path is None:
            return "Pages folder not configured", 404

    if path != "" and os.path.exists(os.path.join(pages_folder_path, path)):
        return send_from_directory(pages_folder_path, path)
    else:
        index_path = os.path.join(pages_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(pages_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/src/')
def home():
    return 'Welcome to Vercel!'

def handler(environ, start_response):
    return app(environ, start_response)

if __name__ == '__main__':
    with app.app_context():
        from sqlalchemy import inspect, text
        conn = db.engine.connect()
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('note')]
        if 'order' not in columns:
            conn.execute(text('ALTER TABLE note ADD COLUMN "order" INTEGER DEFAULT 0'))
        conn.close()
    app.run(host='0.0.0.0', port=5001, debug=True)
