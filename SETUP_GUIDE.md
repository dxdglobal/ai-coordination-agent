# 🚀 AI Coordination Agent - Complete Setup Guide

## ✅ Will It Run? YES! (With proper setup)

### 📋 Prerequisites
- **Python 3.8+** installed
- **Node.js 16+** and npm installed  
- **Git** installed
- **Internet connection** for API calls

### 🔧 Setup Steps

#### 1. Clone and Navigate
```bash
git clone https://github.com/dxdglobal/ai-coordination-agent.git
cd ai-coordination-agent
```

#### 2. Backend Setup
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env

# Edit .env file with your API keys:
# - OPENAI_API_KEY=your_openai_key_here
# - DB_PASSWORD=3@6*t:lU (already set)
# - Other API keys as needed
```

#### 3. Frontend Setup  
```bash
cd ../frontend

# Install Node dependencies
npm install
```

#### 4. Database Setup
The database is pre-configured and connected:
- **Host**: 92.113.22.65
- **Database**: u906714182_sqlrrefdvdv  
- **User**: u906714182_sqlrrefdvdv
- **Password**: 3@6*t:lU (in .env)

No additional database setup needed!

### 🚀 Running the Project

#### Option 1: Easy Start (Windows)
```bash
# Run the automated startup script
start_servers.bat
```

#### Option 2: Manual Start
```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

### 🌐 Access URLs
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/health

### 🎯 Features Available

#### ✅ Working Features
1. **Enhanced Chat System** - Real-time AI conversations
2. **Task Management** - View and analyze tasks
3. **Semantic Search** - Advanced search in tasks
4. **DDS AI Integration** - AI assistant functionality
5. **Database Integration** - Full CRM connectivity
6. **Background Services** - Task monitoring
7. **API Endpoints** - RESTful services

#### 🔑 API Keys Needed
- **OPENAI_API_KEY** - For AI functionality (required)
- **TWILIO_*** - For WhatsApp (optional)
- **TELEGRAM_BOT_TOKEN** - For Telegram (optional)
- **ZENDESK_*** - For Zendesk integration (optional)

### 🐛 Troubleshooting

#### Common Issues & Solutions

1. **"Module not found" error**
   ```bash
   pip install -r requirements.txt
   ```

2. **Port already in use**
   - Frontend: Change port in `vite.config.js`
   - Backend: Change port in `app.py`

3. **Database connection error**
   - Check `.env` file has correct DB_PASSWORD
   - Verify internet connection

4. **OpenAI API errors**
   - Add valid OPENAI_API_KEY to `.env`
   - Check API quota/billing

### 📁 Project Structure
```
ai-coordination-agent/
├── backend/                 # Flask API server
│   ├── app.py              # Main application
│   ├── routes/             # API endpoints  
│   ├── services/           # Business logic
│   ├── models/             # Data models
│   └── requirements.txt    # Python dependencies
├── frontend/               # React + Vite app
│   ├── src/               # Source code
│   ├── package.json       # Node dependencies
│   └── vite.config.js     # Vite configuration
└── start_servers.bat      # Easy startup script
```

### 🎉 Success Indicators

When running correctly, you should see:
- ✅ Backend: "Running on http://127.0.0.1:5000"
- ✅ Frontend: "Local: http://localhost:5173"
- ✅ No red error messages in terminals
- ✅ Web pages load successfully

### 🆘 Need Help?

If issues persist:
1. Check all API keys in `.env`
2. Verify Python/Node versions
3. Ensure internet connectivity
4. Check console logs for specific errors

**The project WILL RUN successfully with proper setup!** 🚀