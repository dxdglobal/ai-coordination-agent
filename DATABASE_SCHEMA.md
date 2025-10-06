# Database Schema Documentation

## 🗄️ AI Coordination Agent Database Schema

### Entity Relationship Diagram (ERD)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     USERS       │    │    PROJECTS     │    │   EMPLOYEES     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ crm_user_id     │    │ name            │    │ name            │
│ email           │    │ description     │    │ email           │
│ name            │    │ status          │    │ department      │
│ role            │    │ start_date      │    │ position        │
│ preferences     │    │ end_date        │    │ manager_id (FK) │
│ ai_settings     │    │ deadline        │    │ is_active       │
│ last_login      │    │ created_at      │    │ created_at      │
│ is_active       │    │ updated_at      │    │ hire_date       │
│ created_at      │    └─────────────────┘    └─────────────────┘
│ updated_at      │           │                        │
└─────────────────┘           │                        │
         │                    │                        │
         │                    ▼                        │
         │          ┌─────────────────┐                │
         │          │     TASKS       │                │
         │          ├─────────────────┤                │
         │          │ id (PK)         │                │
         │          │ title           │◄───────────────┘
         │          │ description     │ assigned_to (FK)
         │          │ status          │
         │          │ priority        │
         │          │ project_id (FK) │
         │          │ start_time      │
         │          │ end_time        │
         │          │ estimated_hours │
         │          │ actual_hours    │
         │          │ created_at      │
         │          │ updated_at      │
         │          └─────────────────┘
         │                    │
         │                    ▼
         │          ┌─────────────────┐
         │          │    COMMENTS     │
         │          ├─────────────────┤
         │          │ id (PK)         │
         │          │ content         │
         │          │ author          │
         │          │ task_id (FK)    │
         │          │ created_at      │
         │          └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│ NOTIFICATIONS   │    │MEMORY_EMBEDDINGS│
├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │
│ user_id (FK)    │    │ content         │
│ title           │    │ content_type    │
│ message         │    │ embedding_vector│
│ type            │    │ embedding_model │
│ read            │    │ source_id       │
│ action_url      │    │ source_table    │
│ metadata        │    │ keywords        │
│ task_id (FK)    │    │ summary         │
│ project_id (FK) │    │ access_count    │
│ created_at      │    │ last_accessed   │
│ read_at         │    │ created_at      │
└─────────────────┘    │ updated_at      │
                       └─────────────────┘
```

### Additional Supporting Tables

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│CONVERSATION_    │    │PROMPT_TEMPLATES │    │   AI_ACTIONS    │
│   HISTORY       │    ├─────────────────┤    ├─────────────────┤
├─────────────────┤    │ id (PK)         │    │ id (PK)         │
│ id (PK)         │    │ name            │    │ prompt          │
│ session_id      │    │ category        │    │ action_type     │
│ user_query      │    │ template        │    │ target_type     │
│ ai_response     │    │ usage_count     │    │ target_id       │
│ query_type      │    │ success_rate    │    │ action_data     │
│ response_time_ms│    │ last_used       │    │ executed        │
│ confidence_score│    │ created_at      │    │ result          │
│ data_sources    │    └─────────────────┘    │ created_at      │
│ user_satisfaction│                          │ executed_at     │
│ created_at      │                          └─────────────────┘
└─────────────────┘
```

## 📊 Table Specifications

### Core Tables

#### 1. USERS
**Purpose**: User management with CRM integration
**Key Features**:
- CRM synchronization via `crm_user_id`
- Role-based access control
- AI interaction preferences
- Activity tracking

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    crm_user_id INTEGER UNIQUE,
    email VARCHAR(120) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    preferences JSONB,
    ai_settings JSONB,
    last_login TIMESTAMP,
    last_activity TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. PROJECTS
**Purpose**: Project organization and tracking
**Key Features**:
- Status workflow management
- Timeline tracking
- Task aggregation

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status project_status DEFAULT 'todo',
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. TASKS
**Purpose**: Task management with rich metadata
**Key Features**:
- Priority and status tracking
- Time estimation and tracking
- Employee assignment
- Project association

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status task_status DEFAULT 'todo',
    priority task_priority DEFAULT 'medium',
    project_id INTEGER REFERENCES projects(id),
    assigned_to INTEGER REFERENCES employees(id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2),
    assignee VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. COMMENTS
**Purpose**: Task discussion and collaboration
**Key Features**:
- Rich text content
- Author tracking
- Temporal ordering

