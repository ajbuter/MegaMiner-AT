extends Node2D


const BLOOD_SPLATTER_FX = preload("res://objects/big_blood_splatter.tscn")
const HIT_SPARK_FX = preload("res://objects/sparks.tscn")

const GRASS_RED_TEX = preload("res://Assets/HD_Skin/grass_red.png")
const GRASS_BLUE_TEX = preload("res://Assets/HD_Skin/grass_blue.png")
const PATH_TEX = preload("res://Assets/HD_Skin/path.png")

const BLUE_RECRUIT = preload("res://objects/bluemerc.tscn")
const RED_RECRUIT = preload("res://objects/redmerc.tscn")

const ENEMY = preload("res://objects/demon.tscn")
const ENEMY_SPAWNER = preload("res://Assets/HD_Skin/enemy_spawner.png")


const CROSSBOW = preload("res://Assets/HD_Skin/crossbow/crossbow.png")
const CANNON = preload("res://Assets/HD_Skin/cannon/cannon.png")
const GATLING = preload("res://Assets/HD_Skin/gatling/gatling.png")
const HOUSE = preload("res://Assets/HD_Skin/house/house.png")
const CHURCH = preload("res://Assets/HD_Skin/church/church.png")

const BLUE_CROSSBOW = preload("res://Assets/HD_Skin/crossbow/blue_crossbow.png")
const BLUE_CANNON = preload("res://Assets/HD_Skin/cannon/blue_cannon.png")
const BLUE_GATLING = preload("res://Assets/HD_Skin/gatling/blue_gatling.png")
const BLUE_HOUSE = preload("res://Assets/HD_Skin/house/blue_house.png")
const BLUE_CHURCH = preload("res://Assets/HD_Skin/church/blue_church.png")

const STRUTS = preload("res://Assets/HD_Skin/stand.png")
const BLUE_STRUTS = preload("res://Assets/HD_Skin/blue_stand.png")

const RED_CASTLE : Texture = preload("res://Assets/HD_Skin/Red_base.png")
const BLUE_CASTLE: Texture = preload("res://Assets/HD_Skin/Blue_base.png")

const UNDERNEATH_TILE = preload("res://objects/underneath_tile.tscn")

@export var UI : GameUI

var previous_game_state : Dictionary 
var current_game_state : Dictionary

var is_player1_ai : bool
var is_player2_ai : bool

var play1ready : bool = false
var play2ready : bool = false

var initial : bool  = true

var backend_running : bool = false

var turn_interval_max : float = 0.6 
var turn_interval : float = 0
var path_to_game_state

@onready var world: Node2D = $World
@onready var tiles = $World/Tiles
@onready var mercenaries: Node2D = $World/Mercenaries
@onready var towers: Node2D = $World/Towers
@onready var demons: Node2D = $World/Demons
@onready var misc_entities: Node2D = $"World/Misc Entities"
@onready var spawners: Node2D = $"World/Spawners"

var processID
var stdio : FileAccess
var thread
var stderr : FileAccess

signal next_turn

func _ready():
	#for p: Node2D in [tiles, mercenaries, towers, demons, misc_entities, spawners]:
		#for n in p.get_children():
			#p.remove_child(n)
			#n.queue_free() 
	UI.action.connect(_on_ui_action)
	next_turn.connect(UI.on_next_turn)

