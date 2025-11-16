class_name PlayerSelect
extends Control

@export var is_player_1 : bool = true

var is_AI : bool = true

var ready_to_play : bool = false

@export var human_icon : Sprite2D
@export var ai_icon : Sprite2D

@export var line_edit : LineEdit
@export var file_picker : Button

@export var file_dialog : FileDialog


func _ready():
	file_dialog.file_selected.connect(_on_file_dialog_file_selected)
	is_AI = true
	_set_mode(true)

# Sets whether or not a Human or an AI will be playing
func _set_mode(AI : bool):
	if AI && !is_AI: # If AI presses, and it currently isn't AI, change visuals
		ai_icon.visible = true
		human_icon.visible = false
		
		line_edit.focus_mode = Control.FOCUS_NONE
		line_edit.placeholder_text = "Open a file..."
		line_edit.editable = false
		line_edit.selecting_enabled = false
		
		file_picker.show()
		is_AI = true
	elif !AI && is_AI: # If Human presses, and it currently Human AI, change visuals
		ai_icon.visible = false
		human_icon.visible = true
		
		line_edit.focus_mode = Control.FOCUS_CLICK
		line_edit.placeholder_text = "Type team name..."
		line_edit.editable = true
		line_edit.selecting_enabled = true
		
		file_picker.hide()
		is_AI = false

func _on_human_pressed():
	_set_mode(false)

func _on_ai_pressed():
	_set_mode(true)

func _on_file_picker_pressed():
	file_dialog.visible = true


func _on_file_dialog_file_selected(path : String):
	if path.ends_with(".py"):
		GlobalPaths.convert_string_to_readable(path)
		if is_player_1:
			GlobalPaths.AI_agent1_file_path = path
		else:
			GlobalPaths.AI_agent2_file_path = path
		
		line_edit.text = path
	else:
		printerr("Select File isn't supported!")
