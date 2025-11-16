class_name GameUI
extends CanvasLayer

@onready var main_menu : Control = $"Main Menu"

@onready var human_ai_select : Control = $"Human AI select"

@onready var game_ui: Control = $"Game UI"

var ai1 : bool = false
var ai2 : bool = false

signal start_game(is_ai1 : bool, is_ai2 : bool)

signal action(player_1 : bool, build : String, x : int, y : int, tower_to_build : String ,merc_direction : String)

var red_turn : bool = true

func _ready():
	main_menu.visible = true
	human_ai_select.visible = false
	game_ui.visible = false

func _process(_delta: float) -> void:
	pass

func _update_turns_progressed(new_value):
	$"Game UI/Turns/PanelContainer/Turns Progressed".text = str(int(new_value))
	$"Game UI/Turns/PanelContainer/TextureProgressBar".value = int(new_value)

func _update_money_values(left_value, right_value):
	$"Game UI/LeftSideStates/Money/Money".text = str(int(left_value))
	
	$"Game UI/RightSideStates/Money/Money".text = str(int(right_value))

func _update_base_health(is_left : bool, new_value):
	if is_left:
		var tween = get_tree().create_tween()
		tween.tween_property($"Game UI/LeftSideStates/Health/TextureProgressBar", "value", new_value, 1.5)
	else:
		var tween = get_tree().create_tween()
		tween.tween_property($"Game UI/RightSideStates/Health/TextureProgressBar", "value", new_value, 1.5)
		
func _update_building_prices(game_state):
	for bldg: String in ["House", "Crossbow", "Minigun", "Cannon", "Church"]:
		get_node("Game UI/LeftSideStates/Human Control/Build OPtions/" + bldg).text = bldg + "\n$" + str(game_state["TowerPricesR"][bldg]).pad_decimals(0)
		get_node("Game UI/RightSideStates/Human Control/Build OPtions/" + bldg).text = bldg + "\n$" + str(game_state["TowerPricesB"][bldg]).pad_decimals(0)

func _update_team_names(rName: String, bName: String):
	$"Game UI/LeftSideStates/TeamName/Name".text = rName
	$"Game UI/RightSideStates/TeamName/Name".text = bName

func _update_postgame_popup(victory, reason):
	$"Game UI/Scroll/ReasonLabel".text = reason
	match victory:
		'r':   
			$"Game UI/Scroll/Label".text = "RED WINS!"
			_scroll_popup($"Game UI/Scroll")
		'b':   
			$"Game UI/Scroll/Label".text = "BLUE WINS!"
			_scroll_popup($"Game UI/Scroll")
		'tie': 
			$"Game UI/Scroll/Label".text = "TIE?!?!??!?"
			_scroll_popup($"Game UI/Scroll")
		_: # no winner
			pass

# Make scroll appear after game ends
func _scroll_popup(scroll: Node2D):
	await get_tree().create_timer(0.5).timeout
	scroll.position.y = -200
	scroll.visible = true;
	var tween = get_tree().create_tween()
	tween.set_trans(Tween.TRANS_ELASTIC)
	tween.tween_property(scroll, "position", Vector2(600, 300), 2)


func _on_main_menu_play_game() -> void:
	human_ai_select.visible = true
	main_menu.visible = false
	
func _on_human_ai_select_go(is_ai: bool, is_ai2: bool) -> void:
	ai1 = is_ai
	ai2 = is_ai2
	
	if ai1 and ai2:
		pass
	elif not ai1 and ai2:
		red_turn = true
	elif ai1 and not ai2:
		red_turn = false
	else:
		pass
	
	start_game.emit(is_ai, is_ai2)
	main_menu.hide()
	human_ai_select.hide()
	game_ui.show()
	
	if !is_ai:
		$"Game UI/LeftSideStates".active = true
		$"Game UI/LeftSideStates/Human Control".show()
	if !is_ai2:
		$"Game UI/RightSideStates".active = true
		if is_ai:
			$"Game UI/RightSideStates/Human Control".show()

func _on_human_ai_select_back() -> void:
	main_menu.visible = true
	human_ai_select.visible = false

func _on_right_side_states_action(is_player1: bool, build: String, x: int, y: int, tower_to_build: String, merc_direction: String) -> void:
	if tower_to_build == "skip" and is_player1:
		action.emit(is_player1, build, x, y, tower_to_build, merc_direction)
		action.emit(!is_player1, build, x, y, tower_to_build, merc_direction)
	
	elif is_player1 == red_turn:
		action.emit(is_player1, build, x, y, tower_to_build, merc_direction)
		
		if ai1 == ai2: #and tower_to_build != "skip":
			red_turn = !red_turn
			$"Game UI/Turns/Player Turn".modulate = Color(255,255,255)
			if red_turn:
				$"Game UI/Turns/Player Turn".text = "Red Player's Turn\n<---"
				$"Game UI/LeftSideStates/Human Control".show()
				$"Game UI/RightSideStates/Human Control".hide()
				var tween = get_tree().create_tween()
				tween.tween_property($"Game UI/Turns/Player Turn", "modulate", Color(255,255,255,0), 5.0)
				$"Game UI/AnimationPlayer".play("red Side glow")
				print("Red players turn!")
			else:
				$"Game UI/Turns/Player Turn".text = "Blue Player's Turn\n--->"
				$"Game UI/LeftSideStates/Human Control".hide()
				$"Game UI/RightSideStates/Human Control".show()
				var tween = get_tree().create_tween()
				tween.tween_property($"Game UI/Turns/Player Turn", "modulate", Color(255,255,255,0), 5.0)
				$"Game UI/AnimationPlayer".play("blue side glow")
				print("blue players turn!")

func on_next_turn():	
	$"Game UI/LeftSideStates"._on_next_turn()
	$"Game UI/RightSideStates"._on_next_turn()
	

# postgame back button
func _on_back_button_pressed():
	#game_ui.visible = false
	#human_ai_select.visible = true
	get_tree().change_scene_to_file("res://game.tscn")
