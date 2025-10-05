#!/usr/bin/env python3

import sys
import os
import importlib

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 CHECKING PROJECT DEPENDENCIES")
    print("=" * 50)
    
    required_packages = [
        'flask',
        'flask_cors', 
        'mysql.connector',
        'requests',
        'dotenv',
        'chromadb',
        'openai'
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            if package == 'mysql.connector':
                import mysql.connector
            elif package == 'flask_cors':
                import flask_cors
            elif package == 'dotenv':
                import dotenv
            else:
                importlib.import_module(package)
            
            installed_packages.append(package)
            print(f"   ✅ {package}")
            
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    print("\n📊 DEPENDENCY SUMMARY:")
    print(f"   ✅ Installed: {len(installed_packages)}")
    print(f"   ❌ Missing: {len(missing_packages)}")
    
    if missing_packages:
        print(f"\n⚠️  MISSING PACKAGES:")
        for pkg in missing_packages:
            print(f"      - {pkg}")
        print(f"\n💡 TO FIX: pip install {' '.join(missing_packages)}")
        return False
    
    print(f"\n🎉 ALL DEPENDENCIES INSTALLED!")
    return True

def check_environment():
    """Check environment configuration"""
    print("\n🔧 CHECKING ENVIRONMENT SETUP")
    print("=" * 50)
    
    env_file = '.env'
    env_example = '.env.example'
    
    if os.path.exists(env_file):
        print("   ✅ .env file exists")
        
        # Check for critical variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            db_password = os.getenv('DB_PASSWORD')
            if db_password:
                print("   ✅ DB_PASSWORD configured")
            else:
                print("   ⚠️  DB_PASSWORD not set")
                
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key != 'your_openai_api_key_here':
                print("   ✅ OPENAI_API_KEY configured")
            else:
                print("   ⚠️  OPENAI_API_KEY not set (optional for basic functionality)")
                
        except Exception as e:
            print(f"   ⚠️  Error reading .env: {e}")
    else:
        print("   ❌ .env file missing")
        if os.path.exists(env_example):
            print("   💡 Copy .env.example to .env and configure")
        return False
    
    return True

def check_database_connection():
    """Test database connectivity"""
    print("\n🗄️  TESTING DATABASE CONNECTION")
    print("=" * 50)
    
    try:
        import mysql.connector
        from dotenv import load_dotenv
        load_dotenv()
        
        connection = mysql.connector.connect(
            host='92.113.22.65',
            user='u906714182_sqlrrefdvdv',
            password=os.getenv('DB_PASSWORD', '3@6*t:lU'),
            database='u906714182_sqlrrefdvdv'
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result:
            print("   ✅ Database connection successful")
            cursor.close()
            connection.close()
            return True
            
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def check_app_startup():
    """Test if Flask app can start"""
    print("\n🚀 TESTING FLASK APP STARTUP")
    print("=" * 50)
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Try to import the main app
        from app import app
        print("   ✅ Flask app imports successfully")
        
        # Check if app can be configured
        app.config['TESTING'] = True
        print("   ✅ Flask app configuration works")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Flask app startup failed: {e}")
        return False

def main():
    """Run all checks"""
    print("🔍 AI COORDINATION AGENT - STARTUP READINESS CHECK")
    print("=" * 60)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Environment", check_environment), 
        ("Database", check_database_connection),
        ("Flask App", check_app_startup)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {name} check failed with error: {e}")
    
    print(f"\n📊 FINAL RESULTS:")
    print("=" * 60)
    print(f"   Passed: {passed}/{total} checks")
    
    if passed == total:
        print("\n🎉 PROJECT IS READY TO RUN!")
        print("💡 Execute: python app.py")
        print("🌐 Then visit: http://localhost:5000")
    else:
        print(f"\n⚠️  PROJECT NEEDS {total - passed} FIXES BEFORE RUNNING")
        print("💡 Review the failed checks above")
    
    return passed == total

if __name__ == "__main__":
    main()