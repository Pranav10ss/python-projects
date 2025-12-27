import asyncio
import json
import websockets
import pygame
from render import Render, UIState

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.username = ""
        self.render = None
        self.websocket = None

    async def start(self):
        uri = f"ws://{self.host}:{self.port}"

        async with websockets.connect(uri) as ws:
            self.websocket = ws

            self.render = Render(None, None, self)
            asyncio.create_task(self.receive_loop())

            while True:
                self.render.run_frame()
                await asyncio.sleep(0.016)

    async def receive_loop(self):
        try:
            async for msg in self.websocket:
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    self.username = msg
                    self.render.username = msg
                    continue
                
                # result screen
                if data.get("type") == "result":
                    self.render.ui_state = UIState.GAME_OVER
                    self.render.state = None

                    if data["winner"] == self.username:
                        self.render.game_over_message = "YOU WIN!"
                    else:
                        self.render.game_over_message = "YOU LOST!"
                    continue
                
                # Waiting message
                if data.get("type") == "waiting":
                    if self.render.ui_state in (UIState.USERNAME, UIState.WAITING):
                        self.render.ui_state = UIState.WAITING
                    continue
                
                # game state
                if self.render.ui_state in (UIState.WAITING, UIState.USERNAME):
                    self.render.game_over_message = ""
                    self.render.dimensions = data["dimensions"]
                    self.render.setup_game_screen()

                    # Determine role once players match
                    player = data["players"].get(self.username)
                    if player:
                        self.render.instruction_role = player["role"]
                        self.render.instruction_start_time = pygame.time.get_ticks()
                        self.render.ui_state = UIState.INSTRUCTIONS

                    self.render.screen = pygame.display.set_mode(
                        (self.render.screen_width, self.render.screen_height)
                    )

                # Always update state and set to GAME when receiving game state
                self.render.state = data
                if self.render.ui_state == UIState.WAITING:
                    self.render.ui_state == UIState.GAME

        except websockets.exceptions.ConnectionClosed:
            pass
        
        finally:
            # when server is terminated - force exit UI loop
            self.render.ui_state = UIState.GAME_OVER
            self.render.game_over_message = "Server terminated"

    def send_username(self, username):
        self.username = username
        asyncio.create_task(
            self.websocket.send(json.dumps({"username": username}))
        )

    def send_direction(self, key):
        asyncio.create_task(
            self.websocket.send(json.dumps({"direction": key}))
        )

    def send_action(self, action):
        asyncio.create_task(
            self.websocket.send(json.dumps({"action": action}))
        )

if __name__ == "__main__":
    host = input("Enter server IP: ")
    asyncio.run(Client(host, 5050).start())