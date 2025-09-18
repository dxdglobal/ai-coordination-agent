# Backend - AI Coordination Agent

Flask-based REST API server for the AI Coordination Agent project management system.

## 🏗️ Architecture

This Flask backend provides:
- **RESTful API**: Comprehensive REST endpoints for projects, tasks, and comments
- **AI Integration**: OpenAI-powered coordination assistance and chat
- **Database Models**: SQLAlchemy models with support for SQLite, PostgreSQL, and MySQL
- **External Integrations**: WhatsApp, Telegram, Email, Voice, and Zendesk services
- **Modular Design**: Blueprint-based architecture for scalable development

## 📁 Project Structure

```
/backend
├── app.py                 # Flask application factory and entry point
├── config.py              # Environment configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── /models               # Database models
│   └── models.py         # SQLAlchemy model definitions
├── /routes               # API route handlers
│   ├── api.py           # Core API endpoints (projects, tasks, comments)
│   ├── ai.py            # AI coordination endpoints
│   └── integrations.py  # External integration endpoints
└── /services             # Business logic and integrations
    ├── ai_service.py     # OpenAI integration service
    ├── email_service.py  # Email notification service
    ├── telegram_service.py # Telegram bot service
    ├── voice_service.py  # Speech recognition service
    ├── whatsapp_service.py # WhatsApp integration service
    └── zendesk_service.py # Zendesk API service
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required: SECRET_KEY, OPENAI_API_KEY
# Optional: Integration API keys for WhatsApp, Telegram, etc.
```

### 3. Run the Server

```bash
python app.py
# Server starts on http://localhost:5000
```

## 🔧 Configuration

### Required Environment Variables

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database Configuration
DATABASE_TYPE=sqlite  # or postgresql, mysql

# AI Configuration
OPENAI_API_KEY=your-openai-api-key-here
```

### Optional Integration Variables

```env
# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Email
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Zendesk
ZENDESK_API_TOKEN=your-zendesk-token
ZENDESK_DOMAIN=your-domain.zendesk.com
ZENDESK_EMAIL=your-zendesk-email@company.com
```

### Database Configuration

#### SQLite (Development - Default)
```env
DATABASE_TYPE=sqlite
# No additional configuration needed
```

#### PostgreSQL (Production)
```env
DATABASE_TYPE=postgresql
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=project_management
```

#### MySQL
```env
DATABASE_TYPE=mysql
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=project_management
```

## 📊 Database Models

### Project Model
- `id`: Primary key
- `name`: Project name
- `description`: Project description
- `status`: Project status (active, completed, on_hold)
- `created_at`, `updated_at`: Timestamps
- `deadline`: Project deadline

### Task Model
- `id`: Primary key
- `title`: Task title
- `description`: Task description
- `status`: Task status (todo, in_progress, done)
- `priority`: Priority level (low, medium, high)
- `project_id`: Foreign key to Project
- `assigned_to`: Task assignee
- `time_estimate`, `time_spent`: Time tracking
- `created_at`, `updated_at`, `due_date`: Timestamps

### Comment Model
- `id`: Primary key
- `content`: Comment text
- `task_id`: Foreign key to Task
- `author`: Comment author
- `created_at`: Timestamp

### Label Model
- `id`: Primary key
- `name`: Label name
- `color`: Label color
- `task_id`: Foreign key to Task

### Integration Model
- `id`: Primary key
- `type`: Integration type (whatsapp, telegram, email, voice, zendesk)
- `data`: JSON data for integration
- `created_at`: Timestamp

### AIAction Model
- `id`: Primary key
- `action_type`: Type of AI action
- `data`: JSON data for action
- `status`: Action status
- `created_at`: Timestamp

## 🔌 API Endpoints

### Projects API (`/api/projects`)
- `GET /` - List all projects
- `POST /` - Create new project
- `GET /{id}` - Get project by ID
- `PUT /{id}` - Update project
- `DELETE /{id}` - Delete project

### Tasks API (`/api/tasks`)
- `GET /` - List tasks (supports filtering: `?project_id=1&status=todo&assigned_to=user`)
- `POST /` - Create new task
- `GET /{id}` - Get task by ID
- `PUT /{id}` - Update task
- `PATCH /{id}/status` - Update task status only
- `DELETE /{id}` - Delete task

### Comments API (`/api/comments`)
- `GET /` - List comments (supports filtering: `?task_id=1`)
- `POST /` - Create new comment
- `GET /{id}` - Get comment by ID
- `PUT /{id}` - Update comment
- `DELETE /{id}` - Delete comment

### AI API (`/ai/`)
- `POST /analyze` - Analyze workspace with AI
- `POST /chat` - Chat with AI agent
- `GET /suggestions` - Get AI coordination suggestions
- `GET /actions` - Get pending AI actions

### Integration APIs (`/integrations/`)
- `POST /whatsapp/send` - Send WhatsApp message
- `POST /telegram/send` - Send Telegram message
- `POST /email/send` - Send email notification
- `POST /voice/transcribe` - Transcribe voice to text
- `GET /zendesk/tickets` - Get Zendesk tickets
- `GET /history` - Get integration message history

## 🤖 AI Service

The AI service (`services/ai_service.py`) provides:

### Workspace Analysis
- Analyzes projects, tasks, and their relationships
- Identifies bottlenecks and areas for improvement
- Provides actionable recommendations

### Chat Interface
- Natural language processing for user queries
- Context-aware responses based on workspace data
- Integration with project management operations

### Coordination Features
- Automatic task follow-up suggestions
- Priority analysis and recommendations
- Time tracking insights and optimization

## 🔗 Integration Services

### WhatsApp Service (`services/whatsapp_service.py`)
- Send messages via Twilio WhatsApp API
- Handle incoming webhook messages
- Message history tracking

### Telegram Service (`services/telegram_service.py`)
- Bot command handling
- Send notifications and updates
- Interactive bot responses

### Email Service (`services/email_service.py`)
- SMTP email sending
- Template-based notifications
- Task and project updates

### Voice Service (`services/voice_service.py`)
- Speech-to-text transcription
- Voice command processing
- Audio file handling

### Zendesk Service (`services/zendesk_service.py`)
- Ticket creation and management
- Customer support integration
- Bidirectional sync capabilities

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=. tests/
```

