#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Powered Job Hunting Dashboard
Real-time Flask web application with Kanban board and automation
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-job-hunting-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Database setup
DB_PATH = './job_database.db'

def init_database():
    """Initialize SQLite database with job application data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create applications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        position TEXT NOT NULL,
        status TEXT NOT NULL,
        salary_min INTEGER,
        salary_max INTEGER,
        location TEXT,
        applied_date DATE,
        interview_date DATE,
        notes TEXT,
        fit_score INTEGER,
        priority TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create resume versions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resume_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        version TEXT NOT NULL,
        company_target TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create AI agents status table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        last_run TIMESTAMP,
        next_run TIMESTAMP,
        results_count INTEGER DEFAULT 0,
        success_rate REAL DEFAULT 0.0
    )
    """)
    
    conn.commit()
    conn.close()

def seed_sample_data():
    """Add sample data for demonstration"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Sample applications
    sample_applications = [
        # Target Companies
        ('Amazon Robotics', 'Senior Software Engineer - Robotics', 'target', 180000, 220000, 'Seattle, WA', None, None, 'Perfect match for fleet management experience', 95, 'high'),
        ('NVIDIA', 'Staff Engineer - Autonomous Systems', 'target', 200000, 280000, 'Santa Clara, CA', None, None, 'GPU acceleration + ROS2 experience valuable', 88, 'high'),
        ('Uber ATG', 'Principal Engineer - Self-Driving', 'target', 190000, 260000, 'San Francisco, CA', None, None, 'Autonomous vehicle deployment experience', 92, 'high'),
        ('Rivian', 'Senior Robotics Engineer', 'target', 160000, 200000, 'Irvine, CA', None, None, 'Electric vehicle + autonomy intersection', 85, 'medium'),
        
        # Applied Companies  
        ('Waymo', 'Staff Software Engineer - Fleet Operations', 'applied', 190000, 250000, 'Mountain View, CA', '2024-12-15', None, 'Remote ops console experience highly relevant', 96, 'high'),
        ('Tesla', 'Senior Software Engineer - Autopilot', 'applied', 175000, 235000, 'Austin, TX', '2024-12-14', None, 'Production autonomous systems deployment', 90, 'high'),
        ('Cruise', 'Principal Engineer - Remote Operations', 'applied', 180000, 240000, 'San Francisco, CA', '2024-12-16', None, 'Direct match for remote ops background', 94, 'high'),
        ('Aurora', 'Staff Engineer - Autonomous Systems', 'applied', 200000, 280000, 'Pittsburgh, PA', '2024-12-13', None, 'Research + production experience valued', 91, 'high'),
        
        # Interview Stage
        ('Boston Dynamics', 'Senior Robotics Software Engineer', 'interview', 170000, 210000, 'Boston, MA', '2024-12-10', '2024-12-20', 'Technical interview tomorrow 2 PM!', 89, 'high'),
        ('Zoox', 'Staff Engineer - Fleet Management', 'interview', 185000, 245000, 'Foster City, CA', '2024-12-08', '2024-12-22', 'Final round - system design', 93, 'high'),
        
        # Offers
        ('Shopify', 'Staff Engineer - Logistics Robotics', 'offer', 165000, 165000, 'Remote/Toronto', '2024-12-05', '2024-12-12', 'OFFER: $165k + equity, decision due Monday', 87, 'medium')
    ]
    
    # Insert sample data if table is empty
    cursor.execute('SELECT COUNT(*) FROM applications')
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO applications (company, position, status, salary_min, salary_max, location, applied_date, interview_date, notes, fit_score, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_applications)
    
    # Sample AI agents
    sample_agents = [
        ('Daily Job Search', 'active', '2024-12-18 09:00:00', '2024-12-19 09:00:00', 156, 0.72),
        ('Follow-up Manager', 'active', '2024-12-18 11:00:00', '2024-12-19 11:00:00', 23, 0.85),
        ('Resume Optimizer', 'active', '2024-12-16 10:00:00', '2024-12-23 10:00:00', 8, 0.95)
    ]
    
    cursor.execute('SELECT COUNT(*) FROM ai_agents')
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO ai_agents (name, status, last_run, next_run, results_count, success_rate)
        VALUES (?, ?, ?, ?, ?, ?)
        """, sample_agents)
    
    conn.commit()
    conn.close()

@app.route('/')
def dashboard():
    """Main dashboard with Kanban board"""
    return render_template('dashboard.html')

