# AI Coordination Agent - Project Management System

A comprehensive project management coordination system built with React + Vite frontend and Flask backend, featuring AI-powered coordination assistance and multi-platform integrations.

## 🚀 Features

### Core Features
- **Project Management**: Create, manage, and track projects with detailed status monitoring
- **Task Management**: Comprehensive task tracking with status updates, priorities, assignments, and time tracking
- **AI Coordination Agent**: OpenAI-powered assistant that analyzes workflows and suggests improvements
- **Multi-platform Integrations**: WhatsApp, Telegram, Email, Voice, and Zendesk integrations
- **Real-time Dashboard**: Interactive dashboard with statistics and project overviews
- **Comment System**: Task-specific commenting and collaboration features

### AI Capabilities
- Workspace analysis and coordination suggestions
- Task follow-up automation
- Priority analysis and recommendations
- Time tracking insights
- Auto-assignment suggestions
- Interactive chat interface

### Integrations
- **WhatsApp**: Send/receive messages via Twilio
- **Telegram**: Bot integration with command handling
- **Email**: SMTP email notifications and updates
- **Voice**: Speech-to-text transcription and voice commands
- **Zendesk**: Customer support ticket integration

## 🏗️ Architecture

```
/ai-coordination-agent
├── /frontend          # React + Vite application
│   ├── /src
│   │   ├── /components    # Reusable UI components
│   │   ├── /pages         # Page components (Dashboard, Tasks, etc.)
│   │   ├── /context       # React context for API management
│   │   └── App.jsx        # Main application component
│   ├── package.json
│   └── vite.config.js
├── /backend           # Flask application
│   ├── /models           # SQLAlchemy database models
│   ├── /routes           # API route handlers
│   ├── /services         # Business logic and integrations
│   ├── app.py            # Flask application factory
│   ├── config.py         # Configuration management
│   └── requirements.txt
└── README.md
```

## 🛠️ Installation & Setup

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-coordination-agent
   ```

2. **Set up Python virtual environment**
   ```bash
   cd backend
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your API keys and configuration
   # At minimum, set:
   # - SECRET_KEY (generate a secure key)
   # - OPENAI_API_KEY (for AI features)
   # - DATABASE_TYPE (sqlite for development)
   ```

5. **Initialize the database**
   ```bash
   python app.py
   # The database will be created automatically on first run
   ```

6. **Run the Flask server**
   ```bash
   python app.py
   # Server will start on http://localhost:5000
   ```

### Frontend Setup

1. **Open a new terminal and navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # The default configuration should work for local development
   ```

4. **Start the development server**
   ```bash
   npm run dev
   # Frontend will be available at http://localhost:5173
   ```

## 🔧 Configuration

### Required Environment Variables

#### Backend (.env)
- `SECRET_KEY`: Flask secret key for sessions
- `OPENAI_API_KEY`: OpenAI API key for AI features (required for AI functionality)

