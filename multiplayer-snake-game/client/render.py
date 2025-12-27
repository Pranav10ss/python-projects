import pygame
import sys

class UIState:
    USERNAME = "username"
    WAITING = "waiting"
    GAME = "game"
    GAME_OVER = "game_over"
    INSTRUCTIONS = "instructions"

class Render:
    LEADERBOARD_WIDTH = 200
    CELL_SIZE = 15

    COLOURS = {
        1: (255, 0, 0),
        2: (0, 255, 0),
        3: (255, 255, 0),
        4: (0, 0, 255),
        5: (255, 0, 255),
        6: (0, 255, 255),
        7: (255, 255, 255),
    }

    def __init__(self, username, dimensions, client):
        self.username = username
        self.dimensions = dimensions
        self.client = client

        self.width = 0
        self.height = 0
        self.screen_width = 600
        self.screen_height = 400

        # UI state
        self.ui_state = UIState.USERNAME
        self.input_text = ""
        self.state = None

        # Init pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 16)

        # Temporary window (before game starts)
        self.screen = pygame.display.set_mode((600, 400))
        pygame.display.set_caption("Snake")

        self.game_over = False
        self.game_over_message = ""

        # player role instructions
        self.instruction_start_time = None
        self.instruction_role = None

    def cleanup(self):
        pygame.quit()
        sys.exit()

    # called by client thread
    def update_state(self, new_state):
        self.state = new_state
    
    def run_frame(self):
        # game instructions for player based on role
        if self.ui_state == UIState.INSTRUCTIONS:
            now = pygame.time.get_ticks()

            if now - self.instruction_start_time >= 9000:
                self.ui_state = UIState.GAME
                return

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()

            self.draw_instructions()
            pygame.display.flip()
            self.clock.tick(30)
            return
        
        # game over screen
        if self.ui_state == UIState.GAME_OVER:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        self.cleanup()

            self.draw_game_over()
            pygame.display.flip()
            self.clock.tick(30)
            return

        if self.ui_state == UIState.USERNAME:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()
                self.handle_username_input(event)

            self.draw_username_screen()
            pygame.display.flip()
            self.clock.tick(30)
            return
        
        if self.ui_state == UIState.WAITING:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()

            self.screen.fill((0, 0, 0))
            text = self.font.render("Waiting for other player to join...", True, (255, 255, 255))
            self.screen.blit(text, (150, 200))
            pygame.display.flip()
            self.clock.tick(30)
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.cleanup()
                return

            if event.type != pygame.KEYDOWN:
                continue

            if not self.state:
                continue

            # determine role
            player = self.state["players"].get(self.username)
            if not player:
                continue

            role = player["role"]

            # Snake CONTROLS
            if role == "snake":
                if event.key == pygame.K_w:
                    self.client.send_direction("w")
                elif event.key == pygame.K_a:
                    self.client.send_direction("a")
                elif event.key == pygame.K_s:
                    self.client.send_direction("s")
                elif event.key == pygame.K_d:
                    self.client.send_direction("d")

            # CONTROLLER CONTROLS (food movement + spawn_wall)
            if role == "controller":
                if event.key == pygame.K_SPACE:
                    self.client.send_action("spawn_wall")
                elif event.key == pygame.K_UP:
                    self.client.send_action("food_up")
                elif event.key == pygame.K_DOWN:
                    self.client.send_action("food_down")
                elif event.key == pygame.K_LEFT:
                    self.client.send_action("food_left")
                elif event.key == pygame.K_RIGHT:
                    self.client.send_action("food_right")

        # drawing
        if self.ui_state == UIState.GAME:
            self.draw()

        pygame.display.flip()
        self.clock.tick(15)

    # main draw loop
    def draw(self):
        self.screen.fill((0, 0, 0))

        self.draw_board()
        self.draw_food(self.state["food_pos"])
        self.draw_snakes(self.state["players"])
        self.draw_hud()
        player = self.state["players"][self.username]

        if player["role"] == "snake":
            self.draw_score(player["score"])

        self.draw_leaderboard(self.state["players"])
        self.draw_walls(self.state.get("walls", []))

        role = self.state["players"][self.username]["role"]
        label = self.font.render(f"Role: {role.upper()}", True, (200, 200, 200))

        if role == "controller":
            remaining = self.state.get("wall_spawns_left", {}).get(self.username, 0)

            text = self.font.render(
                f"WALL SPAWNS LEFT: {remaining}",
                True,
                (255, 100, 100)
            )
            text_rect = text.get_rect(
                top=10,
                right=self.width * self.CELL_SIZE - 10
            )
            self.screen.blit(text, text_rect)

        self.screen.blit(label, (10, 10))

    def draw_board(self):
        rect = pygame.Rect(
            0, 0,
            self.width * self.CELL_SIZE,
            self.height * self.CELL_SIZE
        )
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)

    def setup_game_screen(self):
        self.height, self.width = self.dimensions

        self.screen_width = (
            self.width * self.CELL_SIZE + self.LEADERBOARD_WIDTH
        )
        self.screen_height = self.height * self.CELL_SIZE

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height)
        )

    def draw_username_screen(self):
        self.screen.fill((0, 0, 0))

        title = self.font.render("Enter Username", True, (255, 255, 255))
        name = self.font.render(self.input_text, True, (0, 255, 0))
        hint = self.font.render("Press ENTER to continue", True, (150, 150, 150))

        self.screen.blit(title, (100, 180))
        self.screen.blit(name, (100, 220))
        self.screen.blit(hint, (100, 260))

    def handle_username_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.input_text:
                self.client.send_username(self.input_text)
                self.ui_state = UIState.WAITING
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                if len(self.input_text) < 12:
                    self.input_text += event.unicode

    def draw_food(self, pos):
        y, x = pos
        pygame.draw.rect(
            self.screen,
            (255, 165, 0),
            pygame.Rect(
                x * self.CELL_SIZE,
                y * self.CELL_SIZE,
                self.CELL_SIZE,
                self.CELL_SIZE
            )
        )

    def draw_snakes(self, players):
        for username, player in players.items():
            if player["role"] != "snake":
                continue 

            colour = self.COLOURS[player["colour"]]
            for y, x in player["segments"]:
                pygame.draw.rect(
                    self.screen,
                    colour,
                    pygame.Rect(
                        x * self.CELL_SIZE,
                        y * self.CELL_SIZE,
                        self.CELL_SIZE,
                        self.CELL_SIZE
                    )
                )

    def draw_score(self, score):
        text = self.font.render(f"Score: {score}", True, (255, 255, 255))
        self.screen.blit(text, (10, self.screen_height - 30))

    def draw_leaderboard(self, players):
        # Only include snake players
        snakes = {
            username: player
            for username, player in players.items()
            if player["role"] == "snake"
        }

        if not snakes:
            return

        x_offset = self.width * self.CELL_SIZE + 10
        y = 10

        # Title
        title = self.font.render("LEADERBOARD", True, (255, 255, 255))
        self.screen.blit(title, (x_offset, y))
        y += 30

        # Sort snakes by score
        for username, snake in sorted(
            snakes.items(),
            key=lambda item: item[1]["score"],
            reverse=True
        ):
            colour = self.COLOURS.get(snake["colour"], (255, 255, 255))
            text = self.font.render(
                f"{username}: {snake['score']}",
                True,
                colour
            )
            self.screen.blit(text, (x_offset, y))
            y += 20

    def draw_game_over(self):
        self.screen.fill((0, 0, 0))

        main_text = self.game_over_message or "GAME OVER"
        text = self.font.render(main_text, True, (255, 0, 0))
        sub = self.font.render("Press Q or ESC to quit", True, (255, 255, 255))

        rect = text.get_rect(
            center=(self.screen_width // 2, self.screen_height // 2)
        )
        sub_rect = sub.get_rect(
            center=(self.screen_width // 2, self.screen_height // 2 + 40)
        )

        self.screen.blit(text, rect)
        self.screen.blit(sub, sub_rect)

    def draw_walls(self, walls):
        WALL_FILL = (90, 90, 90) # dark gray
        WALL_BORDER = (140, 140, 140) # lighter edge

        for wall in walls:
            for y, x in wall["cells"]:
                rect = pygame.Rect(
                    x * self.CELL_SIZE,
                    y * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE
                )

                # fill
                pygame.draw.rect(self.screen, WALL_FILL, rect)

                # border
                pygame.draw.rect(self.screen, WALL_BORDER, rect, 2)

    def draw_instructions(self):
        self.screen.fill((0, 0, 0))

        role = self.instruction_role

        if role == "snake":
            lines = [
                "You are the SNAKE",
                "",
                "Controls:",
                "Move -> W A S D",
                "",
                "GOAL:",
                "Score 5 points to WIN",
                "Avoid walls spawned by the Controller"
            ]
            color = (0, 255, 0)

        else:
            lines = [
                "You are the CONTROLLER",
                "",
                "Controls:",
                "Move food -> Arrow Keys",
                "Spawn wall -> 'SPACE' Key",
                "",
                "GOAL:",
                "Move the food & Spawn the wall to kill the Snake"
            ]
            color = (255, 100, 100)

        y = self.screen_height // 2 - len(lines) * 15
        for line in lines:
            text = self.font.render(line, True, color)
            rect = text.get_rect(center=(self.screen_width // 2, y))
            self.screen.blit(text, rect)
            y += 30

    def draw_hud(self):
        if not self.state:
            return
        
        remaining_time = self.state.get("remaining_time")
        score_to_win = self.state.get("score_to_win")

        if remaining_time is None:
            return
        
        minutes = remaining_time // 60
        seconds = remaining_time % 60

        time_text = self.font.render(
            f"TIME LEFT: {minutes:02}:{seconds:02}",
            True,
            (255, 200, 200)
        )

        win_text = self.font.render(
            f"POINTS TO WIN: {score_to_win}",
            True,
            (200, 200, 255)
        )

        self.screen.blit(time_text, (self.screen_width // 2 - 200, 10))
        self.screen.blit(win_text, (self.screen_width // 2 - 200, 30))