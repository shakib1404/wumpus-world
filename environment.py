# wumpus_world/environment.py
import random
from typing import Set, Tuple, List, Optional
import json

class WumpusEnvironment:
    """Represents the Wumpus World environment"""
    
    def __init__(self, size: int = 10):
        self.size = size
        self.wumpus_pos: Optional[Tuple[int, int]] = None
        self.pits: Set[Tuple[int, int]] = set()
        self.gold_pos: Optional[Tuple[int, int]] = None
        self.agent_pos: Tuple[int, int] = (0, 0)
        self.agent_direction: int = 0  # 0=North, 1=East, 2=South, 3=West
        self.agent_alive: bool = True
        self.agent_has_arrow: bool = True
        self.agent_has_gold: bool = False
        self.wumpus_alive: bool = True
        
    def generate_random_environment(self, pit_probability: float = 0.2):
        """Generate a random Wumpus World environment"""
        # Clear existing environment
        self.pits.clear()
        
        # Place Wumpus (not at start position)
        while True:
            pos = (random.randint(0, self.size-1), random.randint(0, self.size-1))
            if pos != (0, 0):
                self.wumpus_pos = pos
                break
        
        # Place gold (not at start position or Wumpus position)
        while True:
            pos = (random.randint(0, self.size-1), random.randint(0, self.size-1))
            if pos not in [(0, 0), self.wumpus_pos]:
                self.gold_pos = pos
                break
        
        # Place pits
        for x in range(self.size):
            for y in range(self.size):
                if (x, y) not in [(0, 0), self.wumpus_pos, self.gold_pos]:
                    if random.random() < pit_probability:
                        self.pits.add((x, y))
    
    def load_from_file(self, filename: str):
        """Load environment from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.size = data.get('size', 10)
            self.wumpus_pos = tuple(data['wumpus'])
            self.gold_pos = tuple(data['gold'])
            self.pits = set(tuple(pit) for pit in data['pits'])
            
        except FileNotFoundError:
            print(f"File {filename} not found. Generating random environment.")
            self.generate_random_environment()
    
    def save_to_file(self, filename: str):
        """Save current environment to JSON file"""
        data = {
            'size': self.size,
            'wumpus': list(self.wumpus_pos) if self.wumpus_pos else None,
            'gold': list(self.gold_pos) if self.gold_pos else None,
            'pits': [list(pit) for pit in self.pits]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_percepts(self) -> dict:
        """Get current percepts for the agent"""
        x, y = self.agent_pos
        percepts = {
            'stench': False,
            'breeze': False,
            'glitter': False,
            'bump': False,
            'scream': False
        }
        
        # Check for stench (adjacent to Wumpus)
        if self.wumpus_alive and self.wumpus_pos:
            wx, wy = self.wumpus_pos
            if abs(x - wx) + abs(y - wy) == 1:
                percepts['stench'] = True
        
        # Check for breeze (adjacent to pit)
        for px, py in self.pits:
            if abs(x - px) + abs(y - py) == 1:
                percepts['breeze'] = True
                break
        
        # Check for glitter (same position as gold)
        if self.gold_pos == self.agent_pos:
            percepts['glitter'] = True
        
        return percepts
    
    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within bounds"""
        x, y = pos
        return 0 <= x < self.size and 0 <= y < self.size
    
    def move_agent(self, action: str) -> dict:
        """Execute agent action and return result"""
        result = {'success': False, 'percepts': {}, 'game_over': False, 'won': False}
        
        if not self.agent_alive:
            result['game_over'] = True
            return result
        
        x, y = self.agent_pos
        
        if action == 'FORWARD':
            # Calculate new position based on direction
            dx, dy = [(0, 1), (1, 0), (0, -1), (-1, 0)][self.agent_direction]
            new_pos = (x + dx, y + dy)
            
            if self.is_valid_position(new_pos):
                self.agent_pos = new_pos
                result['success'] = True
                
                # Check for death conditions
                if new_pos == self.wumpus_pos and self.wumpus_alive:
                    self.agent_alive = False
                    result['game_over'] = True
                elif new_pos in self.pits:
                    self.agent_alive = False
                    result['game_over'] = True
            else:
                result['percepts']['bump'] = True
        
        elif action == 'TURN_LEFT':
            self.agent_direction = (self.agent_direction - 1) % 4
            result['success'] = True
        
        elif action == 'TURN_RIGHT':
            self.agent_direction = (self.agent_direction + 1) % 4
            result['success'] = True
        
        elif action == 'GRAB':
            if self.agent_pos == self.gold_pos and not self.agent_has_gold:
                self.agent_has_gold = True
                result['success'] = True
        
        elif action == 'SHOOT':
            if self.agent_has_arrow:
                self.agent_has_arrow = False
                result['success'] = True
                
                # Check if arrow hits Wumpus
                x, y = self.agent_pos
                dx, dy = [(0, 1), (1, 0), (0, -1), (-1, 0)][self.agent_direction]
                
                arrow_x, arrow_y = x + dx, y + dy
                while self.is_valid_position((arrow_x, arrow_y)):
                    if (arrow_x, arrow_y) == self.wumpus_pos and self.wumpus_alive:
                        self.wumpus_alive = False
                        result['percepts']['scream'] = True
                        break
                    arrow_x += dx
                    arrow_y += dy
        
        elif action == 'CLIMB':
            if self.agent_pos == (0, 0):
                result['game_over'] = True
                result['won'] = self.agent_has_gold
                result['success'] = True
        
        # Get current percepts
        if self.agent_alive:
            result['percepts'].update(self.get_percepts())
        
        return result
