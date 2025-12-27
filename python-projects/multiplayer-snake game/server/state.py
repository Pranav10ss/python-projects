# state.py
import json
import random
import time

from logging_utils import log_message
from player import Player

class State:
    DIRECTION_MAP = {
        "w": [-1, 0],
        "a": [0, -1],
        "s": [1, 0],
        "d": [0, 1]
    }

    def __init__(self):
        self.dimensions = [30, 50]
        self.food_pos = self.get_random_position()
        self.players = {}
        self.game_started = False
        self.game_over = False
        self.winner = None
        self.game_over_message = ""

        self.walls = [] 
        self.wall_spawns = {} 
        self.WALL_LIMIT = 4
        self.WALL_COOLDOWN = 60
        self.WALL_LIFETIME = 8
        self.SCORE_TO_WIN = 5

        # game delay
        self.START_DELAY = 9
        self.match_start_time = None

        # food speed variables
        self.BASE_TICK = 0.30
        self.MIN_TICK = 0.08
        self.SPEED_STEP = 0.015

        self.tick_interval = self.BASE_TICK

        # snake player time limit
        self.TIME_LIMIT = 60
        self.remaining_time = None

    # Logs a message
    def log_message(self, type, message):
        log_message(type, f"State", message)

    def to_json(self):
        return json.dumps({
            "dimensions": self.dimensions,
            "food_pos": self.food_pos,
            "players": {username: player.to_dict() for username, player in self.players.items()},
            "game_over": self.game_over,
            "game_over_message": self.game_over_message,
            "walls": self.walls,
            "wall_spawns_left": {
                u: max(0, self.WALL_LIMIT - len([
                    t for t in self.wall_spawns.get(u, [])
                    if time.time() - t < self.WALL_COOLDOWN
                ]))
                for u in self.players
            },
            "remaining_time": self.remaining_time,
            "score_to_win": self.SCORE_TO_WIN
        })

    # Gets a random position
    def get_random_position(self, buffer=3):
        return [random.randint(1+buffer, self.dimensions[0]-2-buffer), 
            random.randint(1+buffer, self.dimensions[1]-2-buffer)]

    # Appends a number until the username is unique
    def get_unique_username(self, username):
        suffix, counter = "", 1
        while username+suffix in self.players:
            suffix = str(counter)
            counter += 1

        self.log_message("INFO", f"Unique username: {username+suffix}")
        return username+suffix

    # Adds a new player to the map
    def add_player(self, username, role=None):
        self.log_message("INFO", f"Player {username}: Joining as {role}")

        colour_pair_id = self.get_available_colour()

        if role == "snake":
            y = random.randint(5, self.dimensions[0] - 6)
            x = random.randint(5, self.dimensions[1] - 6)
            segments = [[y, x]]
            direction = random.choice(list(State.DIRECTION_MAP.values()))

        elif role == "controller":
            segments = []
            direction = [0, 0]
            
        else:
            segments = [] # controller has no body
            direction = [0, 0] # no movement

        player = Player(segments, direction, colour_pair_id, role)
        self.players[username] = player

        if len(self.players) == 2:
            self.game_started = True
            self.match_start_time = time.time() + self.START_DELAY

    def get_available_colour(self):
        used_colour = {player.colour for player in self.players.values()}
        for colour in range(1, 8):
            if colour not in used_colour:
                return colour
        return random.randint(1, 7)

    # Removes a player from the map
    def remove_player(self, username):
        if username in self.players:
            self.log_message("INFO", f"Player {username}: Removing from list of players in game")
            self.players.pop(username)
            self.log_message("DEBUG", f"List of players: {[username for username in self.players]}")

    # Gets the segments from all the snakes
    def get_occupied_positions(self):
        occupied_positions = []

        for player in self.players.values():
            occupied_positions.extend(player.segments)

        return occupied_positions

    # Regenerates the food if a snake eats it
    def regenerate_food(self, eater, occupied_positions):
        self.log_message("INFO", f"Player {eater}: Ate food")

        self.food_pos = self.get_random_position()
        while self.food_pos in occupied_positions:
            self.food_pos = self.get_random_position()
        
        self.players[eater].score += 1

        self.tick_interval = max(
            self.MIN_TICK,
            self.tick_interval - self.SPEED_STEP
        )

    # Moves all snakes one step
    def update_state(self):
        now = time.time()

        # No snakes alive
        if not any(p.role == "snake" and p.segments for p in self.players.values()):
            return

        if not self.game_started or now < self.match_start_time or self.game_over:
            return

        # Cleanup expired walls
        self.walls = [w for w in self.walls if w["expires_at"] > now]

        eliminated_players = []
        eater = None

        for username, player in self.players.items():
            if player.role != "snake" or not player.segments:
                continue

            # Occupied positions : other snakes only
            occupied_positions = [
                pos
                for u, p in self.players.items()
                if p.role == "snake" and u != username
                for pos in p.segments
            ]

            old_tail = player.segments[-1]

            # Move snake
            player.add_new_head()

            # Allow moving into own tail
            temp_occupied = occupied_positions.copy()
            if old_tail in temp_occupied:
                temp_occupied.remove(old_tail)

            # Wall collision
            hit_wall = False
            for wall in self.walls:
                if player.get_head() in wall["cells"]:
                    self.log_message("INFO", f"{username} hit a wall")
                    eliminated_players.append(username)
                    hit_wall = True
                    break

            if hit_wall:
                continue

            # Boundary / snake collision
            if not player.check_is_alive(temp_occupied, self.dimensions):
                self.log_message("INFO", f"Player {username}: Has died")
                eliminated_players.append(username)
                continue

            # Food check
            if player.get_head() != self.food_pos:
                player.pop_tail()
            else:
                eater = username

        # Handle food scoring
        if eater is not None:
            self.regenerate_food(eater, [])
            self.sort_leaderboard()

        # Remove eliminated snakes
        for username in eliminated_players:
            self.remove_player(username)

        # Time tracking
        elapsed_time = now - self.match_start_time
        self.remaining_time = max(0, int(self.TIME_LIMIT - elapsed_time))

        # Snake wins by score
        for username, player in self.players.items():
            if (
                player.role == "snake"
                and player.score >= self.SCORE_TO_WIN
                and self.remaining_time > 0
            ):
                self.game_over = True
                self.winner = username
                self.game_over_message = "Snake WON!"
                self.log_message("INFO", self.game_over_message)
                return

        # Controller wins on timeout
        if self.remaining_time <= 0:
            self.game_over = True
            self.winner = next(
                u for u, p in self.players.items() if p.role == "controller"
            )
            self.game_over_message = "You are out of time!"
            self.log_message("INFO", self.game_over_message)
            return

        # Controller wins if snake dies
        if not any(p.role == "snake" for p in self.players.values()):
            self.game_over = True
            self.winner = next(
                u for u, p in self.players.items() if p.role == "controller"
            )
            self.game_over_message = "Controller wins!"
            self.log_message("INFO", self.game_over_message)


    # Sorts the players based on score
    def sort_leaderboard(self):
        self.players = dict(sorted(self.players.items(), key=lambda player: player[1].score, reverse=True))


    # Updates the player's direction to match their keypress
    def update_player_direction(self, username, key):
        if username in self.players and key in State.DIRECTION_MAP:
            player = self.players[username]

            new_dir = State.DIRECTION_MAP[key]
            if not self.is_opposite_direction(new_dir, player.direction):
                player.direction = new_dir
                self.log_message("INFO", f"Player {username}: Direction updated to {key}")

    # Checks if two directions are opposites
    def is_opposite_direction(self, dir1, dir2):
        return [dir1[0]+dir2[0], dir1[1]+dir2[1]] == [0, 0]
    
    def move_food(self, dy, dx):
        y, x = self.food_pos
        ny = max(1, min(self.dimensions[0] - 2, y + dy)) 
        nx = max(1, min(self.dimensions[1] - 2, x + dx)) 
        self.food_pos = [ny, nx]
    
    def spawn_wall_in_front_of_snake(self, controller_username):
        now = time.time()
        history = self.wall_spawns.get(controller_username, [])

        # Remove old timestamps
        history = [t for t in history if now - t < self.WALL_COOLDOWN]
        self.wall_spawns[controller_username] = history

        if len(history) >= self.WALL_LIMIT:
            return False

        # Find the snake
        snake = next((p for p in self.players.values() if p.role == "snake"), None)
        if not snake:
            return False

        head_y, head_x = snake.get_head()
        dy, dx = snake.direction

        # Spawn wall 5 cells ahead
        base_y = head_y + dy * 5
        base_x = head_x + dx * 5

        length = random.randint(5, 7)
        cells = []

        occupied = {
            (y, x)
            for player in self.players.values()
            for y, x in player.segments
        }

        # Wall is perpendicular to movement
        for i in range(-length // 2, length // 2 + 1):
            if dy != 0: # moving vertically : horizontal wall
                y, x = base_y, base_x + i
            else: # moving horizontally : vertical wall
                y, x = base_y + i, base_x

            if (
                1 <= y < self.dimensions[0] - 1 and
                1 <= x < self.dimensions[1] - 1 and
                (y, x) not in occupied
            ):
                cells.append([y, x])

        self.walls.append({
            "cells": cells,
            "expires_at": now + self.WALL_LIFETIME
        })

        history.append(now)
        self.wall_spawns[controller_username] = history
        return True