# Sets up the game visuals
func _on_ui_start_game(is_ai1, is_ai2):
	is_player1_ai = is_ai1
	is_player2_ai = is_ai2
	var process_info 
	
	if is_ai1 and is_ai2:
		process_info = OS.execute_with_pipe("python", 
			[GlobalPaths.backendPath, GameSettings.selected_map, "-a1", GlobalPaths.AI_agent1_file_path, "-a2",GlobalPaths.AI_agent2_file_path, "-v"], 
			true)
		
	elif not is_ai1 and is_ai2:
		process_info = OS.execute_with_pipe("python", 
			[GlobalPaths.backendPath, GameSettings.selected_map, "-h1" , "-a2",GlobalPaths.AI_agent2_file_path, "-v"], 
			true)
		play2ready = true
	
	elif is_ai1 and not is_ai2:
		process_info = OS.execute_with_pipe("python", 
			[GlobalPaths.backendPath, GameSettings.selected_map, "-a1", GlobalPaths.AI_agent1_file_path, "-h2", "-v"], 
			true)
		play1ready = true
	else:
		process_info = OS.execute_with_pipe("python", 
			[GlobalPaths.backendPath, GameSettings.selected_map, "-h1", "-h2", "-v"], 
			true)
	
	processID = process_info["pid"]
	stdio = process_info["stdio"]
	stderr = process_info["stderr"]
	
	if stdio != null:
		print(stdio.get_line())
		var content = stdio.get_line() ##Initial State
		print(stdio.get_line())
		print(stdio.get_line())
		print(stdio.get_line())
		var first_turn
		if is_ai1 and is_ai2:
			first_turn = stdio.get_line() #First turn
	
	
		_draw_game_from_gamestate(content)
		if is_ai1 and is_ai2:
			await get_tree().create_timer(2.0).timeout
			_draw_game_from_gamestate(first_turn)
			turn_interval = turn_interval_max
		backend_running = true


# Updates world visuals
func _draw_game_from_gamestate(game_state : String):
	var game_state_json = JSON.parse_string(game_state)
	current_game_state = game_state_json
	next_turn.emit()
	if initial:
		previous_game_state = current_game_state
		_draw_grid(game_state_json["FloorTiles"])
		
		UI._update_team_names(current_game_state["TeamNameR"], current_game_state["TeamNameB"])
		
		## Setting up castles
		var castle = Sprite2D.new()
		
		castle.texture = RED_CASTLE
		castle.scale.x = 32 /  RED_CASTLE.get_size().x
		castle.scale.y = 32 / RED_CASTLE.get_size().y
		
		castle.position = Vector2(game_state_json["PlayerBaseR"]["x"] * 32, game_state_json["PlayerBaseR"]["y"] * 32) + Vector2(0,-5)
		castle.y_sort_enabled = true
		misc_entities.add_child(castle)
		
		var castle_b = Sprite2D.new()
		
		castle_b.texture = BLUE_CASTLE
		castle_b.scale.x = 32 /  castle_b.texture.get_size().x
		castle_b.scale.y = 32 / castle_b.texture.get_size().y
		
		castle_b.position = Vector2(game_state_json["PlayerBaseB"]["x"] * 32, game_state_json["PlayerBaseB"]["y"] * 32) + Vector2(0,-5)
		castle_b.y_sort_enabled = true
		misc_entities.add_child(castle_b)

		## Setting up spawners
		for spawner in game_state_json["DemonSpawners"]:
			var sprite = Sprite2D.new() 
			sprite.texture = ENEMY_SPAWNER
			sprite.scale.x = 32 /  ENEMY_SPAWNER.get_size().x
			sprite.scale.y = 32 / ENEMY_SPAWNER.get_size().y
			sprite.position = Vector2(spawner.x * 32, spawner.y * 32)
			sprite.z_index = 1
			spawners.add_child(sprite)

		initial = false
		
	# check if player bases damaged and spawn hitspark
	if (game_state_json["PlayerBaseR"]["Health"] < previous_game_state["PlayerBaseR"]["Health"]):
		var spark = HIT_SPARK_FX.instantiate()
		var base : Sprite2D = misc_entities.get_child(0)
		
		base.modulate = Color.RED
		var tween = get_tree().create_tween()
		tween.set_trans(Tween.TRANS_QUAD)
		tween.tween_property(base, "modulate", Color(1.0, 1.0, 1.0, 1.0), 0.15)
	
		add_child(spark)
		spark.global_position = base.global_position
		(spark as GPUParticles2D).emitting = true
		
	if (game_state_json["PlayerBaseB"]["Health"] < previous_game_state["PlayerBaseB"]["Health"]):
		var spark = HIT_SPARK_FX.instantiate()
		var base : Sprite2D = misc_entities.get_child(1)
		
		base.modulate = Color.RED
		var tween = get_tree().create_tween()
		tween.set_trans(Tween.TRANS_QUAD)
		tween.tween_property(base, "modulate", Color(1.0, 1.0, 1.0, 1.0), 0.15)
		
		add_child(spark)
		spark.global_position = base.global_position
		(spark as GPUParticles2D).emitting = true
		
	_draw_mercenaries(game_state_json["Mercenaries"], previous_game_state["Mercenaries"])
	_draw_towers(game_state_json["Towers"])
	_draw_demons(game_state_json["Demons"], previous_game_state["Demons"])
	_update_ui(game_state_json)