```sql
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    author VARCHAR(100),
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. NOTIFICATIONS
**Purpose**: User notification system
**Key Features**:
- Multi-type notifications
- Read status tracking
- Action links
- Context association

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500),
    metadata JSONB,
    task_id INTEGER REFERENCES tasks(id),
    project_id INTEGER REFERENCES projects(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);
```

#### 6. MEMORY_EMBEDDINGS
**Purpose**: Vector storage for AI semantic search
**Key Features**:
- Vector embeddings storage
- Content type classification
- Performance tracking
- Source traceability

```sql
CREATE TABLE memory_embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    embedding_vector JSONB,
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    source_id VARCHAR(100),
    source_table VARCHAR(50),
    keywords JSONB,
    summary TEXT,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    similarity_threshold DECIMAL(3,2) DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Supporting Tables

#### 7. EMPLOYEES
**Purpose**: Staff management and hierarchy
**Key Features**:
- Hierarchical management structure
- HR integration
- Task assignment capabilities

#### 8. CONVERSATION_HISTORY
**Purpose**: AI interaction tracking
**Key Features**:
- Session management
- Performance analytics
- Learning data collection

#### 9. PROMPT_TEMPLATES
**Purpose**: Reusable AI prompts
**Key Features**:
- Template management
- Usage analytics
- Success tracking

## 🔗 Relationships

### Primary Relationships
1. **Users → Notifications** (1:N)
   - Users receive multiple notifications
   - Cascade delete on user removal

2. **Projects → Tasks** (1:N)
   - Projects contain multiple tasks
   - Cascade delete maintains integrity

3. **Tasks → Comments** (1:N)
   - Tasks have multiple comments
   - Comments belong to specific tasks

4. **Employees → Tasks** (1:N)
   - Employees can be assigned multiple tasks
   - Optional assignment (nullable FK)

5. **Users ↔ CRM Users** (1:1)
   - Bi-directional synchronization
   - Optional CRM integration

### Secondary Relationships
1. **Notifications → Tasks/Projects** (N:1)
   - Context-aware notifications
   - Optional associations

2. **Memory Embeddings → Source Tables** (N:1)
   - Flexible source tracking
   - Content type categorization

## 📈 Indexing Strategy

### Performance Indexes
```sql
-- Frequently queried columns
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_comments_task_id ON comments(task_id);
CREATE INDEX idx_embeddings_content_type ON memory_embeddings(content_type);
CREATE INDEX idx_embeddings_source ON memory_embeddings(source_table, source_id);

-- Composite indexes for common queries
CREATE INDEX idx_tasks_status_project ON tasks(status, project_id);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, read);

-- Time-based queries
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_projects_deadline ON projects(deadline);
```

### Vector Indexes (PostgreSQL with pgvector)
```sql
-- Vector similarity search optimization
CREATE INDEX ON memory_embeddings USING ivfflat (embedding_vector) WITH (lists = 100);
```

## 🔄 Data Flow

### CRM Synchronization Flow
```
CRM Database (MySQL)     ←→     AI Database (PostgreSQL)
├── tblstaff            ←→     ├── users
├── tblprojects         ←→     ├── projects  
└── tbltasks            ←→     └── tasks
```

### Vector Embedding Flow
```
Content Input → OpenAI API → Embeddings → ChromaDB/PostgreSQL
     ↓              ↓            ↓             ↓
User Query  → Text Processing → Vector Search → Results
```

### Notification Flow
```
System Event → Notification Creation → User Delivery → Read Status
     ↓                ↓                     ↓            ↓
Task Update    → Database Insert     → API Response → UI Update
```

## 🔐 Security Considerations

### Data Protection
1. **Sensitive Fields**: Encrypted storage for passwords and tokens
2. **Access Control**: Role-based permissions
3. **Audit Trail**: Change tracking for critical tables
4. **Data Retention**: Configurable cleanup policies

### Connection Security
1. **SSL/TLS**: Encrypted database connections
2. **Credential Management**: Environment-based secrets
3. **Network Security**: VPN for CRM access
4. **API Security**: JWT authentication

## 📊 Monitoring & Maintenance

### Health Checks
1. **Connection Status**: Database connectivity monitoring
2. **Table Counts**: Data growth tracking
3. **Index Performance**: Query optimization monitoring
4. **Sync Status**: CRM synchronization health

### Maintenance Tasks
1. **Vacuum/Analyze**: PostgreSQL maintenance
2. **Index Rebuilding**: Performance optimization
3. **Data Archival**: Historical data management
4. **Backup Verification**: Recovery testing

---

**Database Schema Version**: 1.0
**Last Updated**: October 5, 2025
**Task 1.1 Status**: ✅ COMPLETE