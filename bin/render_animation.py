import os
import argparse
import pyluxcore
from time import time, sleep


def main():
    pyluxcore.Init()

    parser = argparse.ArgumentParser(description="PyLuxCore Camera Animation")
    parser.add_argument("config_file", help=".cfg, .lxs, .bcf or .rsm file to render")

    args = parser.parse_args()
    props = pyluxcore.Properties(args.config_file)
    sanitize_render_engine(props)
    # TODO: disable halt conditions and handle them in render_frame(), to prevent LuxCore from stopping the session
    halt_samples = 5

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
            render_frame(session, frame, halt_samples)
            render_times.append(time() - start)
            start = time()
    except KeyboardInterrupt:
        session.Stop()
        return

    session.Stop()
    print("Frame render times:")
    for i, t in enumerate(render_times):
        print("Frame %d: %.3f s" % (i, t))


def sanitize_render_engine(props):
    # Debug
    engine_type = props.Get("renderengine.type").GetString()
    if engine_type.endswith("OCL"):
        props.Set(pyluxcore.Property("renderengine.type", engine_type[:-3] + "CPU"))


def update(session, frame, anim_props_dir):
    print("Update for frame", frame)
    config = session.GetRenderConfig()
    scene = config.GetScene()

    session.BeginSceneEdit()

    frame_props = pyluxcore.Properties(os.path.join(anim_props_dir, "%05d.scn" % frame))
    scene_props = scene.ToProperties()

    # TODO: make generic so any group of keys in frame_props is fetched from scene_props
    new_props = frame_props.GetAllProperties("scene.camera")

    for key in frame_props.GetAllUniqueSubNames("scene.objects"):
        obj_props = scene_props.GetAllProperties(key)
        obj_props_frame = frame_props.GetAllProperties(key)
        obj_props.Set(obj_props_frame)
        new_props.Set(obj_props)

    scene.Parse(new_props)
    session.EndSceneEdit()


def render_frame(session, frame, halt_samples):
    print("Rendering frame", frame)

    while not session.HasDone():
        sleep(1)
        session.UpdateStats()
        stats = session.GetStats()
        elapsed_time = stats.Get("stats.renderengine.time").GetFloat()
        samples = stats.Get("stats.renderengine.pass").GetUnsignedLongLong()
        print("Time: %d s\tSamples: %d" % (elapsed_time, samples))

        # Debug
        if halt_samples and samples >= halt_samples:
            break

    filename = "%05d.png" % frame
    output_props = pyluxcore.Properties()
    session.GetFilm().SaveOutput(filename, pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE, output_props)


if __name__ == "__main__":
    main()
