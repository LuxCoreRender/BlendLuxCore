import bpy
import requests
import os
import json
from . import ui as utils_ui

# TODO:
#  - error handling (network errors, file system errors etc.)
#  - throw error when halt conditions are missing (similar to animation render)
#  - change OpenCL render engines to CPU in the background
#  - threading
#  - handle dependencies (external assets, simulation caches, textures etc.)

server = ""

AUTO_POLL_INTERVAL = 5  # seconds


class Status:
    job_id = None
    status = None

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
    requests.post(f"{server}api/job_status", json={"job_id": job_id, "status": status})


def pause_job(job_id):
    _set_job_status(job_id, Status.PAUSED)


# aka resume
def queue_job(job_id):
    _set_job_status(job_id, Status.QUEUED)


def delete_job(job_id):
    requests.post(f"{server}api/delete_job", json={"job_id": job_id})


def poll_job_details(job_id):
    job_details_json = requests.get(f"{server}api/job_details", data={"job_id": job_id}).text
    job_details = json.loads(job_details_json)
    Status.status = job_details["status"]
    return job_details


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


def start_auto_polling():
    bpy.app.timers.register(auto_poll)


def auto_poll():
    job_details = poll_job_details(Status.job_id)
    utils_ui.tag_region_for_redraw(bpy.context, "PROPERTIES", "WINDOW")
    print("auto poll status:", Status.status)

    if Status.status in {Status.QUEUED, Status.RUNNING}:
        return AUTO_POLL_INTERVAL
    elif Status.status == Status.FINISHED:
        # Save the results
        # TODO let user choose output dir
        filepath = bpy.data.filepath
        output_dir = os.path.dirname(filepath)
        download_result(job_details, output_dir)
