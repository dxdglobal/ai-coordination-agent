from flask import Blueprint, request, jsonify

integrations_bp = Blueprint('integrations', __name__)

# Import here to avoid circular imports
from services.zendesk_service import ZendeskService
from services.whatsapp_service import WhatsAppService
from services.telegram_service import TelegramService
from services.email_service import EmailService
from services.voice_service import VoiceService
from models.models import db, Integration

zendesk_service = ZendeskService()
whatsapp_service = WhatsAppService()
telegram_service = TelegramService()
email_service = EmailService()
voice_service = VoiceService()

# Zendesk Integration
@integrations_bp.route('/zendesk/tickets', methods=['GET'])
def get_zendesk_tickets():
    """Get recent Zendesk tickets"""
    try:
        tickets = zendesk_service.get_recent_tickets()
        return jsonify(tickets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/zendesk/chat-history/<ticket_id>', methods=['GET'])
def get_zendesk_chat_history(ticket_id):
    """Get chat history for a Zendesk ticket"""
    try:
        history = zendesk_service.get_chat_history(ticket_id)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WhatsApp Integration
@integrations_bp.route('/whatsapp/send', methods=['POST'])
def send_whatsapp_message():
    """Send WhatsApp message"""
    data = request.get_json()
    to_number = data.get('to')
    message = data.get('message')
    
    try:
        result = whatsapp_service.send_message(to_number, message)
        
        # Store in database
        integration = Integration(
            platform='whatsapp',
            content=message,
            recipient=to_number,
            metadata={'status': 'sent', 'message_id': result.get('sid')}
        )
        db.session.add(integration)
        db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    """Webhook for receiving WhatsApp messages"""
    data = request.form.to_dict()
    
    try:
        # Process incoming message
        result = whatsapp_service.handle_incoming_message(data)
        
        # Store in database
        integration = Integration(
            platform='whatsapp',
            external_id=data.get('MessageSid'),
            content=data.get('Body'),
            sender=data.get('From'),
            metadata=data
        )
        db.session.add(integration)
        db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Telegram Integration
@integrations_bp.route('/telegram/send', methods=['POST'])
def send_telegram_message():
    """Send Telegram message"""
    data = request.get_json()
    chat_id = data.get('chat_id')
    message = data.get('message')
    
    try:
        result = telegram_service.send_message(chat_id, message)
        
        # Store in database
        integration = Integration(
            platform='telegram',
            content=message,
            recipient=str(chat_id),
            metadata={'message_id': result.get('message_id')}
        )
        db.session.add(integration)
        db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Webhook for receiving Telegram messages"""
    data = request.get_json()
    
    try:
        result = telegram_service.handle_update(data)
        
        # Store in database if it's a message
        if 'message' in data:
            message = data['message']
            integration = Integration(
                platform='telegram',
                external_id=str(message.get('message_id')),
                content=message.get('text'),
                sender=message.get('from', {}).get('username'),
                metadata=data
            )
            db.session.add(integration)
            db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Email Integration
@integrations_bp.route('/email/send', methods=['POST'])
def send_email():
    """Send email"""
    data = request.get_json()
    to_email = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    
    try:
        result = email_service.send_email(to_email, subject, body)
        
        # Store in database
        integration = Integration(
            platform='email',
            content=f"Subject: {subject}\n\n{body}",
            recipient=to_email,
            metadata={'subject': subject, 'status': 'sent'}
        )
        db.session.add(integration)
        db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Voice Integration
@integrations_bp.route('/voice/transcribe', methods=['POST'])
def transcribe_voice():
    """Transcribe voice message"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    try:
        result = voice_service.transcribe_audio(audio_file)
        
        # Store in database
        integration = Integration(
            platform='voice',
            content=result.get('transcription'),
            metadata={'confidence': result.get('confidence'), 'duration': result.get('duration')}
        )
        db.session.add(integration)
        db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/voice/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    data = request.get_json()
    text = data.get('text')
    
    try:
        result = voice_service.text_to_speech(text)
        return result  # Returns audio file
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# General integration history
@integrations_bp.route('/history', methods=['GET'])
def get_integration_history():
    """Get integration message history"""
    platform = request.args.get('platform')
    task_id = request.args.get('task_id')
    project_id = request.args.get('project_id')
    limit = int(request.args.get('limit', 50))
    
    query = Integration.query
    
    if platform:
        query = query.filter(Integration.platform == platform)
    if task_id:
        query = query.filter(Integration.task_id == task_id)
    if project_id:
        query = query.filter(Integration.project_id == project_id)
    
    integrations = query.order_by(Integration.created_at.desc()).limit(limit).all()
    
    return jsonify([integration.to_dict() for integration in integrations])

@integrations_bp.route('/link', methods=['POST'])
def link_integration_to_task():
    """Link an integration message to a task or project"""
    data = request.get_json()
    integration_id = data.get('integration_id')
    task_id = data.get('task_id')
    project_id = data.get('project_id')
    
    integration = Integration.query.get_or_404(integration_id)
    
    if task_id:
        integration.task_id = task_id
    if project_id:
        integration.project_id = project_id
    
    db.session.commit()
    
    return jsonify(integration.to_dict())