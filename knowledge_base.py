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
        
        self.no_pit = set()
        self.no_wumpus = set()
        
        self.wumpuses_killed = 0
        self.wumpus_alive = True
        self.percepts = {}
        self.certainty_map = {}
        self.estimated_wumpus_count = num_wumpuses
        
        self.add_visit((0, 0))
        self.safe_cells.add((0, 0))

    def add_visit(self, pos: Tuple[int, int]):
        self.visited.add(pos)
        self.safe_cells.add(pos)
        
        self.pit_possible.discard(pos)
        self.wumpus_possible.discard(pos)
        self.wumpus_definite.discard(pos)
        self.pit_definite.discard(pos)

    def add_percept(self, pos: Tuple[int, int], percepts: List[str]):
        self.percepts[pos] = percepts
        print("hello i am percepts ",percepts)

        if "Breeze" not in percepts:
         if "Stench" in percepts:
            print("hi")
            self.stench_locations.add(pos)
            if self.wumpus_alive:
                self._add_wumpus_possibilities(pos)
         else:
            self.no_stench_locations.add(pos)
            if self.wumpus_alive:
                self._mark_adjacent_safe_from_wumpus(pos)

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
        self._update_safety_knowledge()

    def _add_pit_possibilities(self, pos: Tuple[int, int]):
        for adj in self._get_adjacent(pos):
            if adj not in self.visited and adj not in self.safe_cells:
                if adj not in self.no_pit:
                    self.pit_possible.add(adj)

    def _add_wumpus_possibilities(self, pos: Tuple[int, int]):
        for adj in self._get_adjacent(pos):
            if adj not in self.visited and adj not in self.safe_cells:
                if adj not in self.no_wumpus:
                    self.wumpus_possible.add(adj)

    def _mark_adjacent_safe_from_pits(self, pos: Tuple[int, int]):
        for adj in self._get_adjacent(pos):
            self.no_pit.add(adj)
            
            self.pit_possible.discard(adj)
            self.pit_definite.discard(adj)
            
            if adj not in self.visited and adj not in self.wumpus_definite:
                if adj not in self.wumpus_possible:
                    self.safe_cells.add(adj)

    def _mark_adjacent_safe_from_wumpus(self, pos: Tuple[int, int]):
        for adj in self._get_adjacent(pos):
            self.no_wumpus.add(adj)
            
            self.wumpus_possible.discard(adj)
            self.wumpus_definite.discard(adj)
            
            if adj not in self.visited and adj not in self.pit_definite:
                if adj not in self.pit_possible:
                    self.safe_cells.add(adj)

    def _update_safety_knowledge(self):
        for pos in list(self.wumpus_possible):
            adjacent_to_no_stench = any(adj in self.no_stench_locations 
                                      for adj in self._get_adjacent(pos))
            
            if adjacent_to_no_stench or pos in self.no_wumpus:
                self.wumpus_possible.discard(pos)
                continue
            
            stench_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                                 if adj in self.stench_locations)
            visited_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                                   if adj in self.visited)
            
            if visited_neighbors > 0:
                self.certainty_map[pos] = min(1.0, stench_neighbors / visited_neighbors)
            else:
                self.certainty_map[pos] = 0.5
        
        for pos in list(self.pit_possible):
            adjacent_to_no_breeze = any(adj in self.no_breeze_locations 
                                      for adj in self._get_adjacent(pos))
            
            if adjacent_to_no_breeze or pos in self.no_pit:
                self.pit_possible.discard(pos)
                if pos not in self.wumpus_possible and pos not in self.wumpus_definite:
                    self.safe_cells.add(pos)

    def _get_adjacent(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = pos
        adjacent = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                adjacent.append((nx, ny))
        return adjacent

    def wumpus_killed(self):
        self.wumpuses_killed += 1
        if self.wumpuses_killed >= self.num_wumpuses:
            self.wumpus_possible.clear()
            self.wumpus_definite.clear()
            self.wumpus_alive = False
            
            for pos in list(self.wumpus_possible):
                if pos not in self.pit_possible and pos not in self.pit_definite:
                    self.safe_cells.add(pos)

    def is_safe(self, pos: Tuple[int, int]) -> bool:
        return pos in self.safe_cells

    def is_dangerous(self, pos: Tuple[int, int]) -> bool:
        if pos in self.visited:
            return False
        
        if pos in self.pit_definite or pos in self.wumpus_definite:
            return True
        
        return pos in self.pit_possible or (self.wumpus_alive and pos in self.wumpus_possible)

    def is_definitely_safe(self, pos: Tuple[int, int]) -> bool:
        if pos in self.visited:
            return True
        
        return ((pos in self.safe_cells and 
                pos not in self.pit_possible and 
                pos not in self.wumpus_possible and
                pos not in self.pit_definite and
                pos not in self.wumpus_definite) or
                (pos in self.no_pit and pos in self.no_wumpus))

    def get_safe_unvisited_cells(self) -> Set[Tuple[int, int]]:
        return self.safe_cells - self.visited

    def get_definitely_safe_unvisited_cells(self) -> Set[Tuple[int, int]]:
        definitely_safe = set()
        for pos in self.safe_cells - self.visited:
            if self.is_definitely_safe(pos):
                definitely_safe.add(pos)
        return definitely_safe

    def get_wumpus_probability(self, pos: Tuple[int, int]) -> float:
        if not self.wumpus_alive or pos not in self.wumpus_possible or pos in self.no_wumpus:
            return 0.0
        return self.certainty_map.get(pos, 0.3)

    def get_pit_probability(self, pos: Tuple[int, int]) -> float:
        if pos not in self.pit_possible or pos in self.no_pit:
            return 0.0
        
        breeze_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                             if adj in self.breeze_locations)
        visited_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                               if adj in self.visited)
        
        if visited_neighbors > 0:
            return min(1.0, breeze_neighbors / visited_neighbors)
        else:
            return 0.2

    def all_wumpuses_dead(self) -> bool:
        return self.wumpuses_killed >= self.num_wumpuses