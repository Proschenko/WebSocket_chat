import logging
import tornado.ioloop
import tornado.web
import tornado.websocket
import redis.asyncio as aioredis
import json
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server.log"),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
    ]
)

# Асинхронный Redis клиент
async_redis_client = aioredis.Redis()

# Словарь активных WebSocket подключений
active_connections = {}

class ChatWebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        self.username = self.get_argument("username", f"User_{len(active_connections) + 1}")
        active_connections[self.username] = self
        self.broadcast_user_list()
        logging.info(f"User connected: {self.username}")

        self.write_message(json.dumps({
            "type": "system",
            "message": f"Welcome to the chat, {self.username}!"
        }))

    async def on_message(self, incoming_message):
        logging.info(f"Message received from {self.username}: {incoming_message}")
        await async_redis_client.publish("chat", json.dumps({
            "type": "message",
            "user": self.username,
            "text": incoming_message
        }))

    def on_close(self):
        if self.username in active_connections:
            del active_connections[self.username]
        self.broadcast_user_list()
        logging.info(f"User disconnected: {self.username}")

    def broadcast_user_list(self):
        current_users = list(active_connections.keys())
        logging.info(f"Active users updated: {current_users}")
        user_update_message = json.dumps({
            "type": "update_users",
            "users": current_users
        })
        for conn in active_connections.values():
            conn.write_message(user_update_message)

    def check_origin(self, origin):
        return True

async def redis_message_listener():
    pubsub_instance = async_redis_client.pubsub()
    await pubsub_instance.subscribe("chat")
    logging.info("Redis listener started")

    async for redis_message in pubsub_instance.listen():
        if redis_message["type"] == "message":
            message_data = redis_message["data"].decode("utf-8") if isinstance(redis_message["data"], bytes) else redis_message["data"]
            logging.info(f"Redis message received: {message_data}")
            for conn in active_connections.values():
                await conn.write_message(message_data)

class HomePageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/index.html")

def create_application():
    return tornado.web.Application([
        (r"/", HomePageHandler),
        (r"/ws", ChatWebSocketHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./static"}),
    ])

if __name__ == "__main__":
    app = create_application()
    app.listen(8888)
    logging.info("Server started on port http://localhost:8888")

    loop = asyncio.get_event_loop()
    loop.create_task(redis_message_listener())

    tornado.ioloop.IOLoop.current().start()
