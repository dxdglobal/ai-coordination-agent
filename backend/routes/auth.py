"""
Authentication Routes
Handles authentication endpoints
"""

from flask import Blueprint, request, jsonify, g
from controllers.auth_controller import auth_controller
from middleware.auth_middleware import auth_required, admin_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    return auth_controller.login()

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    return auth_controller.register()

@auth_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile():
    """Get current user profile"""
    return auth_controller.get_profile(g.current_user['id'])

@auth_bp.route('/logout', methods=['POST'])
@auth_required
def logout():
    """User logout endpoint"""
    return auth_controller.logout(g.current_token)

@auth_bp.route('/verify', methods=['GET'])
@auth_required
def verify_token():
    """Verify token validity"""
    return jsonify({
        'valid': True,
        'user': g.current_user
    }), 200

@auth_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """List all users (admin only)"""
    try:
        import sqlite3
        import os
        
        db_path = os.path.join(os.path.dirname(__file__), '..', 'ai_coordination.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, username, email, role, full_name, created_at, last_login, is_active
            FROM users
            ORDER BY created_at DESC
        """)
        
        users = []
        for row in cur.fetchall():
            users.append({
                'id': row['id'],
                'username': row['username'],
                'email': row['email'],
                'role': row['role'],
                'full_name': row['full_name'],
                'created_at': row['created_at'],
                'last_login': row['last_login'],
                'is_active': bool(row['is_active'])
            })
        
        cur.close()
        conn.close()
        
        return jsonify({'users': users}), 200
        
    except Exception as e:
        print(f"List users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user (admin only)"""
    try:
        data = request.get_json()
        
        import psycopg2
        from config import DATABASE_URL
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if 'username' in data:
            update_fields.append('username = %s')
            update_values.append(data['username'])
        
        if 'email' in data:
            update_fields.append('email = %s')
            update_values.append(data['email'])
        
        if 'role' in data:
            if data['role'] not in ['admin', 'manager', 'team_member', 'client']:
                return jsonify({'error': 'Invalid role'}), 400
            update_fields.append('role = %s')
            update_values.append(data['role'])
        
        if 'full_name' in data:
            update_fields.append('full_name = %s')
            update_values.append(data['full_name'])
        
        if 'is_active' in data:
            update_fields.append('is_active = %s')
            update_values.append(data['is_active'])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        update_values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s RETURNING id, username, email, role, full_name, is_active"
        
        cur.execute(query, update_values)
        updated_user = cur.fetchone()
        
        if not updated_user:
            return jsonify({'error': 'User not found'}), 404
        
        conn.commit()
        
        user_data = {
            'id': updated_user[0],
            'username': updated_user[1],
            'email': updated_user[2],
            'role': updated_user[3],
            'full_name': updated_user[4],
            'is_active': updated_user[5]
        }
        
        cur.close()
        conn.close()
        
        return jsonify({'user': user_data}), 200
        
    except Exception as e:
        print(f"Update user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    try:
        import psycopg2
        from config import DATABASE_URL
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Don't allow deleting the current user
        if user_id == g.current_user['id']:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'User not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        print(f"Delete user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500