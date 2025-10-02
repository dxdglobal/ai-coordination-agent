#!/usr/bin/env python3
"""
Minimal App Test - Check what's preventing startup
"""

print("🔍 Testing App Components...")

try:
    print("1. Testing Flask import...")
    from flask import Flask
    print("   ✅ Flask imported successfully")
except ImportError as e:
    print(f"   ❌ Flask import failed: {e}")

try:
    print("2. Testing Config import...")
    from config import Config
    print("   ✅ Config imported successfully")
except ImportError as e:
    print(f"   ❌ Config import failed: {e}")

try:
    print("3. Testing Models import...")
    from models.models import db
    print("   ✅ Models imported successfully")
except ImportError as e:
    print(f"   ❌ Models import failed: {e}")

try:
    print("4. Testing Routes import...")
    from routes.api import api_bp
    print("   ✅ API routes imported successfully")
except ImportError as e:
    print(f"   ❌ API routes import failed: {e}")

try:
    print("5. Testing AI Routes import...")
    from routes.ai import ai_bp
    print("   ✅ AI routes imported successfully")
except ImportError as e:
    print(f"   ❌ AI routes import failed: {e}")

print("\n6. Testing App Creation...")
try:
    app = Flask(__name__)
    app.config.from_object(Config)
    print("   ✅ Basic Flask app created successfully")
except Exception as e:
    print(f"   ❌ App creation failed: {e}")

print("\n✨ Component test complete!")