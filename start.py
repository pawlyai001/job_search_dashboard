#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Job Hunting Dashboard - Startup Script
Enhanced with ASCII art and better user experience
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def print_banner():
    """Print beautiful ASCII art banner"""
    banner = """
    
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  🚀 AI-POWERED JOB HUNTING COMMAND CENTER 🚀                        ║
║                                                                      ║
║  ████████╗███████╗ ██████╗██╗  ██╗    ██████╗ ██████╗  ██████╗      ║
║  ╚══██╔══╝██╔════╝██╔════╝██║  ██║    ██╔══██╗██╔══██╗██╔═══██╗     ║
║     ██║   █████╗  ██║     ███████║    ██████╔╝██████╔╝██║   ██║     ║
║     ██║   ██╔══╝  ██║     ██╔══██║    ██╔═══╝ ██╔══██╗██║   ██║     ║
║     ██║   ███████╗╚██████╗██║  ██║    ██║     ██║  ██║╚██████╔╝     ║
║     ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝      ║
║                                                                      ║
║           Autonomous Systems • Robotics • AI/ML Engineering          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

    🎯 Target: Senior/Staff Engineer @ Autonomous Vehicle Companies
    💰 Range: $175k - $280k (Based on your expertise)
    📍 Focus: Waymo, Tesla, Boston Dynamics, Aurora, Cruise
    
    ⚡ Features Loaded:
    • Real-time Kanban Job Pipeline
    • Multi-platform Job Search (Beyond LinkedIn!)
    • AI Resume Optimization
    • Automated Follow-up System
    • Telegram Mobile Notifications
    • PDF Export & Application Submission
    
    🤖 AI Agents Status:
    • Daily Job Search (9:00 AM) - ACTIVE 
    • Follow-up Manager (11:00 AM) - ACTIVE
    • Resume Optimizer (Monday 10:00 AM) - ACTIVE

"""
    
    print("\033[96m" + banner + "\033[0m")

def check_dependencies():
    """Check and install required dependencies"""
    print("🔧 Checking dependencies...")
    
    try:
        import flask
        import flask_socketio
        print("✅ Flask dependencies are ready")
    except ImportError:
        print("📦 Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")

def check_database():
    """Check database status"""
    from app import init_database
    init_database()

    conn = sqlite3.connect('./job_applications.db')
    cursor = conn.cursor()
    cursor.execute('SELECT status, COUNT(*) FROM applications GROUP BY status')
    status_counts = dict(cursor.fetchall())
    total = sum(status_counts.values())
    conn.close()

    print(f"📊 Database Status:")
    print(f"   • Total Applications: {total}")
    print(f"   • Targets: {status_counts.get('target', 0)}")
    print(f"   • Applied: {status_counts.get('applied', 0)}")
    print(f"   • Interviews: {status_counts.get('interview', 0)}")
    print(f"   • Offers: {status_counts.get('offer', 0)}")

def show_access_info():
    """Show access information"""
    print("\n🌐 ACCESS INFORMATION:")
    print("   • Local Access: http://localhost:5000")
    print("   • Network Access: http://[your-pc-ip]:5000")
    print("   • Mobile Access: Same WiFi network")
    print("\n📱 TELEGRAM NOTIFICATIONS:")
    print("   • Pairing Status: ✅ APPROVED (Michelle Zhu)")
    print("   • Daily Updates: 9:00 AM (job search)")
    print("   • Follow-ups: 11:00 AM (applications)")
    print("   • Resume Optimization: Monday 10:00 AM")

def main():
    """Main startup function"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print_banner()
    
    print("🚀 Starting AI Job Hunting Dashboard...")
    print(f"⏰ Startup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("👤 User: Zhu Yuting (Autonomous Systems Expert)")
    
    check_dependencies()
    check_database()
    show_access_info()
    
    print("\n" + "="*70)
    print("🎯 COMPETITIVE ADVANTAGES:")
    print("  • Proven autonomous vehicle deployment (30-vehicle fleet)")
    print("  • Quantified performance improvements (2.5x human efficiency)")
    print("  • Rare skill combination (ROS2 + ReactJS + PhD + Leadership)")
    print("  • International deployment experience (Singapore + US)")
    print("  • Research-to-production bridge (Licensed IP + Publications)")
    print("="*70)
    
    print("\n🚁 Launching dashboard server...")
    print("📊 Dashboard will open at: http://localhost:5000")
    print("\n🤖 Your AI agents are working 24/7 to find your next role!")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 70)
    
    # Start the Flask application
    try:
        from app import app, init_database
        init_database()
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped by user")
        print("💼 Your job search continues with scheduled AI agents!")
        print("📱 Telegram notifications remain active")
        print("\n✨ Thank you for using the AI Job Hunting System!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTroubleshooting tips:")
        print("  1. Check if port 5000 is available")
        print("  2. Verify Python dependencies")
        print("  3. Run: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
