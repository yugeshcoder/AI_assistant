# Simple Flask frontend to demonstrate user_sessions in action

from flask import Flask, render_template, request, jsonify
from main import chatbot_api

app = Flask(__name__)

# HTML template as string for simplicity
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Leave Management Chatbot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .chat-messages {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #fafafa;
            border-radius: 5px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
        }
        .user-message {
            background-color: #e3f2fd;
            text-align: right;
        }
        .bot-message {
            background-color: #f1f8e9;
        }
        .input-section {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        input[type="text"] {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            background-color: #2196f3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #1976d2;
        }
        .session-info {
            background-color: #fff3e0;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #ff9800;
        }
        .employee-form {
            background-color: #e8f5e8;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .form-row {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        .form-row input {
            flex: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        .status-bar {
            background-color: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            font-size: 0.9em;
            color: #1976d2;
        }
        .info-prompts {
            background-color: #fff3e0;
            border: 1px solid #ffb74d;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .info-prompts h4 {
            margin-top: 0;
            color: #f57c00;
        }
        .info-prompts ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .info-prompts li {
            color: #e65100;
            font-weight: bold;
        }
        .session-info {
            background-color: #fff3e0;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #ff9800;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Leave Management Chatbot</h1>
        
        <div class="chat-messages" id="chat-messages">
            <div class="message bot-message">
                <strong>Bot:</strong> Hello! I'm your leave management assistant.<br><br>
            </div>
        </div>
        
        <div class="input-section">
            <input type="text" id="user-input" placeholder="Type your message here and press Enter to send..." onkeypress="handleKeyPress(event)" autocomplete="off">
            <button onclick="sendMessage()" title="Send message (or press Enter)">Send</button>
            <button onclick="clearChat()">Clear Chat</button>
        </div>
        
        <div class="status-bar" id="status-bar">
            Ready to chat...
        </div>
    </div>

    <script>
        let sessionId = 'web_session_' + Date.now();
        let messageCount = 0;

        function updateEmployeeInfo() {
            // Since the employee form elements don't exist in current UI, 
            // guide users to use natural conversation instead
            alert('Employee information form is not available in this version. Please provide your information naturally in the chat, like: "Hi, I\\'m John, employee EMP001"');
            
            // Focus on the chat input instead
            const userInput = document.getElementById('user-input');
            if (userInput) {
                userInput.focus();
                userInput.placeholder = "Try: 'Hi, I'm [Your Name], employee [EMP###]'";
            }
        }

        function handleKeyPress(event) {
            console.log('Key pressed:', event.key); // Debug log
            if (event.key === 'Enter') {
                event.preventDefault(); // Prevent form submission
                console.log('Enter key detected, sending message...'); // Debug log
                sendMessage();
            }
        }
        
        // Also add modern event listener for better compatibility
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, setting up event listeners...'); // Debug log
            const userInput = document.getElementById('user-input');
            if (userInput) {
                console.log('User input element found, adding event listener...'); // Debug log
                
                // Add keydown event listener as backup
                userInput.addEventListener('keydown', function(event) {
                    console.log('Keydown event:', event.key); // Debug log
                    if (event.key === 'Enter') {
                        event.preventDefault();
                        console.log('Enter keydown detected, sending message...'); // Debug log
                        sendMessage();
                    }
                });
                
                // Focus on input when page loads
                userInput.focus();
                console.log('Input focused');
            } else {
                console.log('ERROR: user-input element not found!'); // Debug log
            }
        });

        function sendMessage() {
            console.log('sendMessage() called'); // Debug log
            const userInput = document.getElementById('user-input');
            const message = userInput.value.trim();
            console.log('Message to send:', message); // Debug log
            
            if (!message) {
                console.log('Empty message, not sending'); // Debug log
                return;
            }

            // Add user message to chat
            addMessage('user', message);
            userInput.value = '';
            updateStatus('Sending message...');

            // Prepare user info - safely check if elements exist first
            const userInfo = {};
            const employee_id_elem = document.getElementById('employee_id');
            const employee_name_elem = document.getElementById('employee_name');
            const leave_type_elem = document.getElementById('leave_type');
            const start_date_elem = document.getElementById('start_date');
            const end_date_elem = document.getElementById('end_date');

            if (employee_id_elem && employee_id_elem.value) userInfo.employee_id = employee_id_elem.value;
            if (employee_name_elem && employee_name_elem.value) userInfo.name = employee_name_elem.value;
            if (leave_type_elem && leave_type_elem.value) userInfo.current_leave_type = leave_type_elem.value;
            if (start_date_elem && start_date_elem.value) userInfo.current_start_date = start_date_elem.value;
            if (end_date_elem && end_date_elem.value) userInfo.current_end_date = end_date_elem.value;

            // Send to backend
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId,
                    user_info: userInfo
                })
            })
            .then(response => response.json())
            .then(data => {
                addMessage('bot', data.response);
                updateStatus('Message sent successfully!');
            })
            .catch(error => {
                console.error('Error:', error);
                addMessage('bot', 'Sorry, there was an error processing your request.');
                updateStatus('Error sending message');
            });
        }

        function addMessage(sender, message) {
            const chatMessages = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'Bot'}:</strong> ${message}`;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            messageCount++;
        }

        function updateStatus(message) {
            document.getElementById('status-bar').textContent = message;
            setTimeout(() => {
                document.getElementById('status-bar').textContent = 'Ready to chat...';
            }, 3000);
        }

        function clearChat() {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = '<div class="message bot-message"><strong>Bot:</strong> Chat cleared! How can I help you?</div>';
            messageCount = 0;
            updateStatus('Chat cleared');
        }

        function showSessions() {
            fetch('/sessions')
            .then(response => response.json())
            .then(data => {
                let sessionsText = `Active Sessions (${Object.keys(data.sessions).length}):\n`;
                for (const [sessionId, sessionInfo] of Object.entries(data.sessions)) {
                    sessionsText += `• ${sessionId}: ${sessionInfo.employee_id} - ${sessionInfo.name}\n`;
                }
                alert(sessionsText);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error retrieving sessions');
            });
        }
        
        function quickIntro() {
            document.getElementById('user-input').value = "Hi, I\\'m [Your Name], employee [EMP###], I need help with leave management";
            document.getElementById('user-input').focus();
        }
        
        function quickBalance() {
            document.getElementById('user-input').value = "Can you check my leave balance?";
            document.getElementById('user-input').focus();
        }
        
        function quickApply() {
            document.getElementById('user-input').value = "I want to apply for leave from [start date] to [end date]";
            document.getElementById('user-input').focus();
        }
        
        // Add a welcome message when page loads
        document.addEventListener('DOMContentLoaded', function() {
            updateStatus('Welcome! Try typing "Hi, I\\'m [Your Name], employee [EMP###]" to get started.');
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    
    response = chatbot_api(
        user_message=data.get('message', ''),
        session_id=data.get('session_id'),
        user_info=data.get('user_info', {})
    )
    
    return jsonify(response)

@app.route('/sessions', methods=['GET'])
def sessions():
    from main import get_all_sessions
    return jsonify({
        'sessions': get_all_sessions(),
        'total': len(get_all_sessions())
    })

if __name__ == '__main__':
    print("🚀 Starting Leave Management Chatbot Web Interface")
    print("📱 Open your browser to: http://localhost:5000")
    print("💡 This demonstrates how user_sessions work in a real frontend")
    app.run(debug=True, port=5000)