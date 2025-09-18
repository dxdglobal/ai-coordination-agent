import requests
from config import Config
import base64

class ZendeskService:
    def __init__(self):
        self.domain = Config.ZENDESK_DOMAIN
        self.email = Config.ZENDESK_EMAIL
        self.token = Config.ZENDESK_API_TOKEN
        self.base_url = f"https://{self.domain}.zendesk.com/api/v2"
        
        # Create authentication header
        credentials = f"{self.email}/token:{self.token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
    
    def get_recent_tickets(self, limit=50):
        """Get recent tickets from Zendesk"""
        if not all([self.domain, self.email, self.token]):
            return {'error': 'Zendesk credentials not configured'}
        
        try:
            url = f"{self.base_url}/tickets.json"
            params = {
                'sort_by': 'updated_at',
                'sort_order': 'desc',
                'per_page': limit
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'tickets': data.get('tickets', []),
                'count': len(data.get('tickets', []))
            }
        
        except requests.exceptions.RequestException as e:
            return {'error': f'Failed to fetch Zendesk tickets: {str(e)}'}
    
    def get_chat_history(self, ticket_id):
        """Get chat history for a specific ticket"""
        if not all([self.domain, self.email, self.token]):
            return {'error': 'Zendesk credentials not configured'}
        
        try:
            # Get ticket comments/conversations
            url = f"{self.base_url}/tickets/{ticket_id}/comments.json"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            comments = data.get('comments', [])
            
            # Format chat history
            chat_history = []
            for comment in comments:
                chat_history.append({
                    'id': comment.get('id'),
                    'author_id': comment.get('author_id'),
                    'body': comment.get('body'),
                    'html_body': comment.get('html_body'),
                    'public': comment.get('public'),
                    'created_at': comment.get('created_at'),
                    'type': comment.get('type', 'comment')
                })
            
            return {
                'success': True,
                'ticket_id': ticket_id,
                'chat_history': chat_history
            }
        
        except requests.exceptions.RequestException as e:
            return {'error': f'Failed to fetch chat history: {str(e)}'}
    
    def create_ticket(self, subject, description, requester_email):
        """Create a new ticket in Zendesk"""
        if not all([self.domain, self.email, self.token]):
            return {'error': 'Zendesk credentials not configured'}
        
        try:
            url = f"{self.base_url}/tickets.json"
            
            ticket_data = {
                "ticket": {
                    "subject": subject,
                    "comment": {
                        "body": description
                    },
                    "requester": {
                        "email": requester_email
                    },
                    "priority": "normal",
                    "type": "question"
                }
            }
            
            response = requests.post(url, headers=self.headers, json=ticket_data)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'ticket': data.get('ticket')
            }
        
        except requests.exceptions.RequestException as e:
            return {'error': f'Failed to create ticket: {str(e)}'}
    
    def update_ticket(self, ticket_id, status=None, priority=None, comment=None):
        """Update an existing ticket"""
        if not all([self.domain, self.email, self.token]):
            return {'error': 'Zendesk credentials not configured'}
        
        try:
            url = f"{self.base_url}/tickets/{ticket_id}.json"
            
            update_data = {"ticket": {}}
            
            if status:
                update_data["ticket"]["status"] = status
            if priority:
                update_data["ticket"]["priority"] = priority
            if comment:
                update_data["ticket"]["comment"] = {"body": comment}
            
            response = requests.put(url, headers=self.headers, json=update_data)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'ticket': data.get('ticket')
            }
        
        except requests.exceptions.RequestException as e:
            return {'error': f'Failed to update ticket: {str(e)}'}
    
    def search_tickets(self, query):
        """Search tickets in Zendesk"""
        if not all([self.domain, self.email, self.token]):
            return {'error': 'Zendesk credentials not configured'}
        
        try:
            url = f"{self.base_url}/search.json"
            params = {
                'query': f'type:ticket {query}'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'results': data.get('results', []),
                'count': data.get('count', 0)
            }
        
        except requests.exceptions.RequestException as e:
            return {'error': f'Failed to search tickets: {str(e)}'}