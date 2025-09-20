import React, { useState, useEffect } from 'react';
import './RLFeedback.css';

const RLFeedback = ({ conversationId, onFeedbackSent, strategyUsed }) => {
  const [feedback, setFeedback] = useState({
    user_rating: 0,
    task_completed: false,
    response_helpful: false,
    response_clear: false,
    would_recommend: false,
    comments: ''
  });
  
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleRatingClick = (rating) => {
    setFeedback(prev => ({ ...prev, user_rating: rating }));
  };

  const handleCheckboxChange = (field, value) => {
    setFeedback(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmitFeedback = async () => {
    if (!conversationId) return;
    
    setIsLoading(true);
    
    try {
      const response = await fetch('http://localhost:5001/ai/rl/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          feedback: {
            ...feedback,
            strategy_used: strategyUsed,
            timestamp: new Date().toISOString()
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        setIsSubmitted(true);
        if (onFeedbackSent) {
          onFeedbackSent(result);
        }
      } else {
        console.error('Feedback submission failed:', result.error);
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="rl-feedback-container submitted">
        <div className="feedback-success">
          <span className="success-icon">✅</span>
          <p>Thank you for your feedback! This helps me learn and improve.</p>
          <small>Your input contributes to the AI's reinforcement learning system.</small>
        </div>
      </div>
    );
  }

  return (
    <div className="rl-feedback-container">
      <div className="feedback-header">
        <h4>Help me learn and improve</h4>
        <p>Your feedback trains the AI using reinforcement learning</p>
        {strategyUsed && (
          <small className="strategy-info">Strategy used: {strategyUsed}</small>
        )}
      </div>

      <div className="feedback-section">
        <div className="rating-section">
          <label>How would you rate this response?</label>
          <div className="rating-buttons">
            <button
              className={`rating-btn ${feedback.user_rating === -1 ? 'selected negative' : ''}`}
              onClick={() => handleRatingClick(-1)}
              title="Poor response"
            >
              👎
            </button>
            <button
              className={`rating-btn ${feedback.user_rating === 0 ? 'selected neutral' : ''}`}
              onClick={() => handleRatingClick(0)}
              title="Okay response"
            >
              😐
            </button>
            <button
              className={`rating-btn ${feedback.user_rating === 1 ? 'selected positive' : ''}`}
              onClick={() => handleRatingClick(1)}
              title="Great response"
            >
              👍
            </button>
          </div>
        </div>

        <div className="quick-feedback">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={feedback.response_helpful}
              onChange={(e) => handleCheckboxChange('response_helpful', e.target.checked)}
            />
            This response was helpful
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={feedback.task_completed}
              onChange={(e) => handleCheckboxChange('task_completed', e.target.checked)}
            />
            This helped me complete my task
          </label>
        </div>

        <div className="advanced-toggle">
          <button
            className="toggle-btn"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Feedback
          </button>
        </div>

        {showAdvanced && (
          <div className="advanced-feedback">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={feedback.response_clear}
                onChange={(e) => handleCheckboxChange('response_clear', e.target.checked)}
              />
              The response was clear and easy to understand
            </label>
            
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={feedback.would_recommend}
                onChange={(e) => handleCheckboxChange('would_recommend', e.target.checked)}
              />
              I would recommend this AI to others
            </label>

            <div className="comments-section">
              <label htmlFor="comments">Additional comments (optional):</label>
              <textarea
                id="comments"
                value={feedback.comments}
                onChange={(e) => setFeedback(prev => ({ ...prev, comments: e.target.value }))}
                placeholder="How can I improve my responses?"
                rows="3"
              />
            </div>
          </div>
        )}

        <div className="feedback-actions">
          <button
            className="submit-feedback-btn"
            onClick={handleSubmitFeedback}
            disabled={isLoading || feedback.user_rating === 0}
          >
            {isLoading ? 'Training AI...' : 'Submit Feedback'}
          </button>
        </div>
      </div>

      <div className="rl-info">
        <small>
          🧠 This feedback is used for reinforcement learning to improve future responses.
          Your input helps the AI learn what works best!
        </small>
      </div>
    </div>
  );
};

export default RLFeedback;