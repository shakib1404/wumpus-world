# wumpus_world/knowledge_base.py
from typing import Set, Tuple, List, Dict
from enum import Enum

class Proposition:
    """Represents a logical proposition in the Wumpus World."""
    
    def __init__(self, name: str, x: int = None, y: int = None):
        self.name = name
        self.x = x
        self.y = y
    
    def __str__(self) -> str:
        if self.x is not None and self.y is not None:
            return f"{self.name}({self.x},{self.y})"
        return self.name
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Proposition):
            return False
        return self.name == other.name and self.x == other.x and self.y == other.y
    
    def __hash__(self) -> int:
        return hash((self.name, self.x, self.y))

class Clause:
    """Represents a logical clause (disjunction of literals) in the knowledge base."""
    
    def __init__(self, literals: List[Tuple[Proposition, bool]]):
        self.literals = literals  # List of (proposition, is_positive)
    
    def __str__(self) -> str:
        literal_strs = [str(prop) if is_positive else f"¬{prop}" 
                        for prop, is_positive in self.literals]
        return " ∨ ".join(literal_strs)

class KnowledgeBase:
    """Propositional Logic Knowledge Base for Wumpus World."""
    
    def __init__(self, world_size: int):
        self.world_size = world_size
        self.clauses: List[Clause] = []
        self.facts: Set[Proposition] = set()
        self.visited: Set[Tuple[int, int]] = {(0, 0)}  # Start position is always visited
        self.safe_cells: Set[Tuple[int, int]] = {(0, 0)}  # Start position is always safe
        self.wumpus_possible: Set[Tuple[int, int]] = set()
        self.pit_possible: Set[Tuple[int, int]] = set()
        
        # Initialize knowledge base with adjacency rules
        self._add_initial_knowledge()
    
    def _add_initial_knowledge(self):
        """Add initial knowledge about the world, including adjacency rules."""
        for x in range(self.world_size):
            for y in range(self.world_size):
                if (x, y) != (0, 0):  # Skip the starting position
                    self.wumpus_possible.add((x, y))
                    self.pit_possible.add((x, y))
                self._add_adjacency_rules(x, y)
    
    def _add_adjacency_rules(self, x: int, y: int):
        """Add logical rules for breezes and stenches based on adjacent cells."""
        adjacent = self._get_adjacent_cells(x, y)
        
        # Breeze rules: Breeze(x,y) ↔ (Pit(ax1,ay1) ∨ Pit(ax2,ay2) ∨ ...)
        breeze_prop = Proposition("Breeze", x, y)
        pit_props = [Proposition("Pit", ax, ay) for ax, ay in adjacent]
        
        if pit_props:
            # Breeze → (Pit in at least one adjacent cell)
            self.clauses.append(Clause([(breeze_prop, False)] + [(p, True) for p in pit_props]))
            # No pits in adjacent cells → No breeze
            self.clauses.append(Clause([(breeze_prop, True)] + [(p, False) for p in pit_props]))
        
        # Stench rules: Stench(x,y) ↔ (Wumpus(ax1,ay1) ∨ Wumpus(ax2,ay2) ∨ ...)
        stench_prop = Proposition("Stench", x, y)
        wumpus_props = [Proposition("Wumpus", ax, ay) for ax, ay in adjacent]
        
        if wumpus_props:
            # Stench → (Wumpus in at least one adjacent cell)
            self.clauses.append(Clause([(stench_prop, False)] + [(w, True) for w in wumpus_props]))
            # No Wumpus in adjacent cells → No stench
            self.clauses.append(Clause([(stench_prop, True)] + [(w, False) for w in wumpus_props]))
    
    def _get_adjacent_cells(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Return valid adjacent cells for a given position."""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # North, South, East, West
        adjacent = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.world_size and 0 <= ny < self.world_size:
                adjacent.append((nx, ny))
        return adjacent
    
    def add_percept(self, x: int, y: int, percepts: Dict[str, bool]):
        """Add percept information to the knowledge base and update inferences."""
        self.visited.add((x, y))
        self.safe_cells.add((x, y))  # Current cell is safe if visited
        
        # Remove current cell from possible danger sets
        self.wumpus_possible.discard((x, y))
        self.pit_possible.discard((x, y))
        
        # Process percepts
        if percepts.get('breeze', False):
            self.facts.add(Proposition("Breeze", x, y))
        else:
            self.facts.add(Proposition("NoBreeze", x, y))
            # No breeze implies adjacent cells are pit-free
            for ax, ay in self._get_adjacent_cells(x, y):
                self.safe_cells.add((ax, ay))
                self.pit_possible.discard((ax, ay))
        
        if percepts.get('stench', False):
            self.facts.add(Proposition("Stench", x, y))
        else:
            self.facts.add(Proposition("NoStench", x, y))
            # No stench implies adjacent cells are Wumpus-free
            for ax, ay in self._get_adjacent_cells(x, y):
                self.safe_cells.add((ax, ay))
                self.wumpus_possible.discard((ax, ay))
        
        if percepts.get('glitter', False):
            self.facts.add(Proposition("Glitter", x, y))
        
        # Update possible danger cells
        self._update_dangerous_cells()
    
    def _update_dangerous_cells(self):
        """Update sets of cells that could contain pits or the Wumpus."""
        # Start with all unvisited, non-safe cells as potentially dangerous
        for x in range(self.world_size):
            for y in range(self.world_size):
                if (x, y) not in self.visited and (x, y) not in self.safe_cells:
                    if self._could_contain_pit(x, y):
                        self.pit_possible.add((x, y))
                    if self._could_contain_wumpus(x, y):
                        self.wumpus_possible.add((x, y))
    
    def _could_contain_pit(self, x: int, y: int) -> bool:
        """Check if a cell could contain a pit based on current knowledge."""
        for ax, ay in self._get_adjacent_cells(x, y):
            if (ax, ay) in self.visited and Proposition("Breeze", ax, ay) in self.facts:
                return True
            if (ax, ay) in self.visited and Proposition("NoBreeze", ax, ay) in self.facts:
                return False
        return True  # Unknown if no adjacent cells have breeze information
    
    def _could_contain_wumpus(self, x: int, y: int) -> bool:
        """Check if a cell could contain the Wumpus based on current knowledge."""
        for ax, ay in self._get_adjacent_cells(x, y):
            if (ax, ay) in self.visited and Proposition("Stench", ax, ay) in self.facts:
                return True
            if (ax, ay) in self.visited and Proposition("NoStench", ax, ay) in self.facts:
                return False
        return True  # Unknown if no adjacent cells have stench information
    
    def is_safe(self, x: int, y: int) -> bool:
        """Check if a cell is known to be safe."""
        return (x, y) in self.safe_cells
    
    def get_safe_unvisited_cells(self) -> List[Tuple[int, int]]:
        """Return a list of safe, unvisited cells."""
        return sorted([(x, y) for x, y in self.safe_cells if (x, y) not in self.visited])
    
    def get_knowledge_summary(self) -> Dict[str, int]:
        """Return a summary of current knowledge."""
        return {
            'visited': len(self.visited),
            'safe_cells': len(self.safe_cells),
            'possible_pits': len(self.pit_possible),
            'possible_wumpus': len(self.wumpus_possible),
            'facts': len(self.facts),
            'clauses': len(self.clauses)
        }
    
    def add_safe_cell(self, x: int, y: int):
        """Mark a cell as safe and remove it from danger sets."""
        self.safe_cells.add((x, y))
        self.wumpus_possible.discard((x, y))
        self.pit_possible.discard((x, y))
    
    def add_visited(self, x: int, y: int):
        """Mark a cell as visited and safe."""
        self.visited.add((x, y))
        self.safe_cells.add((x, y))
        self.wumpus_possible.discard((x, y))
        self.pit_possible.discard((x, y))