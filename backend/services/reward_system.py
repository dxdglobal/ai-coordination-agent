# Reinforcement Learning Reward System for AI Agent
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from models.models import db, ConversationHistory
from sqlalchemy import func, desc
import logging

class AIRewardSystem:
    """
    Reinforcement Learning Reward System that learns from user interactions
    to improve AI responses through reward-based feedback
    """
    
    def __init__(self):
        self.reward_weights = {
            'user_satisfaction': 0.4,      # Direct user feedback (thumbs up/down)
            'response_time': 0.1,          # Faster responses get small rewards
            'task_completion': 0.3,        # Did the AI help complete a task?
            'conversation_length': 0.1,    # Engaging conversations
            'repeat_usage': 0.1           # User returns for more help
        }
        
        self.reward_history = []
        self.learning_rate = 0.01
        self.discount_factor = 0.95
        
    def calculate_reward(self, conversation_id: str, feedback_data: Dict[str, Any]) -> float:
        """
        Calculate reward based on multiple factors
        """
        try:
            conversation = ConversationHistory.query.get(conversation_id)
            if not conversation:
                return 0.0
            
            total_reward = 0.0
            reward_breakdown = {}
            
            # 1. User Satisfaction Reward (explicit feedback)
            user_rating = feedback_data.get('user_rating', 0)  # -1, 0, 1 (thumbs down, neutral, up)
            satisfaction_reward = user_rating * self.reward_weights['user_satisfaction']
            reward_breakdown['user_satisfaction'] = satisfaction_reward
            total_reward += satisfaction_reward
            
            # 2. Response Time Reward (faster is better, within reason)
            response_time = conversation.response_time or 5000
            time_reward = self._calculate_time_reward(response_time) * self.reward_weights['response_time']
            reward_breakdown['response_time'] = time_reward
            total_reward += time_reward
            
            # 3. Task Completion Reward
            task_completed = feedback_data.get('task_completed', False)
            completion_reward = (1.0 if task_completed else 0.0) * self.reward_weights['task_completion']
            reward_breakdown['task_completion'] = completion_reward
            total_reward += completion_reward
            
            # 4. Conversation Engagement Reward
            engagement_reward = self._calculate_engagement_reward(conversation) * self.reward_weights['conversation_length']
            reward_breakdown['conversation_length'] = engagement_reward
            total_reward += engagement_reward
            
            # 5. Repeat Usage Reward (user comes back)
            repeat_reward = self._calculate_repeat_usage_reward(conversation.session_id) * self.reward_weights['repeat_usage']
            reward_breakdown['repeat_usage'] = repeat_reward
            total_reward += repeat_reward
            
            # Store reward for learning
            self._store_reward(conversation_id, total_reward, reward_breakdown)
            
            # Update conversation with reward
            conversation.confidence_score = max(0.0, min(1.0, 0.5 + total_reward))
            db.session.commit()
            
            return total_reward
            
        except Exception as e:
            logging.error(f"Error calculating reward: {e}")
            return 0.0
    
    def _calculate_time_reward(self, response_time_ms: float) -> float:
        """Calculate reward based on response time"""
        # Optimal response time: 1-3 seconds
        optimal_time = 2000  # 2 seconds
        if response_time_ms <= optimal_time:
            return 1.0
        elif response_time_ms <= 5000:  # Up to 5 seconds is acceptable
            return 1.0 - ((response_time_ms - optimal_time) / 3000) * 0.5
        else:  # Penalty for very slow responses
            return max(0.0, 0.5 - ((response_time_ms - 5000) / 10000))
    
    def _calculate_engagement_reward(self, conversation: ConversationHistory) -> float:
        """Calculate reward based on conversation engagement"""
        try:
            # Count messages in this session
            session_messages = ConversationHistory.query.filter_by(
                session_id=conversation.session_id
            ).count()
            
            # Reward longer conversations (up to a point)
            if session_messages <= 3:
                return session_messages / 3.0  # 0.33, 0.66, 1.0
            elif session_messages <= 10:
                return 1.0  # Sweet spot
            else:
                return max(0.5, 1.0 - ((session_messages - 10) / 20))  # Diminishing returns
                
        except Exception as e:
            logging.error(f"Error calculating engagement reward: {e}")
            return 0.0
    
    def _calculate_repeat_usage_reward(self, session_id: str) -> float:
        """Calculate reward for repeat usage patterns"""
        try:
            # Check if user has multiple sessions (indicates satisfaction)
            user_sessions = db.session.query(ConversationHistory.session_id).distinct().count()
            
            # Check recent usage (last 24 hours)
            recent_usage = ConversationHistory.query.filter(
                ConversationHistory.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            repeat_score = min(1.0, (user_sessions - 1) * 0.2 + recent_usage * 0.1)
            return repeat_score
            
        except Exception as e:
            logging.error(f"Error calculating repeat usage reward: {e}")
            return 0.0
    
    def _store_reward(self, conversation_id: str, reward: float, breakdown: Dict[str, float]):
        """Store reward data for learning"""
        reward_data = {
            'conversation_id': conversation_id,
            'reward': reward,
            'breakdown': breakdown,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.reward_history.append(reward_data)
        
        # Keep only last 1000 rewards for memory efficiency
        if len(self.reward_history) > 1000:
            self.reward_history = self.reward_history[-1000:]
    
    def get_reward_analytics(self) -> Dict[str, Any]:
        """Get analytics about rewards and learning"""
        try:
            if not self.reward_history:
                return {'message': 'No reward data available yet'}
            
            rewards = [r['reward'] for r in self.reward_history]
            recent_rewards = rewards[-50:] if len(rewards) >= 50 else rewards
            
            analytics = {
                'total_rewards_given': len(rewards),
                'average_reward': np.mean(rewards),
                'recent_average_reward': np.mean(recent_rewards),
                'reward_trend': 'improving' if np.mean(recent_rewards) > np.mean(rewards) else 'declining',
                'best_reward': max(rewards),
                'worst_reward': min(rewards),
                'reward_distribution': {
                    'positive_rewards': len([r for r in rewards if r > 0]),
                    'negative_rewards': len([r for r in rewards if r < 0]),
                    'neutral_rewards': len([r for r in rewards if r == 0])
                }
            }
            
            # Analyze reward components
            if self.reward_history:
                component_analysis = {}
                for component in self.reward_weights.keys():
                    component_rewards = [
                        r['breakdown'].get(component, 0) 
                        for r in self.reward_history 
                        if 'breakdown' in r
                    ]
                    if component_rewards:
                        component_analysis[component] = {
                            'average': np.mean(component_rewards),
                            'contribution': np.mean(component_rewards) / analytics['average_reward'] if analytics['average_reward'] != 0 else 0
                        }
                
                analytics['component_analysis'] = component_analysis
            
            return analytics
            
        except Exception as e:
            logging.error(f"Error getting reward analytics: {e}")
            return {'error': str(e)}
    
    def adjust_reward_weights(self, performance_data: Dict[str, float]):
        """
        Adjust reward weights based on performance data (reinforcement learning)
        """
        try:
            # Simple gradient-based adjustment
            for component, current_weight in self.reward_weights.items():
                if component in performance_data:
                    # Increase weight if component is performing well
                    performance_score = performance_data[component]
                    adjustment = self.learning_rate * (performance_score - 0.5)  # 0.5 is neutral
                    new_weight = current_weight + adjustment
                    
                    # Keep weights within reasonable bounds
                    self.reward_weights[component] = max(0.05, min(0.8, new_weight))
            
            # Normalize weights to sum to 1.0
            total_weight = sum(self.reward_weights.values())
            for component in self.reward_weights:
                self.reward_weights[component] /= total_weight
            
            return self.reward_weights
            
        except Exception as e:
            logging.error(f"Error adjusting reward weights: {e}")
            return self.reward_weights
    
    def predict_response_quality(self, prompt_features: Dict[str, Any]) -> float:
        """
        Predict expected reward for a given prompt using historical data
        """
        try:
            if not self.reward_history:
                return 0.5  # Neutral prediction
            
            # Simple feature-based prediction
            # In a more sophisticated system, this could use ML models
            
            prompt_length = len(prompt_features.get('user_message', ''))
            prompt_complexity = prompt_features.get('complexity_score', 0.5)
            time_of_day = datetime.now().hour
            
            # Historical patterns
            recent_performance = np.mean([r['reward'] for r in self.reward_history[-20:]])
            
            # Simple heuristic prediction
            length_factor = min(1.0, prompt_length / 100)  # Normalize prompt length
            time_factor = 1.0 if 9 <= time_of_day <= 17 else 0.8  # Business hours
            complexity_factor = 1.0 - (prompt_complexity * 0.3)  # Simpler prompts often work better
            
            predicted_reward = recent_performance * length_factor * time_factor * complexity_factor
            
            return max(-1.0, min(1.0, predicted_reward))
            
        except Exception as e:
            logging.error(f"Error predicting response quality: {e}")
            return 0.5
    
    def get_learning_recommendations(self) -> List[str]:
        """
        Get recommendations for improving AI performance based on reward patterns
        """
        recommendations = []
        
        try:
            analytics = self.get_reward_analytics()
            
            if analytics.get('recent_average_reward', 0) < analytics.get('average_reward', 0):
                recommendations.append("Recent performance declining - consider reviewing response patterns")
            
            if analytics.get('component_analysis'):
                components = analytics['component_analysis']
                
                worst_component = min(components.keys(), key=lambda k: components[k]['average'])
                recommendations.append(f"Focus on improving {worst_component} - lowest performing component")
                
                best_component = max(components.keys(), key=lambda k: components[k]['average'])
                recommendations.append(f"Leverage {best_component} strategies - highest performing component")
            
            if analytics.get('reward_distribution', {}).get('negative_rewards', 0) > analytics.get('reward_distribution', {}).get('positive_rewards', 0):
                recommendations.append("High negative feedback - review conversation patterns and response quality")
            
            recommendations.append("Continue collecting user feedback to improve reward accuracy")
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            recommendations.append("Error analyzing performance - ensure reward data is being collected")
        
        return recommendations

# Global reward system instance
reward_system = AIRewardSystem()

# Example usage and testing
if __name__ == "__main__":
    # Test reward system
    reward_sys = AIRewardSystem()
    
    # Simulate feedback
    test_feedback = {
        'user_rating': 1,  # Thumbs up
        'task_completed': True,
        'response_helpful': True
    }
    
    # Calculate reward (would need real conversation_id in practice)
    # reward = reward_sys.calculate_reward("test_conv_123", test_feedback)
    # print(f"Calculated reward: {reward}")
    
    # Get analytics
    analytics = reward_sys.get_reward_analytics()
    print("Reward Analytics:", analytics)
    
    # Get recommendations
    recommendations = reward_sys.get_learning_recommendations()
    print("Learning Recommendations:", recommendations)