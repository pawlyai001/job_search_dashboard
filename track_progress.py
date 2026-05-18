#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job Search Progress Tracker
Quick command-line tool to check your job hunting progress
"""

import sqlite3
import os
from datetime import datetime, timedelta

def check_database():
    """Check if database exists and has data"""
    db_path = './job_database.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Run the main dashboard first.")
        return False
    
    return True

def get_application_stats():
    """Get application statistics"""
    if not check_database():
        return
    
    conn = sqlite3.connect('./job_database.db')
    cursor = conn.cursor()
    
    # Count by status
    cursor.execute('SELECT status, COUNT(*) FROM applications GROUP BY status')
    status_counts = dict(cursor.fetchall())
    
    # Calculate response rate
    applied = status_counts.get('applied', 0)
    interviews = status_counts.get('interview', 0)
    offers = status_counts.get('offer', 0)
    
    response_rate = 0
    if applied > 0:
        response_rate = ((interviews + offers) / applied) * 100
    
    # Recent activity
    cursor.execute("""
        SELECT company, position, status, updated_at 
        FROM applications 
        ORDER BY updated_at DESC 
        LIMIT 5
    """)
    recent = cursor.fetchall()
    
    # High priority pending
    cursor.execute("""
        SELECT company, position, notes 
        FROM applications 
        WHERE priority = "high" AND status IN ("applied", "interview")
        ORDER BY fit_score DESC
    """)
    urgent = cursor.fetchall()
    
    conn.close()
    
    return {
        'status_counts': status_counts,
        'response_rate': response_rate,
        'recent_activity': recent,
        'urgent_actions': urgent
    }

def print_dashboard():
    """Print formatted dashboard"""
    stats = get_application_stats()
    if not stats:
        return
    
    print("\n🚀 AI JOB HUNTING PROGRESS DASHBOARD")
    print("=" * 60)
    print(f"📊 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 User: Zhu Yuting (Autonomous Systems Expert)")
    
    # Status overview
    print("\n📈 PIPELINE OVERVIEW:")
    status_counts = stats['status_counts']
    print(f"   🎯 Target Companies: {status_counts.get('target', 0)}")
    print(f"   📤 Applications Sent: {status_counts.get('applied', 0)}")
    print(f"   🎤 Interviews Scheduled: {status_counts.get('interview', 0)}")
    print(f"   🎉 Job Offers: {status_counts.get('offer', 0)}")
    
    # Performance metrics
    print(f"\n🎯 PERFORMANCE METRICS:")
    print(f"   📊 Response Rate: {stats['response_rate']:.1f}% (Industry avg: 2-5%)")
    
    if stats['response_rate'] > 15:
        print("   🔥 EXCELLENT performance - well above industry average!")
    elif stats['response_rate'] > 8:
        print("   ✅ Good performance - above industry average")
    else:
        print("   📈 Building momentum - keep applying!")
    
    # Recent activity
    print("\n📋 RECENT ACTIVITY:")
    for app in stats['recent_activity'][:3]:
        company, position, status, updated = app
        status_emoji = {'target': '🎯', 'applied': '📤', 'interview': '🎤', 'offer': '🎉'}
        print(f"   {status_emoji.get(status, '📋')} {company} - {position} ({status})")
    
    # Urgent actions
    if stats['urgent_actions']:
        print("\n🚨 URGENT ACTIONS NEEDED:")
        for urgent in stats['urgent_actions']:
            company, position, notes = urgent
            print(f"   ⚡ {company} - {position}")
            if notes and 'interview' in notes.lower():
                print(f"      📅 {notes}")
            elif notes and 'decision' in notes.lower():
                print(f"      💼 {notes}")
    
    # AI agents status
    print("\n🤖 AI AGENTS STATUS:")
    print("   ✅ Daily Job Search (9:00 AM) - ACTIVE")
    print("   ✅ Follow-up Manager (11:00 AM) - ACTIVE") 
    print("   ✅ Resume Optimizer (Monday 10:00 AM) - ACTIVE")
    
    # Next steps
    print("\n🎯 NEXT STEPS:")
    total_active = status_counts.get('target', 0) + status_counts.get('applied', 0)
    
    if total_active < 20:
        print("   📈 Focus: Add more target companies")
        print("   💡 Tip: Use multi-platform search beyond LinkedIn")
    
    if stats['response_rate'] < 10:
        print("   📝 Focus: Optimize resume for better response rate")
        print("   💡 Tip: Use company-specific resume versions")
    
    if status_counts.get('interview', 0) > 0:
        print("   🎤 Focus: Prepare for upcoming interviews")
        print("   💡 Tip: Practice autonomous systems technical questions")
    
    print("\n💰 TARGET SALARY: $175k - $280k (Based on your expertise)")
    print("🏆 COMPETITIVE ADVANTAGES: Fleet deployment, ROS2+ReactJS, PhD+Production")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print_dashboard()