func _draw_grid(tile_grid : Array):
	var layer_y : int = 0
	var alt_y = false
	for layer in tile_grid:
		var character_x = 0
		var alt_x = false
		
		for character in layer:
			var sprite = Sprite2D.new()

			if character == 'b':
				sprite.texture = GRASS_BLUE_TEX
			elif character == 'O':
				sprite.texture = PATH_TEX
			elif character == 'r':
				sprite.texture = GRASS_RED_TEX
			
			if alt_x == alt_y:
				sprite.self_modulate = Color8(255, 255, 255)
			else:
				sprite.self_modulate = Color8(220, 220, 220)
			
			sprite.scale = Vector2(0.125,0.125)
			sprite.position = Vector2(character_x * 32, layer_y * 32)
			tiles.add_child(sprite)
			character_x += 1
			
			# add "underneath" tile area
			if character in ['b', 'O', 'r']:
				var underneath = UNDERNEATH_TILE.instantiate()
				underneath.position = sprite.position + Vector2(0,48)
				tiles.add_child(underneath)
				
			
			alt_x = !alt_x
			
		layer_y += 1
		alt_y = !alt_y
	
	
	world.offset.x = (get_viewport_rect().size.x - (tile_grid[0].length() * 32)) / 2
	world.offset.y = (get_viewport_rect().size.y - (tile_grid.size() * 32)) / 2
	
	world.position = world.offset
	
	GlobalPaths.tile_grid = tiles

#func _delete_mercs():
	#for i in mercenaries.get_children():
		#i.queue_free()

# Draws the mercanaries
func _draw_mercenaries(mercs : Array, prev_mercs: Array):
	#print(mercs)
	var count = 0
	for merc in mercs:
		# find previous state of this merc
		var prev_merc = null
		for _merc in prev_mercs:
			if (_merc["Name"] == merc["Name"]):
				prev_merc = _merc
				break
				
		if mercenaries.get_child_count() - 1 < count:
			var pos = Vector2(merc["x"] * 32, merc["y"] * 32)
			var sprite : RedMerc
			if merc["Team"] == "b":
				sprite = BLUE_RECRUIT.instantiate()
				
			else:
				sprite = RED_RECRUIT.instantiate()
				
			sprite.position = pos
			mercenaries.add_child(sprite)
		else:
			var child : RedMerc = mercenaries.get_child(count)
			
			if merc["Team"] == 'r':
				child._update_values(merc["Name"], merc["Health"])
			
			if merc["State"] == "dead":
				child.reparent(world)
				child.die(turn_interval_max, BLOOD_SPLATTER_FX)
				count -= 1
			elif merc["State"] == "moving":
				var tween = get_tree().create_tween()
				child.move(child.position - Vector2(merc["x"] * 32, merc["y"] * 32))
				tween.tween_property(child, "position", Vector2(merc["x"] * 32, merc["y"] * 32), turn_interval_max)
				tween.tween_callback(child.idle)
			else:
					child.attack(Vector2(1,0))
					
			if (prev_merc && merc["Health"] < prev_merc["Health"] && is_instance_valid(child)):
				child.hurt()
		
		count += 1

