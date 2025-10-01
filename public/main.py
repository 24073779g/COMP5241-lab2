import os
from flask import Flask
from flask_cors import CORS
from db.user import db
from routes.user import user_bp
from routes.note import note_bp
from dotenv import load_dotenv
from flask import send_from_directory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

CORS(app)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(note_bp, url_prefix='/api')

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()


# Add this route handler
@app.route('/')
def serve_index():
    return send_from_directory('pages', 'index.html')

# Keep this for Vercel
application = app

# Vercel serverless function handler
application = app

# Local development
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)