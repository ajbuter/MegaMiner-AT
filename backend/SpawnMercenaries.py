from GameState import GameState
from Mercenary import Mercenary
from Utils import log_msg

def spawn_single_mercenary(game_state: GameState, x: int, y: int, team_color: str):
    merc = Mercenary(x, y, team_color, game_state)
    game_state.entity_grid[y][x] = merc
    game_state.mercs.append(merc)

    team_name = "Red" if team_color == 'r' else "Blue"
    log_msg(f"{team_name} player spawned mercenary {merc.name} at ({x},{y})")


def spawn_mercenaries(game_state: GameState):

    bx = game_state.player_base_r.x
    by = game_state.player_base_r.y

    if game_state.player_base_r.mercenary_queued_up > 0 and game_state.entity_grid[by - 1][bx] == None:
        spawn_single_mercenary(game_state, bx, by - 1, "r")
        game_state.player_base_r.mercenary_queued_up = 0

    if game_state.player_base_r.mercenary_queued_down > 0 and game_state.entity_grid[by + 1][bx] == None:
        spawn_single_mercenary(game_state, bx, by + 1, "r")
        game_state.player_base_r.mercenary_queued_down = 0

    if game_state.player_base_r.mercenary_queued_left > 0 and game_state.entity_grid[by][bx - 1] == None:
        spawn_single_mercenary(game_state, bx - 1, by, "r")
        game_state.player_base_r.mercenary_queued_left = 0

    if game_state.player_base_r.mercenary_queued_right > 0 and game_state.entity_grid[by][bx + 1] == None:
        spawn_single_mercenary(game_state, bx + 1, by, "r")
        game_state.player_base_r.mercenary_queued_right = 0


    bx = game_state.player_base_b.x
    by = game_state.player_base_b.y
    
    if game_state.player_base_b.mercenary_queued_up > 0 and game_state.entity_grid[by - 1][bx] == None:
        spawn_single_mercenary(game_state, bx, by - 1, "b")
        game_state.player_base_b.mercenary_queued_up = 0

    if game_state.player_base_b.mercenary_queued_down > 0 and game_state.entity_grid[by + 1][bx] == None:
        spawn_single_mercenary(game_state, bx, by + 1, "b")
        game_state.player_base_b.mercenary_queued_down = 0

    if game_state.player_base_b.mercenary_queued_left > 0 and game_state.entity_grid[by][bx - 1] == None:
        spawn_single_mercenary(game_state, bx - 1, by, "b")
        game_state.player_base_b.mercenary_queued_left = 0

    if game_state.player_base_b.mercenary_queued_right > 0 and game_state.entity_grid[by][bx + 1] == None:
        spawn_single_mercenary(game_state, bx + 1, by, "b")
        game_state.player_base_b.mercenary_queued_right = 0


    