from GameState import GameState
from AIAction import AIAction 
from Tower import Tower
from Cannon import Cannon
from Crossbow import Crossbow
from House import House
from Minigun import Minigun
from Church import Church
from Utils import log_msg
import Constants

# Phase 1: Build or Destroy Towers

def build_tower_phase(game_state: GameState, ai_action_r: AIAction, ai_action_b: AIAction) -> None:
    """
    Process tower building and destruction for both players.
    
    Valid build requires:
    1. Player has enough money for the tower
    2. Target tile is in player's territory
    3. Target tile is empty (no entity present)
    
    Raises exceptions on invalid actions.
    """
    if ai_action_r.action == "build":
        _build_tower(game_state, ai_action_r, is_red_player=True)
    elif ai_action_r.action == "destroy":
        _destroy_tower(game_state, ai_action_r, is_red_player=True)
    
    if ai_action_b.action == "build":
        _build_tower(game_state, ai_action_b, is_red_player=False)
    elif ai_action_b.action == "destroy":
        _destroy_tower(game_state, ai_action_b, is_red_player=False)


def _build_tower(game_state: GameState, action: AIAction, is_red_player: bool) -> None:
    """Build a tower for the specified player."""
    x, y = action.x, action.y
    
    # Get player-specific data
    current_team = "r" if is_red_player else "b"
    player_name = "Red" if is_red_player else "Blue"
    money = game_state.money_r if is_red_player else game_state.money_b
    
    # Validate placement
    if game_state.is_out_of_bounds(x,y):
        log_msg(f"{player_name} player tried to build out-of-bounds at ({x}, {y})")
        return

    if game_state.floor_tiles[y][x] != current_team:
        log_msg(f"{player_name} player tried to build outside their territory at ({x}, {y})")
        return
    
    if game_state.entity_grid[y][x] is not None:
        log_msg(f"{player_name} player tried to build on occupied space at ({x}, {y})")
        return
    
    # Create the tower
    tower = _create_tower(action.tower_type, x, y, current_team, game_state)
    if tower is None: return

    # Check money
    if money < tower.get_price(game_state, current_team):
        log_msg(f"{player_name} player doesn't have enough money to build {action.tower_type} (costs {tower.get_price(game_state, current_team)}, has {money})")
        return
    
    # Build the tower
    game_state.towers.append(tower)
    game_state.entity_grid[y][x] = tower
    
    # Deduct money
    if is_red_player:
        game_state.money_r -= tower.get_price(game_state, current_team)
    else:
        game_state.money_b -= tower.get_price(game_state, current_team)

    tower.increase_price(game_state, "r" if is_red_player else "b")
    
    log_msg(f"{player_name} built a {action.tower_type} tower at ({x},{y})")


def _destroy_tower(game_state: GameState, action: AIAction, is_red_player: bool) -> None:
    """Destroy a tower and refund half its value."""
    x, y = action.x, action.y
    
    # Get player-specific data
    current_team = "r" if is_red_player else "b"
    player_name = "Red" if is_red_player else "Blue"
    
    # Validate destruction
    if game_state.is_out_of_bounds(x,y):
        log_msg(f"{player_name} player tried to destroy out-of-bounds at ({x}, {y})")
        return

    if game_state.floor_tiles[y][x] != current_team:
        log_msg(f"{player_name} player tried to destroy tower outside their territory at ({x}, {y})")
        return
    
    tower = game_state.entity_grid[y][x]
    if tower is None:
        log_msg(f"{player_name} player tried to destroy tower at empty location ({x}, {y})")
        return
    
    if not isinstance(tower, Tower):
        log_msg(f"{player_name} player tried to destroy non-tower entity at ({x}, {y})")
        return
    
    # Destroy the tower
    refund = 0
    if isinstance(tower, Cannon):
        refund = Constants.CANNON_BASE_PRICE
    elif isinstance(tower, Crossbow):
        refund = Constants.CROSSBOW_BASE_PRICE
    elif isinstance(tower, Minigun):
        refund = Constants.MINIGUN_BASE_PRICE
    elif isinstance(tower, House):
        refund = Constants.HOUSE_BASE_PRICE
    elif isinstance(tower, Church):
        refund = Constants.CHURCH_BASE_PRICE

    game_state.towers.remove(tower)
    game_state.entity_grid[y][x] = None
    
    # Refund money
    if is_red_player:
        game_state.money_r += refund
    else:
        game_state.money_b += refund
    
    log_msg(f"{player_name} destroyed a tower at ({x},{y}) and was refunded ${refund}")


def _create_tower(tower_type: str, x: int, y: int, team_color: str, game_state: GameState) -> Tower:
    """Factory function to create towers by name."""
    tower_type = tower_type.lower()
    
    if tower_type == "house":
        return House(x, y, team_color, game_state)
    elif tower_type == "cannon":
        return Cannon(x, y, team_color, game_state)
    elif tower_type == "minigun":
        return Minigun(x, y, team_color, game_state)
    elif tower_type == "crossbow":
        return Crossbow(x, y, team_color, game_state)
    elif tower_type == "church":
        return Church(x, y, team_color, game_state)
    else:
        team_name = 'Red' if team_color == 'r' else 'Blue'
        log_msg(f"{team_name} team tried to build an invalid type of tower: {tower_type}")
        return None