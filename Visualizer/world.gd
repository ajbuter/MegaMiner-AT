extends Node2D

@export var zoom_speed: float = 0.1
@export var min_zoom: float = 0.5
@export var max_zoom: float = 5.0

var zoom : Vector2 = Vector2(1,1)
var offset : Vector2 = Vector2.ZERO

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		var mouse_relative_motion: Vector2 = event.relative
		position = position + mouse_relative_motion
		
		#position.x = clamp(new_position.x, 0, get_viewport_rect().size.x - offset.x * 2)
		#position.y = clamp(new_position.y, 0, get_viewport_rect().size.y - offset.y)
	if event is InputEventMouseButton:
		
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom.x = clamp(zoom.x - zoom_speed, min_zoom, max_zoom)
			zoom.y = clamp(zoom.y - zoom_speed, min_zoom, max_zoom)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom.x = clamp(zoom.x + zoom_speed, min_zoom, max_zoom)
			zoom.y = clamp(zoom.y + zoom_speed, min_zoom, max_zoom)

func _process(_delta: float) -> void:
	
	if scale != zoom:
		scale = zoom
		
