import websocket
import json
import random
import time

ws = websocket.WebSocket()
ws.connect("ws://localhost:8000/ws")

while True:
    attack_data = {
        "type": "telemetry",
        "data": {
            "speed": random.randint(120, 160),
            "acceleration": random.randint(20, 40),
            "latitude": 13.5,
            "longitude": 78.5,
            "temperature": 50
        }
    }
    ws.send(json.dumps(attack_data))
    time.sleep(1)
