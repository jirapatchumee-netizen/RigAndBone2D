extends Node2D

const CHARACTER = preload('res://generated/characters/inquisitor/visual.tscn')
var actor: CharacterBody2D
var visual: Node2D
var player: AnimationPlayer
var hitbox: Area2D
var dummy: Area2D
var status: Label
var attacking = false
var elapsed = 0.0
var damaged = false
var hp = 100
var damage_count = 0
var hit_start = 0.0
var hit_end = 0.0

func _ready():
    actor = CharacterBody2D.new()
    actor.position = Vector2(350,320)
    add_child(actor)
    visual = CHARACTER.instantiate()
    actor.add_child(visual)
    player = visual.get_node('AnimationPlayer')
    player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
    var animation = player.get_animation('attack')
    hit_start = animation.get_marker_time('hit_start')
    hit_end = animation.get_marker_time('hit_end')
    var sockets = visual.get_meta('sockets')
    var tip = visual.get_node(sockets.weapon_tip)
    hitbox = Area2D.new()
    hitbox.collision_layer = 0
    hitbox.collision_mask = 2
    tip.add_child(hitbox)
    var shape = CollisionShape2D.new()
    var circle = CircleShape2D.new()
    circle.radius = 23
    shape.shape = circle
    shape.position = Vector2(22,0)
    hitbox.add_child(shape)
    dummy = Area2D.new()
    dummy.position = Vector2(520,305)
    dummy.collision_layer = 2
    dummy.collision_mask = 0
    add_child(dummy)
    var dummy_shape = CollisionShape2D.new()
    var rectangle = RectangleShape2D.new()
    rectangle.size = Vector2(48,110)
    dummy_shape.shape = rectangle
    dummy.add_child(dummy_shape)
    status = Label.new()
    status.position = Vector2(30,25)
    add_child(status)
    idle()
    update_status()

func idle():
    player.play('idle')
    player.advance(0)

func attack():
    if attacking: return
    attacking = true
    elapsed = 0
    damaged = false
    player.play('attack')
    player.advance(0)

func _physics_process(delta):
    if not attacking:
        var direction = float(Input.is_physical_key_pressed(KEY_RIGHT))-float(Input.is_physical_key_pressed(KEY_LEFT))
        actor.velocity = Vector2(direction*160,0)
        actor.move_and_slide()
        actor.position.x = clampf(actor.position.x,120,800)
        if Input.is_physical_key_pressed(KEY_SPACE): attack()
    else:
        elapsed += delta
        player.advance(delta)
        if elapsed >= hit_start and elapsed <= hit_end and not damaged and hitbox.overlaps_area(dummy):
            hp = maxi(0,hp-10)
            damage_count += 1
            damaged = true
        if elapsed >= player.get_animation('attack').length:
            attacking = false
            idle()
    update_status()
    queue_redraw()

func update_status():
    status.text = 'LEFT / RIGHT: move     SPACE: attack\nTarget HP: %d     Hits: %d' % [hp,damage_count]

func _draw():
    draw_line(Vector2(0,400),Vector2(960,400),Color(0.2,0.3,0.4),2)
    if dummy:
        draw_rect(Rect2(dummy.position-Vector2(24,55),Vector2(48,110)),Color(0.65,0.35,0.2))
        draw_circle(dummy.position-Vector2(0,75),20,Color(0.8,0.6,0.3))
