class_name Crossbow
extends Sprite2D

var str_name : String

var targets : Array

@onready var animation_player: AnimationPlayer = $AnimationPlayer

func shoot(speed : float):
	
	animation_player.play("shoot", 0, speed)
	


func _on_animation_player_animation_changed(old_name: StringName, new_name: StringName) -> void:
	if new_name == "shoot":
		targets.pop_front()
		rotation = position.angle_to(targets.front())
