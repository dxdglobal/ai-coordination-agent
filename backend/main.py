#!/usr/bin/env python3
"""
AI Coordination Agent - Main Entry Point
========================================

A next-generation virtual project coordinator that operates alongside existing CRM systems.
Integrates through REST APIs, maintains AI-powered memory database, and leverages OpenAI
reasoning models, RAG, and multi-agent role systems for intelligent project coordination.

Key Features:
- Centralized project, task, and user tracking
- AI memory with RAG for contextual responses
- Proactive monitoring and intelligent escalation
- Multi-channel notifications (in-app, email, WhatsApp)
- Human-like reasoning and decision making
- Handbook compliance enforcement
- Conversational ChatGPT-style interface
- Automated reporting and analytics

Author: DDS Global
Version: 2.0.0
Date: October 2025
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_coordinator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def print_banner():
    """Print startup banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║              AI COORDINATION AGENT v2.0                      ║
    ║         Next-Generation Virtual Project Coordinator          ║
    ║                                                               ║
    ║  • Intelligent Task Monitoring & Escalation                  ║
    ║  • AI Memory with RAG for Contextual Responses               ║
    ║  • Multi-Agent Role System (MetaGPT-style)                   ║
    ║  • Automated Reporting & Handbook Compliance                 ║
    ║  • Multi-Channel Notifications (Email, WhatsApp)             ║
    ║                                                               ║
    ║  Starting services...                                         ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Main entry point for AI Coordination Agent"""
    try:
        print_banner()
        
        logger.info("🚀 Starting AI Coordination Agent...")
        logger.info(f"📍 Project root: {project_root}")
        logger.info(f"🔧 Configuration: {Config.DATABASE_TYPE} database")
        logger.info(f"🤖 AI Provider: {Config.DEFAULT_AI_PROVIDER}")
        
        # Create Flask application
        app = create_app()
        
        logger.info("✅ AI Coordination Agent initialized successfully")
        logger.info(f"🌐 Server starting on http://127.0.0.1:5001")
        logger.info("📊 Access dashboard at: http://127.0.0.1:5001/dashboard")
        logger.info("💬 Chat interface at: http://127.0.0.1:5001/chat")
        
        # Start the server
        app.run(
            host='127.0.0.1',
            port=5001,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 AI Coordination Agent stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start AI Coordination Agent: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()