func _draw_towers(data_towers : Array):
	print(data_towers)
	
	var count = 0
	for tower in data_towers:
		if towers.get_child_count() - 1 < count:
			var pos = Vector2(tower["x"] * 32, tower["y"] * 32)
			var sprite : Sprite2D
			var makeStruts : bool = false
			
			match tower["Type"]:
				"Crossbow":
					sprite = Sprite2D.new()
					sprite.texture = CROSSBOW if tower["Team"] == "r" else BLUE_CROSSBOW
					sprite.scale = Vector2(32 / sprite.texture.get_size().x, 32 / sprite.texture.get_size().y)
					sprite.y_sort_enabled = true
					makeStruts = true;
				"Cannon":
					sprite = Sprite2D.new()
					sprite.texture = CANNON if tower["Team"] == "r" else BLUE_CANNON
					sprite.scale = Vector2(32 / sprite.texture.get_size().x, 32 / sprite.texture.get_size().y)
					sprite.y_sort_enabled = true
					makeStruts = true;
				"Minigun":
					sprite = Sprite2D.new()
					sprite.texture = GATLING if tower["Team"] == "r" else BLUE_GATLING
					sprite.scale = Vector2(32 / sprite.texture.get_size().x, 32 / sprite.texture.get_size().y)
					sprite.y_sort_enabled = true
					makeStruts = true;
				"House":
					sprite = Sprite2D.new()
					sprite.texture = HOUSE if tower["Team"] == "r" else BLUE_HOUSE
					sprite.scale = Vector2(32 / sprite.texture.get_size().x, 32 / sprite.texture.get_size().y)
					sprite.y_sort_enabled = true
				"Church":
					sprite = Sprite2D.new()
					sprite.texture = CHURCH if tower["Team"] == "r" else BLUE_CHURCH
					sprite.scale = Vector2(32 / sprite.texture.get_size().x, 32 / sprite.texture.get_size().y)
					sprite.y_sort_enabled = true
			
			##sprite = CROSSBOW.instantiate()
			var parentNode: Node2D = Node2D.new();
			parentNode.name = tower["Name"]
			parentNode.position = pos + Vector2(0, -5)
			sprite.name = tower["Name"] + "Sprite"
			#sprite.position = pos + Vector2(0,-5)
			parentNode.add_child(sprite)
			towers.add_child(parentNode)
			
			var cooldownLabel: Label = Label.new()
			cooldownLabel.text = str(int(tower["Cooldown"]))
			cooldownLabel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			cooldownLabel.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			cooldownLabel.scale *= 0.8
			parentNode.add_child(cooldownLabel)
			cooldownLabel.global_position = parentNode.global_position
						
			if (makeStruts):
				var strut1 = Sprite2D.new()
				strut1.scale = Vector2(32 / sprite.texture.get_size().x, 32 / sprite.texture.get_size().y)
				strut1.texture = STRUTS if tower["Team"] == "r" else BLUE_STRUTS
				parentNode.add_child(strut1)
				#strut1.reparent(towerStands)
				strut1.z_index = -1
				strut1.global_position = sprite.global_position
		else:
			var child = towers.get_child(count)
			var prev_tower = null
			if len(previous_game_state["Towers"]) > 0:
				prev_tower = previous_game_state["Towers"][count]
			
			while (child.name != tower["Name"]):
				child.free()
				if count >= towers.get_child_count():
					child = null
					break
				child = towers.get_child(count)
			
			if child == null:
				continue
			
			(child.get_child(1) as Label).text = str(int(tower["Cooldown"]))
			if tower["Type"] != "Church":
				var tween = get_tree().create_tween()
				tween.set_trans(Tween.TRANS_QUAD)
				for target in tower["Targets"]:
					var theta = atan2((target[1] - tower["y"]), (target[0] - tower["x"])) + (PI * 0.5)
					tween.tween_property(child.get_child(0), "rotation", theta, turn_interval_max / 2.0)
					#tween.tween_property(child.get_child(0), "rotation", -theta, turn_interval_max / 2.0)
					if child is Crossbow:
						tween.tween_callback(child.shoot.bind(turn_interval_max / 2))
						
			
			
			# darken tower based on cooldown
			var c : float = max (2.718 ** (-tower["Cooldown"] * 0.3), 0.4)
			child.get_child(0).self_modulate = Color(c, c, c, 1.0)
			child.get_child(0).self_modulate.a = 1
			
			# animate towers being "activated" based on cooldown
			if (prev_tower && prev_tower["Cooldown"] == 0 && tower["Cooldown"] != 0):
				var sprite = child.get_child(0)
				var tween = get_tree().create_tween()
				tween.set_trans(Tween.TRANS_BOUNCE)
				tween.tween_property(sprite, "scale", sprite.scale, turn_interval_max / 2.0)
				sprite.scale *= 1.1
			
		count += 1


