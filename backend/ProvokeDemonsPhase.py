from GameState import GameState
from AIAction import AIAction
import Constants
from Utils import log_msg

# Return True if Player 1 successfully provoked the demons XOR Player 2 successfully provoked the demons
def provoke_demons_phase(game_state: GameState, ai_action_r: AIAction, ai_action_b: AIAction) -> bool:
    provoked_b = False
    provoked_r = False
    
    if ai_action_r.provoke_demons:
        if game_state.money_r >= Constants.PROVOKE_DEMONS_PRICE:
            game_state.money_r -= Constants.PROVOKE_DEMONS_PRICE
            provoked_r = True
            log_msg('Red provoked the demons!')
        else:
            log_msg(f'Red tried to provoke the demons, but was too poor! (Had ${game_state.money_r}, cost: ${Constants.PROVOKE_DEMONS_PRICE})')
        
    if ai_action_b.provoke_demons:
        if game_state.money_b >= Constants.PROVOKE_DEMONS_PRICE:
            game_state.money_b -= Constants.PROVOKE_DEMONS_PRICE
            provoked_b = True
            log_msg('Blue provoked the demons!')
        else:
            log_msg(f'Blue tried to provoke the demons, but was too poor! (Had ${game_state.money_b}, cost: ${Constants.PROVOKE_DEMONS_PRICE})')

    # prisoner's dilemma!
    if provoked_r and provoked_b:
        log_msg('Both teams provoked the demons at the same time. All demons are wiped from the map!!!')
        for demon in game_state.demons:
            demon.state = 'dead'
        return False
    
    if provoked_b:
        log_msg('Only blue provoked the demons this turn. Spawning more demons!')
        return True
    
    if provoked_r:
        log_msg('Only red provoked the demons this turn. Spawning more demons!')
    


