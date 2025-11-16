class_name RedMerc
extends Node2D

var str_name
@export var panel : Panel
@export var mouse_detect : Area2D
@export var sprite_anim: AnimatedSprite2D

func _ready() -> void:
	
	if mouse_detect != null:
		mouse_detect.mouse_entered.connect(show_panel)
		mouse_detect.mouse_exited.connect(show_panel)
	
func show_panel():
	panel.show()

func hide_panel():
	panel.hide()

func _update_values(nam : String, health : int):
	$Panel/VBoxContainer/Name.text = nam
	$Panel/VBoxContainer/HP.text = str(health) + "/20"

func move(direction : Vector2):
	match direction.normalized():
		Vector2(-1,0):
			sprite_anim.flip_h = false
		Vector2(1,0):
			sprite_anim.flip_h = true
	
	sprite_anim.play("walk")

func attack(_direction : Vector2):
	await get_tree().create_timer(randf() * 0.25).timeout # randomize animation timing
	sprite_anim.play("attack")
	
func hurt():
	await get_tree().create_timer(0.35).timeout # wait for attack anims to play
	self.rotation_degrees = randf() * 30 - 15
	self.modulate = Color.RED
	var tween = get_tree().create_tween()
	tween.set_trans(Tween.TRANS_QUAD)
	tween.tween_property(self, "rotation_degrees", 0, 0.15)
	tween.tween_property(self, "modulate", Color(1.0, 1.0, 1.0, 1.0), 0.15)

func idle():
	sprite_anim.play("default")
	
func die(time : float, particle):
	var blood_splatter_effect = particle.instantiate()
	await get_tree().create_timer(time).timeout # wait for attack anims to play
	self.get_parent().add_child(blood_splatter_effect)
	blood_splatter_effect.global_position = self.global_position
	(blood_splatter_effect as GPUParticles2D).emitting = true
	self.free()
	
