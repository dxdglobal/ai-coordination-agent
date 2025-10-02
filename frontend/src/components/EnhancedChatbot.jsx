import React, { useState, useEffect, useRef } from 'react';
import './EnhancedChatbot.css';

const EnhancedChatbot = () => {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const [lastResponse, setLastResponse] = useState(null);
    const messagesEndRef = useRef(null);

    // Initialize session
    useEffect(() => {
        const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        setSessionId(newSessionId);
        checkConnection();
    }, []);

    // Auto scroll to bottom
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const checkConnection = async () => {
        try {
            const response = await fetch('http://127.0.0.1:5001/health');
            if (response.ok) {
                setConnectionStatus('connected');
                addSystemMessage('🚀 Enhanced AI Chatbot System is online and ready!');
            } else {
                setConnectionStatus('error');
                addSystemMessage('⚠️ Connection issues detected. Please check if the backend is running.');
            }
        } catch (error) {
            setConnectionStatus('error');
            addSystemMessage('❌ Cannot connect to backend. Please start the Enhanced Chatbot System on port 5001.');
        }
    };

    const addSystemMessage = (content) => {
        const systemMessage = {
            id: Date.now(),
            type: 'system',
            content,
            timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, systemMessage]);
    };

    const sendMessage = async () => {
        if (!inputMessage.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: inputMessage,
            timestamp: new Date().toLocaleTimeString()
        };

        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            const response = await fetch('http://127.0.0.1:5001/ai/enhanced_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: inputMessage,
                    session_id: sessionId
                })
            });

            const data = await response.json();

            if (data.success) {
                const assistantMessage = {
                    id: data.prompt_id || Date.now(),
                    type: 'assistant',
                    content: data.response,
                    timestamp: new Date().toLocaleTimeString(),
                    metadata: {
                        processing_time: data.processing_time_ms,
                        records_found: data.records_found,
                        tables_scanned: data.tables_scanned,
                        analysis: data.analysis,
                        conversation_length: data.conversation_length
                    }
                };

                setMessages(prev => [...prev, assistantMessage]);
                setLastResponse(assistantMessage);

                // Auto-suggest follow-up questions
                if (data.analysis && data.analysis.intent) {
                    addSuggestedQuestions(data.analysis.intent, data.records_found);
                }
            } else {
                const errorMessage = {
                    id: Date.now(),
                    type: 'error',
                    content: `Error: ${data.error}`,
                    timestamp: new Date().toLocaleTimeString()
                };
                setMessages(prev => [...prev, errorMessage]);
            }
        } catch (error) {
            const errorMessage = {
                id: Date.now(),
                type: 'error',
                content: `Connection error: ${error.message}`,
                timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, errorMessage]);
        }

        setInputMessage('');
        setIsLoading(false);
    };

    const addSuggestedQuestions = (intent, recordsFound) => {
        const suggestions = {
            'employee_query': [
                'Show active employees only',
                'Who is the manager of this department?',
                'Show employee contact details'
            ],
            'project_query': [
                'Show project deadlines',
                'Which projects are overdue?',
                'Show project team members'
            ],
            'task_query': [
                'Show high priority tasks',
                'What tasks are due today?',
                'Show completed tasks this week'
            ]
        };

        const relevantSuggestions = suggestions[intent] || [
            'Tell me more details',
            'Show me related information',
            'What else can you find?'
        ];

        setTimeout(() => {
            const suggestionMessage = {
                id: Date.now(),
                type: 'suggestions',
                content: 'Here are some follow-up questions you might ask:',
                suggestions: relevantSuggestions,
                timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, suggestionMessage]);
        }, 1000);
    };

    const sendFeedback = async (messageId, feedback, rating = 3) => {
        try {
            await fetch('http://127.0.0.1:5001/ai/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message_id: messageId,
                    feedback: feedback,
                    rating: rating
                })
            });
            
            addSystemMessage(`✅ Feedback recorded: ${feedback} (${rating}/5)`);
        } catch (error) {
            addSystemMessage(`❌ Failed to record feedback: ${error.message}`);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setInputMessage(suggestion);
    };

    const formatMessage = (content) => {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/📊|📝|👤|👥|🔍|✅|🔄|⭕|🔴|🟡|🟢|📧|🏢|📱|📅/g, '<span class="emoji">$&</span>');
    };

    return (
        <div className="enhanced-chatbot">
            <div className="chatbot-header">
                <div className="header-title">
                    <h2>🤖 Enhanced AI Chatbot</h2>
                    <div className={`connection-status ${connectionStatus}`}>
                        <span className="status-dot"></span>
                        {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
                    </div>
                </div>
                <div className="header-info">
                    <span>Session: {sessionId?.substr(-8)}</span>
                    <span>Messages: {messages.filter(m => m.type === 'user' || m.type === 'assistant').length}</span>
                </div>
            </div>

            <div className="messages-container">
                {messages.map((message) => (
                    <div key={message.id} className={`message ${message.type}-message`}>
                        <div className="message-content">
                            {message.type === 'suggestions' ? (
                                <div className="suggestions-container">
                                    <p>{message.content}</p>
                                    <div className="suggestions">
                                        {message.suggestions.map((suggestion, index) => (
                                            <button
                                                key={index}
                                                className="suggestion-button"
                                                onClick={() => handleSuggestionClick(suggestion)}
                                            >
                                                {suggestion}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }} />
                            )}
                        </div>
                        
                        <div className="message-footer">
                            <span className="timestamp">{message.timestamp}</span>
                            
                            {message.metadata && (
                                <div className="metadata">
                                    <span title="Processing Time">⏱️ {message.metadata.processing_time}ms</span>
                                    <span title="Records Found">📊 {message.metadata.records_found} records</span>
                                    <span title="Tables Scanned">🗃️ {message.metadata.tables_scanned.length} tables</span>
                                    <span title="Conversation Length">💬 {message.metadata.conversation_length}</span>
                                </div>
                            )}

                            {message.type === 'assistant' && (
                                <div className="feedback-buttons">
                                    <button 
                                        className="feedback-btn positive"
                                        onClick={() => sendFeedback(message.id, 'positive', 5)}
                                        title="This was helpful"
                                    >
                                        👍
                                    </button>
                                    <button 
                                        className="feedback-btn negative"
                                        onClick={() => sendFeedback(message.id, 'negative', 2)}
                                        title="This wasn't helpful"
                                    >
                                        👎
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                
                {isLoading && (
                    <div className="message assistant-message">
                        <div className="message-content">
                            <div className="typing-indicator">
                                <div className="typing-dot"></div>
                                <div className="typing-dot"></div>
                                <div className="typing-dot"></div>
                                <span>Analyzing with OpenAI and scanning database...</span>
                            </div>
                        </div>
                    </div>
                )}
                
                <div ref={messagesEndRef} />
            </div>

            <div className="input-container">
                <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about employees, projects, tasks, or business data..."
                    className="message-input"
                    disabled={isLoading || connectionStatus !== 'connected'}
                />
                <button
                    onClick={sendMessage}
                    disabled={isLoading || !inputMessage.trim() || connectionStatus !== 'connected'}
                    className="send-button"
                >
                    {isLoading ? '🔄' : '🚀'}
                </button>
            </div>

            <div className="capabilities-footer">
                <div className="capabilities">
                    <span>✨ Features:</span>
                    <span>🧠 Advanced NLP</span>
                    <span>💾 Conversation History</span>
                    <span>🔍 Multi-table Search</span>
                    <span>⭐ Smart Feedback</span>
                    <span>📊 Real-time Analytics</span>
                </div>
            </div>
        </div>
    );
};

export default EnhancedChatbot;