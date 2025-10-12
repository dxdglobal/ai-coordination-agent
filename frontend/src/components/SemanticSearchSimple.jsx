import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, IconButton, Paper, Typography, Chip, CircularProgress } from '@mui/material';
import { Send as SendIcon, Clear as ClearIcon } from '@mui/icons-material';

const SemanticSearch = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const currentInput = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: currentInput,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // RAG System: Use new task management query endpoint
      console.log(`🤖 SENDING TO RAG SYSTEM: "${currentInput}"`);
      
      const response = await fetch('http://127.0.0.1:5001/ai/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: currentInput
        }),
      });

      const data = await response.json();
      
      // Handle RAG system response
      if (data.success) {
        let content = '';
        let contextualInfo = '';
        
        // Check if it's a RAG response with AI-generated content
        if (data.ai_response) {
          const aiResponse = data.ai_response;
          
          if (aiResponse.response_type === 'task_list') {
            content = `📋 **Task List for ${aiResponse.employee}**\n\n`;
            content += `Found ${aiResponse.total_count} tasks:\n\n`;
            
            aiResponse.tasks.forEach((task, index) => {
              content += `${index + 1}. **${task.name}**\n`;
              content += `   • Status: ${task.status}\n`;
              content += `   • Priority: ${task.priority}\n`;
              content += `   • Due: ${new Date(task.due_date).toLocaleDateString()}\n`;
              content += `   • Project: ${task.project}\n\n`;
            });
            
            contextualInfo = `🎯 Retrieved from CRM database`;
            
          } else if (aiResponse.response_type === 'task_summary') {
            content = `📊 **Task Summary for ${aiResponse.employee}**\n\n`;
            content += `${aiResponse.ai_summary}\n\n`;
            
            if (aiResponse.key_insights && aiResponse.key_insights.length > 0) {
              content += `**Key Insights:**\n`;
              aiResponse.key_insights.forEach(insight => {
                content += `• ${insight}\n`;
              });
            }
            
            if (aiResponse.task_breakdown) {
              content += `\n**Task Breakdown:**\n`;
              content += `• By Status: ${Object.entries(aiResponse.task_breakdown.by_status).map(([k,v]) => `${k}(${v})`).join(', ')}\n`;
              content += `• By Priority: ${Object.entries(aiResponse.task_breakdown.by_priority).map(([k,v]) => `${k}(${v})`).join(', ')}\n`;
            }
            
            contextualInfo = `🤖 AI-powered analysis using GPT-4o`;
            
          } else {
            content = aiResponse.message || data.response || "I've processed your request.";
            contextualInfo = `🤖 RAG system response`;
          }
        } else {
          content = data.response || data.message || "I've processed your request.";
          contextualInfo = `🔍 Search completed`;
        }
        
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: content,
          timestamp: new Date(),
          isAIQuery: true,
          contextualInfo: contextualInfo
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(data.error || 'RAG query failed');
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `I apologize, but I encountered an error: ${error.message}. Please try again.`,
        timestamp: new Date(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
      {/* Messages Container */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          mb: 2,
          p: 1,
          border: '1px solid #e0e0e0',
          borderRadius: 2,
          backgroundColor: '#f8f9fa',
        }}
      >
        {messages.length === 0 && (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
              🤖 Task Management RAG System
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              AI-powered task analysis with NLP intent detection and GPT-4o integration
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontWeight: 'bold' }}>
              Try these example queries:
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxWidth: 400, mx: 'auto' }}>
              {[
                "Show all tasks for Çağla Şahar",
                "Summarize John Smith's current workload", 
                "List urgent tasks for Maria Garcia",
                "Analyze project deadlines for next week"
              ].map((example, index) => (
                <Chip
                  key={index}
                  label={example}
                  variant="outlined"
                  size="small"
                  clickable
                  onClick={() => {
                    setInput(example);
                    inputRef.current?.focus();
                  }}
                  sx={{ 
                    cursor: 'pointer',
                    '&:hover': { backgroundColor: '#f0f0f0' }
                  }}
                />
              ))}
            </Box>
          </Box>
        )}

        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              mb: 2,
              display: 'flex',
              justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <Paper
              elevation={1}
              sx={{
                p: 2,
                maxWidth: '80%',
                backgroundColor: message.type === 'user' ? '#1976d2' : '#ffffff',
                color: message.type === 'user' ? 'white' : 'black',
                borderRadius: 2,
                '& pre': {
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'monospace',
                  fontSize: '0.9em',
                  backgroundColor: '#f5f5f5',
                  padding: '8px',
                  borderRadius: '4px',
                  overflow: 'auto',
                },
              }}
            >
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {message.content}
              </Typography>
              
              {message.contextualInfo && (
                <Chip
                  label={message.contextualInfo}
                  size="small"
                  sx={{ mt: 1 }}
                  color="primary"
                  variant="outlined"
                />
              )}
            </Paper>
          </Box>
        ))}

        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Paper elevation={1} sx={{ p: 2, borderRadius: 2 }}>
              <CircularProgress size={20} sx={{ mr: 1 }} />
              <Typography variant="body2" component="span">
                AI is analyzing your request...
              </Typography>
            </Paper>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        <TextField
          ref={inputRef}
          multiline
          maxRows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about employee tasks, request summaries, or analyze workloads (e.g., 'Show all tasks for John' or 'Summarize Maria's work')..."
          variant="outlined"
          size="small"
          sx={{ flex: 1 }}
          disabled={isLoading}
        />
        
        <IconButton
          onClick={handleSendMessage}
          disabled={!input.trim() || isLoading}
          color="primary"
          sx={{ mb: 0.5 }}
        >
          <SendIcon />
        </IconButton>
        
        <IconButton
          onClick={clearChat}
          disabled={messages.length === 0}
          color="secondary"
          sx={{ mb: 0.5 }}
        >
          <ClearIcon />
        </IconButton>
      </Box>
    </Box>
  );
};

export default SemanticSearch;