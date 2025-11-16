# MegaMiner 2025
MegaMiner is a yearly competition held by Computer Science students at Missouri S&T. Teams of up to 4 people create AI agents to compete in a video game tournament. This year, the game is ApocaWarlords, a competitive 2-player turn-based tower defense game. If you want to make an AI agent, the first thing you need to do is to understand the rules/mechanics of the game. To learn the rules of the game, read the [rules document](https://github.com/EliotTexK/MegaMiner2025/tree/main/rules). Then, once you've done that, see the instructions below for creating/testing your agent.

## Installation
1. Clone this repository to get access to maps and the example AI Agents.
2. Install the latest version of Python. The game has been tested on the most recent version, and the tournament itself will also use it.
3. Get the Visualizer executable from our [Releases](https://github.com/EliotTexK/MegaMiner2025/releases). If you are on Windows, download the .exe file and the .pck file. If you are on Linux, download the .x86-64 file and the .pck file. Put both files in the Visualizer folder of the repository you just cloned.

## How The Software Works
When it comes to running MegaMiner 2025, whether you are testing your AI, or hosting a competition, there are 4 programs/processes involved:
- The Backend - This is a game server made with Python that runs the core game logic. You can run it using the command-line, or if you're using the Visualizer, the Visualizer will run it for you. It will manage 2 competing AI agents by sending the state of the game to them and recieving their inputs. It will print out a representation of the game state each turn and write to a log file.
- The Visualizer - This is a GUI application which displays the game graphically. It does this by running the Backend and interpreting the game state it prints out.
- The two AI Agents - these are Python files written by competitors. These are meant to be run by the Backend as sub-processes. Each turn, they receive game state from the backend and send back controls ( AI Actions ) for that turn.

## How To Run The Visualizer
Go to the Visualizer folder/directory where you put the executable. Then, double-click it, or run it using the command-line. Click the "Play Game" button. From there, select a map and your AI agents. The Visualizer also allows the game to be playable by humans, and you can select that option. When you're ready to start, click the "Fight" button.

## How To Run The Backend ( No Visualizer )
Change directories to `backend`. Run the following command:

`python3 main.py ../maps/your_map.json -a1 ../AI_Agents/your_red_player_ai.py -a2 ../AI_Agents/your_blue_player_ai.py`

But substitute the map and AI agents you want. For example:

`python3 main.py ../maps/map2.json -a1 ../AI_Agents/ExampleAgentRuleBased.py -a2 ../AI_Agents/ExampleAgentRuleBased.py`

## How To Create An Agent
Take a look at `ExampleAgentRuleBased.py` and/or `AgentTemplate.py`. You will be copying the format of those files, and making your own custom version of the `Agent` class. All you need to do is fill out two functions:
1. `initialize_and_set_name` - Gets called at the start of the game, and gives you access to the game's initial state, and importantly, **which team you are on**. Do any initialization you want to here. Return a python string containing your team's name.
2. `do_turn` - Gets called every turn, and has access to the game's state at that turn. This function should return an object of type `AIAction`, representing what you want your agent to do at that turn.
If you want your agent to import libraries or custom python files, or have access to data files (like model weights for deep RL), just let the event organizers know.

## Game State Format
The functions you will be writing for your `Agent` will recieve the state of the game as a big python dictionary. If you *really want to* understand the technical details of how this dictionary created, you can read the code, but doing that is not necessary for creating an agent. However, it *is* necessary to understand the [rules of the game](https://github.com/EliotTexK/MegaMiner2025/tree/main/rules). So, read those or the description below might confuse you!

1. **Team Names** - `game_state["TeamNameR"]` and `game_state["TeamNameB"]`

2. **Victory Condition** - `game_state["Victory"]` - Will be the string `'r'` if the Red player has won, `'b'` if the Blue player has won, `'tie'` if the result of the game is a tie, or the empty string `''` if the game is not over yet.

3. **Remaining Turns and Current Turn** - `game_state["TurnsRemaining"]` and `game_state["CurrentTurn"]`

4. **Player Bases**
    - `game_state["PlayerBaseR"]["Health"]`, `game_state["PlayerBaseB"]["Health"]`
    - `game_state["PlayerBaseR"]["Money"]`, `game_state["PlayerBaseB"]["Money"]`
    - `game_state["PlayerBaseR"]["x"]`, `game_state["PlayerBaseB"]["x"]`
    - `game_state["PlayerBaseR"]["y"]`, `game_state["PlayerBaseB"]["y"]`

5. **Amount Of Money Each Player Has** - `game_state["RedTeamMoney"]` and `game_state["BlueTeamMoney"]`

6. **Floor Tiles** - `game_state["FloorTiles"]` - a 2d array (list of python strings) representing the floor tiles at each position. `'r'` represents Red territory, `'b'` represents Blue territory, `'O'` represents path tiles, and `' '` represents an empty space. For example:
```python
game_state["FloorTiles"] = [
    "rrrrrr     bbbbbb",
    "rrOOOOOOOOOOOOObb",
    "rrOrrr     bbbObb",
    "rrOOOOOOOOOOOOObb",
    "rrOrrr     bbbObb",
    "rrOOOOOOOOOOOOObb",
    "rrrrrr     bbbbbb"
]
```
You should index this list like: `game_state["FloorTiles"][y][x]`.

In the above example, `game_state["FloorTiles"][2][15] = 'b'`

7. **Towers** - a python list of all towers
    - `game_state["Towers"][i]["Name"]` - unique id for the Tower
    - `game_state["Towers"][i]["Type"]` - One of the following: `"Crossbow"`, `"House"`, `"Cannon"`, `"Minigun"`, or `"Church"`
    - `game_state["Towers"][i]["Team"]`
    - `game_state["Towers"][i]["x"]`
    - `game_state["Towers"][i]["y"]`
    - `game_state["Towers"][i]["Cooldown"]`

8. **Mecenaries** - a python list of all mercenaries
    - `game_state["Mercenaries"][i]["Name"]` - unique id for the Mercenary 
    - `game_state["Mercenaries"][i]["Team"]`
    - `game_state["Mercenaries"][i]["x"]`
    - `game_state["Mercenaries"][i]["y"]`
    - `game_state["Mercenaries"][i]["Health"]`
    - `game_state["Mercenaries"][i]["State"]` - will be `"waiting"`, `"fighting"`, or `"moving"`

9. **Demons** - a python list of all demons
    - `game_state["Demons"][i]["Name"]` - unique id for the Demon
    - `game_state["Demons"][i]["Team"]` - **the team the Demon is targeting**
    - `game_state["Demons"][i]["x"]`
    - `game_state["Demons"][i]["y"]`
    - `game_state["Demons"][i]["Health"]`
    - `game_state["Demons"][i]["State"]` - will be `"fighting"` or `"moving"`

10. **Positions of Entities (Demons, Towers, Mercenaries)** - `game_state["EntityGrid"]` - A 2d array ( list of python lists ) representing Demons, Towers, and Mercenaries at each position. This is technically redundant, but exists for your convenience. Sometimes you might want to know what object is at some position, without having to look through and check the Mercenary, Demon, and Tower lists. Index this list the same way as you index the FloorTiles array ( index like `game_state["EntityGrid"][y][x]` ).

11. **Current Prices of Towers For Both Teams** - `game_state["TowerPricesR"]` and `game_state["TowerPricesB"]`, both are python dictionaries.

For example, the following would represent Red's tower prices before they bought any towers:
```python
game_state["TowerPricesR"] = {
    "House" :    10,
    "Crossbow" :  8,
    "Cannon" :   10,
    "Minigun" :  20,
    "Church" :   15
}
```

## AIAction Format

See the `AIAction` class at the top of `ExampleAgentRuleBased.py`.

## How to Play as a Human

The visualizer provides a UI which allows the user to manually play the game as a human. In order to use this feature, select the button labeled "Human" on the AI selection screen and enter a name.

During the game, all buttons in the UI have tooltips which can be seen by hovering over them with the mouse. It is recommended to view all these tooltips to understand what UI buttons correspond to which game action.

*NOTE: While playing as a human, the `S` key acts as a hotkey for the Pass Turn button. If both players are humans, this will pass both player's turns.*

## Map Selection in the Tournament

AI agents will compete in a tournament bracket. Each head-to-head matchup consists of three different maps, and the agent that wins best 2 out of 3 advances.

Map Selection by Tournament Tier

Round 1 uses preselected, public maps for each tier:

Tier 1 – Round 1: map1.json

Tier 2 – Round 1: map4.json

Tier 3 – Round 1: map5.json

Tier 4 – Round 1: map6.json

Round 2 maps are also preselected but kept secret.
However, they are guaranteed to be drawn from the existing maps in the repository.

Round 3 maps are preselected as well, but completely hidden.
These maps do not appear in the repository at all.