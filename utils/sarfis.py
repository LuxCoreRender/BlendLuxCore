import bpy
import requests
import os
import json
from . import ui as utils_ui
from . import get_abspath
from time import time

# TODO:
#  - error handling (network errors, file system errors etc.)
#  - throw error when halt conditions are missing (similar to animation render)
#  - threading
#  - handle dependencies (external assets, simulation caches, textures etc.)
#  - download frames immediately once they are done (while others are still rendering)

server = ""

AUTO_POLL_INTERVAL = 5  # seconds


class Progress:
    def update(self, job_tasks):
        self.frame_count = len(job_tasks)
        self.finished = 0
        self.errored = 0
        frame_times = []

        for frame, stats in job_tasks.items():
            status = stats["status"]
            if status == Status.FINISHED:
                self.finished += 1
                frame_times.append((int(frame), stats["time"]))
            elif status == Status.ERROR:
                self.errored += 1

        if frame_times:
            frame_times.sort(key=lambda elem: elem[1])
            self.time_min = frame_times[0]
            self.time_max = frame_times[-1]
            self.time_median = frame_times[(len(frame_times) - 1) // 2]
        else:
            self.time_min = 0, 0
            self.time_max = 0, 0
            self.time_median = 0, 0


class Status:
    job_id = None
    status = None
    progress = None
    time_start = None
    time_end = None

    # status types
    QUEUED = "queued"
    PAUSED = "paused"
    RUNNING = "running"
    ERROR = "error"
    FINISHED = "finished"


def _upload(filepath):
    # TODO progress report in UI?
    _json = {
        "file_name": os.path.basename(filepath),
        "bucket": "lux-test-bucket"
    }
    signed_url = requests.post(f"{server}api/signed_upload", json=_json).text
    with open(filepath, "rb") as f:
        requests.put(signed_url, f)


def create_job(filepath, start_frame, end_frame):
    assert start_frame <= end_frame

    _upload(filepath)

    _json = {
        "name": "Jobs Name",
        "type": "blender",
        "version": "280",
        "operation": "render",
        "start": str(start_frame),
        "end": str(end_frame),
        "input": os.path.basename(filepath),
        "output": "output/"
    }
    job_id = requests.post(f"{server}api/blender_job", json=_json).text
    Status.job_id = job_id
    return job_id


def _set_job_status(job_id, status):
    assert status in {Status.QUEUED, Status.PAUSED}
    requests.get(f"{server}api/job_status", data={"job_id": job_id, "status": status})


def pause_job(job_id):
    print("Pausing job")
    _set_job_status(job_id, Status.PAUSED)


# aka resume
def queue_job(job_id):
    print("Queueing/resuming job")
    _set_job_status(job_id, Status.QUEUED)


def delete_job(job_id):
    print("Deleting job")
    requests.get(f"{server}api/delete_job", data={"job_id": job_id})


def poll_job_details(job_id):
    response = requests.get(f"{server}api/job_details", data={"job_id": job_id})

    if response.status_code == requests.codes.ok:
        if response.text:
            job_details = json.loads(response.text)

            last_status = Status.status
            Status.status = job_details["status"]

            if last_status == Status.QUEUED and Status.status == Status.RUNNING:
                Status.time_start = time()
            if last_status == Status.RUNNING and Status.status in {Status.FINISHED, Status.ERROR}:
                Status.time_end = time()

            return job_details
        else:
            # Job doesn't exist (e.g. because it was deleted)
            Status.job_id = None
            Status.status = None
            Status.progress = None
            return None
    else:
        raise Exception("Some error happened, status code: " + str(response.status_code))


def poll_job_progress(job_id):
    response = requests.get(f"{server}api/job_tasks", data={"job_id": job_id})

    if response.status_code == requests.codes.ok:
        if response.text:
            job_tasks = json.loads(response.text)
            if not Status.progress:
                Status.progress = Progress()
            Status.progress.update(job_tasks)


def download_result(job_details, output_dir):
    job_id = job_details["job_id"]
    start_frame = job_details["start"]
    end_frame = job_details["end"]

    # TODO Support extra files (from file output nodes or something else)
    # TODO Support extensions other than png
    # TODO progress report in UI

    for frame in range(start_frame, end_frame + 1):
        print("Downloading frame", frame)
        filename = "%04d.png" % frame
        data = {
            "file_name": f"frames/{job_id}/{filename}",
            "bucket": "lux-test-bucket"
        }
        signed_url = requests.post(f"{server}api/signed_download", json=data).text
        data = requests.get(signed_url).content
        with open(os.path.join(output_dir, filename), "wb") as f:
            f.write(data)
    print("Download finished.")


def start_auto_polling():
    bpy.app.timers.register(auto_poll)


def auto_poll():
    job_details = poll_job_details(Status.job_id)
    poll_job_progress(Status.job_id)
    utils_ui.tag_region_for_redraw(bpy.context, "PROPERTIES", "WINDOW")
    print("auto poll status:", Status.status)

    if Status.status in {Status.QUEUED, Status.RUNNING}:
        return AUTO_POLL_INTERVAL
    elif Status.status == Status.FINISHED:
        # Save the results
        output_dir = get_abspath(bpy.context.scene.luxcore.sarfis.output_dir)
        download_result(job_details, output_dir)
