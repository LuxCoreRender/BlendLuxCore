
import os
import argparse
import pyluxcore
from time import time, sleep


def sanitize_render_engine(props):
    # Debug
    engine_type = props.Get("renderengine.type").GetString()
    if engine_type.endswith("OCL"):
        props.Set(pyluxcore.Property("renderengine.type", engine_type[:-3] + "CPU"))


def main():
    pyluxcore.Init()

    parser = argparse.ArgumentParser(description="PyLuxCore Camera Animation")
    parser.add_argument("config_file", help=".cfg, .lxs, .bcf or .rsm file to render")

    args = parser.parse_args()
    props = pyluxcore.Properties(args.config_file)
    sanitize_render_engine(props)

    pyluxcore.AddFileNameResolverPath(os.path.dirname(args.config_file))

    render_times = []
    start = time()
    config = pyluxcore.RenderConfig(props)
    session = pyluxcore.RenderSession(config)
    session.Start()
    print("Startup time:", time() - start)

    anim_props_dir = os.path.join(os.path.dirname(args.config_file), "anim")
    frame_start = 1
    frame_end = 5

    try:
        for frame in range(frame_start, frame_end + 1):
            update(session, frame, anim_props_dir)
            render_frame(session, frame)
            render_times.append(time() - start)
            start = time()
    except KeyboardInterrupt:
        session.Stop()
        return

    session.Stop()
    print("Frame render times:")
    for i, t in enumerate(render_times):
        print("Frame %d: %.3f s" % (i, t))


def update(session, frame, anim_props_dir):
    print("Update for frame", frame)
    config = session.GetRenderConfig()
    scene = config.GetScene()

    session.BeginSceneEdit()

    # This works
    # cameraProps = scene.ToProperties().GetAllProperties("scene.camera")
    # fov = 70 - 10 * frame
    # print("fov:", fov)
    # cameraProps.Set(pyluxcore.Property("scene.camera.fieldofview", fov))
    # scene.Parse(cameraProps)

    frame_props = pyluxcore.Properties(os.path.join(anim_props_dir, "%05d.scn" % frame))
    # frame_props = pyluxcore.Properties()
    # if frame > 1:
    #     t = [float(elem) for elem in
    #          "1 0 0 0 0 1 0 0 0 0 1 0 0.45968633890151978 -0.63940036296844482 0.18945108354091644 1".split(" ")]
    #     print(t)
    #     frame_props.Set(pyluxcore.Property("scene.objects.Mesh_animated_140570184019464000.transformation", t))
    print("Setting frame props for frame", frame)
    print(frame_props)
    # scene_props = scene.ToProperties()
    # old = scene_props.ToString()

    # scene_props.Set(frame_props)

    # new = scene_props.ToString()
    # print("Changes:")
    # for i, old_line in enumerate(old.split("\n")):
    #     new_line = new.split("\n")[i]
    #     if new_line != old_line:
    #         print("<")
    #         print(old_line)
    #         print(">")
    #         print(new_line)
    #         print("-")
    # print("-----")

    # scene.Parse(scene_props)
    scene_props = scene.ToProperties()
    new_props = frame_props.GetAllProperties("scene.camera")

    for key in frame_props.GetAllUniqueSubNames("scene.objects"):
        obj_props = scene_props.GetAllProperties(key)
        obj_props_frame = frame_props.GetAllProperties(key)
        obj_props.Set(obj_props_frame)
        new_props.Set(obj_props)

    scene.Parse(new_props)



    # if frame > 1:
    #     t = [float(elem) for elem in
    #          "1 0 0 0 0 1 0 0 0 0 1 0 0.45968633890151978 -0.63940036296844482 0.18945108354091644 1".split(" ")]
    #     scene.UpdateObjectTransformation("Mesh_Sphere__001_140282129500680000", t)

    # __import__('code').interact(local=dict(globals(), **locals()))

    session.EndSceneEdit()


def render_frame(session, frame):
    print("Rendering frame", frame)

    while not session.HasDone():
        sleep(1)
        session.UpdateStats()
        stats = session.GetStats()
        elapsed_time = stats.Get("stats.renderengine.time").GetFloat()
        current_pass = stats.Get("stats.renderengine.pass").GetUnsignedLongLong()
        print("Time: %d s\tSamples: %d" % (elapsed_time, current_pass))

        # Debug
        if current_pass > 1:
            break

    filename = "%05d.png" % frame
    output_props = pyluxcore.Properties()
    session.GetFilm().SaveOutput(filename, pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE, output_props)


if __name__ == "__main__":
    main()
