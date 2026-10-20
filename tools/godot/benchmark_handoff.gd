extends SceneTree

func _initialize(): call_deferred('benchmark')

func benchmark():
    root.size = Vector2i(960,540)
    DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
    var scene = load('res://generated/characters/inquisitor/visual.tscn')
    var results = []
    for count in [1,25,100]:
        var container = Node2D.new()
        root.add_child(container)
        for i in count:
            var actor = scene.instantiate()
            actor.scale = Vector2(0.3,0.3)
            actor.position = Vector2(40+(i%10)*90,50+(i/10)*48)
            container.add_child(actor)
            actor.get_node('AnimationPlayer').play('attack')
        for i in 30: await process_frame
        var samples = []
        var previous = Time.get_ticks_usec()
        for i in 120:
            await RenderingServer.frame_post_draw
            var current = Time.get_ticks_usec()
            samples.append((current-previous)/1000.0)
            previous = current
        samples.sort()
        var total = 0.0
        for sample in samples: total+=sample
        results.append({'actors':count,'meanFrameMs':total/samples.size(),'p95FrameMs':samples[113],
            'drawCalls':Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
            'textureMemoryBytes':Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)})
        container.queue_free()
        await process_frame
    var report = {'godot':Engine.get_version_info().string,'renderer':'gl_compatibility',
        'workload':'960x540, 0.3 scale visible cutout actors, attack playback; 30 warmup + 120 frames, vsync disabled; no game AI/physics',
        'results':results}
    FileAccess.open('res://../../reports/godot-render-benchmark.json',FileAccess.WRITE).store_string(JSON.stringify(report,'  '))
    print(JSON.stringify(report))
    quit()
