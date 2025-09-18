import openai
import json
from typing import Dict, Any, List, Optional
from config import Config

class AIProviderService:
    """
    Service to manage multiple AI providers and their configurations
    """
    
    def __init__(self):
        self.providers = Config.AI_PROVIDERS
        self.default_provider = Config.DEFAULT_AI_PROVIDER
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI clients for all configured providers"""
        for provider_name, config in self.providers.items():
            try:
                if config["credential_type"] == "openai":
                    self.clients[provider_name] = openai.OpenAI(
                        api_key=config["openai_api_key"],
                        organization=config.get("openai_organization")
                    )
                elif config["credential_type"] == "deepseek":
                    self.clients[provider_name] = openai.OpenAI(
                        api_key=config["api_key"],
                        base_url=config["base_url"]
                    )
                print(f"✅ Initialized AI provider: {provider_name}")
            except Exception as e:
                print(f"❌ Failed to initialize {provider_name}: {str(e)}")
    
    def get_provider_config(self, provider_name: str = None) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        if provider_name is None:
            provider_name = self.default_provider
        
        return self.providers.get(provider_name, {})
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """List all configured AI providers"""
        return [
            {
                "name": name,
                "credential_name": config.get("credential_name"),
                "credential_type": config.get("credential_type"),
                "description": config.get("description"),
                "model": config.get("openai_model") or config.get("model"),
                "environment": config.get("environment"),
                "status": "active" if name in self.clients else "error"
            }
            for name, config in self.providers.items()
        ]
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       provider_name: str = None,
                       **kwargs) -> str:
        """
        Get chat completion from specified provider
        """
        if provider_name is None:
            provider_name = self.default_provider
        
        if provider_name not in self.clients:
            raise ValueError(f"Provider '{provider_name}' not available")
        
        config = self.providers[provider_name]
        client = self.clients[provider_name]
        
        # Get model name
        model = config.get("openai_model") or config.get("model", "gpt-3.5-turbo")
        
        # Default parameters
        params = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 800)
        }
        
        try:
            response = client.chat.completions.create(**params)
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Error from {provider_name}: {str(e)}")
    
    def analyze_query_intent(self, query: str, provider_name: str = None) -> Dict[str, Any]:
        """
        Analyze user query to determine intent and routing
        """
        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant that analyzes user queries for a project management system.
                Determine the intent and classify the query type. Respond with JSON only.
                
                Query types:
                - database_analytics: Questions about database stats, counts, totals
                - search: Search for specific projects, tasks, or content
                - general_chat: General conversation or help
                - task_management: Creating, updating, or managing tasks
                - project_management: Creating, updating, or managing projects
                
                Response format:
                {
                    "intent": "description of what user wants",
                    "query_type": "one of the types above",
                    "confidence": 0.9,
                    "suggested_action": "what the system should do",
                    "keywords": ["extracted", "keywords"]
                }"""
            },
            {
                "role": "user",
                "content": f"Analyze this query: '{query}'"
            }
        ]
        
        try:
            response = self.chat_completion(messages, provider_name, temperature=0.2)
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "intent": "general query",
                "query_type": "general_chat",
                "confidence": 0.5,
                "suggested_action": "process as general chat",
                "keywords": query.split()
            }
        except Exception as e:
            raise Exception(f"Error analyzing query: {str(e)}")
    
    def generate_smart_response(self, 
                              query: str, 
                              context: Dict[str, Any] = None,
                              provider_name: str = None) -> str:
        """
        Generate intelligent response based on query and context
        """
        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context, indent=2)}"
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an AI coordination agent for a project management system.
                You help users manage projects, tasks, and analyze data.
                
                Be helpful, concise, and provide actionable insights.
                Use the provided context to give accurate, specific answers.{context_str}"""
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        return self.chat_completion(messages, provider_name)
    
    def switch_provider(self, provider_name: str) -> bool:
        """
        Switch the default provider
        """
        if provider_name in self.providers and provider_name in self.clients:
            self.default_provider = provider_name
            return True
        return False
    
    def test_provider(self, provider_name: str) -> Dict[str, Any]:
        """
        Test if a provider is working correctly
        """
        try:
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, I am working correctly!'"}
            ]
            
            response = self.chat_completion(test_messages, provider_name)
            
            return {
                "provider": provider_name,
                "status": "success",
                "response": response,
                "config": self.get_provider_config(provider_name)
            }
        except Exception as e:
            return {
                "provider": provider_name,
                "status": "error",
                "error": str(e),
                "config": self.get_provider_config(provider_name)
            }