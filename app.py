from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

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
    c.execute('''CREATE TABLE IF NOT EXISTS resume (
        id INTEGER PRIMARY KEY, content TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER, section TEXT, original TEXT,
        suggested TEXT, reason TEXT, accepted INTEGER DEFAULT -1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
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

@app.route('/api/update_url', methods=['POST'])
def update_url():
    data = request.json
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('UPDATE applications SET job_url=? WHERE id=?', (data['job_url'], data['id']))
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

@app.route('/api/resume', methods=['GET'])
def get_resume():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT content FROM resume WHERE id = 1')
    row = c.fetchone()
    conn.close()
    return jsonify({'content': row[0] if row else ''})

@app.route('/api/resume', methods=['POST'])
def save_resume():
    content = request.json.get('content', '')
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO resume (id, content, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)', (content,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/suggest/<int:job_id>', methods=['POST'])
def suggest_changes(job_id):
    import anthropic, os
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT company, position, notes, requirements FROM applications WHERE id = ?', (job_id,))
    job = c.fetchone()
    c.execute('SELECT content FROM resume WHERE id = 1')
    resume_row = c.fetchone()
    conn.close()

    if not job:
        return jsonify({'error': 'Job not found'}), 404
    if not resume_row or not resume_row[0]:
        return jsonify({'error': 'No resume saved. Click "My Resume Template" to add your resume first.'}), 400

    company, position, notes, reqs_json = job
    requirements = json.loads(reqs_json) if reqs_json else []
    # Strip HTML tags so Claude receives clean plain text
    import re
    resume_content = re.sub(r'<[^>]+>', '', resume_row[0]).strip()

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'ANTHROPIC_API_KEY environment variable not set'}), 500

    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are a professional resume optimizer.

Role: {position} at {company}
Requirements:
{chr(10).join(f'- {r}' for r in requirements)}
Notes: {notes or 'N/A'}

Resume:
{resume_content}

Return a JSON array of specific resume edits. Each object must have:
- "section": which resume section to change (e.g. "Summary", "Skills", "Experience - Company Name")
- "original": exact current text to replace (empty string "" if it's a new addition)
- "suggested": the improved replacement text
- "reason": one sentence explaining why this helps for this specific role

Focus on high-impact changes only (3-6 suggestions). Return ONLY valid JSON, no markdown."""

    msg = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=2000,
        messages=[{'role': 'user', 'content': prompt}]
    )
    raw = msg.content[0].text.strip()
    if raw.startswith('```'):
        raw = raw.split('```')[1]
        if raw.startswith('json'): raw = raw[4:]
    suggestions = json.loads(raw.strip())

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('DELETE FROM suggestions WHERE job_id = ?', (job_id,))
    for s in suggestions:
        c.execute('INSERT INTO suggestions (job_id, section, original, suggested, reason) VALUES (?,?,?,?,?)',
                  (job_id, s['section'], s.get('original',''), s['suggested'], s['reason']))
    conn.commit()
    conn.close()

    return jsonify({'suggestions': suggestions})

@app.route('/api/suggestions/<int:job_id>', methods=['GET'])
def get_suggestions(job_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id, section, original, suggested, reason, accepted FROM suggestions WHERE job_id = ? ORDER BY id', (job_id,))
    rows = c.fetchall()
    conn.close()
    return jsonify([{'id': r[0], 'section': r[1], 'original': r[2], 'suggested': r[3], 'reason': r[4], 'accepted': r[5] == 1} for r in rows])

@app.route('/api/suggestions/<int:suggestion_id>/accept', methods=['POST'])
def accept_suggestion(suggestion_id):
    accepted = request.json.get('accepted', True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('UPDATE suggestions SET accepted = ? WHERE id = ?', (1 if accepted else 0, suggestion_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/resume/<int:job_id>')
def view_resume(job_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT company, position FROM applications WHERE id = ?', (job_id,))
    job = c.fetchone()
    c.execute('SELECT content FROM resume WHERE id = 1')
    resume_row = c.fetchone()
    c.execute('SELECT original, suggested FROM suggestions WHERE job_id = ? AND accepted = 1', (job_id,))
    accepted = c.fetchall()
    conn.close()

    if not resume_row or not resume_row[0]:
        return '<p style="font-family:sans-serif;padding:40px;">No resume saved yet. Go back and add your resume template first.</p>', 404

    import re
    html_content = resume_row[0]
    # Apply accepted suggestions on plain text then re-embed in HTML
    plain = re.sub(r'<[^>]+>', '', html_content).strip()
    for original, suggested in accepted:
        if original:
            plain = plain.replace(original, suggested)
        else:
            plain = suggested + '\n\n' + plain
    # Convert back to basic HTML paragraphs if suggestions were applied
    if accepted:
        content = ''.join(f'<p>{line}</p>' if line.strip() else '' for line in plain.split('\n'))
    else:
        content = html_content

    company = job[0] if job else ''
    position = job[1] if job else ''
    return render_template('resume.html', content=content, company=company, position=position)

@app.route('/api/compare', methods=['POST'])
def compare_jobs():
    ids = request.json.get('ids', [])
    if not ids:
        return jsonify({'jobs': []})
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(f'SELECT company, position, requirements FROM applications WHERE id IN ({",".join("?"*len(ids))})', ids)
    rows = c.fetchall()
    conn.close()
    jobs = [{'company': r[0], 'position': r[1], 'requirements': json.loads(r[2]) if r[2] else []} for r in rows]
    return jsonify({'jobs': jobs})


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
