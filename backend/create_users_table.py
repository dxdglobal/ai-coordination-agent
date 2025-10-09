#!/usr/bin/env python3
"""
Create users table with authentication and roles support
"""

import sqlite3
import bcrypt
import os

def create_users_table():
    """Create users table with role-based authentication using SQLite"""
    
    # Use SQLite for development
    db_path = os.path.join(os.path.dirname(__file__), 'ai_coordination.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # Create users table (SQLite version)
        print("Creating users table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'team_member' CHECK (role IN ('admin', 'manager', 'team_member', 'client')),
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            );
        """)
        
        # Create indexes for performance
        print("Creating indexes...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);")
        
        # Check if admin user exists
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cur.fetchone():
            # Create default admin user
            print("Creating default admin user...")
            admin_password = "admin123"  # Change this in production
            password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name) 
                VALUES (?, ?, ?, ?, ?)
            """, ('admin', 'admin@example.com', password_hash, 'admin', 'System Administrator'))
            
            # Create sample users for testing
            print("Creating sample users...")
            
            # Manager user
            manager_password = "manager123"
            manager_hash = bcrypt.hashpw(manager_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name) 
                VALUES (?, ?, ?, ?, ?)
            """, ('manager', 'manager@example.com', manager_hash, 'manager', 'Project Manager'))
            
            # Team member user
            team_password = "team123"
            team_hash = bcrypt.hashpw(team_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name) 
                VALUES (?, ?, ?, ?, ?)
            """, ('teammember', 'team@example.com', team_hash, 'team_member', 'Team Member'))
            
            # Client user
            client_password = "client123"
            client_hash = bcrypt.hashpw(client_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name) 
                VALUES (?, ?, ?, ?, ?)
            """, ('client', 'client@example.com', client_hash, 'client', 'Client User'))
        
        # Add user relationships to existing tables (if they exist)
        print("Adding user relationships to existing tables...")
        
        # Check if tasks table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        if cur.fetchone():
            # Check if columns exist before adding them
            cur.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cur.fetchall()]
            
            if 'created_by' not in columns:
                cur.execute("ALTER TABLE tasks ADD COLUMN created_by INTEGER REFERENCES users(id)")
            if 'assigned_to' not in columns:
                cur.execute("ALTER TABLE tasks ADD COLUMN assigned_to INTEGER REFERENCES users(id)")
        else:
            print("⚠️  Tasks table not found, skipping task table modifications")
        
        # Check if projects table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
        if cur.fetchone():
            cur.execute("PRAGMA table_info(projects)")
            columns = [row[1] for row in cur.fetchall()]
            
            if 'created_by' not in columns:
                cur.execute("ALTER TABLE projects ADD COLUMN created_by INTEGER REFERENCES users(id)")
            if 'manager_id' not in columns:
                cur.execute("ALTER TABLE projects ADD COLUMN manager_id INTEGER REFERENCES users(id)")
        else:
            print("⚠️  Projects table not found, skipping project table modifications")
        
        # Create user sessions table for JWT token management
        print("Creating user sessions table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                user_agent TEXT,
                ip_address TEXT
            );
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON user_sessions(token_hash);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);")
        
        conn.commit()
        print("✅ Users table and authentication system created successfully!")
        
        print("\n📋 Default Users Created:")
        print("1. Admin: username='admin', password='admin123'")
        print("2. Manager: username='manager', password='manager123'")
        print("3. Team Member: username='teammember', password='team123'")
        print("4. Client: username='client', password='client123'")
        print(f"\n📁 Database created at: {db_path}")
        print("\n⚠️  Change these passwords in production!")
        
    except Exception as e:
        print(f"❌ Error creating users table: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_users_table()