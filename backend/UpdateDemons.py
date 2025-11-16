from typing import List
from GameState import GameState
from Demon import Demon
from PlayerBase import PlayerBase
from Mercenary import Mercenary
from Entity import Entity
from Utils import log_msg
import Constants

def update_demons(game_state: GameState):
    # Determine all demon states
    moving: List[Demon] = []
    fighting: List[Demon] = []
    set_all_demon_states(game_state, game_state.demons, moving, fighting)

    # Move all demons in moving state
    move_all_demons(game_state, moving)

    # Apply combat effects for all demons in fighting state
    for demon in fighting:
        do_demon_combat_single(game_state, demon)

# Side effect: All demon objects will have their state set appropiately
# Side effect: moving, fighting and waiting lists will be populated
def set_all_demon_states(game_state: GameState, demons: List[Demon], 
                        moving: List[Demon],
                        fighting: List[Demon]):
    
    for demon in demons:
        if demon.state == 'dead':
            continue
        else:
            demon.state = 'deciding'

    for demon in demons:
        if demon.state != 'deciding':
            continue

        next_tile1 = demon.get_adjacent_path_tile(game_state, 1)
        next_tile2 = demon.get_adjacent_path_tile(game_state, 2)
        blocking_entity1 = game_state.entity_grid[next_tile1[1]][next_tile1[0]]
        blocking_entity2 = game_state.entity_grid[next_tile2[1]][next_tile2[0]]

        # check for entities that guarantee 'fighting'

        # fighting if there is anything within 1 space
        if blocking_entity1 is not None:
            if isinstance(blocking_entity1, Demon) and blocking_entity1.target_team != demon.target_team:
                demon.state = 'fighting'
                demon.block_entity_behind(game_state)
            elif isinstance(blocking_entity1, Mercenary):
                # Don't move in tandem with mercenaries, since they did their movement in the last phase
                demon.state = 'fighting'
                demon.block_entity_behind(game_state)
        else:
            if demon.get_attackable_player_base(game_state) != None:
                demon.state = 'fighting'
                demon.block_entity_behind(game_state)
            elif blocking_entity2 is not None:
                if isinstance(blocking_entity2, Demon) and blocking_entity2.target_team != demon.target_team:
                    demon.state = 'fighting'
                    demon.block_entity_behind(game_state)
                # Mercs and demons move during different phases, so path tiles are never contested between them
        
        # if not guaranteed blocked by anything, then moving
        if demon.state == 'deciding':
            demon.state = 'moving'
    
    for demon in demons:
        # add to correct list
        if demon.state == 'fighting': fighting.append(demon)
        if demon.state == 'moving': moving.append(demon)


def move_all_demons(game_state: GameState, demons: List[Demon]):
    # remove moving demons
    for demon in demons:
        game_state.entity_grid[demon.y][demon.x] = None

    # set new position
    for demon in demons:
        new_pos = demon.get_adjacent_path_tile(game_state, 1)
        demon.x = new_pos[0]
        demon.y = new_pos[1]

    # add moving demons back
    for demon in demons:
        game_state.entity_grid[demon.y][demon.x] = demon
        log_msg(f"Demon {demon.name} moved to ({demon.x},{demon.y})")


def do_demon_combat_single(game_state: GameState, demon: Demon):
    next_tile1 = demon.get_adjacent_path_tile(game_state, 1)
    next_tile2 = demon.get_adjacent_path_tile(game_state, 2)
    target1: Entity = game_state.entity_grid[next_tile1[1]][next_tile1[0]]
    target2: Entity = game_state.entity_grid[next_tile2[1]][next_tile2[0]]
    
    # if tile 1 space in front is empty, we are contesting space with enemy 2 spaces in front 
    if target1 != None:
        b4_health = target1.health
        target1.health -= demon.attack_pow
        log_msg(f'Demon {demon.name} attacked opponent {target1.name} at ({next_tile1[0]},{next_tile1[1]}). Target health went from {b4_health} to {target1.health}')
    elif target2 != None:
        b4_health = target2.health
        target2.health -= demon.attack_pow
        log_msg(f'Demon {demon.name} attacked opponent {target2.name} at ({next_tile2[0]},{next_tile2[1]}). Target health went from {b4_health} to {target1.health}')
    else:
        # attack the player base if we have reached the end of the path, and there is nobody else to fight
        attackable_base = demon.get_attackable_player_base(game_state)
        if attackable_base != None:
            attackable_base.health -= demon.attack_pow
            log_msg(f'Demon {demon.name} attacked {attackable_base.name} at ({attackable_base.x},{attackable_base.y})')