@app.route('/api/applications')
def get_applications():
    """Get all applications grouped by status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, company, position, status, salary_min, salary_max, location, 
           applied_date, interview_date, notes, fit_score, priority
    FROM applications
    ORDER BY fit_score DESC, created_at DESC
    """)
    
    applications = cursor.fetchall()
    conn.close()
    
    # Group by status
    grouped = {'target': [], 'applied': [], 'interview': [], 'offer': []}
    
    for app in applications:
        app_data = {
            'id': app[0],
            'company': app[1],
            'position': app[2],
            'status': app[3],
            'salary_min': app[4],
            'salary_max': app[5],
            'location': app[6],
            'applied_date': app[7],
            'interview_date': app[8],
            'notes': app[9],
            'fit_score': app[10],
            'priority': app[11]
        }
        
        if app[3] in grouped:
            grouped[app[3]].append(app_data)
    
    return jsonify(grouped)

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Count applications by status
    cursor.execute('SELECT status, COUNT(*) FROM applications GROUP BY status')
    status_counts = dict(cursor.fetchall())
    
    # Calculate response rate (applied -> interview/offer)
    applied_count = status_counts.get('applied', 0)
    interview_count = status_counts.get('interview', 0) 
    offer_count = status_counts.get('offer', 0)
    
    response_rate = 0
    if applied_count > 0:
        response_rate = ((interview_count + offer_count) / applied_count) * 100
    
    # Average salary range
    cursor.execute('SELECT AVG(salary_min), AVG(salary_max) FROM applications WHERE salary_min IS NOT NULL')
    avg_salary = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        'total_targets': status_counts.get('target', 0),
        'total_applied': status_counts.get('applied', 0),
        'total_interviews': status_counts.get('interview', 0),
        'total_offers': status_counts.get('offer', 0),
        'response_rate': round(response_rate, 1),
        'avg_salary_min': int(avg_salary[0]) if avg_salary[0] else 0,
        'avg_salary_max': int(avg_salary[1]) if avg_salary[1] else 0
    })

@app.route('/api/agents')
def get_agents():
    """Get AI agents status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, status, last_run, next_run, results_count, success_rate FROM ai_agents')
    agents = cursor.fetchall()
    conn.close()
    
    agents_data = []
    for agent in agents:
        agents_data.append({
            'name': agent[0],
            'status': agent[1],
            'last_run': agent[2],
            'next_run': agent[3],
            'results_count': agent[4],
            'success_rate': agent[5]
        })
    
    return jsonify(agents_data)

@app.route('/api/move_application', methods=['POST'])
def move_application():
    """Move application to different status"""
    data = request.get_json()
    app_id = data.get('id')
    new_status = data.get('status')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE applications 
    SET status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (new_status, app_id))
    
    conn.commit()
    conn.close()
    
    # Emit update to all connected clients
    socketio.emit('application_moved', {'id': app_id, 'status': new_status})
    
    return jsonify({'success': True})

@app.route('/api/applications', methods=['POST'])
def add_application():
    """Add a new job application — called by Hermes agent"""
    data = request.get_json()

    required = ['company', 'position']
    if not all(data.get(f) for f in required):
        return jsonify({'success': False, 'error': 'company and position are required'}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO applications (company, position, status, salary_min, salary_max,
        location, applied_date, notes, fit_score, priority)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('company'),
        data.get('position'),
        data.get('status', 'target'),
        data.get('salary_min'),
        data.get('salary_max'),
        data.get('location'),
        data.get('applied_date'),
        data.get('notes'),
        data.get('fit_score', 0),
        data.get('priority', 'medium'),
    ))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    socketio.emit('application_added', {'id': new_id, **data})
    return jsonify({'success': True, 'id': new_id})


@app.route('/api/export_resume/<int:app_id>')
def export_resume(app_id):
    """Export customized resume for specific application"""
    # This would generate a PDF resume customized for the company
    # For now, return a placeholder
    return jsonify({
        'success': True,
        'message': f'Resume exported for application {app_id}',
        'filename': f'resume_application_{app_id}.pdf'
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('status', {'msg': 'Connected to AI Job Hunting Dashboard'})

def background_task():
    """Background task to simulate real-time updates"""
    while True:
        time.sleep(30)  # Update every 30 seconds
        socketio.emit('heartbeat', {'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Initialize database and sample data
    init_database()
    seed_sample_data()
    
    # Start background task
    thread = threading.Thread(target=background_task)
    thread.daemon = True
    thread.start()
    
    print("🚀 AI Job Hunting Dashboard Starting...")
    print("📊 Dashboard: http://localhost:5000")
    print("🎯 Ready to help you land your dream role!")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
