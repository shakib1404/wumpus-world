import random
import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

class CellType(Enum):
    EMPTY = "empty"
    WALL = "wall"
    WOMPHUS = "womphus"
    GOLD = "gold"
    PIT = "pit"
    BREEZE = "breeze"
    STENCH = "stench"
    AGENT = "agent"

class ActionType(Enum):
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    GRAB = "grab"
    SHOOT = "shoot"
    CLIMB = "climb"

@dataclass
class GameState:
    agent_pos: Tuple[int, int]
    agent_alive: bool
    agent_has_gold: bool
    agent_has_arrow: bool
    womphus_alive: bool
    womphus_pos: Tuple[int, int]
    score: int
    game_over: bool
    won: bool

class WomphusWorld:
    def __init__(self, width: int = 4, height: int = 4, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.grid = [[CellType.EMPTY for _ in range(width)] for _ in range(height)]
        
        if seed is not None:
            random.seed(seed)
        
        # Initialize game state
        self.agent_pos = (0, 0)  # Start at bottom-left
        self.agent_alive = True
        self.agent_has_gold = False
        self.agent_has_arrow = True
        self.womphus_alive = True
        self.womphus_pos = (0, 0)
        self.gold_pos = (0, 0)
        self.pits = []
        self.score = 0
        self.game_over = False
        self.won = False
        
        self._generate_world()
    
    def _generate_world(self):
        """Generate the world with womphus, gold, and pits"""
        # Place walls around the border
        for i in range(self.height):
            for j in range(self.width):
                if i == 0 or i == self.height - 1 or j == 0 or j == self.width - 1:
                    if not (i == 0 and j == 0):  # Don't put wall at start position
                        continue
        
        # Place womphus (not at start position)
        while True:
            x, y = random.randint(1, self.width - 2), random.randint(1, self.height - 2)
            if (x, y) != (0, 0):
                self.womphus_pos = (x, y)
                break
        
        # Place gold (not at start position or womphus position)
        while True:
            x, y = random.randint(1, self.width - 2), random.randint(1, self.height - 2)
            if (x, y) != (0, 0) and (x, y) != self.womphus_pos:
                self.gold_pos = (x, y)
                break
        
        # Place pits (20% chance per cell, not at start, womphus, or gold)
        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                if ((j, i) != (0, 0) and 
                    (j, i) != self.womphus_pos and 
                    (j, i) != self.gold_pos and 
                    random.random() < 0.2):
                    self.pits.append((j, i))
        
        self._update_grid()
    
    def _update_grid(self):
        """Update the grid with all elements"""
        # Clear grid
        for i in range(self.height):
            for j in range(self.width):
                self.grid[i][j] = CellType.EMPTY
        
        # Place womphus
        if self.womphus_alive:
            wx, wy = self.womphus_pos
            self.grid[wy][wx] = CellType.WOMPHUS
        
        # Place gold
        if not self.agent_has_gold:
            gx, gy = self.gold_pos
            self.grid[gy][gx] = CellType.GOLD
        
        # Place pits
        for px, py in self.pits:
            self.grid[py][px] = CellType.PIT
        
        # Place breezes (adjacent to pits)
        for px, py in self.pits:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = px + dx, py + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    self.grid[ny][nx] == CellType.EMPTY):
                    self.grid[ny][nx] = CellType.BREEZE
        
        # Place stench (adjacent to womphus)
        if self.womphus_alive:
            wx, wy = self.womphus_pos
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = wx + dx, wy + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    self.grid[ny][nx] == CellType.EMPTY):
                    self.grid[ny][nx] = CellType.STENCH
        
        # Place agent
        ax, ay = self.agent_pos
        if self.agent_alive:
            self.grid[ay][ax] = CellType.AGENT
    
    def get_percepts(self) -> Dict[str, Any]:
        """Get current percepts for the agent"""
        x, y = self.agent_pos
        percepts = {
            "position": self.agent_pos,
            "stench": False,
            "breeze": False,
            "glitter": False,
            "bump": False,
            "scream": False
        }
        
        # Check adjacent cells for stench and breeze
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if self.womphus_alive and (nx, ny) == self.womphus_pos:
                    percepts["stench"] = True
                if (nx, ny) in self.pits:
                    percepts["breeze"] = True
        
        # Check for gold at current position
        if (x, y) == self.gold_pos and not self.agent_has_gold:
            percepts["glitter"] = True
        
        return percepts
    
    def is_valid_move(self, x: int, y: int) -> bool:
        """Check if a move to (x, y) is valid"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def execute_action(self, action: ActionType) -> Dict[str, Any]:
        """Execute an action and return the result"""
        if self.game_over:
            return {"success": False, "message": "Game is over"}
        
        result = {"success": False, "message": "", "percepts": {}}
        
        if action == ActionType.MOVE_UP:
            x, y = self.agent_pos
            new_pos = (x, y + 1)
            if self.is_valid_move(new_pos[0], new_pos[1]):
                self.agent_pos = new_pos
                result["success"] = True
                self.score -= 1  # Movement cost
            else:
                result["message"] = "Bump! Hit a wall"
                result["percepts"] = {"bump": True}
        
        elif action == ActionType.MOVE_DOWN:
            x, y = self.agent_pos
            new_pos = (x, y - 1)
            if self.is_valid_move(new_pos[0], new_pos[1]):
                self.agent_pos = new_pos
                result["success"] = True
                self.score -= 1
            else:
                result["message"] = "Bump! Hit a wall"
                result["percepts"] = {"bump": True}
        
        elif action == ActionType.MOVE_LEFT:
            x, y = self.agent_pos
            new_pos = (x - 1, y)
            if self.is_valid_move(new_pos[0], new_pos[1]):
                self.agent_pos = new_pos
                result["success"] = True
                self.score -= 1
            else:
                result["message"] = "Bump! Hit a wall"
                result["percepts"] = {"bump": True}
        
        elif action == ActionType.MOVE_RIGHT:
            x, y = self.agent_pos
            new_pos = (x + 1, y)
            if self.is_valid_move(new_pos[0], new_pos[1]):
                self.agent_pos = new_pos
                result["success"] = True
                self.score -= 1
            else:
                result["message"] = "Bump! Hit a wall"
                result["percepts"] = {"bump": True}
        
        elif action == ActionType.GRAB:
            if self.agent_pos == self.gold_pos and not self.agent_has_gold:
                self.agent_has_gold = True
                result["success"] = True
                result["message"] = "Grabbed gold!"
                self.score += 1000
            else:
                result["message"] = "Nothing to grab here"
        
        elif action == ActionType.SHOOT:
            if self.agent_has_arrow:
                self.agent_has_arrow = False
                result["success"] = True
                self.score -= 10  # Arrow cost
                
                # Check if womphus is in line of sight
                x, y = self.agent_pos
                # For simplicity, assume arrow goes in random direction
                # In a real implementation, you'd specify direction
                if self.womphus_alive and self._is_in_line_of_sight(self.agent_pos, self.womphus_pos):
                    self.womphus_alive = False
                    result["message"] = "Arrow hit! Womphus is dead!"
                    result["percepts"] = {"scream": True}
                else:
                    result["message"] = "Arrow missed!"
            else:
                result["message"] = "No arrow to shoot"
        
        elif action == ActionType.CLIMB:
            if self.agent_pos == (0, 0):
                if self.agent_has_gold:
                    self.game_over = True
                    self.won = True
                    self.score += 1000
                    result["success"] = True
                    result["message"] = "Climbed out with gold! You won!"
                else:
                    self.game_over = True
                    result["success"] = True
                    result["message"] = "Climbed out without gold."
            else:
                result["message"] = "Can only climb at the starting position (0, 0)"
        
        # Check for death conditions after movement
        if result["success"] and action in [ActionType.MOVE_UP, ActionType.MOVE_DOWN, 
                                          ActionType.MOVE_LEFT, ActionType.MOVE_RIGHT]:
            if self.agent_pos in self.pits:
                self.agent_alive = False
                self.game_over = True
                self.score -= 1000
                result["message"] = "Fell into a pit! Game over!"
            elif self.agent_pos == self.womphus_pos and self.womphus_alive:
                self.agent_alive = False
                self.game_over = True
                self.score -= 1000
                result["message"] = "Eaten by womphus! Game over!"
        
        # Update grid and get percepts
        self._update_grid()
        if not self.game_over:
            result["percepts"].update(self.get_percepts())
        
        return result
    
    def _is_in_line_of_sight(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """Check if two positions are in line of sight (same row or column)"""
        return pos1[0] == pos2[0] or pos1[1] == pos2[1]
    
    def get_game_state(self) -> GameState:
        """Get current game state"""
        return GameState(
            agent_pos=self.agent_pos,
            agent_alive=self.agent_alive,
            agent_has_gold=self.agent_has_gold,
            agent_has_arrow=self.agent_has_arrow,
            womphus_alive=self.womphus_alive,
            womphus_pos=self.womphus_pos,
            score=self.score,
            game_over=self.game_over,
            won=self.won
        )
    
    def get_visible_grid(self) -> List[List[str]]:
        """Get a representation of what the agent can see"""
        visible = [["?" for _ in range(self.width)] for _ in range(self.height)]
        
        # Agent can see their current position
        x, y = self.agent_pos
        visible[y][x] = "A"
        
        # Show percepts
        percepts = self.get_percepts()
        if percepts["glitter"]:
            visible[y][x] = "G"
        if percepts["stench"]:
            visible[y][x] += "S"
        if percepts["breeze"]:
            visible[y][x] += "B"
        
        return visible
    
    def print_world(self, show_all: bool = False):
        """Print the world state"""
        print(f"Score: {self.score}")
        print(f"Agent: {self.agent_pos}, Alive: {self.agent_alive}")
        print(f"Gold: {'Has gold' if self.agent_has_gold else 'No gold'}")
        print(f"Arrow: {'Has arrow' if self.agent_has_arrow else 'No arrow'}")
        print(f"Womphus: {self.womphus_pos}, Alive: {self.womphus_alive}")
        print()
        
        if show_all:
            print("Full world:")
            for i in range(self.height - 1, -1, -1):
                row = ""
                for j in range(self.width):
                    cell = self.grid[i][j]
                    if cell == CellType.EMPTY:
                        row += "."
                    elif cell == CellType.WOMPHUS:
                        row += "W"
                    elif cell == CellType.GOLD:
                        row += "G"
                    elif cell == CellType.PIT:
                        row += "P"
                    elif cell == CellType.BREEZE:
                        row += "B"
                    elif cell == CellType.STENCH:
                        row += "S"
                    elif cell == CellType.AGENT:
                        row += "A"
                    row += " "
                print(f"{i}: {row}")
        else:
            print("Visible world:")
            visible = self.get_visible_grid()
            for i in range(self.height - 1, -1, -1):
                row = ""
                for j in range(self.width):
                    row += visible[i][j] + " "
                print(f"{i}: {row}")
        
        print("   " + " ".join(str(i) for i in range(self.width)))
        print()

# Example usage and simple AI agent
class SimpleAI:
    def __init__(self):
        self.visited = set()
        self.safe_cells = set()
        self.dangerous_cells = set()
    
    def choose_action(self, world: WomphusWorld) -> ActionType:
        """Simple AI that chooses actions based on percepts"""
        percepts = world.get_percepts()
        pos = percepts["position"]
        
        self.visited.add(pos)
        
        # If there's gold, grab it
        if percepts["glitter"]:
            return ActionType.GRAB
        
        # If we have gold, go back to start
        if world.agent_has_gold:
            if pos == (0, 0):
                return ActionType.CLIMB
            # Simple pathfinding back to (0, 0)
            x, y = pos
            if x > 0:
                return ActionType.MOVE_LEFT
            elif y > 0:
                return ActionType.MOVE_DOWN
        
        # Avoid dangerous cells
        if percepts["breeze"] or percepts["stench"]:
            # Try to move to a safe cell
            for action in [ActionType.MOVE_UP, ActionType.MOVE_DOWN, 
                          ActionType.MOVE_LEFT, ActionType.MOVE_RIGHT]:
                # This would need better logic in a real implementation
                pass
        
        # Random exploration
        actions = [ActionType.MOVE_UP, ActionType.MOVE_DOWN, 
                   ActionType.MOVE_LEFT, ActionType.MOVE_RIGHT]
        return random.choice(actions)

# Game runner
def run_game():
    world = WomphusWorld(4, 4, seed=42)
    ai = SimpleAI()
    
    print("Starting Womphus World Game!")
    world.print_world(show_all=True)
    
    max_turns = 100
    turn = 0
    
    while not world.game_over and turn < max_turns:
        turn += 1
        print(f"\n--- Turn {turn} ---")
        
        # AI chooses action
        action = ai.choose_action(world)
        print(f"AI chooses: {action.value}")
        
        # Execute action
        result = world.execute_action(action)
        print(f"Result: {result['message']}")
        
        # Print current state
        world.print_world(show_all=False)
        
        if world.game_over:
            if world.won:
                print("🎉 AI WON! 🎉")
            else:
                print("💀 AI LOST! 💀")
            break
    
    if turn >= max_turns:
        print("Game ended due to turn limit")
    
    final_state = world.get_game_state()
    print(f"Final score: {final_state.score}")

if __name__ == "__main__":
    run_game()