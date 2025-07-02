from flask import Flask
import os

# --------------------- APP CONFIGURATION ---------------------
app = Flask(__name__)
app.secret_key = 'secret'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --------------------- IMPORT AND INITIALISE MODULES ---------------------
import db_utils
import routes

routes.register_routes(app)

# --------------------- MAIN ---------------------
if __name__ == '__main__':
    app.run(debug=True)