#### Optional Integration Keys
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`: For WhatsApp integration
- `TELEGRAM_BOT_TOKEN`: For Telegram bot integration
- `EMAIL_USER`, `EMAIL_PASSWORD`: For email notifications
- `ZENDESK_API_TOKEN`, `ZENDESK_DOMAIN`, `ZENDESK_EMAIL`: For Zendesk integration

#### Frontend (.env)
- `VITE_API_BASE_URL`: Backend API URL (default: http://localhost:5000)

### Database Configuration

The system supports multiple databases:

#### SQLite (Default - Development)
```env
DATABASE_TYPE=sqlite
```

#### PostgreSQL (Production)
```env
DATABASE_TYPE=postgresql
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_NAME=project_management
```

#### MySQL
```env
DATABASE_TYPE=mysql
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_NAME=project_management
```

## 📱 Usage

### Dashboard
- Access the main dashboard at http://localhost:5173
- View project statistics, recent tasks, and AI suggestions
- Navigate between different sections using the top navigation

### Project Management
- Create new projects with descriptions, deadlines, and status tracking
- View project progress and task completion rates
- Manage project lifecycle from creation to completion

### Task Management
- Create tasks with priorities, assignments, and time estimates
- Update task status using the status dropdown
- Add comments and collaborate on tasks
- Filter tasks by project, status, assignee, or search terms

### AI Chat Interface
- Access the AI agent via the "AI Chat" tab
- Use predefined prompts for common operations:
  - "Analyze Workspace" - Get AI insights on current projects
  - "Follow Up Tasks" - Get suggestions for task follow-ups
  - "Status Overview" - Comprehensive status report
  - "Suggest Improvements" - Workflow optimization suggestions
- Chat naturally with the AI about project coordination needs

### Integrations
- Configure and test various integrations from the Integrations page
- Send messages via WhatsApp, Telegram, or Email
- View integration message history
- Set up webhooks for incoming messages

## 🔌 API Endpoints

### Projects API
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Tasks API
- `GET /api/tasks` - List tasks (with filtering)
- `POST /api/tasks` - Create new task
- `GET /api/tasks/{id}` - Get task details
- `PUT /api/tasks/{id}` - Update task
- `PATCH /api/tasks/{id}/status` - Update task status
- `DELETE /api/tasks/{id}` - Delete task

### AI API
- `POST /ai/analyze` - Analyze workspace with AI
- `POST /ai/chat` - Chat with AI agent
- `GET /ai/suggestions` - Get AI coordination suggestions
- `GET /ai/actions` - Get pending AI actions

### Integration APIs
- `POST /integrations/whatsapp/send` - Send WhatsApp message
- `POST /integrations/telegram/send` - Send Telegram message
- `POST /integrations/email/send` - Send email
- `GET /integrations/history` - Get integration message history

## 🤖 AI Features

### Workspace Analysis
The AI agent can analyze your workspace and provide insights on:
- Task completion rates and bottlenecks
- Resource allocation and workload distribution
- Priority adjustments needed
- Timeline and deadline analysis

### Coordination Suggestions
Get AI-powered suggestions for:
- Overdue tasks requiring attention
- Tasks stalled in progress
- Unassigned tasks needing ownership
- Priority rebalancing recommendations

### Chat Interface
- Natural language interaction with the AI agent
- Context-aware responses based on current workspace data
- Actionable suggestions and automated task creation
- Integration with project data for informed responses

## 🔧 Development

### Code Structure

#### Frontend (React + Vite)
- **Components**: Reusable UI components using Material-UI
- **Pages**: Main application pages (Dashboard, Projects, Tasks, Chat, Integrations)
- **Context**: API context for centralized backend communication
- **Hooks**: Custom hooks for data fetching and state management

#### Backend (Flask)
- **Models**: SQLAlchemy models for database entities
- **Routes**: API endpoints organized by functionality
- **Services**: Business logic and external service integrations
- **Configuration**: Environment-based configuration management

### Adding New Features

1. **Backend**: Add new models, routes, and services
2. **Frontend**: Create components and integrate with API context
3. **Documentation**: Update API documentation and usage examples

### Testing

#### Backend Testing
```bash
cd backend
python -m pytest tests/
```

#### Frontend Testing
```bash
cd frontend
npm run test
```

## 🚀 Deployment

### Backend Deployment

#### Using Docker
```bash
cd backend
docker build -t ai-coordination-backend .
docker run -p 5000:5000 --env-file .env ai-coordination-backend
```

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend Deployment

#### Build for Production
```bash
cd frontend
npm run build
```

#### Deploy to Static Hosting
- The `dist/` folder contains the production build
- Deploy to services like Netlify, Vercel, or AWS S3

### Environment Setup for Production

1. **Set production environment variables**
2. **Use a production database (PostgreSQL/MySQL)**
3. **Configure CORS for your domain**
4. **Set up SSL certificates**
5. **Configure API keys for integrations**

## 🔒 Security Considerations

- **API Keys**: Store all API keys in environment variables, never in code
- **Database**: Use strong passwords and restrict database access
- **CORS**: Configure CORS settings for production domains
- **HTTPS**: Use HTTPS in production for all communications
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Input Validation**: Validate all user inputs and API parameters

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add new feature'`
5. Push to the branch: `git push origin feature/new-feature`
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the documentation above
2. Review the example environment files
3. Check the GitHub issues for common problems
4. Create a new issue with detailed information about your problem

## 📈 Roadmap

- [ ] Mobile app development
- [ ] Advanced AI automation workflows
- [ ] Real-time collaboration features
- [ ] Advanced analytics and reporting
- [ ] Integration with more third-party services
- [ ] Multi-tenant support
- [ ] Advanced security features