func _draw_demons(dem_array : Array, prev_array : Array):
	var count = 0
	for dem in dem_array:
		# find previous state of this dem
		var prev_dem = null
		for _dem in prev_array:
			if (_dem["Name"] == dem["Name"]):
				prev_dem = _dem
				break
				
		if prev_dem == null:
			var pos = Vector2(dem["x"] * 32, dem["y"] * 32)
			var demon_obj : RedMerc = ENEMY.instantiate()
			if dem["Team"] == "b":
				demon_obj.sprite_anim.flip_h = false
			else:
				demon_obj.sprite_anim.flip_h = true
			
			demon_obj.position = pos
			demon_obj.str_name = dem["Name"]
			demons.add_child(demon_obj)
		else:
					
			var child = null
			for n: RedMerc in demons.get_children():
				if (n.str_name == dem["Name"]):
					child = n
					break
			if dem["State"] == "dead" || prev_dem["State"] == "dead":
				child.reparent(world)
				child.die(turn_interval_max, BLOOD_SPLATTER_FX)
				count -= 1		
			elif dem["State"] == "moving":
				var tween = get_tree().create_tween()
				child.move(child.position - Vector2(dem["x"] * 32, dem["y"] * 32))
				tween.tween_property(child, "position", Vector2(dem["x"] * 32, dem["y"] * 32), turn_interval_max)
				tween.tween_callback(child.idle)
			else:
				child.attack(Vector2(1,0))
				
			if (prev_dem && dem["Health"] < prev_dem["Health"] && is_instance_valid(child)):
				child.hurt()
				
		count += 1

func _process(delta):
	if backend_running:
		if is_player1_ai and is_player2_ai: ## If both players are AI
			turn_interval -= 1.0 * delta
			if turn_interval <= 0:
				AI_game_turn()
				turn_interval = turn_interval_max
		else:
			if play1ready and play2ready:
				
				if stdio.get_error() == OK:
					var content = stdio.get_line()
					if !content.begins_with("--WINNER"):
						previous_game_state = current_game_state
						_draw_game_from_gamestate(content)
					else:
						print(content)
						backend_running = false
					stdio.store_line("--NEXT TURN--")
					stdio.flush() # Ensure data is written to the pipe
				
				play1ready = is_player1_ai
				play2ready = is_player2_ai

func AI_game_turn():
	var content : String = ""
	if stdio.get_error() == OK:
		stdio.store_line("--NEXT TURN--")
		stdio.flush() # Ensure data is written to the pipe
		content = stdio.get_line()
	else:
		printerr("Open file error: ", stdio.get_error())
		backend_running = false
	
	previous_game_state = current_game_state
	
	if !content.begins_with("--WINNER"):
		_draw_game_from_gamestate(content)
	else:
		backend_running = false


func _on_ui_action(is_player1 : bool, action : String , x: int, y: int, to_build : String ,merc : String) -> void:
	if is_player1:
		play1ready = true
	else:
		play2ready = true
	
	if stdio.get_error() == OK:
		var player_action = "{\"action\": \"" + action + "\", \"x\": " + str(x) + ", \"y\": " + str(y) + ", \"tower_type\": \"" + to_build + "\", \"merc_direction\": \"" + merc + "\"}"
		#print(player_action)
		stdio.store_line(player_action)
		stdio.flush() # Ensure data is written to the pipe

func _update_ui(gamestate):
	UI._update_turns_progressed(gamestate["TurnsRemaining"])
	UI._update_money_values(gamestate["PlayerBaseR"]["Money"], gamestate["PlayerBaseB"]["Money"])
	UI._update_base_health(true, gamestate["PlayerBaseR"]["Health"])
	UI._update_base_health(false, gamestate["PlayerBaseB"]["Health"])
	UI._update_building_prices(gamestate)
	UI._update_postgame_popup(gamestate["Victory"], gamestate["VictoryReason"])

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		if processID != null:
			OS.kill(processID) ##Terminates the process
			get_tree().quit()

func _close_backend():
	stdio.close()
	stderr.close()
	OS.kill(processID)
