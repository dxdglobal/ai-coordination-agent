# 🚀 Vector Database Setup Instructions

## Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
# Navigate to backend directory
cd backend

# Install vector database dependencies
pip install chromadb==0.4.18 numpy==1.24.3 sentence-transformers==2.2.2

# Or install all requirements
pip install -r requirements.txt
```

### 2. Initialize Vector Database
```bash
# Start your backend server
python app.py

# Then call the initialization endpoint
curl -X POST http://localhost:5000/ai/vector/initialize
```

### 3. Test Vector Database
```bash
# Test storing business knowledge
curl -X POST http://localhost:5000/ai/vector/business-knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Project management best practices: Set clear goals, communicate regularly, track progress",
    "topic": "project_management",
    "source": "best_practices_guide"
  }'

# Test searching knowledge
curl -X POST http://localhost:5000/ai/vector/search-knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to manage projects effectively?",
    "n_results": 3
  }'

# Get vector database statistics
curl http://localhost:5000/ai/vector/stats
```

## 🎯 What Vector Database Adds

### Enhanced Chat Features:
- **Semantic Context**: AI finds relevant past conversations
- **Smart Prompts**: Suggests effective prompts based on similarity
- **Business Knowledge**: Searches company processes and best practices
- **Learning**: Improves responses based on successful interactions

### New API Endpoints:
- `POST /ai/smart_chat` - Enhanced chat with vector context
- `POST /ai/vector/prompt-suggestions` - Get prompt suggestions
- `POST /ai/vector/business-knowledge` - Store business knowledge
- `POST /ai/vector/search-knowledge` - Semantic knowledge search
- `GET /ai/vector/stats` - Vector database statistics

### Frontend Integration:
Your Chat.jsx will automatically use vector context when calling `/ai/smart_chat`

## 🔧 Advanced Configuration

### Custom Embedding Models:
```python
# In vector_service.py, you can switch to different embedding models:

# Use sentence-transformers (free, local)
from chromadb.utils import embedding_functions
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Use OpenAI embeddings (requires API key, more accurate)
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-ada-002"
)
```

### Production Deployment:
```python
# For production, consider switching to Pinecone or Qdrant
# Update vector_service.py with production vector database

# Pinecone example:
import pinecone
pinecone.init(api_key="your-api-key", environment="your-env")
```

## 📊 Database Storage Locations

### Vector Data:
- **Local**: `./chroma_db/` directory (created automatically)
- **Contents**: Embeddings, metadata, indices

### Traditional Data:
- **MySQL**: Remote server (92.113.22.65)
- **Contents**: Business data, conversation metadata

## 🚦 Verification Steps

1. **Check Installation**:
   ```bash
   python -c "import chromadb; print('ChromaDB installed successfully')"
   ```

2. **Verify API**:
   ```bash
   curl http://localhost:5000/ai/vector/stats
   ```

3. **Test Enhanced Chat**:
   ```javascript
   // In your frontend
   fetch('http://localhost:5000/ai/smart_chat', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       message: "Help me prioritize my tasks",
       use_vector_context: true
     })
   })
   ```

## 🔍 Troubleshooting

### Common Issues:
1. **Import Error**: Make sure all dependencies are installed
2. **OpenAI API**: Ensure OPENAI_API_KEY is set in .env
3. **Storage**: Check write permissions for ./chroma_db/ directory
4. **Memory**: Vector operations require some RAM (adjust n_results if needed)

### Performance Tips:
- Start with local embeddings (sentence-transformers) for development
- Use OpenAI embeddings for better semantic understanding
- Limit n_results to 3-5 for faster responses
- Initialize business knowledge once, then query as needed