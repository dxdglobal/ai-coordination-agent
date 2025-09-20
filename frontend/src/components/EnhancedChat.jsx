import React, { useState, useEffect, useRef } from 'react';
import RLFeedback from './RLFeedback';
import './EnhancedChat.css';

const EnhancedChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showFeedback, setShowFeedback] = useState({});
  const [rlEnabled, setRlEnabled] = useState(true);
  const [strategyPreference, setStrategyPreference] = useState('auto');
  const [analytics, setAnalytics] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load RL analytics on component mount
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:5001/ai/rl/analytics');
      const data = await response.json();
      if (data.success) {
        setAnalytics(data.analytics);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const generateConversationId = () => {
    return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    const conversationId = generateConversationId();
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const endpoint = rlEnabled ? '/ai/rl/chat' : '/ai/chat';
      const payload = {
        message: inputMessage,
        conversation_id: conversationId,
        ...(rlEnabled && strategyPreference !== 'auto' && { preferred_strategy: strategyPreference })
      };

      const response = await fetch(`http://localhost:5001${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (data.success) {
        const aiMessage = {
          id: Date.now() + 1,
          text: data.response,
          sender: 'ai',
          timestamp: new Date().toISOString(),
          conversationId: conversationId,
          strategyUsed: data.strategy_used,
          confidence: data.confidence,
          responseTime: data.response_time
        };

        setMessages(prev => [...prev, aiMessage]);
        
        // Show feedback option for RL-enabled responses
        if (rlEnabled) {
          setShowFeedback(prev => ({
            ...prev,
            [aiMessage.id]: true
          }));
        }
      } else {
        console.error('Chat error:', data.error);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedbackSent = (messageId, result) => {
    setShowFeedback(prev => ({
      ...prev,
      [messageId]: false
    }));
    
    // Reload analytics after feedback
    loadAnalytics();
    
    console.log('Feedback processed:', result);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const optimizeStrategies = async () => {
    try {
      const response = await fetch('http://localhost:5001/ai/rl/optimize', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        alert('Strategy optimization completed!');
        loadAnalytics();
      }
    } catch (error) {
      console.error('Error optimizing strategies:', error);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="enhanced-chat-container">
      <div className="chat-header">
        <h2>AI Coordination Agent with Reinforcement Learning</h2>
        
        <div className="chat-controls">
          <div className="rl-toggle">
            <label>
              <input
                type="checkbox"
                checked={rlEnabled}
                onChange={(e) => setRlEnabled(e.target.checked)}
              />
              Enable RL Mode
            </label>
          </div>

          {rlEnabled && (
            <div className="strategy-selector">
              <label htmlFor="strategy">Strategy:</label>
              <select
                id="strategy"
                value={strategyPreference}
                onChange={(e) => setStrategyPreference(e.target.value)}
              >
                <option value="auto">Auto-Select</option>
                <option value="direct_answer">Direct Answer</option>
                <option value="clarifying_question">Ask Questions</option>
                <option value="step_by_step_guide">Step-by-Step</option>
                <option value="suggestion_with_alternatives">Suggestions</option>
                <option value="empathetic_response">Empathetic</option>
              </select>
            </div>
          )}

          <button 
            className="optimize-btn"
            onClick={optimizeStrategies}
            disabled={!rlEnabled}
          >
            Optimize Strategies
          </button>
        </div>

        {analytics && rlEnabled && (
          <div className="analytics-summary">
            <span>Total Conversations: {analytics.total_conversations}</span>
            <span>Avg Rating: {analytics.average_rating?.toFixed(2) || 'N/A'}</span>
            <span>Completion Rate: {(analytics.completion_rate * 100)?.toFixed(1)}%</span>
          </div>
        )}
      </div>

      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender}`}>
            <div className="message-content">
              <div className="message-text">{message.text}</div>
              <div className="message-meta">
                <span className="timestamp">{formatTimestamp(message.timestamp)}</span>
                {message.strategyUsed && (
                  <span className="strategy-badge">
                    Strategy: {message.strategyUsed}
                  </span>
                )}
                {message.confidence && (
                  <span className="confidence-badge">
                    Confidence: {(message.confidence * 100).toFixed(0)}%
                  </span>
                )}
                {message.responseTime && (
                  <span className="time-badge">
                    {message.responseTime.toFixed(2)}s
                  </span>
                )}
              </div>
            </div>
            
            {message.sender === 'ai' && showFeedback[message.id] && rlEnabled && (
              <RLFeedback
                conversationId={message.conversationId}
                strategyUsed={message.strategyUsed}
                onFeedbackSent={(result) => handleFeedbackSent(message.id, result)}
              />
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="message ai loading">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <div className="input-container">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            rows="1"
            disabled={isLoading}
          />
          <button 
            onClick={sendMessage} 
            disabled={isLoading || !inputMessage.trim()}
            className="send-button"
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
        
        {rlEnabled && (
          <div className="rl-info-bar">
            🧠 Reinforcement Learning Active - Your feedback helps me improve!
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedChat;