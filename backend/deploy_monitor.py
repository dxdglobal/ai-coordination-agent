#!/usr/bin/env python3
"""
Enhanced Task Monitor Service Launcher
=====================================
Simple deployment script to run the 24/7 task monitor
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing required dependencies...")
    required_packages = ['mysql-connector-python', 'schedule']
    
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def test_database_connection():
    """Test database connectivity"""
    print("🔍 Testing database connection...")
    try:
        import mysql.connector
        
        db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv',
            'password': '3@6*t:lU',
            'database': 'u906714182_sqlrrefdvdv'
        }
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tbltasks")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print(f"✅ Database connected successfully! Found {count} tasks")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_startup_batch():
    """Create a Windows batch file for easy startup"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable
    
    batch_content = f'''@echo off
title Enhanced Task Monitor - 24/7
echo Starting Enhanced Task Monitor...
cd /d "{current_dir}"
"{python_exe}" enhanced_task_monitor.py
pause
'''
    
    batch_file = os.path.join(current_dir, 'start_monitor.bat')
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print(f"✅ Created startup script: {batch_file}")
    return batch_file

def run_quick_test():
    """Run a quick test of the monitoring system"""
    print("🧪 Running quick test of the monitoring system...")
    
    try:
        from enhanced_task_monitor import EnhancedTaskMonitor
        
        # Initialize monitor
        monitor = EnhancedTaskMonitor()
        
        # Test getting tasks
        tasks = monitor.get_all_tasks_with_metrics()
        print(f"✅ Successfully retrieved {len(tasks)} tasks")
        
        # Test performance calculation
        monitor.update_employee_performance(tasks)
        print(f"✅ Performance analysis complete for {monitor.stats['employees_monitored']} employees")
        
        # Generate sample report
        report = monitor.generate_performance_report()
        print("📊 Sample Performance Report:")
        print("-" * 30)
        print(report[:500] + "..." if len(report) > 500 else report)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 ENHANCED TASK MONITOR DEPLOYMENT")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Exiting.")
        return False
    
    print()
    
    # Step 2: Test database connection
    if not test_database_connection():
        print("❌ Database connection test failed. Please check configuration.")
        return False
    
    print()
    
    # Step 3: Run quick test
    if not run_quick_test():
        print("❌ System test failed. Please check the logs.")
        return False
    
    print()
    
    # Step 4: Create startup script
    batch_file = create_startup_batch()
    
    print()
    print("🎉 DEPLOYMENT SUCCESSFUL!")
    print("=" * 50)
    print("Next steps:")
    print(f"1. Double-click '{batch_file}' to start the monitor")
    print("2. Or run: python enhanced_task_monitor.py")
    print("3. Monitor will run continuously, checking every 3 hours")
    print("4. Press Ctrl+C to stop the monitor")
    print("5. Check 'enhanced_task_monitor.log' for detailed logs")
    print()
    
    # Ask if user wants to start now
    start_now = input("🚀 Start the monitor now? (y/n): ").lower().strip()
    
    if start_now == 'y':
        print("🔄 Starting Enhanced Task Monitor...")
        try:
            from enhanced_task_monitor import EnhancedTaskMonitor
            monitor = EnhancedTaskMonitor()
            monitor.start_enhanced_24_7_monitoring()
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped by user")
        except Exception as e:
            print(f"❌ Error starting monitor: {e}")
    else:
        print("👋 Setup complete! Run the monitor when you're ready.")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Deployment interrupted by user")
    except Exception as e:
        print(f"❌ Deployment error: {e}")