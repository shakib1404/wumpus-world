# wumpus_world/knowledge_base.py
from typing import Set, Tuple, List, Dict, Optional
from enum import Enum

class Proposition:
    """Represents a logical proposition"""
    
    def __init__(self, name: str, x: int = None, y: int = None):
        self.name = name
        self.x = x
        self.y = y
    
    def __str__(self):
        if self.x is not None and self.y is not None:
            return f"{self.name}({self.x},{self.y})"
        return self.name
    
    def __eq__(self, other):
        return isinstance(other, Proposition) and \
               self.name == other.name and self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.name, self.x, self.y))

class Clause:
    """Represents a logical clause (disjunction of literals)"""
    
    def __init__(self, literals: List[Tuple[Proposition, bool]]):
        self.literals = literals  # List of (proposition, is_positive)
    
    def __str__(self):
        literal_strs = []
        for prop, is_positive in self.literals:
            if is_positive:
                literal_strs.append(str(prop))
            else:
                literal_strs.append(f"¬{prop}")
        return " ∨ ".join(literal_strs)

class KnowledgeBase:
    """Propositional Logic Knowledge Base for Wumpus World"""
    
    def __init__(self, world_size: int):
        self.world_size = world_size
        self.clauses: List[Clause] = []
        self.facts: Set[Proposition] = set()
        self.visited: Set[Tuple[int, int]] = set()
        self.safe_cells: Set[Tuple[int, int]] = set()
        self.unsafe_cells: Set[Tuple[int, int]] = set()
        self.wumpus_possible: Set[Tuple[int, int]] = set()
        self.pit_possible: Set[Tuple[int, int]] = set()
        
        # Add initial knowledge
        self._add_initial_knowledge()
    
    def _add_initial_knowledge(self):
        """Add initial knowledge about the world"""
        # (0,0) is safe
        self.safe_cells.add((0, 0))
        
        # Add knowledge about adjacent cells relationships
        for x in range(self.world_size):
            for y in range(self.world_size):
                self._add_adjacency_rules(x, y)
    
    def _add_adjacency_rules(self, x: int, y: int):
        """Add rules about breezes and stenches"""
        adjacent = self._get_adjacent_cells(x, y)
        
        if adjacent:
            # Breeze at (x,y) iff there's a pit in adjacent cell
            breeze_prop = Proposition("Breeze", x, y)
            
            # Breeze → (Pit in at least one adjacent cell)
            pit_props = [Proposition("Pit", ax, ay) for ax, ay in adjacent]
            breeze_implies_pit = Clause([(breeze_prop, False)] + [(p, True) for p in pit_props])
            self.clauses.append(breeze_implies_pit)
            
            # No pit in any adjacent cell → No breeze
            no_pits_implies_no_breeze = Clause([(breeze_prop, True)] + [(p, False) for p in pit_props])
            self.clauses.append(no_pits_implies_no_breeze)
            
            # Similar rules for Stench and Wumpus
            stench_prop = Proposition("Stench", x, y)
            wumpus_props = [Proposition("Wumpus", ax, ay) for ax, ay in adjacent]
            
            stench_implies_wumpus = Clause([(stench_prop, False)] + [(w, True) for w in wumpus_props])
            self.clauses.append(stench_implies_wumpus)
            
            no_wumpus_implies_no_stench = Clause([(stench_prop, True)] + [(w, False) for w in wumpus_props])
            self.clauses.append(no_wumpus_implies_no_stench)
    
    def _get_adjacent_cells(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get valid adjacent cells"""
        adjacent = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.world_size and 0 <= ny < self.world_size:
                adjacent.append((nx, ny))
        return adjacent
    
    def add_percept(self, x: int, y: int, percepts: dict):
        """Add percept information to knowledge base"""
        self.visited.add((x, y))
        
        # Add facts based on percepts
        if percepts.get('breeze', False):
            self.facts.add(Proposition("Breeze", x, y))
        else:
            self.facts.add(Proposition("NoBreeze", x, y))
            # If no breeze, adjacent cells are safe from pits
            for ax, ay in self._get_adjacent_cells(x, y):
                if (ax, ay) not in self.visited:
                    self.safe_cells.add((ax, ay))
        
        if percepts.get('stench', False):
            self.facts.add(Proposition("Stench", x, y))
        else:
            self.facts.add(Proposition("NoStench", x, y))
            # If no stench, adjacent cells are safe from Wumpus
            for ax, ay in self._get_adjacent_cells(x, y):
                if (ax, ay) not in self.visited:
                    self.safe_cells.add((ax, ay))
        
        if percepts.get('glitter', False):
            self.facts.add(Proposition("Glitter", x, y))
        
        # Current cell is safe
        self.safe_cells.add((x, y))
        
        # Update possible dangerous cells
        self._update_dangerous_cells()
    
    def _update_dangerous_cells(self):
        """Update sets of possibly dangerous cells based on current knowledge"""
        self.wumpus_possible.clear()
        self.pit_possible.clear()
        
        for x in range(self.world_size):
            for y in range(self.world_size):
                if (x, y) not in self.visited and (x, y) not in self.safe_cells:
                    # Check if this cell could contain a pit or Wumpus
                    if self._could_contain_pit(x, y):
                        self.pit_possible.add((x, y))
                    if self._could_contain_wumpus(x, y):
                        self.wumpus_possible.add((x, y))
    
    def _could_contain_pit(self, x: int, y: int) -> bool:
        """Check if cell could contain a pit based on current knowledge"""
        # Check adjacent cells for breezes
        for ax, ay in self._get_adjacent_cells(x, y):
            if (ax, ay) in self.visited:
                if Proposition("Breeze", ax, ay) in self.facts:
                    return True
        return False
    
    def _could_contain_wumpus(self, x: int, y: int) -> bool:
        """Check if cell could contain Wumpus based on current knowledge"""
        # Check adjacent cells for stenches
        for ax, ay in self._get_adjacent_cells(x, y):
            if (ax, ay) in self.visited:
                if Proposition("Stench", ax, ay) in self.facts:
                    return True
        return False
    
    def is_safe(self, x: int, y: int) -> bool:
        """Check if a cell is known to be safe"""
        return (x, y) in self.safe_cells
    
    def get_safe_unvisited_cells(self) -> List[Tuple[int, int]]:
        """Get list of safe unvisited cells"""
        return [(x, y) for x, y in self.safe_cells if (x, y) not in self.visited]
    
    def get_knowledge_summary(self) -> dict:
        """Get summary of current knowledge"""
        return {
            'visited': len(self.visited),
            'safe_cells': len(self.safe_cells),
            'possible_pits': len(self.pit_possible),
            'possible_wumpus': len(self.wumpus_possible),
            'facts': len(self.facts),
            'clauses': len(self.clauses)
        }