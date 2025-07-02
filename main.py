from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret'  # For flashing messages

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
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --------------------- ROUTES ---------------------

@app.route('/')
def index():
    return redirect(url_for('learner_access_form'))

# ---------- Learner Access Form ----------
@app.route('/learner-access', methods=['GET', 'POST'])
def learner_access_form():
    if request.method == 'POST':
        programme_description = request.form.get('programme_description')

        # Enforce 500-word limit server-side
        if len(programme_description.split()) > 500:
            flash('Programme description exceeds 500-word limit.')
            return redirect(url_for('learner_access_form'))

        pathways_qa = ', '.join(request.form.getlist('pathways_qa'))
        pathways_qe = ', '.join(request.form.getlist('pathways_qe'))
        internationalisation_qa = ', '.join(request.form.getlist('internationalisation_qa'))
        internationalisation_qe = ', '.join(request.form.getlist('internationalisation_qe'))

        conn = sqlite3.connect('psef.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO learner_access (
                programme_description,
                pathways_qa,
                pathways_qe,
                internationalisation_qa,
                internationalisation_qe,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            programme_description,
            pathways_qa,
            pathways_qe,
            internationalisation_qa,
            internationalisation_qe,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

        return redirect(url_for('success'))

    return render_template('learner_access.html')

# ---------- Success Page ----------
@app.route('/success')
def success():
    return "<h2>Form submitted successfully ✅</h2><p><a href='/learner-access'>Back to form</a> | <a href='/dashboard'>View Dashboard</a></p>"

# ---------- Dashboard ----------
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

