# Database Setup Instructions

## MySQL Database Configuration

Your AI Coordination Agent is now configured to use the following MySQL database:

- **Host**: 92.113.22.65
- **Database**: u906714182_sqlrrefdvdv
- **Username**: u906714182_sqlrrefdvdv
- **Password**: 3@6*t:lU
- **Port**: 3306

## Setup Steps

### 1. Install Dependencies

Make sure you're in the backend directory and install the required packages:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Verify Environment Configuration

The `.env` file has been updated with your database credentials. Verify it contains:

```
DATABASE_TYPE=mysql
DB_HOST=92.113.22.65
DB_USER=u906714182_sqlrrefdvdv
DB_PASSWORD=3@6*t:lU
DB_NAME=u906714182_sqlrrefdvdv
DB_PORT=3306
```

### 3. Initialize Database

Run the database initialization script to test connection and create tables:

```bash
python init_db.py
```

This script will:
- Test the database connection
- Create all necessary tables for the AI Coordination Agent
- Verify the setup was successful

### 4. Start the Backend Server

Once the database is initialized, start the Flask server:

```bash
python app.py
```

The server will start on `http://localhost:5000`

## Database Tables

The following tables will be created in your MySQL database:

1. **projects** - Store project information
2. **tasks** - Store task details and assignments
3. **comments** - Store task comments and discussions
4. **labels** - Store task labels and categories
5. **integrations** - Store integration history and data
6. **ai_actions** - Store AI-generated actions and suggestions

## Troubleshooting

### Connection Issues
- Verify the database server is accessible from your location
- Check if the credentials are correct
- Ensure the MySQL server allows connections from your IP

### Permission Issues
- Make sure the database user has CREATE, INSERT, UPDATE, DELETE permissions
- Verify the user can create tables in the specified database

### Dependency Issues
- If `mysql-connector-python` fails to install, try: `pip install mysql-connector-python==8.2.0`
- For Windows, you might need: `pip install mysql-connector-python --no-cache-dir`

## Testing the Setup

1. Run `python init_db.py` - should show "Database initialization completed successfully!"
2. Start the server with `python app.py`
3. Test the API endpoints:
   - GET `http://localhost:5000/api/projects` - should return empty array `[]`
   - GET `http://localhost:5000/api/tasks` - should return empty array `[]`

## Next Steps

Once the database is set up and the backend is running:

1. Start the frontend: `cd ../frontend && npm run dev`
2. Access the application at `http://localhost:5173`
3. Begin creating projects and tasks through the AI Coordination Agent interface

Your MySQL database is now configured and ready for production use!