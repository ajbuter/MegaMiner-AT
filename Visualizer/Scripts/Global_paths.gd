extends Node

var backendPath : String = "../backend/main.py"

var AI_agent1_file_path : String = "../backend/AI_Agents/AgentTemplate.py"
var AI_agent2_file_path : String = "../backend/AI_Agents/AgentTemplate.py"

var player_one_selecting : bool = false

var tile_grid : Node2D

# So depending on the system, the still will have '\' which doesn't work, so this function just changes '\' to '/'
func convert_string_to_readable(string : String):
	for i in string:
		if i == '\'':
			i = '/'
