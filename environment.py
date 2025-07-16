import random
from typing import Set, Tuple, List

class WumpusEnvironment:
    def __init__(self, size=10, num_wumpuses=2):
        self.size = size
        self.num_wumpuses = num_wumpuses
        self.reset()

    def reset(self):
        self.pits = set()
        self.wumpus_positions = set()
        self.wumpus_alive = set()
        self.gold_pos = (8, 8)
        self.agent_pos = (0, 0)
        self.agent_direction = 0
        self.agent_alive = True
        self.agent_has_gold = False
        self.agent_has_arrow = True
        self.generate_random_environment()

    def generate_random_environment(self):
        self.pits.clear()
        self.wumpus_positions.clear()
        self.wumpus_alive.clear()
        
        safe_zone = {(0, 0), (0, 1), (1, 0)}
        
        num_pits = random.randint(int(self.size * self.size * 0.08), int(self.size * self.size * 0.10))
        for _ in range(num_pits):
            while True:
                pos = (random.randint(0, self.size-1), random.randint(0, self.size-1))
                if pos not in safe_zone and pos not in self.pits:
                    self.pits.add(pos)
                    break

        for _ in range(self.num_wumpuses):
            while True:
                pos = (random.randint(0, self.size-1), random.randint(0, self.size-1))
                if (pos not in safe_zone and pos not in self.pits and 
                    pos not in self.wumpus_positions and
                    self._minimum_wumpus_distance(pos)):
                    self.wumpus_positions.add(pos)
                    self.wumpus_alive.add(pos)
                    break

        while True:
            pos = (random.randint(0, self.size-1), random.randint(0, self.size-1))
            if pos not in safe_zone and pos not in self.pits and pos not in self.wumpus_positions:
                self.gold_pos = pos
                break

        self.agent_pos = (0, 0)
        self.agent_direction = 0
        self.agent_alive = True
        self.agent_has_gold = False
        self.agent_has_arrow = True

    def _minimum_wumpus_distance(self, pos: Tuple[int, int], min_dist=3) -> bool:
        for wpos in self.wumpus_positions:
            if abs(pos[0] - wpos[0]) + abs(pos[1] - wpos[1]) < min_dist:
                return False
        return True

    def get_percepts(self) -> List[str]:
        percepts = []
        x, y = self.agent_pos

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
          nx, ny = x + dx, y + dy
          if 0 <= nx < self.size and 0 <= ny < self.size:
             if (nx, ny) in self.wumpus_alive:
                percepts.append("Stench")
                break

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if (nx, ny) in self.pits:
                    percepts.append("Breeze")
                    break

        if self.agent_pos == self.gold_pos and not self.agent_has_gold:
            percepts.append("Glitter")

        return percepts

    def execute_action(self, action: str) -> str:
        if not self.agent_alive:
            return "Agent is dead"

        if action == "Forward":
            return self._move_forward()
        elif action == "TurnLeft":
            return self._turn_left()
        elif action == "TurnRight":
            return self._turn_right()
        elif action == "Grab":
            return self._grab_gold()
        elif action == "Shoot":
            return self._shoot_arrow()
        elif action == "Climb":
            return self._climb()
        else:
            return "Invalid action"

    def _move_forward(self) -> str:
        x, y = self.agent_pos
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dx, dy = directions[self.agent_direction]
        new_x, new_y = x + dx, y + dy

        if new_x < 0 or new_x >= self.size or new_y < 0 or new_y >= self.size:
            return "Bump"

        self.agent_pos = (new_x, new_y)

        if self.agent_pos in self.pits:
            self.agent_alive = False
            return "Fell into pit - Agent died"

        if self.agent_pos in self.wumpus_alive:
            self.agent_alive = False
            return "Eaten by Wumpus - Agent died"

        return "Moved forward"

    def _turn_left(self) -> str:
        self.agent_direction = (self.agent_direction - 1) % 4
        return "Turned left"

    def _turn_right(self) -> str:
        self.agent_direction = (self.agent_direction + 1) % 4
        return "Turned right"

    def _grab_gold(self) -> str:
        if self.agent_pos == self.gold_pos and not self.agent_has_gold:
            self.agent_has_gold = True
            return "Grabbed gold"
        return "No gold here"

    def _shoot_arrow(self) -> str:
        if not self.agent_has_arrow:
            return "No arrow to shoot"

        self.agent_has_arrow = False
        x, y = self.agent_pos
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dx, dy = directions[self.agent_direction]

        # Arrow has 70% chance to hit if aimed correctly
        hit_chance = random.random()
        if hit_chance > 0.7:  # 30% chance to miss
            return "Arrow missed"

        while True:
            x, y = x + dx, y + dy
            if x < 0 or x >= self.size or y < 0 or y >= self.size:
                return "Arrow missed - hit wall"

            if (x, y) in self.wumpus_alive:
                self.wumpus_alive.remove((x, y))
                return "Arrow hit Wumpus - Wumpus died (Scream)"

    def _climb(self) -> str:
        if self.agent_pos == (0, 0):
            return "Climbed out of cave"
        return "Can only climb from starting position (0,0)"