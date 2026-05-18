from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)

DB = 'job_applications.db'

def init_database():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT, position TEXT, location TEXT,
        salary TEXT, status TEXT DEFAULT 'target',
        applied_date TEXT, notes TEXT, job_url TEXT,
        match_score INTEGER DEFAULT 80, requirements TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT status, COUNT(*) FROM applications GROUP BY status')
    counts = dict(c.fetchall())
    conn.close()
    applied = counts.get('applied', 0)
    interview = counts.get('interview', 0)
    offer = counts.get('offer', 0)
    rate = round((interview + offer) / applied * 100, 1) if applied > 0 else 0
    return jsonify({
        'total_targets': counts.get('target', 0),
        'total_applied': applied,
        'total_interviews': interview,
        'total_offers': offer,
        'response_rate': rate,
    })

@app.route('/api/move_application', methods=['POST'])
def move_application():
    data = request.json
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('UPDATE applications SET status=? WHERE id=?', (data['status'], data['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/applications')
def get_applications():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT * FROM applications ORDER BY match_score DESC')
    apps = c.fetchall()
    conn.close()
    
    applications = []
    for app in apps:
        applications.append({
            'id': app[0],
            'company': app[1],
            'position': app[2],
            'location': app[3] if len(app) > 3 else 'N/A',
            'salary': app[4] if len(app) > 4 else app[3],
            'status': app[5] if len(app) > 5 else app[4],
            'applied_date': app[6] if len(app) > 6 else app[5],
            'notes': app[7] if len(app) > 7 else app[6],
            'job_url': app[8] if len(app) > 8 else '#',
            'match_score': app[9] if len(app) > 9 else 85,
            'requirements': json.loads(app[10]) if len(app) > 10 and app[10] else []
        })
    
    return jsonify(applications)

@app.route('/api/add_application', methods=['POST'])
def add_application():
    data = request.json
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""INSERT INTO applications 
                 (company, position, location, salary, status, applied_date, notes, job_url, match_score, requirements) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (data.get('company', ''), 
               data.get('position', ''),
               data.get('location', ''),
               data.get('salary', ''), 
               data.get('status', 'target'),
               datetime.now().strftime('%Y-%m-%d'), 
               data.get('notes', ''),
               data.get('job_url', '#'),
               data.get('match_score', 80),
               json.dumps(data.get('requirements', []))))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_database()
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║  🚀 AI Job Hunting System - Zhu Yuting Edition          ║
    ║                                                        ║
    ║  🌐 Dashboard: http://localhost:5000                   ║
    ║  📱 Mobile: http://[your-ip]:5000                      ║
    ║  🤖 Database: 5 AI-matched jobs loaded                 ║
    ║  💰 Salary Range: $180k - $320k                       ║
    ╚════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)
