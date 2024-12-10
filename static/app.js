document.addEventListener("DOMContentLoaded", () => {
    let username = prompt("Enter your username:");
    while (!username || username.trim() === "") {
        username = prompt("Username cannot be empty. Please enter your username:");
    }

    const socket = new WebSocket(`ws://localhost:8888/ws?username=${encodeURIComponent(username)}`);
    console.log(`[WebSocket] Connecting as user: ${username}`);

    const contactsContainer = document.getElementById("contacts");
    const messagesContainer = document.getElementById("messages");
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");

    const header = document.createElement("div");
    header.id = "header";
    header.textContent = `Welcome, ${username}!`;
    document.getElementById("chat-container").prepend(header);

    socket.onopen = function () {
        console.log(`[WebSocket] Connected as user: ${username}`);
    };

    socket.onmessage = function (event) {
        console.log(`[WebSocket] Message received: ${event.data}`);
        const data = JSON.parse(event.data);

        if (data.type === "update_users") {
            contactsContainer.innerHTML = "";
            data.users.forEach((user) => {
                const contact = document.createElement("li");
                contact.textContent = user;
                contact.className = "status online";
                contactsContainer.appendChild(contact);
            });
            console.log(`[WebSocket] Updated active users: ${data.users}`);
        } else if (data.type === "message") {
            const message = document.createElement("li");
            message.textContent = `${data.user}: ${data.text}`;
            message.className = data.user === username ? "outgoing" : "incoming";
            messagesContainer.appendChild(message);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } else if (data.type === "system") {
            const message = document.createElement("li");
            message.textContent = data.message;
            message.className = "system";
            messagesContainer.appendChild(message);
        }
    };

    socket.onerror = function (error) {
        console.error(`[WebSocket] Error: ${error.message}`);
    };

    socket.onclose = function () {
        console.warn(`[WebSocket] Connection closed.`);
    };

    sendButton.onclick = function () {
        if (messageInput.value.trim() !== "") {
            console.log(`[WebSocket] Sending message: ${messageInput.value.trim()}`);
            socket.send(messageInput.value.trim());
            messageInput.value = "";
        }
    };
});
