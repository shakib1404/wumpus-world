# wumpus_world/agent.py
import random
from typing import List, Tuple, Optional, Set
from knowledge_base import KnowledgeBase
from environment import WumpusEnvironment

class WumpusAgent:
    """Logical Agent for Wumpus World"""
    
    def __init__(self, world_size: int = 10):
        self.world_size = world_size
        self.kb = KnowledgeBase(world_size)
        self.position = (0, 0)
        self.direction = 0  # 0=North, 1=East, 2=South, 3=West
        self.has_arrow = True
        self.has_gold = False
        self.path_taken: List[Tuple[int, int]] = [(0, 0)]
        self.action_sequence: List[str] = []
        self.current_plan: List[str] = []
        
        # Loop detection
        self.position_visit_count: dict = {(0, 0): 1}
        self.max_visits_per_cell = 3
        
    def get_direction_name(self) -> str:
        """Get current direction as string"""
        return ['North', 'East', 'South', 'West'][self.direction]
    
    def update_position(self, new_pos: Tuple[int, int]):
        """Update agent's position and track visits"""
        self.position = new_pos
        self.path_taken.append(new_pos)
        
        # Update visit count for loop detection
        if new_pos in self.position_visit_count:
            self.position_visit_count[new_pos] += 1
        else:
            self.position_visit_count[new_pos] = 1
    
    def add_percepts(self, percepts: dict):
        """Add new percepts to knowledge base"""
        x, y = self.position
        self.kb.add_percept(x, y, percepts)
    
    def plan_path_to(self, target: Tuple[int, int]) -> List[str]:
        """Plan a path to target position using A* search"""
        if target == self.position:
            return []
        
        # Simple breadth-first search for pathfinding
        from collections import deque
        
        queue = deque([(self.position, [])])
        visited = {self.position}
        
        while queue:
            pos, path = queue.popleft()
            x, y = pos
            
            # Check all four directions
            for direction, (dx, dy) in enumerate([(0, 1), (1, 0), (0, -1), (-1, 0)]):
                new_pos = (x + dx, y + dy)
                
                if (new_pos not in visited and 
                    0 <= new_pos[0] < self.world_size and 
                    0 <= new_pos[1] < self.world_size and
                    self.kb.is_safe(new_pos[0], new_pos[1])):
                    
                    # Calculate moves needed to reach new_pos from pos
                    moves = self._calculate_moves_to_direction(direction, path)
                    new_path = path + moves + ['FORWARD']
                    
                    if new_pos == target:
                        return new_path
                    
                    visited.add(new_pos)
                    queue.append((new_pos, new_path))
        
        return []  # No safe path found
    
    def _calculate_moves_to_direction(self, target_direction: int, current_path: List[str]) -> List[str]:
        """Calculate moves needed to face target direction"""
        # Simulate current direction after executing current_path
        sim_direction = self.direction
        for action in current_path:
            if action == 'TURN_LEFT':
                sim_direction = (sim_direction - 1) % 4
            elif action == 'TURN_RIGHT':
                sim_direction = (sim_direction + 1) % 4
        
        moves = []
        while sim_direction != target_direction:
            # Choose shortest rotation
            diff = (target_direction - sim_direction) % 4
            if diff <= 2:
                moves.append('TURN_RIGHT')
                sim_direction = (sim_direction + 1) % 4
            else:
                moves.append('TURN_LEFT')
                sim_direction = (sim_direction - 1) % 4
        
        return moves
    
    def is_in_loop(self) -> bool:
        """Check if agent is potentially in a loop"""
        return self.position_visit_count.get(self.position, 0) > self.max_visits_per_cell
    
    def choose_action(self, percepts: dict) -> str:
        """Choose next action based on logical reasoning"""
        # Add current percepts to knowledge base
        self.add_percepts(percepts)
        
        # If we have gold and we're at start, climb out
        if self.has_gold and self.position == (0, 0):
            return 'CLIMB'
        
        # If we see glitter, grab the gold
        if percepts.get('glitter', False) and not self.has_gold:
            self.has_gold = True
            return 'GRAB'
        
        # If we have gold, plan path back to start
        if self.has_gold:
            if self.position != (0, 0):
                if not self.current_plan:
                    self.current_plan = self.plan_path_to((0, 0))
                
                if self.current_plan:
                    action = self.current_plan.pop(0)
                    self.action_sequence.append(action)
                    return action
        
        # Explore safe unvisited cells
        safe_unvisited = self.kb.get_safe_unvisited_cells()
        
        # Filter out cells we've visited too many times (loop avoidance)
        safe_unvisited = [cell for cell in safe_unvisited 
                         if self.position_visit_count.get(cell, 0) < self.max_visits_per_cell]
        
        if safe_unvisited:
            # Choose closest safe cell
            target = min(safe_unvisited, 
                        key=lambda cell: abs(cell[0] - self.position[0]) + abs(cell[1] - self.position[1]))
            
            if not self.current_plan:
                self.current_plan = self.plan_path_to(target)
            
            if self.current_plan:
                action = self.current_plan.pop(0)
                self.action_sequence.append(action)
                return action
        
        # If no safe moves and we detect a loop, try random safe action
        if self.is_in_loop():
            # Try to move to a less visited adjacent safe cell
            x, y = self.position
            adjacent_safe = []
            
            for direction, (dx, dy) in enumerate([(0, 1), (1, 0), (0, -1), (-1, 0)]):
                new_pos = (x + dx, y + dy)
                if (0 <= new_pos[0] < self.world_size and 
                    0 <= new_pos[1] < self.world_size and
                    self.kb.is_safe(new_pos[0], new_pos[1])):
                    visit_count = self.position_visit_count.get(new_pos, 0)
                    adjacent_safe.append((new_pos, direction, visit_count))
            
            if adjacent_safe:
                # Choose least visited safe adjacent cell
                best_cell = min(adjacent_safe, key=lambda x: x[2])
                target_direction = best_cell[1]
                
                # Turn to face the target direction
                if self.direction != target_direction:
                    diff = (target_direction - self.direction) % 4
                    if diff <= 2:
                        self.action_sequence.append('TURN_RIGHT')
                        return 'TURN_RIGHT'
                    else:
                        self.action_sequence.append('TURN_LEFT')
                        return 'TURN_LEFT'
                else:
                    self.action_sequence.append('FORWARD')
                    return 'FORWARD'
        
        # If we have an arrow and can shoot the Wumpus, do it
        if (self.has_arrow and 
            len(self.kb.wumpus_possible) == 1 and 
            percepts.get('stench', False)):
            
            wumpus_pos = list(self.kb.wumpus_possible)[0]
            x, y = self.position
            wx, wy = wumpus_pos
            
            # Check if Wumpus is in line of sight
            if x == wx or y == wy:
                # Determine direction to Wumpus
                if x == wx:
                    target_direction = 0 if wy > y else 2  # North or South
                else:
                    target_direction = 1 if wx > x else 3  # East or West
                
                # Face the Wumpus and shoot
                if self.direction == target_direction:
                    self.has_arrow = False
                    self.action_sequence.append('SHOOT')
                    return 'SHOOT'
                else:
                    # Turn towards Wumpus
                    diff = (target_direction - self.direction) % 4
                    if diff <= 2:
                        self.action_sequence.append('TURN_RIGHT')
                        return 'TURN_RIGHT'
                    else:
                        self.action_sequence.append('TURN_LEFT')
                        return 'TURN_LEFT'
        
        # Default: try to explore randomly but safely
        safe_directions = []
        x, y = self.position
        
        for direction, (dx, dy) in enumerate([(0, 1), (1, 0), (0, -1), (-1, 0)]):
            new_pos = (x + dx, y + dy)
            if (0 <= new_pos[0] < self.world_size and 
                0 <= new_pos[1] < self.world_size and
                self.kb.is_safe(new_pos[0], new_pos[1])):
                safe_directions.append(direction)
        
        if safe_directions:
            target_direction = random.choice(safe_directions)
            if self.direction != target_direction:
                diff = (target_direction - self.direction) % 4
                if diff <= 2:
                    self.action_sequence.append('TURN_RIGHT')
                    return 'TURN_RIGHT'
                else:
                    self.action_sequence.append('TURN_LEFT')
                    return 'TURN_LEFT'
            else:
                self.action_sequence.append('FORWARD')
                return 'FORWARD'
        
        # If no safe actions available, climb out if at start
        if self.position == (0, 0):
            return 'CLIMB'
        
        # Last resort: turn randomly
        self.action_sequence.append('TURN_RIGHT')
        return 'TURN_RIGHT'
    
    def get_status(self) -> dict:
        """Get current agent status"""
        return {
            'position': self.position,
            'direction': self.get_direction_name(),
            'has_arrow': self.has_arrow,
            'has_gold': self.has_gold,
            'path_length': len(self.path_taken),
            'actions_taken': len(self.action_sequence),
            'knowledge': self.kb.get_knowledge_summary(),
            'current_plan': len(self.current_plan),
            'loop_detected': self.is_in_loop()
        }