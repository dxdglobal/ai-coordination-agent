# Service module exports
from .ai_service import AICoordinationService

# Optional imports for services with external dependencies
try:
    from .telegram_service import TelegramService
except ImportError:
    pass

try:
    from .email_service import EmailService
except ImportError:
    pass