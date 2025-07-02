import sqlite3

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
            status TEXT DEFAULT "draft",
            draft_description TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Initialise database immediately when imported
init_db()
