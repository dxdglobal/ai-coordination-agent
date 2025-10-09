"""
Authentication Middleware
Handles JWT token verification and role-based access control
"""

from functools import wraps
from flask import request, jsonify, g
from controllers.auth_controller import auth_controller

def auth_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token is required'}), 401
        
        # Verify token
        payload = auth_controller.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Validate session
        session_data = auth_controller.validate_session(token)
        if not session_data:
            return jsonify({'error': 'Session expired or invalid'}), 401
        
        # Store user info in flask.g for use in the route
        g.current_user = {
            'id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role']
        }
        g.current_token = token
        
        return f(*args, **kwargs)
    
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        @auth_required
        def decorated_function(*args, **kwargs):
            user_role = g.current_user['role']
            
            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_roles': list(allowed_roles),
                    'current_role': user_role
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    return role_required('admin')(f)

def manager_or_admin_required(f):
    """Decorator to require manager or admin role"""
    return role_required('admin', 'manager')(f)

def team_access_required(f):
    """Decorator to require team member, manager, or admin role"""
    return role_required('admin', 'manager', 'team_member')(f)

def client_access_required(f):
    """Decorator for routes accessible to all authenticated users"""
    return role_required('admin', 'manager', 'team_member', 'client')(f)

# Role hierarchy for easier permission checking
ROLE_HIERARCHY = {
    'admin': 4,
    'manager': 3,
    'team_member': 2,
    'client': 1
}

def has_permission(user_role, required_role):
    """Check if user role has permission for required role"""
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)

def permission_required(required_role):
    """Decorator to require minimum role level"""
    def decorator(f):
        @wraps(f)
        @auth_required
        def decorated_function(*args, **kwargs):
            user_role = g.current_user['role']
            
            if not has_permission(user_role, required_role):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_minimum_role': required_role,
                    'current_role': user_role
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def optional_auth(f):
    """Decorator for optional authentication (doesn't fail if no token)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
                
                # Verify token if provided
                payload = auth_controller.verify_token(token)
                if payload:
                    session_data = auth_controller.validate_session(token)
                    if session_data:
                        g.current_user = {
                            'id': payload['user_id'],
                            'username': payload['username'],
                            'role': payload['role']
                        }
                        g.current_token = token
            except:
                pass  # Ignore token errors for optional auth
        
        # Set anonymous user if no valid token
        if not hasattr(g, 'current_user'):
            g.current_user = None
            g.current_token = None
        
        return f(*args, **kwargs)
    
    return decorated_function