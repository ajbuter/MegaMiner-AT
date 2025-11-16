from GameState import GameState
from AIAction import AIAction
from Utils import log_msg
import Constants

# Phase 2: Buy Mercenaries

def buy_mercenary_phase(game_state: GameState, ai_action_r: AIAction, ai_action_b: AIAction) -> None:
    """
    Process mercenary purchases for both players.
    
    Valid purchase requires:
    1. Player has at least 20 money
    2. There is a path tile ("O") in the specified direction
    """
    _process_mercenary_purchase(game_state, ai_action_r, is_red_player=True)
    _process_mercenary_purchase(game_state, ai_action_b, is_red_player=False)


def _process_mercenary_purchase(game_state: GameState, action: AIAction, is_red_player: bool) -> None:
    """Process a single player's mercenary purchase."""
   
    # Get player-specific data
    if is_red_player:
        money = game_state.money_r
        base = game_state.player_base_r
        player_name = "Red"
    else:
        money = game_state.money_b
        base = game_state.player_base_b
        player_name = "Blue"
    
    if action.merc_direction == "":
        return

    # Check if player has enough money
    if money < 20:
        log_msg(f"{player_name} tried to buy a merc, but had no money")
        return
    
    # Direction offsets: (dy, dx) since coordinates are (y, x) in tile_grid
    directions = {
        "N": (0, -1),
        "S": (0, 1),
        "W": (-1, 0),
        "E": (1, 0)
    }
    
    if action.merc_direction not in directions:
        log_msg(f"Invalid direction specified by {player_name}: {action.merc_direction}")
        return
    
    dx, dy = directions[action.merc_direction]
    target_y = base.y + dy
    target_x = base.x + dx
    
    # Check if there's a path tile in that direction
    if (game_state.is_out_of_bounds(target_x, target_y) or
        game_state.floor_tiles[target_y][target_x] != "O"):
        log_msg(f"{player_name} player tried to queue in direction {action.merc_direction}, but there was no path there")
        return
    
    # Queue the mercenary and deduct money
    if action.merc_direction == "N":
        base.mercenary_queued_up += 1
    elif action.merc_direction == "S":
        base.mercenary_queued_down += 1
    elif action.merc_direction == "W":
        base.mercenary_queued_left += 1
    elif action.merc_direction == "E":
        base.mercenary_queued_right += 1
    
    if is_red_player:
        game_state.money_r -= Constants.MERCENARY_PRICE
    else:
        game_state.money_b -= Constants.MERCENARY_PRICE
    
    log_msg(f"{player_name} queued a mercenary in direction {action.merc_direction}")