import random
from typing import Set, Tuple, List, Optional, Dict
from collections import deque
from heapq import heappush, heappop
from knowledge_base import KnowledgeBase
from Action import ActionSelector, Action

class WumpusAgent:
    def __init__(self, size=10):
        self.size = size
        self.reset()

    def reset(self):
        self.position = (0, 0)
        self.direction = 0
        self.has_arrow = True
        self.has_gold = False
        self.kb = KnowledgeBase(self.size)
        self.plan = deque()
        self.returning_home = False
        self.score = 0
        self.move_count = 0
        self.shot_attempted = False
        self.last_stench_positions = set()
        self.consecutive_stench = 0
        self.danger_threshold = 0.1
        self.last_safe_position = (0, 0)
        
        self.action_selector = ActionSelector(
            epsilon=0.1,
            curiosity_weight=0.3,
            decay_rate=0.995
        )

    def get_action(self, percepts: List[str]) -> str:
        
        self.kb.add_percept(self.position, percepts)
        self.move_count += 1

        if "Stench" in percepts:
            self.last_stench_positions.add(self.position)
            self.consecutive_stench += 1
        else:
            self.consecutive_stench = 0

        if "Glitter" in percepts and not self.has_gold:
            return "Grab"

        if "Scream" in percepts:
            self.kb.wumpus_killed()
            self.score += 100
            self.shot_attempted = False
            self.last_stench_positions = set()
            self.consecutive_stench = 0

        if self.has_gold and self.position == (0, 0):
            return "Climb"

        if self.has_gold and not self.returning_home:
            self.returning_home = True
            self.plan.clear()
            path = self._find_safe_path_to_start()
            if path:
                self.plan.extend(self._path_to_actions(path))

        if self.plan:
            next_action = self.plan.popleft()
            if next_action == "Forward":
                next_pos = self._get_next_position()
                if not self._is_definitely_safe(next_pos):
                    self.plan.clear()
                    return self._choose_action_with_selector(percepts)
            return next_action

        return self._choose_action_with_selector(percepts)
    def _choose_action_with_selector(self, percepts: List[str]) -> str:
     available_actions = self.action_selector.get_available_actions(
        self.position, 
        self.size, 
        self.has_arrow
     )
    
     safe_actions = self._filter_safe_actions(available_actions, percepts)

     if self.kb.safe_cells==self.kb.visited:
        print("No safe actions available, considering risky moves")
        risky_action = self._choose_risky_move(available_actions, percepts)
        if risky_action:
            return risky_action
    
     if safe_actions:
        selected_action = self.action_selector.select_action(
            self.position,
            self.kb,
            safe_actions,
            self.has_arrow
        )
        return self._convert_action_to_command(selected_action)
     
     if self._should_make_risky_move():
        print("No safe actions available, considering risky moves")
        risky_action = self._choose_risky_move(available_actions, percepts)
        if risky_action:
            return risky_action
    
     return self._emergency_action(percepts)
    
    def _should_make_risky_move(self) -> bool:
     safe_unvisited = self._get_definitely_safe_unvisited()
     return len(safe_unvisited) == 0

    def _choose_risky_move(self, available_actions: List[Action], percepts: List[str]) -> Optional[str]:
     risky_moves = []
     print(available_actions)
    
     for action in available_actions:
        if action.value.startswith("move_"):
            target_pos = self._get_target_position_from_action(action)
            if target_pos is None:
                continue
                
            if target_pos not in self.kb.visited:
                pit_prob = self.kb.get_pit_probability(target_pos)
                wumpus_prob = self.kb.get_wumpus_probability(target_pos)
                risk_score = pit_prob * 1000 + wumpus_prob * 1000
                
                info_bonus = self._calculate_information_gain(target_pos)
                risk_score -= info_bonus
                
                risky_moves.append((risk_score, action, target_pos))
     print(risky_moves)
     if not risky_moves:
        return None
        
     risky_moves.sort(key=lambda x: x[0])
     print("sorted moves",risky_moves)
    
     best_score, best_action, best_pos = risky_moves[0]
    
     if best_score <=940:
        return self._convert_action_to_command(best_action)
    
     return None
 
    def _calculate_information_gain(self, pos: Tuple[int, int]) -> float:
     if pos in self.kb.visited:
        return 0.0
        
     info_gain = 0.0
    
     for adj in self._get_adjacent(pos):
        if adj in self.kb.pit_possible or adj in self.kb.wumpus_possible:
            info_gain += 50.0
        
     unknown_adjacent = sum(1 for adj in self._get_adjacent(pos) 
                          if adj not in self.kb.visited)
     info_gain += unknown_adjacent * 20.0 
    
     return info_gain
 
    def _filter_safe_actions(self, actions: List[Action], percepts: List[str]) -> List[Action]:
     safe_actions = []
     for action in actions:
        if action in [Action.GRAB, Action.CLIMB]:
            safe_actions.append(action)
            continue
            
        if action.value.startswith("shoot_"):
            if self.has_arrow:
                safe_actions.append(action)
            continue
            
        if action.value.startswith("move_"):
            target_pos = self._get_target_position_from_action(action)
            if target_pos is None:
                continue
                
            if self._is_definitely_safe(target_pos):
                safe_actions.append(action)
    
     return safe_actions
    def _is_action_safe(self, action: Action, percepts: List[str]) -> bool:
        if action in [Action.GRAB, Action.CLIMB]:
            return True
        
        if action.value.startswith("shoot_"):
            return self.has_arrow
        
        if action.value.startswith("move_"):
            target_pos = self._get_target_position_from_action(action)
            if target_pos is None:
                return False
            
            return self._is_definitely_safe(target_pos)
        
        return True

    def _get_target_position_from_action(self, action: Action) -> Optional[Tuple[int, int]]:
        x, y = self.position
        
        if action == Action.MOVE_UP:
            return (x, y + 1) if y + 1 < self.size else None
        elif action == Action.MOVE_DOWN:
            return (x, y - 1) if y - 1 >= 0 else None
        elif action == Action.MOVE_LEFT:
            return (x - 1, y) if x - 1 >= 0 else None
        elif action == Action.MOVE_RIGHT:
            return (x + 1, y) if x + 1 < self.size else None
        
        return None

    def _convert_action_to_command(self, action: Action) -> str:
        if action == Action.GRAB:
            return "Grab"
        elif action == Action.CLIMB:
            return "Climb"
        elif action in [Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT]:
            return self._handle_movement_action(action)
        elif action in [Action.SHOOT_UP, Action.SHOOT_DOWN, Action.SHOOT_LEFT, Action.SHOOT_RIGHT]:
            return self._handle_shooting_action(action)
        
        return "TurnLeft"

    def _handle_movement_action(self, action: Action) -> str:
        required_dir = self._get_required_direction_for_action(action)
        
        if self.direction == required_dir:
            return "Forward"
        else:
            self.plan.appendleft("Forward")
            return self._get_turn_action(required_dir)

    def _handle_shooting_action(self, action: Action) -> str:
        required_dir = self._get_required_direction_for_action(action)
        
        if self.direction == required_dir:
            return "Shoot"
        else:
            self.plan.appendleft("Shoot")
            return self._get_turn_action(required_dir)

    def _get_required_direction_for_action(self, action: Action) -> int:
        if action in [Action.MOVE_UP, Action.SHOOT_UP]:
            return 0
        elif action in [Action.MOVE_RIGHT, Action.SHOOT_RIGHT]:
            return 1
        elif action in [Action.MOVE_DOWN, Action.SHOOT_DOWN]:
            return 2
        elif action in [Action.MOVE_LEFT, Action.SHOOT_LEFT]:
            return 3
        
        return self.direction

    def _choose_action(self, percepts: List[str]) -> str:
        if self._is_in_immediate_danger(percepts):
            return self._emergency_action(percepts)

        if "Stench" in percepts and not self.shot_attempted and self.has_arrow:
            shoot_action = self._try_shoot_wumpus(percepts)
            if shoot_action:
                return shoot_action

        safe_unvisited = self._get_definitely_safe_unvisited()
        if safe_unvisited:
            target = self._choose_best_safe_target(safe_unvisited)
            path = self._find_safe_path_to_position(target)
            if path:
                self.plan.extend(self._path_to_actions(path))
                return self.plan.popleft()

        if not self.returning_home:
            self.returning_home = True
            path = self._find_safe_path_to_start()
            if path:
                self.plan.extend(self._path_to_actions(path))
                return self.plan.popleft()

        return self._emergency_action(percepts)

    def _is_in_immediate_danger(self, percepts: List[str]) -> bool:
        if ("Stench" in percepts or "Breeze" in percepts) and not self.shot_attempted:
            return True
        
        if not self._is_definitely_safe(self.position):
            return True
            
        return False

    def _emergency_action(self, percepts: List[str]) -> str:
        safe_moves = self._get_safe_adjacent_moves()
        
        if safe_moves:
            if self.last_safe_position in safe_moves:
                target = self.last_safe_position
            else:
                target = min(safe_moves, key=lambda pos: self._manhattan_distance(pos, self.last_safe_position))
            
            actions = self._get_actions_to_adjacent(target)
            if actions:
                return actions[0]
        
        if "Stench" in percepts and self.has_arrow and not self.shot_attempted:
            shoot_action = self._try_shoot_wumpus(percepts)
            if shoot_action:
                return shoot_action
        
        return "TurnLeft"

    def _get_safe_adjacent_moves(self) -> List[Tuple[int, int]]:
        safe_moves = []
        x, y = self.position
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.size and 0 <= ny < self.size and 
                self._is_definitely_safe((nx, ny))):
                safe_moves.append((nx, ny))
        
        return safe_moves

    def _is_definitely_safe(self, pos: Tuple[int, int]) -> bool:
        if pos in self.kb.visited:
            return True
        
        if pos in self.kb.safe_cells:
            if pos in self.kb.pit_possible or pos in self.kb.wumpus_possible:
                return False
            return True
        
        return False

    def _get_definitely_safe_unvisited(self) -> Set[Tuple[int, int]]:
        safe_unvisited = set()
        
        for pos in self.kb.safe_cells:
            if pos not in self.kb.visited and self._is_definitely_safe(pos):
                safe_unvisited.add(pos)
        
        return safe_unvisited

    def _choose_best_safe_target(self, safe_targets: Set[Tuple[int, int]]) -> Tuple[int, int]:
        def target_score(pos):
            distance_score = 1.0 / (1 + self._manhattan_distance(self.position, pos))
            
            unexplored_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                                     if adj not in self.kb.visited and self._is_definitely_safe(adj))
            exploration_score = unexplored_neighbors * 0.5
            
            return distance_score + exploration_score
        
        return max(safe_targets, key=target_score)

    def _try_shoot_wumpus(self, percepts: List[str]) -> Optional[str]:
        if not self.has_arrow or self.shot_attempted or not self.kb.wumpus_alive:
            return None

        if "Stench" in percepts:
            x, y = self.position
            
            possible_targets = []
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.size and 0 <= ny < self.size and 
                    (nx, ny) in self.kb.wumpus_possible and
                    self.kb.get_wumpus_probability((nx, ny)) > 0.7):
                    possible_targets.append((nx, ny))
            
            if possible_targets:
                target = max(possible_targets, key=lambda pos: self.kb.get_wumpus_probability(pos))
                required_dir = self._get_direction_to_position(target)
                
                if required_dir == self.direction:
                    self.shot_attempted = True
                    return "Shoot"
                else:
                    turn_action = self._get_turn_action(required_dir)
                    self.plan.appendleft("Shoot")
                    return turn_action

        return None

    def _find_safe_path_to_position(self, target: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Find a path using only definitely safe cells"""
        if self.position == target:
            return []

        open_set = [(0, self.position)]
        came_from = {}
        g_score = {self.position: 0}

        while open_set:
            current = heappop(open_set)[1]
            
            if current == target:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return list(reversed(path))

            for neighbor in self._get_adjacent(current):
                if not self._is_definitely_safe(neighbor):
                    continue

                tentative_g_score = g_score[current] + 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + self._manhattan_distance(neighbor, target)
                    heappush(open_set, (f_score, neighbor))

        return []

    def _find_safe_path_to_start(self) -> List[Tuple[int, int]]:
        """Find a safe path back to starting position"""
        return self._find_safe_path_to_position((0, 0))

    def _get_next_position(self) -> Tuple[int, int]:
        """Get the position agent would move to if going forward"""
        x, y = self.position
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dx, dy = directions[self.direction]
        return (x + dx, y + dy)

    def _path_to_actions(self, path: List[Tuple[int, int]]) -> List[str]:
        """Convert path to sequence of actions"""
        if not path:
            return []

        actions = []
        current_pos = self.position
        current_dir = self.direction

        for next_pos in path:
            required_dir = self._get_direction_to_position(next_pos, current_pos)
            
            while current_dir != required_dir:
                if self._get_turn_direction(current_dir, required_dir) == "left":
                    actions.append("TurnLeft")
                    current_dir = (current_dir - 1) % 4
                else:
                    actions.append("TurnRight")
                    current_dir = (current_dir + 1) % 4

            actions.append("Forward")
            current_pos = next_pos

        return actions

    def _get_actions_to_adjacent(self, target: Tuple[int, int]) -> List[str]:
        """Get actions to move to adjacent cell"""
        required_dir = self._get_direction_to_position(target)
        actions = []
        current_dir = self.direction

        while current_dir != required_dir:
            if self._get_turn_direction(current_dir, required_dir) == "left":
                actions.append("TurnLeft")
                current_dir = (current_dir - 1) % 4
            else:
                actions.append("TurnRight")
                current_dir = (current_dir + 1) % 4

        actions.append("Forward")
        return actions

    def _get_direction_to_position(self, target: Tuple[int, int], from_pos: Tuple[int, int] = None) -> int:
        """Get direction needed to reach target position"""
        if from_pos is None:
            from_pos = self.position

        fx, fy = from_pos
        tx, ty = target

        if tx > fx:
            return 1  # East
        elif tx < fx:
            return 3  # West
        elif ty > fy:
            return 0  # North
        else:
            return 2  # South

    def _get_turn_direction(self, current_dir: int, target_dir: int) -> str:
        """Determine if we should turn left or right"""
        diff = (target_dir - current_dir) % 4
        return "left" if diff == 3 else "right"

    def _get_turn_action(self, target_dir: int) -> str:
        """Get the turn action needed to face target direction"""
        return "TurnLeft" if self._get_turn_direction(self.direction, target_dir) == "left" else "TurnRight"

    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _get_adjacent(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all adjacent positions within bounds"""
        x, y = pos
        adjacent = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                adjacent.append((nx, ny))
        return adjacent

    def update_state(self, action: str, result: str):
        """Update agent state based on action result"""
        if action == "Forward" and "Moved forward" in result:
            x, y = self.position
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            dx, dy = directions[self.direction]
            new_pos = (x + dx, y + dy)
            
            # Update last safe position before moving
            if self._is_definitely_safe(self.position):
                self.last_safe_position = self.position
            
            self.position = new_pos
            self.kb.add_visit(self.position)
            self.score -= 1

        elif action == "TurnLeft":
            self.direction = (self.direction - 1) % 4

        elif action == "TurnRight":
            self.direction = (self.direction + 1) % 4

        elif action == "Grab" and "Grabbed gold" in result:
            self.has_gold = True
            self.score += 1000

        elif action == "Shoot":
            self.has_arrow = False
            self.score -= 10
            if "Wumpus died" in result:
                self.kb.wumpus_killed()

        elif action == "Climb" and "Climbed out" in result:
            self.score += 500

    def get_score(self) -> int:
        return self.score

    def is_alive(self) -> bool:
        return True