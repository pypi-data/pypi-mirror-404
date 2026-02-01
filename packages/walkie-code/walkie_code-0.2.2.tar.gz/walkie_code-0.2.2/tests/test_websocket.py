"""Tests for WebSocket client"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from websocket_client import WebSocketClient


@pytest.fixture
def ws_client():
    """Create WebSocket client for testing"""
    return WebSocketClient("wss://test.example.com", "test_token_123")


def test_initialization(ws_client):
    """Test WebSocket client initialization"""
    assert ws_client.endpoint == "wss://test.example.com"
    assert ws_client.device_token == "test_token_123"
    assert ws_client.ws is None
    assert ws_client.retry_delay == 1
    assert ws_client.max_retry_delay == 30


@patch('websocket_client.create_connection')
def test_connect(mock_create_connection, ws_client):
    """Test WebSocket connection"""
    mock_ws = Mock()
    mock_create_connection.return_value = mock_ws
    
    result = ws_client.connect()
    
    assert result is True
    assert ws_client.ws == mock_ws
    assert mock_ws.send.call_count == 2  # identify + confirmation message
    
    # Verify identify message
    first_call = mock_ws.send.call_args_list[0][0][0]
    identify_msg = json.loads(first_call)
    assert identify_msg['action'] == 'identify'
    assert identify_msg['role'] == 'desktop'
    assert identify_msg['token'] == 'test_token_123'


def test_send_message(ws_client):
    """Test sending text message"""
    mock_ws = Mock()
    ws_client.ws = mock_ws
    
    ws_client.send_message("Hello, world!")
    
    mock_ws.send.assert_called_once()
    sent_msg = json.loads(mock_ws.send.call_args[0][0])
    assert sent_msg['action'] == 'sendText'
    assert sent_msg['text'] == "Hello, world!"


def test_send_notification(ws_client):
    """Test sending system notification"""
    mock_ws = Mock()
    ws_client.ws = mock_ws
    
    ws_client.send_notification("Test notification", "warning")
    
    mock_ws.send.assert_called_once()
    sent_msg = json.loads(mock_ws.send.call_args[0][0])
    assert sent_msg['action'] == 'systemNotification'
    assert sent_msg['message'] == "Test notification"
    assert sent_msg['severity'] == "warning"


def test_receive_message(ws_client):
    """Test receiving message"""
    mock_ws = Mock()
    mock_ws.recv.return_value = '{"type": "test", "data": "value"}'
    ws_client.ws = mock_ws
    
    result = ws_client.receive_message()
    
    assert result == {"type": "test", "data": "value"}


def test_close(ws_client):
    """Test closing connection"""
    mock_ws = Mock()
    ws_client.ws = mock_ws
    
    ws_client.close()
    
    mock_ws.close.assert_called_once()
    assert ws_client.ws is None


def test_get_retry_delay(ws_client):
    """Test retry delay with exponential backoff"""
    assert ws_client.get_retry_delay() == 1
    assert ws_client.get_retry_delay() == 2
    assert ws_client.get_retry_delay() == 4
    assert ws_client.get_retry_delay() == 8
    
    # Set to near max
    ws_client.retry_delay = 25
    assert ws_client.get_retry_delay() == 25
    assert ws_client.get_retry_delay() == 30  # capped at max
