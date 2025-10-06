"""
User Service - Task 1.3
========================

Business logic service for user management, authentication, and profile operations.
Integrates with CRM systems and provides secure password handling.

Features:
- User CRUD operations with validation
- Password hashing and authentication
- Role-based access control
- Profile management
- CRM synchronization
- Account security (lockout, password policies)

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from services.base_service import (
    BaseService, ServiceException, ValidationException, 
    NotFoundException, ConflictException
)
from database.models import User, UserRole, UserStatus
from database.schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserToken
)

# Configure logging
logger = logging.getLogger(__name__)

class AuthenticationException(ServiceException):
    """Exception for authentication failures"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_FAILED")

class AccountLockedException(ServiceException):
    """Exception for locked user accounts"""
    def __init__(self, locked_until: datetime = None):
        message = "Account is locked"
        if locked_until:
            message += f" until {locked_until.isoformat()}"
        super().__init__(message, "ACCOUNT_LOCKED")

class UserService(BaseService[User, UserCreate, UserUpdate, UserResponse]):
    """Service for user management and authentication"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(User, db_session)
        
        # Password policy settings
        self.min_password_length = 8
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self.password_expiry_days = 90
    
    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """
        Hash password with salt using PBKDF2
        
        Args:
            password: Plain text password
            salt: Optional salt (generates new if not provided)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if not salt:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA-256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100k iterations
        )
        
        return password_hash.hex(), salt
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Plain text password
            password_hash: Stored password hash
            salt: Password salt
            
        Returns:
            True if password matches
        """
        computed_hash, _ = self._hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)
    
    def _validate_password_policy(self, password: str) -> None:
        """
        Validate password against policy
        
        Args:
            password: Password to validate
            
        Raises:
            ValidationException: If password doesn't meet policy
        """
        if len(password) < self.min_password_length:
            raise ValidationException(
                f"Password must be at least {self.min_password_length} characters long",
                "password"
            )
        
        # Check for basic complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValidationException(
                "Password must contain at least one uppercase letter, one lowercase letter, and one digit",
                "password"
            )
    
    def _check_account_lockout(self, user: User) -> None:
        """
        Check if account is locked and raise exception if so
        
        Args:
            user: User to check
            
        Raises:
            AccountLockedException: If account is locked
        """
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise AccountLockedException(user.locked_until)
    
    def _increment_failed_attempts(self, user: User) -> None:
        """
        Increment failed login attempts and lock account if needed
        
        Args:
            user: User to update
        """
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        if user.failed_login_attempts >= self.max_failed_attempts:
            user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
            self._log_operation("account_locked", user.id)
        
        self.db.commit()
    
    def _reset_failed_attempts(self, user: User) -> None:
        """
        Reset failed login attempts on successful authentication
        
        Args:
            user: User to update
        """
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        self.db.commit()
    
    def create(self, schema: UserCreate, created_by: str = None) -> User:
        """
        Create new user with password hashing
        
        Args:
            schema: User creation data
            created_by: User performing the creation
            
        Returns:
            Created user instance
            
        Raises:
            ConflictException: If username or email already exists
            ValidationException: If data validation fails
        """
        try:
            self._log_operation("create_user", details={"username": schema.username})
            
            # Validate password policy
            self._validate_password_policy(schema.password)
            
            # Check for existing username
            existing_user = self.db.query(User).filter(
                or_(
                    User.username == schema.username,
                    User.email == schema.email
                )
            ).first()
            
            if existing_user:
                if existing_user.username == schema.username:
                    raise ConflictException("Username already exists", "username")
                else:
                    raise ConflictException("Email already exists", "email")
            
            # Hash password
            password_hash, salt = self._hash_password(schema.password)
            
            # Create user
            user_data = schema.dict(exclude={'password'})
            user = User(
                **user_data,
                password_hash=password_hash,
                salt=salt,
                password_changed_at=datetime.utcnow(),
                created_by=created_by
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            self._log_operation("user_created", user.id)
            
            # TODO: Trigger CRM sync
            # self._sync_to_crm(user, "create")
            
            return user
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (ConflictException, ValidationException)):
                raise
            self._handle_db_error(e, "create_user")
        finally:
            self._close_session_if_needed(self.db)
    
    def update(self, entity_id: str, schema: UserUpdate, updated_by: str = None) -> Optional[User]:
        """
        Update user information
        
        Args:
            entity_id: User ID
            schema: Update data
            updated_by: User performing the update
            
        Returns:
            Updated user instance
            
        Raises:
            NotFoundException: If user not found
            ConflictException: If username or email conflicts
        """
        try:
            self._log_operation("update_user", entity_id)
            
            user = self.get_or_404(entity_id)
            
            # Check for username/email conflicts
            if schema.username or schema.email:
                conflict_query = self.db.query(User).filter(User.id != entity_id)
                
                conditions = []
                if schema.username:
                    conditions.append(User.username == schema.username)
                if schema.email:
                    conditions.append(User.email == schema.email)
                
                if conditions:
                    existing_user = conflict_query.filter(or_(*conditions)).first()
                    if existing_user:
                        if existing_user.username == schema.username:
                            raise ConflictException("Username already exists", "username")
                        else:
                            raise ConflictException("Email already exists", "email")
            
            # Update fields
            update_data = schema.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_by = updated_by
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            self._log_operation("user_updated", entity_id)
            
            # TODO: Trigger CRM sync
            # self._sync_to_crm(user, "update")
            
            return user
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (NotFoundException, ConflictException)):
                raise
            self._handle_db_error(e, "update_user", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def authenticate(self, login_data: UserLogin) -> Optional[User]:
        """
        Authenticate user with username/password
        
        Args:
            login_data: Login credentials
            
        Returns:
            Authenticated user or None
            
        Raises:
            AuthenticationException: If authentication fails
            AccountLockedException: If account is locked
        """
        try:
            self._log_operation("authenticate", details={"username": login_data.username})
            
            # Find user by username or email
            user = self.db.query(User).filter(
                or_(
                    User.username == login_data.username,
                    User.email == login_data.username
                ),
                User.status == UserStatus.ACTIVE,
                User.is_deleted == False
            ).first()
            
            if not user:
                self._log_operation("auth_failed", details={"reason": "user_not_found"})
                raise AuthenticationException()
            
            # Check if account is locked
            self._check_account_lockout(user)
            
            # Verify password
            if not self._verify_password(login_data.password, user.password_hash, user.salt):
                self._increment_failed_attempts(user)
                self._log_operation("auth_failed", user.id, {"reason": "invalid_password"})
                raise AuthenticationException()
            
            # Reset failed attempts on successful login
            self._reset_failed_attempts(user)
            
            self._log_operation("auth_success", user.id)
            return user
            
        except Exception as e:
            if isinstance(e, (AuthenticationException, AccountLockedException)):
                raise
            self._handle_db_error(e, "authenticate")
        finally:
            self._close_session_if_needed(self.db)
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            AuthenticationException: If current password is incorrect
            ValidationException: If new password doesn't meet policy
        """
        try:
            self._log_operation("change_password", user_id)
            
            user = self.get_or_404(user_id)
            
            # Verify current password
            if not self._verify_password(current_password, user.password_hash, user.salt):
                raise AuthenticationException("Current password is incorrect")
            
            # Validate new password
            self._validate_password_policy(new_password)
            
            # Hash new password
            password_hash, salt = self._hash_password(new_password)
            
            # Update password
            user.password_hash = password_hash
            user.salt = salt
            user.password_changed_at = datetime.utcnow()
            user.failed_login_attempts = 0
            user.locked_until = None
            
            self.db.commit()
            
            self._log_operation("password_changed", user_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (AuthenticationException, ValidationException)):
                raise
            self._handle_db_error(e, "change_password", user_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def reset_password(self, user_id: str, new_password: str, reset_by: str = None) -> bool:
        """
        Reset user password (admin function)
        
        Args:
            user_id: User ID
            new_password: New password
            reset_by: Admin user performing the reset
            
        Returns:
            True if password reset successfully
        """
        try:
            self._log_operation("reset_password", user_id, {"reset_by": reset_by})
            
            user = self.get_or_404(user_id)
            
            # Validate new password
            self._validate_password_policy(new_password)
            
            # Hash new password
            password_hash, salt = self._hash_password(new_password)
            
            # Update password
            user.password_hash = password_hash
            user.salt = salt
            user.password_changed_at = datetime.utcnow()
            user.failed_login_attempts = 0
            user.locked_until = None
            user.updated_by = reset_by
            
            self.db.commit()
            
            self._log_operation("password_reset", user_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ValidationException):
                raise
            self._handle_db_error(e, "reset_password", user_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def unlock_account(self, user_id: str, unlocked_by: str = None) -> bool:
        """
        Unlock user account
        
        Args:
            user_id: User ID
            unlocked_by: Admin user performing the unlock
            
        Returns:
            True if account unlocked successfully
        """
        try:
            self._log_operation("unlock_account", user_id, {"unlocked_by": unlocked_by})
            
            user = self.get_or_404(user_id)
            
            user.failed_login_attempts = 0
            user.locked_until = None
            user.updated_by = unlocked_by
            
            self.db.commit()
            
            self._log_operation("account_unlocked", user_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            self._handle_db_error(e, "unlock_account", user_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            username: Username to search for
            
        Returns:
            User instance or None
        """
        try:
            user = self.db.query(User).filter(
                User.username == username,
                User.is_deleted == False
            ).first()
            
            return user
            
        except Exception as e:
            self._handle_db_error(e, "get_by_username")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            email: Email to search for
            
        Returns:
            User instance or None
        """
        try:
            user = self.db.query(User).filter(
                User.email == email,
                User.is_deleted == False
            ).first()
            
            return user
            
        except Exception as e:
            self._handle_db_error(e, "get_by_email")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_role(self, role: UserRole, status: UserStatus = UserStatus.ACTIVE) -> List[User]:
        """
        Get users by role
        
        Args:
            role: User role to filter by
            status: User status to filter by
            
        Returns:
            List of users with the specified role
        """
        try:
            users = self.db.query(User).filter(
                User.role == role,
                User.status == status,
                User.is_deleted == False
            ).all()
            
            return users
            
        except Exception as e:
            self._handle_db_error(e, "get_by_role")
        finally:
            self._close_session_if_needed(self.db)
    
    def search_users(
        self,
        query: str,
        role: UserRole = None,
        status: UserStatus = None,
        limit: int = 20
    ) -> List[User]:
        """
        Search users by name, username, or email
        
        Args:
            query: Search query
            role: Optional role filter
            status: Optional status filter
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        try:
            db_query = self.db.query(User).filter(User.is_deleted == False)
            
            # Apply text search
            if query:
                search_conditions = [
                    User.username.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                    User.first_name.ilike(f"%{query}%"),
                    User.last_name.ilike(f"%{query}%")
                ]
                db_query = db_query.filter(or_(*search_conditions))
            
            # Apply filters
            if role:
                db_query = db_query.filter(User.role == role)
            if status:
                db_query = db_query.filter(User.status == status)
            
            users = db_query.limit(limit).all()
            return users
            
        except Exception as e:
            self._handle_db_error(e, "search_users")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics
        
        Returns:
            Dictionary with user statistics
        """
        try:
            stats = self.get_statistics()
            
            # Add role-based statistics
            role_stats = {}
            for role in UserRole:
                count = self.count({"role": role})
                role_stats[role.value] = count
            
            # Add status-based statistics
            status_stats = {}
            for status in UserStatus:
                count = self.count({"status": status})
                status_stats[status.value] = count
            
            # Add security statistics
            locked_count = self.db.query(User).filter(
                User.locked_until.isnot(None),
                User.locked_until > datetime.utcnow(),
                User.is_deleted == False
            ).count()
            
            stats.update({
                "by_role": role_stats,
                "by_status": status_stats,
                "locked_accounts": locked_count
            })
            
            return stats
            
        except Exception as e:
            self._handle_db_error(e, "get_user_statistics")
        finally:
            self._close_session_if_needed(self.db)

# Export service
__all__ = ["UserService", "AuthenticationException", "AccountLockedException"]