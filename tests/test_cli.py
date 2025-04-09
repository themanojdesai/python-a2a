"""
Tests for the command-line interface.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import io

from python_a2a.cli import main, parse_args, send_command, serve_command


class TestCLI:
    def test_parse_args_send(self):
        """Test parsing arguments for the send command"""
        with patch('sys.argv', ['a2a', 'send', 'https://example.com/a2a', 'Hello']):
            args = parse_args()
            
            assert args.command == 'send'
            assert args.endpoint == 'https://example.com/a2a'
            assert args.message == 'Hello'
    
    def test_parse_args_serve(self):
        """Test parsing arguments for the serve command"""
        with patch('sys.argv', ['a2a', 'serve', '--host', 'localhost', '--port', '8080']):
            args = parse_args()
            
            assert args.command == 'serve'
            assert args.host == 'localhost'
            assert args.port == 8080
            assert args.debug is False
    
    def test_parse_args_openai(self):
        """Test parsing arguments for the openai command"""
        with patch('sys.argv', ['a2a', 'openai', '--api-key', 'test-key', '--model', 'gpt-4']):
            args = parse_args()
            
            assert args.command == 'openai'
            assert args.api_key == 'test-key'
            assert args.model == 'gpt-4'
            assert args.temperature == 0.7  # Default value
    
    @patch('python_a2a.cli.A2AClient')
    def test_send_command(self, MockClient):
        """Test the send command"""
        # Setup mock
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content.type = "text"
        mock_response.content.text = "Response text"
        mock_client.send_message.return_value = mock_response
        
        # Create args
        args = MagicMock()
        args.endpoint = "https://example.com/a2a"
        args.message = "Hello"
        
        # Run command
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            result = send_command(args)
            
            # Check result
            assert result == 0
            assert mock_client.send_message.called
            
            # Check output
            output = fake_out.getvalue()
            assert "Sending message..." in output
    
    @patch('python_a2a.cli.run_server')
    @patch('python_a2a.cli.A2AServer')
    def test_serve_command(self, MockServer, mock_run_server):
        """Test the serve command"""
        # Setup mocks
        mock_server = MagicMock()
        MockServer.return_value = mock_server
        
        # Create args
        args = MagicMock()
        args.host = "localhost"
        args.port = 8080
        args.debug = True
        
        # Run command
        result = serve_command(args)
        
        # Check result
        assert result == 0
        assert MockServer.called
        mock_run_server.assert_called_once_with(
            agent=mock_server,
            host="localhost",
            port=8080,
            debug=True
        )
    
    def test_main_no_command(self):
        """Test main with no command"""
        with patch('sys.argv', ['a2a']), patch('sys.stderr', new=io.StringIO()):
            with pytest.raises(SystemExit):
                main()
    
    def test_main_invalid_command(self):
        """Test main with an invalid command"""
        with patch('sys.argv', ['a2a', 'invalid']), patch('sys.stderr', new=io.StringIO()):
            with pytest.raises(SystemExit):
                main()
    
    @patch('python_a2a.cli.send_command')
    def test_main_send(self, mock_send):
        """Test main with the send command"""
        mock_send.return_value = 0
        
        with patch('sys.argv', ['a2a', 'send', 'https://example.com/a2a', 'Hello']):
            result = main()
            
            assert result == 0
            assert mock_send.called