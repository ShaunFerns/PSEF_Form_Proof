from flask import render_template, request, redirect, url_for, flash, send_from_directory, make_response
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from weasyprint import HTML
import os
import io
import zipfile
from utils import allowed_file

def register_routes(app):
    @app.route('/')
    def index():
        return redirect(url_for('section4'))

    @app.route('/learner-access', methods=['GET', 'POST'])
    def learner_access_form():
        draft_id = request.args.get('draft_id')
        draft = None
        if draft_id:
            conn = sqlite3.connect('psef.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT * FROM learner_access WHERE id = ? AND status = "draft"', (draft_id,))
            draft = c.fetchone()
            conn.close()
        else:
            conn = sqlite3.connect('psef.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT * FROM learner_access WHERE status = "draft" ORDER BY created_at DESC LIMIT 1')
            draft = c.fetchone()
            conn.close()

        if request.method == 'POST':
            action = request.form.get('action')
            programme_description = request.form.get('programme_description')
            draft_description = request.form.get('draft_description') if action == "save" else None

            pathways_qa_list = request.form.getlist('pathways_qa')
            pathways_qe_list = request.form.getlist('pathways_qe')
            internationalisation_qa_list = request.form.getlist('internationalisation_qa')
            internationalisation_qe_list = request.form.getlist('internationalisation_qe')

            evidence_files = []

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

            if status == "submitted":
                missing_qa = [label for label in required_qa_labels if label not in pathways_qa_list]
                if missing_qa:
                    errors.append(f"All QA checkboxes must be checked. Missing: {', '.join(missing_qa)}.")
                missing_files = [label for label in required_qa_labels if label not in qa_uploaded_files]
                if missing_files:
                    errors.append(f"Evidence files required for: {', '.join(missing_files)} before submission.")

            qe_file_fields = {
                'qe_file_map_of_opportunities': '',
                'qe_file_barrier_modules': '',
                'qe_file_collaboration_fe': '',
                'qe_file_collaborative_development': '',
                'qe_file_qualification_equivalency': '',
                'qe_file_orientation': '',
                'qe_file_supports': '',
                'qe_file_culturally_inclusive': ''
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
                                       internationalisation_qe_list=internationalisation_qe_list,
                                       draft_description=draft_description or '')

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
                        status = ?,
                        draft_description = ?
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
                    draft_description,
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
                        status,
                        draft_description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    programme_description,
                    ', '.join(pathways_qa_list),
                    ', '.join(pathways_qe_list),
                    ', '.join(internationalisation_qa_list),
                    ', '.join(internationalisation_qe_list),
                    '; '.join(evidence_files),
                    datetime.now().isoformat(),
                    status,
                    draft_description
                ))
            conn.commit()
            conn.close()

            return redirect(url_for('success'))

        return render_template('learner_access.html',
                               programme_description=draft['programme_description'] if draft else '',
                               pathways_qa_list=draft['pathways_qa'].split(', ') if draft and draft['pathways_qa'] else [],
                               pathways_qe_list=draft['pathways_qe'].split(', ') if draft and draft['pathways_qe'] else [],
                               internationalisation_qa_list=draft['internationalisation_qa'].split(', ') if draft and draft['internationalisation_qa'] else [],
                               internationalisation_qe_list=draft['internationalisation_qe'].split(', ') if draft and draft['internationalisation_qe'] else [],
                               draft_description=draft['draft_description'] if draft and draft['draft_description'] else '')

    @app.route('/drafts')
    def drafts():
        conn = sqlite3.connect('psef.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM learner_access WHERE status = "draft" ORDER BY created_at DESC')
        drafts = c.fetchall()
        conn.close()
        return render_template('drafts.html', drafts=drafts)

    @app.route('/edit_draft/<int:draft_id>')
    def edit_draft(draft_id):
        return redirect(url_for('learner_access_form', draft_id=draft_id))

    @app.route('/delete_draft/<int:draft_id>', methods=['POST'])
    def delete_draft(draft_id):
        conn = sqlite3.connect('psef.db')
        c = conn.cursor()
        c.execute('DELETE FROM learner_access WHERE id = ? AND status = "draft"', (draft_id,))
        conn.commit()
        conn.close()
        flash("Draft deleted successfully.")
        return redirect(url_for('drafts'))

    @app.route('/success')
    def success():
        return "<h2>Form processed successfully ✅</h2><p><a href='/learner-access'>Submit Another</a> | <a href='/dashboard'>View Dashboard</a> | <a href='/drafts'>View Drafts</a></p>"

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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

    @app.route('/section4')
    def section4():
        return render_template('section4.html')

    @app.route('/section4/1')
    def section4_1():
        return render_template('section4_1.html')

    @app.route('/section4/2')
    def section4_2():
        return render_template('section4_2.html')

    @app.route('/section4/3')
    def section4_3():
        return render_template('section4_3.html')

    @app.route('/section4/4')
    def section4_4():
        return render_template('section4_4.html')

    @app.route('/section4/5')
    def section4_5():
        return render_template('section4_5.html')

