from Game import Game
from AIAction import AIAction
from Utils import log_msg
import Constants
import os
import argparse
import subprocess
import sys


# Main game loop
def main_game_loop(ai_agent_1, ai_agent_2, game: Game):
    while not game.game_state.is_game_over():
        
        # Get agents' actions
        agent_1_action_string = ""
        if ai_agent_1:
            try:
                # Send game state to agent
                if game.game_state.turns_remaining < Constants.MAX_TURNS:
                    ai_agent_1.stdin.write(game.game_state_to_json() + "\n--END OF TURN--\n")
                    ai_agent_1.stdin.flush()
                
                # Read action from agent
                agent_1_action_string = ai_agent_1.stdout.readline().strip()
                
                # Check if agent died (readline returns empty string if process ended)
                if not agent_1_action_string:
                    log_msg('Agent 1 process died or produced no output!')
                    # Read stderr to see what went wrong
                    stderr_output = ai_agent_1.stderr.read()
                    if stderr_output:
                        log_msg(f'Agent 1 stderr: {stderr_output}')
            except Exception as e:
                log_msg(f'Error reading from Agent 1: {e}')
                agent_1_action_string = ""
        else:
            # "Human" input from visualizer or other parent process
            agent_1_action_string = input()
        
        agent_1_action = AIAction('nothing',0,0)
        try:
            agent_1_action = AIAction.from_json(agent_1_action_string)
        except Exception as e:
            log_msg(f'Agent 1 produced invalid JSON! Agent 1 forfeits their turn! Error: {e}')

        agent_2_action_string = ""
        if ai_agent_2:
            try:
                # Send game state to agent
                if game.game_state.turns_remaining < Constants.MAX_TURNS:
                    ai_agent_2.stdin.write(game.game_state_to_json() + "\n--END OF TURN--\n")
                    ai_agent_2.stdin.flush()
                
                # Read action from agent
                agent_2_action_string = ai_agent_2.stdout.readline().strip()
                
                # Check if agent died
                if not agent_2_action_string:
                    log_msg('Agent 2 process died or produced no output!')
                    stderr_output = ai_agent_2.stderr.read()
                    if stderr_output:
                        log_msg(f'Agent 2 stderr: {stderr_output}')
            except Exception as e:
                log_msg(f'Error reading from Agent 2: {e}')
                agent_2_action_string = ""
        else:
            # "Human" input from visualizer or other parent process
            agent_2_action_string = input()
        
        agent_2_action = AIAction('nothing',0,0)
        try:
            agent_2_action = AIAction.from_json(agent_2_action_string)
        except Exception as e:
            log_msg(f'Agent 2 produced invalid JSON! Agent 2 forfeits their turn! Error: {e}')

        # Run the next turn
        game.run_turn(agent_1_action, agent_2_action)
        
        # Print a string representation of the new game state to stdout
        print(game.game_state_to_json())

        # If using the visualizer, wait for "--NEXT TURN--" from stdin
        if cmd_line_args.visualizer:
            while input() != "--NEXT TURN--":
                pass


# Use argparse to parse command line arguments
def get_command_line_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description='Backend for ApocaWarlords.',
        epilog='Example usage: python main.py <map_json_file> -a1 <ai_agent_file_1> -a2 <ai_agent_file_2>'
    )
    parser.add_argument(
        'map_json_file',
        help='Path to the map JSON file, which has tile locations, player base locations, etc.'
    )
    parser.add_argument(
        '-a1',
        '--ai_agent_file_1',
        help='Path to the AI agent 1 python file'
    )
    parser.add_argument(
        '-a2',
        '--ai_agent_file_2',
        help='Path to the AI agent 2 python file'
    )
    parser.add_argument(
        '-h1',
        '--agent_1_is_human',
        action='store_true',
        help='Pass this if agent 1 is a human player...'
    )
    parser.add_argument(
        '-h2',
        '--agent_2_is_human',
        action='store_true',
        help='Pass this if agent 2 is a human player...'
    )
    parser.add_argument(
        '-v',
        '--visualizer',
        action='store_true',
        help='Enable visualizer mode (non-headless). This argument should not be used from the command line.'
    )
    return parser.parse_args()


