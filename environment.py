import random
from typing import Set, Tuple, List

class WumpusEnvironment:
    """Wumpus World Environment Implementation"""
    
    def __init__(self, size=10):
        self.size = size
        self.reset()
    
    def reset(self):
        """Reset environment to initial state"""
        self.pits = set()
        self.wumpus_pos = (1, 1)  # Default position, will be randomized
        self.gold_pos = (8, 8)    # Default position, will be randomized
        self.agent_pos = (0, 0)
        self.agent_direction = 0  # 0=North, 1=East, 2=South, 3=West
        self.agent_alive = True
        self.wumpus_alive = True
        self.agent_has_gold = False
        self.agent_has_arrow = True
        self.generate_random_environment()
    
    # [Rest of the original methods remain unchanged...]
    def generate_random_environment(self):
        """Generate a random Wumpus World environment"""
        self.pits.clear()
        
        # Generate pits (avoid starting position and adjacent cells)
        safe_zone = {(0, 0), (0, 1), (1, 0)}
        
        # Create 15-20% pit density
        num_pits = random.randint(int(self.size * self.size * 0.15), 
                                 int(self.size * self.size * 0.20))
        
        for _ in range(num_pits):
            while True:
                pos = (random.randint(0, self.size-1), random.randint(0, self.size-1))
                if pos not in safe_zone and pos not in self.pits:
                    self.pits.add(pos)
                    break
        
        # Place Wumpus (not in safe zone or pits)
        while True:
            pos = (random.randint(0, self.size-1), random.randint(0, self.size-1))
            if pos not in safe_zone and pos not in self.pits:
                self.wumpus_pos = pos
                break
        
        # Place Gold (not in safe zone, pits, or wumpus location)
        while True:
            pos = (random.randint(0, self.size-1), random.randint(0, self.size-1))
            if (pos not in safe_zone and pos not in self.pits and 
                pos != self.wumpus_pos):
                self.gold_pos = pos
                break
        
        # Reset game state
        self.agent_pos = (0, 0)
        self.agent_direction = 0
        self.agent_alive = True
        self.wumpus_alive = True
        self.agent_has_gold = False
        self.agent_has_arrow = True
    
    def get_percepts(self) -> List[str]:
        """Get current percepts at agent's position"""
        percepts = []
        x, y = self.agent_pos
        
        # Check for stench (Wumpus adjacent)
        if self.wumpus_alive:
            wx, wy = self.wumpus_pos
            if abs(x - wx) + abs(y - wy) == 1:  # Manhattan distance = 1
                percepts.append("Stench")
        
        # Check for breeze (pit adjacent)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if (nx, ny) in self.pits:
                    percepts.append("Breeze")
                    break
        
        # Check for glitter (gold at current position)
        if self.agent_pos == self.gold_pos and not self.agent_has_gold:
            percepts.append("Glitter")
        
        # Check for bump (if agent tried to move outside)
        # This is handled in execute_action
        
        # Check for scream (if wumpus was just killed)
        # This is handled in execute_action
        
        return percepts
    
    def execute_action(self, action: str) -> str:
        """Execute an action and return the result"""
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
        """Move agent forward in current direction"""
        x, y = self.agent_pos
        
        # Direction vectors: North, East, South, West
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dx, dy = directions[self.agent_direction]
        
        new_x, new_y = x + dx, y + dy
        
        # Check bounds
        if new_x < 0 or new_x >= self.size or new_y < 0 or new_y >= self.size:
            return "Bump"
        
        # Move agent
        self.agent_pos = (new_x, new_y)
        
        # Check for death conditions
        if self.agent_pos in self.pits:
            self.agent_alive = False
            return "Fell into pit - Agent died"
        
        if self.agent_pos == self.wumpus_pos and self.wumpus_alive:
            self.agent_alive = False
            return "Eaten by Wumpus - Agent died"
        
        return "Moved forward"
    
    def _turn_left(self) -> str:
        """Turn agent left (counterclockwise)"""
        self.agent_direction = (self.agent_direction - 1) % 4
        return "Turned left"
    
    def _turn_right(self) -> str:
        """Turn agent right (clockwise)"""
        self.agent_direction = (self.agent_direction + 1) % 4
        return "Turned right"
    
    def _grab_gold(self) -> str:
        """Grab gold if at gold position"""
        if self.agent_pos == self.gold_pos and not self.agent_has_gold:
            self.agent_has_gold = True
            return "Grabbed gold"
        return "No gold here"
    
    def _shoot_arrow(self) -> str:
        """Shoot arrow in current direction"""
        if not self.agent_has_arrow:
            return "No arrow to shoot"
        
        self.agent_has_arrow = False
        
        # Trace arrow path
        x, y = self.agent_pos
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dx, dy = directions[self.agent_direction]
        
        # Arrow travels until it hits a wall or the wumpus
        while True:
            x, y = x + dx, y + dy
            
            # Check bounds
            if x < 0 or x >= self.size or y < 0 or y >= self.size:
                return "Arrow missed - hit wall"
            
            # Check if arrow hits wumpus
            if (x, y) == self.wumpus_pos and self.wumpus_alive:
                self.wumpus_alive = False
                return "Arrow hit Wumpus - Wumpus died (Scream)"
        
        return "Arrow missed"
    
    def _climb(self) -> str:
        """Climb out of cave (only from starting position)"""
        if self.agent_pos == (0, 0):
            return "Climbed out of cave"
        return "Can only climb from starting position (0,0)"
    
    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within bounds"""
        x, y = pos
        return 0 <= x < self.size and 0 <= y < self.size
    
    def get_adjacent_positions(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid adjacent positions"""
        x, y = pos
        adjacent = []
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.is_valid_position((nx, ny)):
                adjacent.append((nx, ny))
        
        return adjacent