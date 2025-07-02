from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, make_response
import sqlite3
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from weasyprint import HTML
import zipfile
import io

app = Flask(__name__)
app.secret_key = 'secret'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --------------------- DB INITIALISATION ---------------------
def init_db():
    conn = sqlite3.connect('psef.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS learner_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            programme_description TEXT,
            pathways_qa TEXT,
            pathways_qe TEXT,
            internationalisation_qa TEXT,
            internationalisation_qe TEXT,
            evidence_files TEXT,
            created_at TEXT,
            status TEXT DEFAULT "draft"
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --------------------- Helpers ---------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------- ROUTES ---------------------

@app.route('/')
def index():
    return redirect(url_for('learner_access_form'))

@app.route('/learner-access', methods=['GET', 'POST'])
def learner_access_form():
    if request.method == 'POST':
        action = request.form.get('action')  # "save" or "submit"
        programme_description = request.form.get('programme_description')
        if len(programme_description.split()) > 500:
            flash('Programme description exceeds 500-word limit.')
            return redirect(url_for('learner_access_form'))

        # Collect QA evidence
        pathways_qa_list = []
        internationalisation_qa_list = []
        evidence_files = []

        qa_file_fields = {
            'qa_file_map_of_routes': 'Map of routes into programme',
            'qa_file_equitable_access': 'Equitable access with RPL',
            'qa_file_international_targets': 'International recruitment targets'
        }

        for field, label in qa_file_fields.items():
            file = request.files.get(field)
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                evidence_files.append(filename)
                if 'international_targets' in field:
                    internationalisation_qa_list.append(label)
                else:
                    pathways_qa_list.append(label)
            else:
                if request.form.get('pathways_qa') == label or request.form.get('internationalisation_qa') == label:
                    if 'international_targets' in field:
                        internationalisation_qa_list.append(label)
                    else:
                        pathways_qa_list.append(label)

        # Collect QE evidence
        pathways_qe_list = request.form.getlist('pathways_qe')
        internationalisation_qe_list = request.form.getlist('internationalisation_qe')

        qe_file_fields = {
            'qe_file_map_of_opportunities': 'Map of opportunities beyond programme',
            'qe_file_barrier_modules': 'Barrier modules reduced',
            'qe_file_collaboration_fe': 'Collaboration with FE partners',
            'qe_file_collaborative_development': 'Collaborative programme development',
            'qe_file_qualification_equivalency': 'Qualification equivalency applied',
            'qe_file_orientation': 'Orientation for international learners',
            'qe_file_supports': 'Supports: bridging, language, skills',
            'qe_file_culturally_inclusive': 'Culturally inclusive curriculum'
        }

        for field, label in qe_file_fields.items():
            file = request.files.get(field)
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                evidence_files.append(filename)

        # Validation for submission:
        status = "draft" if action == "save" else "submitted"

        if status == "submitted":
            if (('Map of routes into programme' in pathways_qa_list or
                 'Equitable access with RPL' in pathways_qa_list or
                 'International recruitment targets' in internationalisation_qa_list)
                and len(evidence_files) == 0):
                flash("You have selected QA evidence but have not uploaded any evidence files. Please upload files or save as draft.")
                return redirect(url_for('learner_access_form'))

        # Insert into DB
        conn = sqlite3.connect('psef.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO learner_access (
                programme_description,
                pathways_qa,
                pathways_qe,
                internationalisation_qa,
                internationalisation_qe,
                evidence_files,
                created_at,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            programme_description,
            ', '.join(pathways_qa_list),
            ', '.join(pathways_qe_list),
            ', '.join(internationalisation_qa_list),
            ', '.join(internationalisation_qe_list),
            '; '.join(evidence_files),
            datetime.now().isoformat(),
            status
        ))
        conn.commit()
        conn.close()

        return redirect(url_for('success'))

    return render_template('learner_access.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/success')
def success():
    return "<h2>Form processed successfully ✅</h2><p><a href='/learner-access'>Submit Another</a> | <a href='/dashboard'>View Dashboard</a></p>"

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('psef.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM learner_access ORDER BY created_at DESC')
    entries = c.fetchall()
    conn.close()
    return render_template('dashboard.html', entries=entries)

# --------------------- MAIN ---------------------
if __name__ == '__main__':
    app.run(debug=True)
