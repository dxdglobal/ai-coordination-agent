"""
Authentication Controller
Handles user login, registration, and authentication operations
"""

import jwt
import bcrypt
import hashlib
import sqlite3
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
import os

class AuthController:
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
        self.jwt_expiry_hours = 24
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'ai_coordination.db')

    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory for dict-like access
        return conn

    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def generate_token(self, user_data):
        """Generate JWT token"""
        payload = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'role': user_data['role'],
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def store_session(self, user_id, token, user_agent=None, ip_address=None):
        """Store session in database"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        try:
            # Hash token for storage
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            expires_at = datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours)
            
            cur.execute("""
                INSERT INTO user_sessions (user_id, token_hash, expires_at, user_agent, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, token_hash, expires_at.isoformat(), user_agent, ip_address))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def login(self):
        """Handle user login"""
        try:
            data = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Find user by username or email
            cur.execute("""
                SELECT id, username, email, password_hash, role, full_name, is_active
                FROM users 
                WHERE (username = ? OR email = ?) AND is_active = 1
            """, (username, username))
            
            user_row = cur.fetchone()
            
            if not user_row:
                return jsonify({'error': 'Invalid credentials'}), 401
            
            user_data = {
                'id': user_row['id'],
                'username': user_row['username'],
                'email': user_row['email'],
                'password_hash': user_row['password_hash'],
                'role': user_row['role'],
                'full_name': user_row['full_name'],
                'is_active': user_row['is_active']
            }
            
            # Verify password
            if not self.verify_password(password, user_data['password_hash']):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Update last login
            cur.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            """, (user_data['id'],))
            
            conn.commit()
            
            # Generate JWT token
            token = self.generate_token(user_data)
            
            # Store session
            user_agent = request.headers.get('User-Agent')
            ip_address = request.remote_addr
            self.store_session(user_data['id'], token, user_agent, ip_address)
            
            # Return response
            response_data = {
                'token': token,
                'user': {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'email': user_data['email'],
                    'role': user_data['role'],
                    'full_name': user_data['full_name']
                }
            }
            
            cur.close()
            conn.close()
            
            return jsonify(response_data), 200
            
        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def register(self):
        """Handle user registration"""
        try:
            data = request.get_json()
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            full_name = data.get('full_name', '').strip()
            role = data.get('role', 'team_member')
            
            # Validation
            if not username or not email or not password:
                return jsonify({'error': 'Username, email, and password are required'}), 400
            
            if len(password) < 6:
                return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            
            if role not in ['admin', 'manager', 'team_member', 'client']:
                return jsonify({'error': 'Invalid role specified'}), 400
            
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Check if username or email already exists
            cur.execute("""
                SELECT id FROM users WHERE username = ? OR email = ?
            """, (username, email))
            
            if cur.fetchone():
                return jsonify({'error': 'Username or email already exists'}), 400
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, password_hash, role, full_name))
            
            user_id = cur.lastrowid
            
            # Get the created user data
            cur.execute("""
                SELECT id, username, email, role, full_name FROM users WHERE id = ?
            """, (user_id,))
            
            user_row = cur.fetchone()
            user_data = {
                'id': user_row['id'],
                'username': user_row['username'],
                'email': user_row['email'],
                'role': user_row['role'],
                'full_name': user_row['full_name']
            }
            
            conn.commit()
            
            # Generate JWT token
            token = self.generate_token(user_data)
            
            # Store session
            user_agent = request.headers.get('User-Agent')
            ip_address = request.remote_addr
            self.store_session(user_data['id'], token, user_agent, ip_address)
            
            response_data = {
                'token': token,
                'user': user_data
            }
            
            cur.close()
            conn.close()
            
            return jsonify(response_data), 201
            
        except Exception as e:
            print(f"Registration error: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def get_profile(self, user_id):
        """Get user profile"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, username, email, role, full_name, created_at, last_login
                FROM users WHERE id = ? AND is_active = 1
            """, (user_id,))
            
            user_row = cur.fetchone()
            
            if not user_row:
                return jsonify({'error': 'User not found'}), 404
            
            user_data = {
                'id': user_row['id'],
                'username': user_row['username'],
                'email': user_row['email'],
                'role': user_row['role'],
                'full_name': user_row['full_name'],
                'created_at': user_row['created_at'],
                'last_login': user_row['last_login']
            }
            
            cur.close()
            conn.close()
            
            return jsonify({'user': user_data}), 200
            
        except Exception as e:
            print(f"Get profile error: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def logout(self, token):
        """Handle user logout"""
        try:
            # Invalidate session
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE user_sessions 
                SET is_active = 0 
                WHERE token_hash = ?
            """, (token_hash,))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({'message': 'Logged out successfully'}), 200
            
        except Exception as e:
            print(f"Logout error: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def validate_session(self, token):
        """Validate if session is still active"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT s.user_id, s.expires_at, u.username, u.role
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token_hash = ? AND s.is_active = 1 AND datetime(s.expires_at) > datetime('now')
            """, (token_hash,))
            
            session_row = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if session_row:
                return {
                    'user_id': session_row['user_id'],
                    'expires_at': session_row['expires_at'],
                    'username': session_row['username'],
                    'role': session_row['role']
                }
            return None
            
        except Exception as e:
            print(f"Session validation error: {e}")
            return None

# Global instance
auth_controller = AuthController()