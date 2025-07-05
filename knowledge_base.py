from typing import Set, Tuple, List, Dict
from collections import defaultdict

class KnowledgeBase:
    """Knowledge Base for the Wumpus World Agent"""
    
    def __init__(self, size=10):
        self.size = size
        self.visited = set()
        self.safe_cells = set()
        self.pit_possible = set()
        self.wumpus_possible = set()
        self.pit_definite = set()
        self.wumpus_definite = set()
        self.breeze_locations = set()
        self.stench_locations = set()
        self.wumpus_alive = True
        self.gold_location = None
        self.add_visit((0, 0))
        
    def add_visit(self, pos: Tuple[int, int]):
        """Mark a cell as visited and safe"""
        self.visited.add(pos)
        self.safe_cells.add(pos)
        # Remove from possible danger sets
        self.pit_possible.discard(pos)
        self.wumpus_possible.discard(pos)
        self.pit_definite.discard(pos)
        self.wumpus_definite.discard(pos)
    

    
    def add_percept(self, pos: Tuple[int, int], percepts: List[str]):
        """Process percepts at a given position"""
        if "Breeze" in percepts:
            self.breeze_locations.add(pos)
        
        if "Stench" in percepts:
            self.stench_locations.add(pos)
        
        if "Glitter" in percepts:
            self.gold_location = pos
        
        # Update possible danger locations
        self._update_danger_inference(pos, percepts)
    
    def _update_danger_inference(self, pos: Tuple[int, int], percepts: List[str]):
        """Update danger inference based on percepts"""
        x, y = pos
        adjacent_cells = []
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                adjacent_cells.append((nx, ny))
        
        # If breeze detected, adjacent cells might have pits
        if "Breeze" in percepts:
            for adj_pos in adjacent_cells:
                if adj_pos not in self.visited and adj_pos not in self.safe_cells:
                    self.pit_possible.add(adj_pos)
        else:
            # No breeze means no pits in adjacent cells
            for adj_pos in adjacent_cells:
                if adj_pos not in self.visited:
                    self.safe_cells.add(adj_pos)
                self.pit_possible.discard(adj_pos)
        
        # If stench detected, adjacent cells might have wumpus
        if "Stench" in percepts and self.wumpus_alive:
            for adj_pos in adjacent_cells:
                if adj_pos not in self.visited and adj_pos not in self.safe_cells:
                    self.wumpus_possible.add(adj_pos)
        else:
            # No stench means no wumpus in adjacent cells
            for adj_pos in adjacent_cells:
                self.wumpus_possible.discard(adj_pos)
    
    def wumpus_killed(self):
        """Update knowledge when wumpus is killed"""
        self.wumpus_alive = False
        self.wumpus_possible.clear()
        self.wumpus_definite.clear()
    
    def get_safe_unvisited_cells(self) -> Set[Tuple[int, int]]:
        """Get cells that are safe but not yet visited"""
        return self.safe_cells - self.visited
    
    def is_safe(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is known to be safe"""
        return pos in self.safe_cells
    
    def is_dangerous(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is known to be dangerous"""
        return (pos in self.pit_definite or 
                pos in self.wumpus_definite or
                (pos in self.pit_possible and pos not in self.safe_cells) or
                (pos in self.wumpus_possible and pos not in self.safe_cells and self.wumpus_alive))