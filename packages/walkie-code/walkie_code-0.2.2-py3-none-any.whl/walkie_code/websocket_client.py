"""WebSocket client for VibeVoice communication"""

import json
import ssl
import time
import certifi
from websocket import create_connection


class WebSocketClient:
    """Manages WebSocket connection with auto-reconnect"""

    def __init__(self, endpoint, device_token):
        self.endpoint = endpoint
        self.device_token = device_token
        self.ws = None
        self.retry_delay = 1
        self.max_retry_delay = 30
        self.is_first_connection = True
    
    def connect(self):
        """Establish WebSocket connection and identify"""
        print(f'Connecting to {self.endpoint}')
        self.ws = create_connection(
            self.endpoint,
            sslopt={"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": certifi.where()}
        )

        # Identify as desktop with token
        identify_msg = {
            'action': 'identify',
            'role': 'desktop',
            'token': self.device_token
        }
        print('Identifying with device token...')
        self.ws.send(json.dumps(identify_msg))
        time.sleep(0.2)

        # Send connection confirmation only on first connection
        if self.is_first_connection:
            msg = {'action': 'sendText', 'text': f'Desktop connected with token {self.device_token[:8]}...'}
            print('Sending:', msg)
            self.ws.send(json.dumps(msg))
            self.is_first_connection = False

        # Reset retry delay on successful connection
        self.retry_delay = 1
        print('✓ WebSocket connected')
        return True
    
    def send_message(self, text):
        """Send text message to frontend"""
        if not self.ws:
            raise ConnectionError("WebSocket not connected")
        
        msg = {'action': 'sendText', 'text': text}
        self.ws.send(json.dumps(msg))
    
    def send_notification(self, message, severity='info'):
        """Send system notification to frontend"""
        if not self.ws:
            raise ConnectionError("WebSocket not connected")
        
        msg = {
            'action': 'systemNotification',
            'message': message,
            'severity': severity
        }
        self.ws.send(json.dumps(msg))
    
    def receive_message(self):
        """Receive and parse message from WebSocket"""
        if not self.ws:
            raise ConnectionError("WebSocket not connected")
        
        raw_msg = self.ws.recv()
        
        # Handle empty messages (ping/pong, keepalive)
        if not raw_msg or raw_msg.strip() == '':
            return None
        
        print('Received:', raw_msg)
        return json.loads(raw_msg)
    
    def close(self):
        """Close WebSocket connection"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
    
    def get_retry_delay(self):
        """Get current retry delay and increment for next time"""
        delay = self.retry_delay
        self.retry_delay = min(self.retry_delay * 2, self.max_retry_delay)
        return delay
