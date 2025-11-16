import math
from typing import List
from GameState import GameState
from Mercenary import Mercenary
from Demon import Demon
from PlayerBase import PlayerBase
from Entity import Entity
from Utils import log_msg
import Constants

def update_mercenaries(game_state: GameState):
    # Determine all merc states
    moving: List[Mercenary] = []
    fighting: List[Mercenary] = []
    waiting: List[Mercenary] = []
    set_all_merc_states(game_state, game_state.mercs, moving, fighting, waiting)

    # Move all mercs in moving state
    move_all_mercs(game_state, moving)

    # Apply combat effects for all mercs in fighting state
    for merc in fighting:
        do_merc_combat_single(game_state, merc)

# Side effect: All merc objects will have their state set appropiately
# Side effect: moving, fighting and waiting lists will be populated
def set_all_merc_states(game_state: GameState, mercs: List[Mercenary], 
                        moving: List[Mercenary],
                        fighting: List[Mercenary],
                        waiting: List[Mercenary]):
    
    for merc in mercs:
        if merc.state == 'dead':
            continue
        else:
            merc.state = 'deciding'
    
    for merc in mercs:
        if merc.state != 'deciding':
            continue

        next_tile1 = merc.get_adjacent_path_tile(game_state, 1)
        next_tile2 = merc.get_adjacent_path_tile(game_state, 2)
        blocking_entity1 = game_state.entity_grid[next_tile1[1]][next_tile1[0]]
        blocking_entity2 = game_state.entity_grid[next_tile2[1]][next_tile2[0]]

        # check for entities that guarantee 'fighting' or 'waiting'

        # fighting if rival merc or demon is within 1 space
        if blocking_entity1 is not None:
            if isinstance(blocking_entity1, Demon):
                # Demons move in the next phase, so Mercs and Demons won't move in tandem
                if blocking_entity1.target_team == merc.team:
                    merc.state = 'fighting'
                    merc.block_entity_behind(game_state)
                else:
                    merc.state = 'waiting'
                    merc.block_entity_behind(game_state)
            elif isinstance(blocking_entity1, Mercenary) and blocking_entity1.team != merc.team:
                merc.state = 'fighting'
                merc.block_entity_behind(game_state)
        # fighting if there is no enemy 1 space away and there is an enemy is within 2 spaces
        else:
            if merc.get_attackable_player_base(game_state) != None:
                merc.state = 'fighting'
                merc.block_entity_behind(game_state)
            elif blocking_entity2 is not None:
                if isinstance(blocking_entity2, Mercenary) and blocking_entity2.team != merc.team:
                    merc.state = 'fighting'
                    merc.block_entity_behind(game_state)
                # Mercs and demons move during different phases, so path tiles are never contested between them
        
        # if not guaranteed blocked by anything, then moving
        if merc.state == 'deciding':
            merc.state = 'moving'
    
    for merc in mercs:
        # add to correct list
        if merc.state == 'fighting': fighting.append(merc)
        if merc.state == 'waiting': waiting.append(merc)
        if merc.state == 'moving': moving.append(merc)


def move_all_mercs(game_state: GameState, moving_mercs: List[Mercenary]):
    # remove moving mercs
    for merc in moving_mercs:
        game_state.entity_grid[merc.y][merc.x] = None

    # set new position
    for merc in moving_mercs:
        new_pos = merc.get_adjacent_path_tile(game_state, 1)
        merc.x = new_pos[0]
        merc.y = new_pos[1]

    # add moving mercs back
    for merc in moving_mercs:
        game_state.entity_grid[merc.y][merc.x] = merc
        log_msg(f"Mercenary {merc.name} moved to ({merc.x},{merc.y})")


def do_merc_combat_single(game_state: GameState, merc: Mercenary):
    next_tile1 = merc.get_adjacent_path_tile(game_state, 1)
    next_tile2 = merc.get_adjacent_path_tile(game_state, 2)
    target1: Entity = game_state.entity_grid[next_tile1[1]][next_tile1[0]]
    target2: Entity = game_state.entity_grid[next_tile2[1]][next_tile2[0]]
    
    # if tile 1 space in front is empty, we are contesting space with enemy 2 spaces in front 
    if target1 != None:
        b4_health = target1.health
        target1.health -= merc.attack_pow
        log_msg(f'Mercenary {merc.name} attacked opponent {target1.name} at ({next_tile1[0]},{next_tile1[1]}). Target health went from {b4_health} to {target1.health}')
    elif target2 != None:
        b4_health = target2.health
        target2.health -= merc.attack_pow
        log_msg(f'Mercenary {merc.name} attacked opponent {target2.name} at ({next_tile2[0]},{next_tile2[1]}). Target health went from {b4_health} to {target2.health}')
    else:
        # attack the player base if we have reached the end of the path, and there is nobody else to fight
        attackable_base = merc.get_attackable_player_base(game_state)
        if attackable_base != None:
            attackable_base.health -= Constants.MERCENARY_ATTACK_POWER
            log_msg(f'Mercenary {merc.name} attacked {attackable_base.name} at ({attackable_base.x},{attackable_base.y})')