### Test Structure
```
/tests
├── test_models.py        # Database model tests
├── test_api.py          # API endpoint tests
├── test_ai_service.py   # AI service tests
├── test_integrations.py # Integration service tests
└── conftest.py          # Test configuration
```

## 🚀 Deployment

### Development Server
```bash
python app.py
```

### Production Deployment

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Using Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Environment Considerations

#### Production Settings
```env
DEBUG=False
SECRET_KEY=strong-production-secret-key
DATABASE_TYPE=postgresql
# Use production database credentials
```

#### CORS Configuration
- Configure allowed origins for production domain
- Update CORS settings in `app.py` for your frontend URL

## 🔒 Security

### API Key Management
- Store all API keys in environment variables
- Use different keys for development and production
- Regularly rotate API keys

### Database Security
- Use strong database passwords
- Restrict database access to necessary hosts
- Enable SSL for database connections in production

### Request Validation
- All inputs are validated before processing
- SQL injection protection via SQLAlchemy ORM
- Rate limiting recommended for production

## 🛠️ Development

### Adding New Endpoints
1. Create route handler in appropriate blueprint (`routes/`)
2. Add business logic to service layer (`services/`)
3. Update models if needed (`models/`)
4. Add tests for new functionality

### Adding New Integrations
1. Create service class in `services/`
2. Add configuration variables to `config.py`
3. Create API endpoints in `routes/integrations.py`
4. Update environment template (`.env.example`)

### Database Migrations
```bash
# For schema changes, recreate database in development
# For production, implement proper migration strategy
```

## 📝 Troubleshooting

### Common Issues

#### Database Connection Errors
- Check database credentials in `.env`
- Ensure database server is running
- Verify network connectivity

#### AI Service Errors
- Verify OpenAI API key is valid
- Check API usage limits
- Ensure internet connectivity

#### Integration Failures
- Verify API credentials for each service
- Check service-specific documentation
- Review error logs for specific error messages

### Logging
- Debug logs are enabled in development mode
- Check console output for error details
- Add custom logging as needed for debugging

### Performance Optimization
- Use database indexes for frequently queried fields
- Implement caching for expensive operations
- Consider connection pooling for high-traffic scenarios