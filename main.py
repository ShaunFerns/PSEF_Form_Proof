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
    draft = None
    conn = sqlite3.connect('psef.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM learner_access WHERE status = "draft" ORDER BY created_at DESC LIMIT 1')
    draft = c.fetchone()
    conn.close()

    if request.method == 'POST':
        action = request.form.get('action')
        programme_description = request.form.get('programme_description')

        pathways_qa_list = request.form.getlist('pathways_qa')
        pathways_qe_list = request.form.getlist('pathways_qe')
        internationalisation_qa_list = request.form.getlist('internationalisation_qa')
        internationalisation_qe_list = request.form.getlist('internationalisation_qe')

        evidence_files = []

        # QA upload handling
        qa_file_fields = {
            'qa_file_map_of_routes': 'Map of routes into programme',
            'qa_file_equitable_access': 'Equitable access with RPL',
            'qa_file_international_targets': 'International recruitment targets'
        }

        status = "draft" if action == "save" else "submitted"
        errors = []

        required_qa_labels = list(qa_file_fields.values())
        qa_uploaded_files = []

        for field, label in qa_file_fields.items():
            file = request.files.get(field)
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                evidence_files.append(filename)
                qa_uploaded_files.append(label)

        # Validate: All QA checkboxes ticked + files uploaded
        if status == "submitted":
            missing_qa = [label for label in required_qa_labels if label not in pathways_qa_list]
            if missing_qa:
                errors.append(f"All QA checkboxes must be checked before submission. Missing: {', '.join(missing_qa)}.")

            missing_files = [label for label in required_qa_labels if label not in qa_uploaded_files]
            if missing_files:
                errors.append(f"Evidence files are required for: {', '.join(missing_files)} before submission.")

        # QE upload handling (optional)
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
        for field in qe_file_fields:
            file = request.files.get(field)
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                evidence_files.append(filename)

        if errors:
            for e in errors:
                flash(e)
            return render_template('learner_access.html',
                                   programme_description=programme_description,
                                   pathways_qa_list=pathways_qa_list,
                                   pathways_qe_list=pathways_qe_list,
                                   internationalisation_qa_list=internationalisation_qa_list,
                                   internationalisation_qe_list=internationalisation_qe_list)

        # Insert or update draft
        conn = sqlite3.connect('psef.db')
        c = conn.cursor()
        if draft:
            c.execute('''
                UPDATE learner_access SET
                    programme_description = ?,
                    pathways_qa = ?,
                    pathways_qe = ?,
                    internationalisation_qa = ?,
                    internationalisation_qe = ?,
                    evidence_files = ?,
                    created_at = ?,
                    status = ?
                WHERE id = ?
            ''', (
                programme_description,
                ', '.join(pathways_qa_list),
                ', '.join(pathways_qe_list),
                ', '.join(internationalisation_qa_list),
                ', '.join(internationalisation_qe_list),
                '; '.join(evidence_files),
                datetime.now().isoformat(),
                status,
                draft['id']
            ))
        else:
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

    return render_template('learner_access.html',
                           programme_description=draft['programme_description'] if draft else '',
                           pathways_qa_list=draft['pathways_qa'].split(', ') if draft and draft['pathways_qa'] else [],
                           pathways_qe_list=draft['pathways_qe'].split(', ') if draft and draft['pathways_qe'] else [],
                           internationalisation_qa_list=draft['internationalisation_qa'].split(', ') if draft and draft['internationalisation_qa'] else [],
                           internationalisation_qe_list=draft['internationalisation_qe'].split(', ') if draft and draft['internationalisation_qe'] else [])

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

@app.route('/download_report/<int:entry_id>')
def download_report(entry_id):
    conn = sqlite3.connect('psef.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM learner_access WHERE id = ?', (entry_id,))
    entry = c.fetchone()
    conn.close()

    if not entry:
        return "Entry not found", 404

    evidence_files = entry['evidence_files'].split('; ') if entry['evidence_files'] else []

    rendered = render_template(
        'report_template.html',
        created_at=entry['created_at'],
        programme_name="",
        programme_description=entry['programme_description'],
        pathways_qa=entry['pathways_qa'],
        pathways_qe=entry['pathways_qe'],
        internationalisation_qa=entry['internationalisation_qa'],
        internationalisation_qe=entry['internationalisation_qe'],
        evidence_files=evidence_files,
        url_root=request.url_root
    )

    pdf = HTML(string=rendered).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=PSEF_Report_{entry_id}.pdf'

    return response

@app.route('/download_zip/<int:entry_id>')
def download_zip(entry_id):
    conn = sqlite3.connect('psef.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT evidence_files FROM learner_access WHERE id = ?', (entry_id,))
    entry = c.fetchone()
    conn.close()

    if not entry or not entry['evidence_files']:
        return "No evidence files found for this entry.", 404

    evidence_files = entry['evidence_files'].split('; ')

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for filename in evidence_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                zf.write(file_path, arcname=filename)

    zip_buffer.seek(0)

    return send_from_directory(
        directory='.',
        path=zip_buffer,
        as_attachment=True,
        download_name=f'PSEF_Evidence_Files_{entry_id}.zip'
    )

# --------------------- MAIN ---------------------
if __name__ == '__main__':
    app.run(debug=True)
