const socket = io();

// Логика для страницы личного чата
if (window.location.pathname.includes('/api/personal_chat')) {
    const recipient = window.location.pathname.split('/').pop();
    const messagesDiv = document.getElementById('messages');

    socket.emit('join_room', { recipient });

    socket.on('load_chat', (messages) => {
        messages.forEach(displayMessage);
    });

    socket.on('new_message', (message) => {
        displayMessage(message);
    });

    document.getElementById('message-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const messageInput = document.getElementById('message-input');
        const text = messageInput.value;
        if (text.trim()) {
            socket.emit('send_message', { text, recipient });
            messageInput.value = '';
        }
    });

    function displayMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.textContent = `[${message.timestamp}] ${message.sender}: ${message.text}`;
        messagesDiv.appendChild(messageElement);
    }
}

// Уведомления на главной странице чата
socket.on('new_notification', ({ sender }) => {
    alert(`New message from ${sender}`);
});
