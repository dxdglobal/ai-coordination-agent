"""
NLP Utilities for Intent Detection and Name Extraction
Handles natural language processing for task management queries
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any
import openai
from .config import Config
from .crm_connector import get_crm_connector
from .logger import get_logger

# Initialize components
logger = get_logger()
crm = get_crm_connector()

# Try to import spaCy, fall back to regex if not available
try:
    import spacy
    nlp = spacy.load(Config.SPACY_MODEL)
    SPACY_AVAILABLE = True
    logger.info("spaCy model loaded successfully")
except (ImportError, OSError):
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available, using regex-based NLP")

class NLPProcessor:
    """Natural Language Processing for task management queries"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.employees_cache = []
        self._cache_employees()
    
    def _cache_employees(self):
        """Cache employee names for name extraction"""
        self.employees_cache = crm.get_all_employees()
        logger.debug(f"Cached {len(self.employees_cache)} employee names")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process user query to extract intent and entities
        Args:
            query: User's natural language query
        Returns: Dictionary with intent, employee, confidence, and metadata
        """
        start_time = time.time()
        
        try:
            # Clean and normalize query
            cleaned_query = self._clean_query(query)
            
            # Check if it's a greeting or casual chat
            if self._is_greeting(cleaned_query):
                return {
                    'intent': 'greeting',
                    'employee': None,
                    'confidence': 1.0,
                    'query': query,
                    'is_actionable': False
                }
            
            # Extract employee name (use original query to preserve Turkish characters)
            employee_info = self._extract_employee_name(query)  # Use original query instead of cleaned
            
            # Detect intent
            intent_info = self._detect_intent(cleaned_query)
            
            # Extract task filters (overdue, completed, etc.)
            task_filters = self._extract_task_filters(cleaned_query)
            
            # Combine results
            result = {
                'intent': intent_info['intent'],
                'employee': employee_info['employee'],
                'employee_id': employee_info.get('employee_id'),
                'confidence': min(intent_info['confidence'], employee_info['confidence']),
                'query': query,
                'cleaned_query': cleaned_query,
                'task_filters': task_filters,
                'is_actionable': intent_info['intent'] in Config.SUPPORTED_INTENTS,
                'processing_time': time.time() - start_time
            }
            
            # Log processing results
            logger.log_nlp_processing(
                query, result['intent'], result['employee'] or 'None',
                result['confidence'], result['processing_time']
            )
            
            return result
            
        except Exception as e:
            logger.error("Failed to process NLP query", error=e, 
                        extra_data={'query': query})
            return {
                'intent': 'unknown',
                'employee': None,
                'confidence': 0.0,
                'query': query,
                'is_actionable': False,
                'error': str(e)
            }
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query"""
        # Convert to lowercase and strip whitespace  
        cleaned = query.lower().strip()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Preserve Turkish characters explicitly before removing special chars
        turkish_chars = ['ı', 'ğ', 'ü', 'ş', 'ö', 'ç', 'İ', 'Ğ', 'Ü', 'Ş', 'Ö', 'Ç', 'i̇']
        
        # Simple approach: only remove clearly problematic characters
        # Keep all letters (including Turkish), numbers, spaces, and basic punctuation
        cleaned = re.sub(r'[^\w\s\?\!\.\,\-\'\"]+', ' ', cleaned, flags=re.UNICODE)
        
        return cleaned
    
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting or casual chat"""
        for pattern in Config.GREETING_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _extract_employee_name(self, query: str) -> Dict[str, Any]:
        """
        Extract employee name from query
        Returns: Dictionary with employee name, ID, and confidence
        """
        best_match = None
        best_confidence = 0.0
        
        # Use different strategies based on available tools
        if SPACY_AVAILABLE:
            # Use spaCy for named entity recognition
            doc = nlp(query)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    employee = crm.find_employee_by_name(ent.text)
                    if employee:
                        confidence = 0.9  # High confidence for NER
                        if confidence > best_confidence:
                            best_match = employee
                            best_confidence = confidence
        
        # Fallback: Direct name matching with Turkish character support
        if best_confidence < 0.8:  # Try direct matching if NER confidence is low
            for employee in self.employees_cache:
                # Check various name formats
                name_variants = [
                    employee['firstname'].strip(),
                    employee['lastname'].strip(),
                    employee['full_name'].strip(),
                    f"{employee['firstname'].strip()} {employee['lastname'].strip()}",
                    f"{employee['lastname'].strip()}, {employee['firstname'].strip()}"
                ]
                
                for variant in name_variants:
                    # Turkish character insensitive comparison
                    variant_normalized = self._normalize_turkish_text(variant.lower())
                    query_normalized = self._normalize_turkish_text(query.lower())
                    
                    if variant_normalized in query_normalized:
                        # Calculate confidence based on match quality
                        if variant_normalized == self._normalize_turkish_text(employee['full_name'].lower()):
                            confidence = 0.95  # Full name exact match
                        elif variant_normalized == self._normalize_turkish_text(employee['firstname'].lower()) and len(variant) > 2:
                            confidence = 0.90  # First name match (high confidence for Turkish names)
                        elif variant_normalized == self._normalize_turkish_text(employee['lastname'].lower()) and len(variant) > 2:
                            confidence = 0.85  # Last name match  
                        elif len(variant) > 2:  # Avoid single character matches
                            confidence = 0.8  # Other partial match
                        else:
                            continue
                        
                        if confidence > best_confidence:
                            best_match = employee
                            best_confidence = confidence
        
        # Enhanced firstname-only matching for queries like "tasks for hamza"
        if best_confidence < 0.7:
            for employee in crm.get_all_employees():
                firstname_normalized = self._normalize_turkish_text(employee['firstname'].strip().lower())
                query_normalized = self._normalize_turkish_text(query.lower())
                
                # Check if firstname appears in query with word boundaries
                if re.search(rf'\b{re.escape(firstname_normalized)}\b', query_normalized) and len(firstname_normalized) > 2:
                    confidence = 0.75  # Good confidence for standalone firstname
                    if confidence > best_confidence:
                        best_match = employee
                        best_confidence = confidence
        
        # Additional pass for partial firstname matching (for İlahe, Hamza, etc.)
        if best_confidence < 0.7:
            for employee in crm.get_all_employees():
                firstname_normalized = self._normalize_turkish_text(employee['firstname'].strip().lower())
                query_normalized = self._normalize_turkish_text(query.lower())
                
                # More aggressive partial matching for common first names
                if firstname_normalized in query_normalized and len(firstname_normalized) > 3:
                    confidence = 0.70  # Decent confidence for partial match
                    if confidence > best_confidence:
                        best_match = employee
                        best_confidence = confidence
        
        # OpenAI fallback for complex cases
        if best_confidence < 0.6:  # Lower threshold to allow more matches
            openai_result = self._extract_name_with_openai(query)
            if openai_result['confidence'] > best_confidence:
                employee = crm.find_employee_by_name(openai_result['name'])
                if employee:
                    best_match = employee
                    best_confidence = openai_result['confidence'] * 0.8  # Slightly lower confidence
        
        return {
            'employee': best_match['full_name'] if best_match else None,
            'employee_id': best_match['id'] if best_match else None,
            'confidence': best_confidence
        }
    
    def _extract_name_with_openai(self, query: str) -> Dict[str, Any]:
        """Use OpenAI to extract person names from complex queries"""
        try:
            start_time = time.time()
            
            employee_names = [emp['full_name'] for emp in self.employees_cache]
            
            prompt = f"""
            Extract the person's name from this query if present. The query is about task management.
            
            Available employee names: {', '.join(employee_names[:20])}  # Limit to avoid token overflow
            
            Query: "{query}"
            
            Return only the exact employee name if found, or "NONE" if no employee name is mentioned.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for name extraction
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            extracted_name = response.choices[0].message.content.strip()
            response_time = time.time() - start_time
            
            logger.log_openai_request(
                "gpt-3.5-turbo", response.usage.total_tokens, 
                response_time, True
            )
            
            if extracted_name != "NONE" and extracted_name in employee_names:
                return {
                    'name': extracted_name,
                    'confidence': 0.7
                }
            
        except Exception as e:
            logger.log_openai_request("gpt-3.5-turbo", 0, 0, False, str(e))
        
        return {
            'name': None,
            'confidence': 0.0
        }
    
    def _detect_intent(self, query: str) -> Dict[str, Any]:
        """
        Detect user intent from query
        Returns: Dictionary with intent and confidence
        """
        # Intent detection patterns
        intent_patterns = {
            'list_tasks': [
                r'\b(list|show|display|get)\b.*\btasks?\b',
                r'\btasks?\b.*\b(for|of|assigned to)\b',
                r'\bwhat.*tasks?\b',
                r'\btask.*list\b',
                r'\boverdue\b.*\btasks?\b',  # Handle overdue tasks as list_tasks
                r'\btasks?\b.*\boverdue\b',
                r'\bcompleted?\b.*\btasks?\b',  # Handle completed tasks
                r'\btasks?\b.*\bcompleted?\b'
            ],
            'task_summary': [
                r'\bsummar(y|ize)\b.*\btasks?\b',
                r'\boverview\b.*\btasks?\b',
                r'\bwhat.*working on\b',
                r'\bcurrent.*tasks?\b',
                r'\bfocus.*areas?\b'
            ],
            'performance_report': [
                r'\bperformance\b',
                r'\bprogress\b.*\breport\b',
                r'\bcompletion.*rate\b',
                r'\bhow.*doing\b',
                r'\bproductivity\b',
                r'\bstats?\b.*\btasks?\b'
            ],
            'anomaly_check': [
                r'\banomaly\b',
                r'\bissues?\b.*\btasks?\b',
                r'\bproblems?\b.*\btasks?\b',
                r'\bdelayed?\b',
                r'\bbehind.*schedule\b'
            ]
        }
        
        best_intent = 'unknown'
        best_confidence = 0.0
        
        # Pattern matching
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    confidence = 0.8  # Base confidence for pattern match
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
        
        # Use OpenAI for complex intent detection if pattern matching fails
        if best_confidence < 0.7:
            openai_result = self._detect_intent_with_openai(query)
            if openai_result['confidence'] > best_confidence:
                best_intent = openai_result['intent']
                best_confidence = openai_result['confidence']
        
        return {
            'intent': best_intent,
            'confidence': best_confidence
        }
    
    def _detect_intent_with_openai(self, query: str) -> Dict[str, Any]:
        """Use OpenAI to detect intent for complex queries"""
        try:
            start_time = time.time()
            
            prompt = f"""
            Classify this task management query into one of these categories:
            - list_tasks: User wants to see a list of tasks
            - task_summary: User wants a summary or overview of tasks/work
            - performance_report: User wants performance metrics or progress report
            - anomaly_check: User wants to check for issues, problems, or anomalies
            - unknown: Query doesn't fit any category
            
            Query: "{query}"
            
            Return only the category name.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.1
            )
            
            detected_intent = response.choices[0].message.content.strip().lower()
            response_time = time.time() - start_time
            
            logger.log_openai_request(
                "gpt-3.5-turbo", response.usage.total_tokens, 
                response_time, True
            )
            
            if detected_intent in Config.SUPPORTED_INTENTS:
                return {
                    'intent': detected_intent,
                    'confidence': 0.7
                }
            
        except Exception as e:
            logger.log_openai_request("gpt-3.5-turbo", 0, 0, False, str(e))
        
        return {
            'intent': 'unknown',
            'confidence': 0.0
        }
    
    def refresh_employee_cache(self):
        """Refresh the employee cache"""
        self._cache_employees()
    
    def _normalize_turkish_text(self, text: str) -> str:
        """
        Normalize Turkish text for better matching
        Converts Turkish characters to their closest ASCII equivalents
        """
        # Handle Turkish I/i properly
        text = text.replace('İ', 'I').replace('ı', 'i')
        
        turkish_map = {
            'ğ': 'g', 'Ğ': 'G',
            'ü': 'u', 'Ü': 'U', 
            'ş': 's', 'Ş': 'S',
            'ö': 'o', 'Ö': 'O', 
            'ç': 'c', 'Ç': 'C'
        }
        
        for turkish_char, ascii_char in turkish_map.items():
            text = text.replace(turkish_char, ascii_char)
        
        return text
    
    def _extract_task_filters(self, query: str) -> Dict[str, Any]:
        """
        Extract task-specific filters from query
        Returns: Dictionary with filter criteria
        """
        filters = {}
        
        # Check for overdue tasks
        if re.search(r'\boverdue\b', query, re.IGNORECASE):
            filters['overdue'] = True
            
        # Check for completed tasks
        if re.search(r'\b(completed?|finished|done|approved)\b', query, re.IGNORECASE):
            filters['completed'] = True
            
        # Check for active/pending tasks
        if re.search(r'\b(active|pending|current|ongoing|progress|testing|awaiting|review)\b', query, re.IGNORECASE):
            filters['active'] = True
            
        # Check for on hold tasks
        if re.search(r'\b(hold|paused|suspended)\b', query, re.IGNORECASE):
            filters['on_hold'] = True
            
        # Check for cancelled/rejected tasks
        if re.search(r'\b(cancelled?|rejected|terminated|stopped)\b', query, re.IGNORECASE):
            filters['cancelled'] = True
            
        # Check for archived tasks
        if re.search(r'\b(archived?|old|historical)\b', query, re.IGNORECASE):
            filters['archived'] = True
            
        # Check for priority levels
        if re.search(r'\burgent\b', query, re.IGNORECASE):
            filters['priority'] = 'urgent'
        elif re.search(r'\bhigh\b.*\bpriority\b', query, re.IGNORECASE):
            filters['priority'] = 'high'
            
        return filters

# Global NLP processor instance
nlp_processor = NLPProcessor()

def get_nlp_processor() -> NLPProcessor:
    """Get the global NLP processor instance"""
    return nlp_processor