# Return an empty string if command line arguments are valid.
# Otherwise, return a non-empty string explaining what was wrong with the arguments.
def validate_command_line_arguments(cmd_line_args: argparse.Namespace) -> str:
    
    # Check that map file exists
    if not os.path.exists(cmd_line_args.map_json_file):
        return f'Map file not found: {cmd_line_args.map_json_file}'
    
    # Agent 1: Must have either AI agent file or be human
    if not cmd_line_args.agent_1_is_human:
        if not cmd_line_args.ai_agent_file_1:
            return 'Agent 1 must either be human (--agent_1_is_human) or have an AI agent file (-a1)'
        if not os.path.exists(cmd_line_args.ai_agent_file_1):
            return f'AI agent 1 file not found: {cmd_line_args.ai_agent_file_1}'
    
    # Agent 2: Must have either AI agent file or be human
    if not cmd_line_args.agent_2_is_human:
        if not cmd_line_args.ai_agent_file_2:
            return 'Agent 2 must either be human (--agent_2_is_human) or have an AI agent file (-a2)'
        if not os.path.exists(cmd_line_args.ai_agent_file_2):
            return f'AI agent 2 file not found: {cmd_line_args.ai_agent_file_2}'
    
    return ''


# Entry point for the backend
if __name__ == '__main__':
    # redirect stderr to logfile
    sys.stderr = open('log.txt', 'w')

    try:
        cmd_line_args = get_command_line_arguments()
    except:
        print("Your command-line arguments are wrong! Check log.txt")
        exit(1)

    err = validate_command_line_arguments(cmd_line_args)
    if err != "":
        print(err)
        exit(1)

    # Create AI agents
    ai_agent_1 = None
    if not cmd_line_args.agent_1_is_human:
        try:
            ai_agent_1 = subprocess.Popen(
                [sys.executable, cmd_line_args.ai_agent_file_1],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        except Exception as e:
            print(f"Failed to start Agent 1: {e}")
            exit(1)
            
    ai_agent_2 = None
    if not cmd_line_args.agent_2_is_human:
        try:
            ai_agent_2 = subprocess.Popen(
                [sys.executable, cmd_line_args.ai_agent_file_2],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        except Exception as e:
            print(f"Failed to start Agent 2: {e}")
            exit(1)

    # Initialize the game
    game = Game(map_json_file_path = cmd_line_args.map_json_file)

    # Send initial game state to agents, then get team names
    team_name_r = ""
    if ai_agent_1:
        try:
            ai_agent_1.stdin.write("--YOU ARE RED--\n")
            ai_agent_1.stdin.write(game.game_state_to_json() + "\n--END INITIAL GAME STATE--\n")
            ai_agent_1.stdin.flush()
            team_name_r = ai_agent_1.stdout.readline().strip()
            if not team_name_r:
                log_msg('Agent 1 failed to provide team name!')
                stderr_output = ai_agent_1.stderr.read()
                if stderr_output:
                    log_msg(f'Agent 1 stderr: {stderr_output}')
                team_name_r = "Agent 1 (Red) - ERROR"
        except Exception as e:
            log_msg(f'Error initializing Agent 1: {e}')
            team_name_r = "Agent 1 (Red) - ERROR"
    else:
        team_name_r = "Human Player (Red)"
    
    team_name_b = ""
    if ai_agent_2:
        try:
            ai_agent_2.stdin.write("--YOU ARE BLUE--\n")
            ai_agent_2.stdin.write(game.game_state_to_json() + "\n--END INITIAL GAME STATE--\n")
            ai_agent_2.stdin.flush()
            team_name_b = ai_agent_2.stdout.readline().strip()
            if not team_name_b:
                log_msg('Agent 2 failed to provide team name!')
                stderr_output = ai_agent_2.stderr.read()
                if stderr_output:
                    log_msg(f'Agent 2 stderr: {stderr_output}')
                team_name_b = "Agent 2 (Blue) - ERROR"
        except Exception as e:
            log_msg(f'Error initializing Agent 2: {e}')
            team_name_b = "Agent 2 (Blue) - ERROR"
    else:
        team_name_b = "Human Player (Blue)"

    # Send initial game state and team names to the visualizer (or other parent process)
    game.team_name_r = team_name_r
    game.team_name_b = team_name_b
    print("--BEGIN INITIAL GAME STATE--")
    print(game.game_state_to_json())
    print("--END INITIAL GAME STATE--")
    print(f"--RED TEAM NAME: {team_name_r}--")
    print(f"--BLUE TEAM NAME: {team_name_b}--")

    # Main game loop
    main_game_loop(ai_agent_1, ai_agent_2, game)

    # Print game result
    match game.game_state.victory:
        case 'r':   print(f"--WINNER: {team_name_r} (RED)--")
        case 'b':   print(f"--WINNER: {team_name_b} (BLUE)--")
        case 'tie': print(f"--WINNER: TIE--")
        case _:     print("--RAN OUT OF TURNS--")

    # Clean up subprocesses
    if ai_agent_1:
        ai_agent_1.terminate()
        ai_agent_1.wait()
    if ai_agent_2:
        ai_agent_2.terminate()
        ai_agent_2.wait()