# Reinforcement Learning Enhanced AI Service
from .enhanced_ai_service import EnhancedAIService
from .reward_system import AIRewardSystem
from typing import Dict, List, Any, Optional
import json
import time
from datetime import datetime
import logging

class ReinforcementLearningAI(EnhancedAIService):
    """
    AI Service enhanced with Reinforcement Learning using reward feedback
    to continuously improve response quality and user satisfaction
    """
    
    def __init__(self):
        super().__init__()
        self.reward_system = AIRewardSystem()
        self.response_strategies = {
            'direct_answer': 0.7,
            'clarifying_question': 0.2,
            'step_by_step_guide': 0.8,
            'suggestion_with_alternatives': 0.6,
            'empathetic_response': 0.5
        }
        
    def smart_chat_with_rl(self, user_message: str, session_id: str = None, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced chat with Reinforcement Learning that adapts based on reward feedback
        """
        start_time = time.time()
        
        try:
            # Predict expected quality for this prompt
            prompt_features = self._extract_prompt_features(user_message, context)
            predicted_quality = self.reward_system.predict_response_quality(prompt_features)
            
            # Select response strategy based on historical performance
            strategy = self._select_response_strategy(user_message, predicted_quality)
            
            # Enhance the prompt based on the selected strategy
            enhanced_prompt = self._apply_response_strategy(user_message, strategy, context)
            
            # Get AI response using enhanced strategy
            if context and context.get('use_vector_context', False):
                # Use vector database context
                response_data = super().smart_chat_with_context(
                    enhanced_prompt, session_id, True
                )
            else:
                # Use traditional chat
                ai_response = self.chat(enhanced_prompt)
                response_data = {
                    'response': ai_response,
                    'conversation_id': session_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'vector_context_used': False
                }
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            response_data['response_time_ms'] = response_time
            
            # Add RL-specific data
            response_data.update({
                'predicted_quality': predicted_quality,
                'strategy_used': strategy,
                'rl_enhanced': True,
                'needs_feedback': True,
                'conversation_id': session_id or f"conv_{int(time.time())}"
            })
            
            # Store conversation for reward tracking
            conversation_id = self._store_rl_conversation(
                user_message, response_data, strategy, predicted_quality
            )
            response_data['conversation_id'] = conversation_id
            
            return response_data
            
        except Exception as e:
            logging.error(f"Error in RL chat: {e}")
            # Fallback to standard enhanced chat
            return super().smart_chat_with_context(user_message, session_id, False)
    
    def _extract_prompt_features(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract features from the user prompt for quality prediction"""
        features = {
            'user_message': user_message,
            'message_length': len(user_message),
            'word_count': len(user_message.split()),
            'has_question_mark': '?' in user_message,
            'has_please': 'please' in user_message.lower(),
            'urgency_indicators': any(word in user_message.lower() for word in ['urgent', 'asap', 'quickly', 'now']),
            'complexity_score': self._calculate_complexity_score(user_message),
            'time_of_day': datetime.now().hour,
            'session_context': context or {}
        }
        return features
    
    def _calculate_complexity_score(self, message: str) -> float:
        """Calculate complexity score of the user message"""
        complexity_indicators = [
            'analyze', 'compare', 'explain', 'breakdown', 'strategy',
            'implement', 'design', 'architecture', 'optimize', 'integrate'
        ]
        
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in message.lower())
        word_count = len(message.split())
        
        # Normalize complexity score between 0 and 1
        base_complexity = min(1.0, complexity_count / 3)
        length_complexity = min(0.5, word_count / 100)
        
        return min(1.0, base_complexity + length_complexity)
    
    def _select_response_strategy(self, user_message: str, predicted_quality: float) -> str:
        """Select the best response strategy based on message analysis and historical performance"""
        
        # Analyze message intent
        message_lower = user_message.lower()
        
        # Rule-based strategy selection with RL influence
        if '?' in user_message and predicted_quality < 0.3:
            return 'clarifying_question'  # Ask for clarification if prediction is poor
        elif any(word in message_lower for word in ['how', 'step', 'guide', 'process']):
            return 'step_by_step_guide'
        elif any(word in message_lower for word in ['help', 'stuck', 'problem', 'issue']):
            return 'empathetic_response'
        elif predicted_quality > 0.7:
            return 'direct_answer'  # High confidence, give direct answer
        else:
            return 'suggestion_with_alternatives'
    
    def _apply_response_strategy(self, user_message: str, strategy: str, context: Dict[str, Any] = None) -> str:
        """Apply the selected response strategy to enhance the prompt"""
        
        strategy_prompts = {
            'direct_answer': f"""
            Provide a clear, direct answer to this question: {user_message}
            Be concise but complete. Focus on actionable information.
            """,
            
            'clarifying_question': f"""
            The user asked: {user_message}
            This question needs clarification. Ask 1-2 specific clarifying questions to better understand their needs,
            then provide helpful guidance based on what they might be looking for.
            """,
            
            'step_by_step_guide': f"""
            Provide a detailed step-by-step guide for: {user_message}
            Break it down into clear, numbered steps that are easy to follow.
            Include any important tips or warnings.
            """,
            
            'suggestion_with_alternatives': f"""
            For this request: {user_message}
            Provide your main suggestion along with 2-3 alternative approaches.
            Explain the pros and cons of each option so the user can choose what works best for them.
            """,
            
            'empathetic_response': f"""
            The user is seeking help with: {user_message}
            Respond with empathy and understanding. Acknowledge their situation and provide
            supportive, practical advice. Be encouraging and helpful.
            """
        }
        
        return strategy_prompts.get(strategy, user_message)
    
    def _store_rl_conversation(self, user_message: str, response_data: Dict[str, Any], 
                              strategy: str, predicted_quality: float) -> str:
        """Store conversation with RL metadata for reward tracking"""
        
        conversation_id = response_data.get('conversation_id', f"rl_conv_{int(time.time())}")
        
        # Store additional RL metadata
        rl_metadata = {
            'strategy_used': strategy,
            'predicted_quality': predicted_quality,
            'response_time_ms': response_data.get('response_time_ms', 0),
            'rl_enhanced': True
        }
        
        # This would integrate with your existing conversation storage
        # For now, just add the metadata to the response
        response_data['rl_metadata'] = rl_metadata
        
        return conversation_id
    
    def process_user_feedback(self, conversation_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user feedback and calculate reward to improve future responses
        """
        try:
            # Calculate reward based on feedback
            reward = self.reward_system.calculate_reward(conversation_id, feedback)
            
            # Update strategy performance based on reward
            strategy_used = feedback.get('strategy_used', 'unknown')
            if strategy_used in self.response_strategies:
                # Simple learning: adjust strategy weights based on reward
                current_weight = self.response_strategies[strategy_used]
                adjustment = 0.01 * reward  # Small learning rate
                new_weight = max(0.1, min(1.0, current_weight + adjustment))
                self.response_strategies[strategy_used] = new_weight
            
            # Get updated analytics
            analytics = self.reward_system.get_reward_analytics()
            recommendations = self.reward_system.get_learning_recommendations()
            
            return {
                'reward_calculated': reward,
                'strategy_updated': strategy_used,
                'analytics': analytics,
                'recommendations': recommendations,
                'learning_progress': self._get_learning_progress()
            }
            
        except Exception as e:
            logging.error(f"Error processing feedback: {e}")
            return {'error': str(e)}
    
    def _get_learning_progress(self) -> Dict[str, Any]:
        """Get learning progress metrics"""
        analytics = self.reward_system.get_reward_analytics()
        
        return {
            'total_interactions': analytics.get('total_rewards_given', 0),
            'recent_performance': analytics.get('recent_average_reward', 0),
            'overall_performance': analytics.get('average_reward', 0),
            'improvement_trend': analytics.get('reward_trend', 'unknown'),
            'strategy_weights': self.response_strategies,
            'learning_active': True
        }
    
    def get_rl_analytics(self) -> Dict[str, Any]:
        """Get comprehensive reinforcement learning analytics"""
        reward_analytics = self.reward_system.get_reward_analytics()
        learning_progress = self._get_learning_progress()
        recommendations = self.reward_system.get_learning_recommendations()
        
        return {
            'reward_system': reward_analytics,
            'learning_progress': learning_progress,
            'recommendations': recommendations,
            'response_strategies': self.response_strategies,
            'system_status': 'active',
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """
        Perform optimization based on collected reward data
        """
        try:
            # Get performance data for each strategy
            performance_data = {}
            for strategy in self.response_strategies:
                # This is simplified - in practice, you'd analyze historical data
                performance_data[strategy] = self.response_strategies[strategy]
            
            # Adjust reward weights based on performance
            updated_weights = self.reward_system.adjust_reward_weights(performance_data)
            
            # Normalize strategy weights
            total_strategy_weight = sum(self.response_strategies.values())
            for strategy in self.response_strategies:
                self.response_strategies[strategy] /= total_strategy_weight
            
            return {
                'optimization_completed': True,
                'updated_reward_weights': updated_weights,
                'updated_strategy_weights': self.response_strategies,
                'recommendations': self.reward_system.get_learning_recommendations()
            }
            
        except Exception as e:
            logging.error(f"Error optimizing performance: {e}")
            return {'error': str(e)}

# Example usage
if __name__ == "__main__":
    rl_ai = ReinforcementLearningAI()
    
    # Test RL enhanced chat
    response = rl_ai.smart_chat_with_rl(
        "How can I prioritize my project tasks more effectively?",
        session_id="test_session",
        context={'use_vector_context': False}
    )
    
    print("RL Enhanced Response:", response)
    
    # Simulate user feedback
    feedback = {
        'user_rating': 1,  # Thumbs up
        'task_completed': True,
        'response_helpful': True,
        'strategy_used': response.get('strategy_used')
    }
    
    # Process feedback
    learning_result = rl_ai.process_user_feedback(
        response['conversation_id'], 
        feedback
    )
    
    print("Learning Result:", learning_result)