try:
    import speech_recognition as sr
    from pydub import AudioSegment
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    sr = None
    AudioSegment = None
    SPEECH_RECOGNITION_AVAILABLE = False

import io
import tempfile
import os
from flask import send_file
import requests

class VoiceService:
    def __init__(self):
        self.speech_available = SPEECH_RECOGNITION_AVAILABLE
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio file to text"""
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                audio_file.save(temp_file.name)
                
                # Convert to WAV if needed
                audio = AudioSegment.from_file(temp_file.name)
                wav_file = temp_file.name.replace('.wav', '_converted.wav')
                audio.export(wav_file, format='wav')
                
                # Transcribe using speech recognition
                with sr.AudioFile(wav_file) as source:
                    audio_data = self.recognizer.record(source)
                    
                    try:
                        # Try Google Speech Recognition first
                        text = self.recognizer.recognize_google(audio_data)
                        confidence = 0.9  # Google doesn't provide confidence
                    except sr.UnknownValueError:
                        try:
                            # Fallback to Sphinx
                            text = self.recognizer.recognize_sphinx(audio_data)
                            confidence = 0.7
                        except sr.UnknownValueError:
                            text = ""
                            confidence = 0.0
                
                # Cleanup
                os.unlink(temp_file.name)
                if os.path.exists(wav_file):
                    os.unlink(wav_file)
                
                duration = len(audio) / 1000.0  # Duration in seconds
                
                return {
                    'success': True,
                    'transcription': text,
                    'confidence': confidence,
                    'duration': duration,
                    'language': 'en-US'
                }
        
        except Exception as e:
            return {'error': f'Failed to transcribe audio: {str(e)}'}
    
    def text_to_speech(self, text, voice='en-US', speed=1.0):
        """Convert text to speech (returns audio file)"""
        try:
            # For a real implementation, you would use services like:
            # - Google Text-to-Speech API
            # - Amazon Polly
            # - Azure Speech Services
            # - OpenAI TTS
            
            # This is a placeholder implementation
            # In production, integrate with a real TTS service
            
            # Create a simple response for now
            audio_data = self._generate_placeholder_audio(text)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            return send_file(
                temp_file_path,
                as_attachment=True,
                download_name='speech.mp3',
                mimetype='audio/mpeg'
            )
        
        except Exception as e:
            return {'error': f'Failed to generate speech: {str(e)}'}
    
    def _generate_placeholder_audio(self, text):
        """Generate placeholder audio data"""
        # This is a placeholder - in production, use a real TTS service
        # For now, return empty MP3 header
        return b'\xff\xfb\x90\x00'  # Minimal MP3 header
    
    def analyze_voice_command(self, text):
        """Analyze voice command and extract intent"""
        text = text.lower().strip()
        
        # Define command patterns
        command_patterns = {
            'create_task': ['create task', 'new task', 'add task'],
            'list_tasks': ['list tasks', 'show tasks', 'my tasks'],
            'update_status': ['update status', 'change status', 'mark as'],
            'get_status': ['project status', 'status update', 'overview'],
            'assign_task': ['assign task', 'assign to'],
            'set_priority': ['set priority', 'priority'],
            'add_comment': ['add comment', 'comment on'],
            'schedule_meeting': ['schedule meeting', 'book meeting'],
            'get_help': ['help', 'what can you do', 'commands']
        }
        
        # Extract intent
        intent = 'unknown'
        confidence = 0.0
        entities = {}
        
        for command, patterns in command_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    intent = command
                    confidence = 0.8
                    break
            if intent != 'unknown':
                break
        
        # Extract entities based on intent
        if intent == 'create_task':
            # Extract task title after "create task" or similar
            for pattern in command_patterns['create_task']:
                if pattern in text:
                    title = text.split(pattern, 1)[-1].strip()
                    if title:
                        entities['title'] = title
                    break
        
        elif intent == 'update_status':
            # Extract status keywords
            status_keywords = ['todo', 'in progress', 'done', 'blocked', 'review']
            for status in status_keywords:
                if status in text:
                    entities['status'] = status
                    break
        
        elif intent == 'assign_task':
            # Extract assignee (simple pattern matching)
            words = text.split()
            if 'to' in words:
                to_index = words.index('to')
                if to_index + 1 < len(words):
                    entities['assignee'] = words[to_index + 1]
        
        elif intent == 'set_priority':
            # Extract priority level
            priority_keywords = ['low', 'medium', 'high', 'urgent']
            for priority in priority_keywords:
                if priority in text:
                    entities['priority'] = priority
                    break
        
        return {
            'intent': intent,
            'confidence': confidence,
            'entities': entities,
            'original_text': text
        }
    
    def process_voice_command(self, command_analysis):
        """Process analyzed voice command and return action"""
        intent = command_analysis.get('intent')
        entities = command_analysis.get('entities', {})
        
        if intent == 'create_task':
            title = entities.get('title', 'Untitled Task')
            return {
                'action': 'create_task',
                'parameters': {
                    'title': title,
                    'description': f'Created via voice command: "{command_analysis.get("original_text")}"'
                },
                'response': f'I\'ll create a task titled "{title}" for you.'
            }
        
        elif intent == 'list_tasks':
            return {
                'action': 'list_tasks',
                'parameters': {},
                'response': 'Here are your current tasks:'
            }
        
        elif intent == 'get_status':
            return {
                'action': 'get_status',
                'parameters': {},
                'response': 'Here\'s the current project status:'
            }
        
        elif intent == 'update_status':
            return {
                'action': 'update_status',
                'parameters': {
                    'status': entities.get('status', 'in_progress')
                },
                'response': f'I\'ll update the task status to "{entities.get("status", "in_progress")}"'
            }
        
        elif intent == 'get_help':
            return {
                'action': 'help',
                'parameters': {},
                'response': '''I can help you with voice commands like:
                - "Create task [title]" - Create a new task
                - "List my tasks" - Show your tasks
                - "Project status" - Get status overview
                - "Update status to done" - Change task status
                - "Assign task to [name]" - Assign tasks
                '''
            }
        
        else:
            return {
                'action': 'unknown',
                'parameters': {},
                'response': 'I didn\'t understand that command. Try saying "help" for available commands.'
            }
    
    def create_voice_response(self, text_response):
        """Create voice response for text"""
        # This would integrate with TTS to create audio response
        return self.text_to_speech(text_response)
    
    def transcribe_and_process(self, audio_file):
        """Complete pipeline: transcribe audio and process command"""
        try:
            # Step 1: Transcribe audio
            transcription_result = self.transcribe_audio(audio_file)
            
            if not transcription_result.get('success'):
                return transcription_result
            
            text = transcription_result.get('transcription', '')
            
            if not text:
                return {
                    'success': False,
                    'error': 'No speech detected in audio'
                }
            
            # Step 2: Analyze command
            command_analysis = self.analyze_voice_command(text)
            
            # Step 3: Process command
            action_result = self.process_voice_command(command_analysis)
            
            return {
                'success': True,
                'transcription': text,
                'confidence': transcription_result.get('confidence'),
                'command_analysis': command_analysis,
                'action': action_result,
                'duration': transcription_result.get('duration')
            }
        
        except Exception as e:
            return {'error': f'Failed to process voice command: {str(e)}'}