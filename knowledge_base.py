from typing import Set, Tuple, List, Dict
from collections import defaultdict

class KnowledgeBase:
    def __init__(self, size=10, num_wumpuses=2):
        self.size = size
        self.num_wumpuses = num_wumpuses 
        self.visited = set()
        self.safe_cells = set()
        self.pit_possible = set()
        self.wumpus_possible = set()
        self.wumpus_definite = set()
        self.pit_definite = set() 
        self.breeze_locations = set()
        self.stench_locations = set()
        self.no_stench_locations = set()
        self.no_breeze_locations = set()
        
        # New sets for definitive safety
        self.no_pit = set()      # Positions definitely safe from pits
        self.no_wumpus = set()   # Positions definitely safe from wumpuses
        
        self.wumpuses_killed = 0
        self.wumpus_alive = True
        self.percepts = {}
        self.certainty_map = {}
        self.estimated_wumpus_count = num_wumpuses
        
        # Initialize starting position as safe
        self.add_visit((0, 0))
        self.safe_cells.add((0, 0))

    def add_visit(self, pos: Tuple[int, int]):
        """Mark a position as visited and definitely safe"""
        self.visited.add(pos)
        self.safe_cells.add(pos)
        
        # Remove from danger sets since we've been there safely
        self.pit_possible.discard(pos)
        self.wumpus_possible.discard(pos)
        self.wumpus_definite.discard(pos)
        self.pit_definite.discard(pos)

    def add_percept(self, pos: Tuple[int, int], percepts: List[str]):
        """Add percept information and update knowledge"""
        self.percepts[pos] = percepts
        print("hello i am percepts ",percepts)

        if "Breeze" not in percepts: # Handle stench perception
         if "Stench" in percepts:
            print("hi")
            self.stench_locations.add(pos)
            if self.wumpus_alive:
                self._add_wumpus_possibilities(pos)
         else:
            self.no_stench_locations.add(pos)
            if self.wumpus_alive:
                self._mark_adjacent_safe_from_wumpus(pos)
        
       
        

              # Handle stench perception
        # Handle breeze perception
        if "Breeze" in percepts:
            print("hello")
            self.breeze_locations.add(pos)
            self._add_pit_possibilities(pos)
            
        else:
            self.no_breeze_locations.add(pos)
            self._mark_adjacent_safe_from_pits(pos)
            
        if "Breeze" in percepts and "Stench" not in percepts:
            self.no_stench_locations.add(pos)
            if self.wumpus_alive:
                self._mark_adjacent_safe_from_wumpus(pos)
        # Update probability calculations
        self._update_safety_knowledge()

    def _add_pit_possibilities(self, pos: Tuple[int, int]):
        """Add possible pit locations based on breeze"""
        for adj in self._get_adjacent(pos):
            if adj not in self.visited and adj not in self.safe_cells:
                # Check if position is in no_pit set before adding to pit_possible
                if adj not in self.no_pit:
                    self.pit_possible.add(adj)

    def _add_wumpus_possibilities(self, pos: Tuple[int, int]):
        """Add possible wumpus locations based on stench"""
        for adj in self._get_adjacent(pos):
            if adj not in self.visited and adj not in self.safe_cells:
                # Check if position is in no_wumpus set before adding to wumpus_possible
                if adj not in self.no_wumpus:
                    self.wumpus_possible.add(adj)

    def _mark_adjacent_safe_from_pits(self, pos: Tuple[int, int]):
        """Mark adjacent cells as safe from pits (no breeze detected)"""
        for adj in self._get_adjacent(pos):
            # Add to no_pit set - this position is definitely safe from pits
            self.no_pit.add(adj)
            
            # Remove from pit possibilities
            self.pit_possible.discard(adj)
            self.pit_definite.discard(adj)

           
       
            
            # Mark as safe if not contradicted by wumpus evidence
            if adj not in self.visited and adj not in self.wumpus_definite:
                if adj not in self.wumpus_possible:
                    self.safe_cells.add(adj)

    def _mark_adjacent_safe_from_wumpus(self, pos: Tuple[int, int]):
        """Mark adjacent cells as safe from wumpus (no stench detected)"""
        for adj in self._get_adjacent(pos):
            # Add to no_wumpus set - this position is definitely safe from wumpuses
            self.no_wumpus.add(adj)
            
            # Remove from wumpus possibilities
            self.wumpus_possible.discard(adj)
            self.wumpus_definite.discard(adj)
            
            # Mark as safe if not contradicted by pit evidence
            if adj not in self.visited and adj not in self.pit_definite:
                if adj not in self.pit_possible:
                    self.safe_cells.add(adj)

    def _update_safety_knowledge(self):
        """Update safety knowledge based on all available information"""
        # Update wumpus certainty
        for pos in list(self.wumpus_possible):
            # Check if position is ruled out by no-stench locations or no_wumpus set
            adjacent_to_no_stench = any(adj in self.no_stench_locations 
                                      for adj in self._get_adjacent(pos))
            
            if adjacent_to_no_stench or pos in self.no_wumpus:
                self.wumpus_possible.discard(pos)
                continue
            
            # Calculate probability based on stench evidence
            stench_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                                 if adj in self.stench_locations)
            visited_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                                   if adj in self.visited)
            
            if visited_neighbors > 0:
                self.certainty_map[pos] = min(1.0, stench_neighbors / visited_neighbors)
            else:
                self.certainty_map[pos] = 0.5  # Default uncertainty
        
        # Update pit possibilities
        for pos in list(self.pit_possible):
            # Check if position is ruled out by no-breeze locations or no_pit set
            adjacent_to_no_breeze = any(adj in self.no_breeze_locations 
                                      for adj in self._get_adjacent(pos))
            
            if adjacent_to_no_breeze or pos in self.no_pit:
                self.pit_possible.discard(pos)
                # Mark as safe if not a wumpus location
                if pos not in self.wumpus_possible and pos not in self.wumpus_definite:
                    self.safe_cells.add(pos)

    def _get_adjacent(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all adjacent positions within bounds"""
        x, y = pos
        adjacent = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                adjacent.append((nx, ny))
        return adjacent

    def wumpus_killed(self):
        """Handle wumpus death"""
        self.wumpuses_killed += 1
        if self.wumpuses_killed >= self.num_wumpuses:
            # All wumpuses are dead - clear wumpus-related dangers
            self.wumpus_possible.clear()
            self.wumpus_definite.clear()
            self.wumpus_alive = False
            
            # Mark previously wumpus-threatened cells as safe if no pit threat
            for pos in list(self.wumpus_possible):
                if pos not in self.pit_possible and pos not in self.pit_definite:
                    self.safe_cells.add(pos)

    def is_safe(self, pos: Tuple[int, int]) -> bool:
        """Check if position is known to be safe"""
        return pos in self.safe_cells

    def is_dangerous(self, pos: Tuple[int, int]) -> bool:
        """Check if position is known to be dangerous"""
        if pos in self.visited:
            return False
        
        # Definitely dangerous if confirmed pit or wumpus
        if pos in self.pit_definite or pos in self.wumpus_definite:
            return True
        
        # Possibly dangerous if in possibility sets
        return pos in self.pit_possible or (self.wumpus_alive and pos in self.wumpus_possible)

    def is_definitely_safe(self, pos: Tuple[int, int]) -> bool:
        """Check if position is definitely safe (no possibility of danger)"""
        if pos in self.visited:
            return True
        
        # Must be in safe cells AND not in any danger possibility
        # OR be in both no_pit and no_wumpus sets
        return ((pos in self.safe_cells and 
                pos not in self.pit_possible and 
                pos not in self.wumpus_possible and
                pos not in self.pit_definite and
                pos not in self.wumpus_definite) or
                (pos in self.no_pit and pos in self.no_wumpus))

    def get_safe_unvisited_cells(self) -> Set[Tuple[int, int]]:
        """Get cells that are safe and unvisited"""
        return self.safe_cells - self.visited

    def get_definitely_safe_unvisited_cells(self) -> Set[Tuple[int, int]]:
        """Get cells that are definitely safe and unvisited"""
        definitely_safe = set()
        for pos in self.safe_cells - self.visited:
            if self.is_definitely_safe(pos):
                definitely_safe.add(pos)
        return definitely_safe

    def get_wumpus_probability(self, pos: Tuple[int, int]) -> float:
        """Get probability that wumpus is at given position"""
        if not self.wumpus_alive or pos not in self.wumpus_possible or pos in self.no_wumpus:
            return 0.0
        return self.certainty_map.get(pos, 0.3)

    def get_pit_probability(self, pos: Tuple[int, int]) -> float:
        """Get probability that pit is at given position"""
        if pos not in self.pit_possible or pos in self.no_pit:
            return 0.0
        
        # Calculate based on breeze evidence
        breeze_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                             if adj in self.breeze_locations)
        visited_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                               if adj in self.visited)
        
        if visited_neighbors > 0:
            return min(1.0, breeze_neighbors / visited_neighbors)
        else:
            return 0.2  # Default low probability

    def all_wumpuses_dead(self) -> bool:
        """Check if all wumpuses are dead"""
        return self.wumpuses_killed >= self.num_wumpuses