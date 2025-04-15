document.addEventListener('DOMContentLoaded', function() {
    // Create chat widget HTML
    const chatWidget = document.createElement('div');
    chatWidget.className = 'chat-widget hidden';
    chatWidget.innerHTML = `
        <div class="chat-header">
            <span>Travel Assistant</span>
            <i class="fas fa-times" id="close-chat"></i>
        </div>
        <div class="chat-messages"></div>
        <div class="chat-input">
            <input type="text" placeholder="Type your message...">
            <button><i class="fas fa-paper-plane"></i></button>
        </div>
    `;

    // Add chat widget to body
    document.body.appendChild(chatWidget);

    // Get chat toggle button from navbar
    const chatToggle = document.getElementById('chat-toggle');

    // Get elements
    const messagesContainer = chatWidget.querySelector('.chat-messages');
    const input = chatWidget.querySelector('input');
    const sendButton = chatWidget.querySelector('button');
    const closeButton = chatWidget.querySelector('#close-chat');

    // Add initial bot message
    addMessage('Hello! I am your Travel Assistant. How can I help you today?', 'bot-message');

    // Toggle chat widget
    chatToggle.addEventListener('click', (e) => {
        e.preventDefault();
        chatWidget.classList.toggle('hidden');
        if (!chatWidget.classList.contains('hidden')) {
            input.focus();
        }
    });

    // Close chat widget
    closeButton.addEventListener('click', () => {
        chatWidget.classList.add('hidden');
    });

    // Send message
    function sendMessage() {
        const message = input.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user-message');
        input.value = '';

        // Show typing indicator
        const typingIndicator = addMessage('Typing...', 'bot-message');

        // Send to backend
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            typingIndicator.remove();
            
            if (data.error) {
                addMessage(data.error, 'bot-message error');
            } else {
                addMessage(data.response, 'bot-message');
            }
        })
        .catch(() => {
            // Remove typing indicator
            typingIndicator.remove();
            addMessage('Sorry, there was an error connecting to the server.', 'bot-message error');
        });
    }

    // Add message to chat
    function addMessage(text, className) {
        const message = document.createElement('div');
        message.className = `message ${className}`;
        message.textContent = text;
        messagesContainer.appendChild(message);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return message;
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});