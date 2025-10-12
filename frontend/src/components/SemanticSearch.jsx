import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, TextField, IconButton, Paper, Typography, Chip, CircularProgress, 
  Tooltip 
} from '@mui/material';
import { Send as SendIcon, Clear as ClearIcon, Psychology as PsychologyIcon } from '@mui/icons-material';

// Helper function to render task lists for all task types
const renderTaskList = (tasks, messageContent, taskType) => {
  if (!tasks || !Array.isArray(tasks) || tasks.length === 0) return null;

  // Check if it's a full list request
  const isFullListQuery = messageContent && (
    messageContent.toLowerCase().includes(`complete ${taskType} tasks list`) ||
    messageContent.toLowerCase().includes('showing all') ||
    messageContent.toLowerCase().includes('full list') ||
    messageContent.toLowerCase().includes(`all ${taskType}`)
  );
  
  const maxTasksToShow = isFullListQuery ? tasks.length : Math.min(20, tasks.length);

  // Get appropriate icon and date info based on task type
  const getTaskInfo = (task, type) => {
    switch (type) {
      case 'overdue':
        return {
          icon: '📅',
          dateInfo: `${task.days_overdue || 0} days overdue • Due: ${task.duedate || 'Unknown'}`,
          dateColor: '#d32f2f'
        };
      case 'completed':
        return {
          icon: '✅',
          dateInfo: `Completed: ${task.datefinished || 'Unknown'} • Duration: ${task.completion_days || 0} days`,
          dateColor: '#2e7d32'
        };
      case 'inprogress':
        return {
          icon: '🔄',
          dateInfo: task.days_until_due !== null 
            ? (task.days_until_due >= 0 
              ? `Due in ${task.days_until_due} days • Due: ${task.duedate || 'Unknown'}`
              : `${Math.abs(task.days_until_due)} days overdue • Due: ${task.duedate || 'Unknown'}`)
            : `In Progress • Due: ${task.duedate || 'No due date'}`,
          dateColor: task.days_until_due < 0 ? '#d32f2f' : '#1565c0'
        };
      default:
        return {
          icon: '📋',
          dateInfo: `Status: ${task.status_name || 'Unknown'}`,
          dateColor: '#666'
        };
    }
  };

  return (
    <>
      {tasks.slice(0, maxTasksToShow).map((task, index) => {
        const taskInfo = getTaskInfo(task, taskType);
        return (
          <Box key={task.task_id || index} sx={{ mb: 1, p: 1, backgroundColor: 'white', borderRadius: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              {index + 1}. {task.task_name || 'Unnamed Task'}
            </Typography>
            <Typography variant="caption" sx={{ color: taskInfo.dateColor }}>
              {taskInfo.icon} {taskInfo.dateInfo}
            </Typography>
            <br />
            <Typography variant="caption" sx={{ color: '#666' }}>
              {task.status_name || 'Unknown Status'} • {task.priority_name || 'Unknown Priority'} Priority
              {task.project_name && ` • ${task.project_name}`}
            </Typography>
          </Box>
        );
      })}
      
      {!isFullListQuery && tasks.length > maxTasksToShow && (
        <Typography variant="caption" sx={{ color: '#666', fontStyle: 'italic' }}>
          ... and {tasks.length - maxTasksToShow} more {taskType} tasks (ask for "full list of {taskType} tasks" to see all)
        </Typography>
      )}
      
      {isFullListQuery && (
        <Typography variant="caption" sx={{ color: '#2e7d32', fontStyle: 'italic', fontWeight: 'bold' }}>
          ✅ Showing all {tasks.length} {taskType} tasks above
        </Typography>
      )}
    </>
  );
};

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
      // Use new RAG System endpoint
      const endpoint = 'http://127.0.0.1:5001/ai/query';
      
      console.log(`🤖 SENDING TO RAG SYSTEM: "${currentInput}"`);
      
      const response = await fetch(endpoint, {
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
          contextualInfo = `� Search completed`;
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
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ textAlign: 'center', mt: 4 }}
          >
            AI-powered semantic search for intelligent task discovery and analysis. 
            Ask about overdue, completed, or in-progress tasks for any employee!
          </Typography>
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
              
              {/* Task Data Display - Supports all task types */}
              {message.type === 'assistant' && (
                <>
                  {/* Overdue Tasks Display */}
                  {message.intentType === 'overdue_tasks' && 
                   message.overdue_tasks && 
                   Array.isArray(message.overdue_tasks) && 
                   message.overdue_tasks.length > 0 && (
                    <Box sx={{ mt: 2, p: 2, backgroundColor: '#fff3e0', borderRadius: 1, border: '1px solid #ffcc02' }}>
                      <Typography variant="h6" sx={{ color: '#e65100', mb: 1 }}>
                        🚨 Overdue Tasks Details ({message.overdue_tasks.length} total)
                      </Typography>
                      {renderTaskList(message.overdue_tasks, message.content, 'overdue')}
                    </Box>
                  )}

                  {/* Completed Tasks Display */}
                  {(message.intentType === 'completed_tasks' || 
                    (message.completed_tasks && message.completed_tasks.length > 0)) && (
                    <Box sx={{ mt: 2, p: 2, backgroundColor: '#e8f5e8', borderRadius: 1, border: '1px solid #4caf50' }}>
                      <Typography variant="h6" sx={{ color: '#2e7d32', mb: 1 }}>
                        ✅ Completed Tasks Details ({message.completed_tasks?.length || 0} total)
                      </Typography>
                      {message.completed_tasks && renderTaskList(message.completed_tasks, message.content, 'completed')}
                    </Box>
                  )}

                  {/* In-Progress Tasks Display */}
                  {(message.intentType === 'inprogress_tasks' || 
                    (message.inprogress_tasks && message.inprogress_tasks.length > 0)) && (
                    <Box sx={{ mt: 2, p: 2, backgroundColor: '#e3f2fd', borderRadius: 1, border: '1px solid #2196f3' }}>
                      <Typography variant="h6" sx={{ color: '#1565c0', mb: 1 }}>
                        🔄 In-Progress Tasks Details ({message.inprogress_tasks?.length || 0} total)
                      </Typography>
                      {message.inprogress_tasks && renderTaskList(message.inprogress_tasks, message.content, 'inprogress')}
                    </Box>
                  )}
                </>
              )}
              
              {/* Enhanced NLP Metadata */}
              {message.type === 'assistant' && (
                <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {message.contextualInfo && (
                    <Chip
                      label={message.contextualInfo}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  )}
                  
                  {message.employeeDetected && (
                    <Chip
                      label={`👤 ${message.employeeDetected}`}
                      size="small"
                      color="secondary"
                      variant="outlined"
                    />
                  )}
                  
                  {message.intentConfidence && message.intentConfidence > 0.7 && (
                    <Chip
                      label={`🎯 ${Math.round(message.intentConfidence * 100)}% confidence`}
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  )}
                  
                  {message.contextTasks && message.contextTasks > 0 && (
                    <Chip
                      label={`📊 ${message.contextTasks} context tasks`}
                      size="small"
                      color="info"
                      variant="outlined"
                    />
                  )}
                </Box>
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
          placeholder="Try: 'Hamza overdue tasks', 'Hamza completed tasks', 'Hamza in-progress tasks', or 'Full list of Hamza completed tasks'"
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