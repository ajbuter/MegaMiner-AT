from DemonSpawner import DemonSpawner
from Demon import Demon
from GameState import GameState
from Utils import log_msg
import Constants

def spawn_demons(game_state: GameState, provoke_demons: bool):
    for demon_spawner in game_state.demon_spawners:
        spawner : DemonSpawner = demon_spawner

        if spawner.reload_time_left <= 0:
            spawner.queued += 1
            spawner.reload_time_left = Constants.DEMON_SPAWNER_RELOAD_TURNS
        else:
            spawner.reload_time_left -= 1
        if provoke_demons:
            spawner.queued += 1

        at_target_space = game_state.entity_grid[spawner.y][spawner.x]

        # Wait to spawn until space is clear
        if spawner.queued > 0:
            if at_target_space == None:
                new_demon = Demon(
                    spawner.x,
                    spawner.y,
                    spawner.target_team,
                    spawner.activation_count,
                    game_state
                )
                game_state.entity_grid[new_demon.y][new_demon.x] = new_demon
                game_state.demons.append(new_demon)

                spawner.queued -= 1
                spawner.activation_count += 1

                log_msg(f"Spawned demon {new_demon.name} at ({new_demon.x},{new_demon.y})")

            else:
                log_msg(f"Waiting to spawn demon at ({spawner.x},{spawner.y})")