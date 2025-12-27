import asyncio
import json
import websockets
import logging
import random

from state import State
from logging_utils import log_message

logging.getLogger("websockets").setLevel(logging.WARNING)

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.state = State()
        self.clients = {}

        self.state_lock = asyncio.Lock()
        self.game_started = False

        self.match_start_time = None
        self.START_DELAY = 9 # match instruction screen time
        self.SCORE_TO_WIN = 5

    def log(self, level, msg):
        log_message(level, "Server", msg)

    async def handler(self, websocket):
        try:
            # receive username
            msg = await websocket.recv()
            data = json.loads(msg)
            username = data["username"]

            async with self.state_lock:
                unique_username = self.state.get_unique_username(username)
                self.clients[websocket] = unique_username

                if len(self.state.players) == 0:
                    # first player joins and waits for second player
                    self.state.add_player(unique_username, role=None)

                elif len(self.state.players) == 1:
                    # once the second player joins, both players are assigned roles automatically
                    existing_username = next(iter(self.state.players))

                    roles = ["snake", "controller"]
                    random.shuffle(roles)

                    existing_player = self.state.players.pop(existing_username)

                    # re-add existing player with correct role
                    self.state.add_player(existing_username, role=roles[0])

                    # add second player
                    self.state.add_player(unique_username, role=roles[1])

            # send unique username back
            await websocket.send(unique_username)
            self.log("INFO", f"{unique_username} connected.")

            # main receive loop
            async for msg in websocket:
                data = json.loads(msg)
                async with self.state_lock:
                    if "direction" in data:
                        self.state.update_player_direction(unique_username, data["direction"])
                    elif "action" in data:

                        # controller actions
                        player = self.state.players.get(unique_username)
                        if player and player.role == "controller":
                            if data["action"] == "food_up":
                                self.state.move_food(-1, 0)
                            elif data["action"] == "food_down":
                                self.state.move_food(1, 0)
                            elif data["action"] == "food_left":
                                self.state.move_food(0, -1)
                            elif data["action"] == "food_right":
                                self.state.move_food(0, 1)
                            elif data["action"] == "spawn_wall":
                                if player.role == "controller":
                                    self.state.spawn_wall_in_front_of_snake(unique_username)

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.disconnect(websocket)
        
    async def disconnect(self, websocket):
        async with self.state_lock:
            username = self.clients.pop(websocket, None)
            if username:
                self.state.remove_player(username)
                self.log("INFO", f"{username} disconnected.")

    async def broadcast_loop(self):
        while True:
            async with self.state_lock:
                if len(self.state.players) < 2:
                    message = json.dumps({"type": "waiting"})
                else:
                    self.state.update_state()

                    if self.state.game_over:
                        message = json.dumps({
                            "type": "result",
                            "winner": self.state.winner
                        })
                    else:
                        message = self.state.to_json()

            for ws in list(self.clients):
                try:
                    await ws.send(message)
                except:
                    await self.disconnect(ws)

            await asyncio.sleep(self.state.tick_interval)

    async def start(self):
        self.log("INFO", f"Server running on {self.host}:{self.port}")

        async with websockets.serve(self.handler, self.host, self.port):
            asyncio.create_task(self.broadcast_loop())
            await asyncio.Future()

if __name__ == "__main__":
    server = Server("0.0.0.0", 5050)
    asyncio.run(server.start())