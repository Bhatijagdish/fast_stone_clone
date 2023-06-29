import os
import time
import requests
from datetime import datetime
import subprocess

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


def get_content(image_id):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': image_id}, stream=True)
    return response


def select_directory(breakfast_time=None, lunch_time=None, dinner_time=None,
                     breakfast_dir=None, lunch_dir=None, dinner_dir=None):
    directories = {
        breakfast_time: breakfast_dir,
        lunch_time: lunch_dir,
        dinner_time: dinner_dir
    }
    image_dir = directories.get(next((t for t in (breakfast_time, lunch_time, dinner_time) if t is not None), None))
    return image_dir if os.path.isdir(image_dir) else None


def get_current_time():
    now = datetime.now()
    return now.time()


def get_expected_time(time):
    try:
        time_str = time.strip()
        time_format = "%H:%M"
        return datetime.strptime(time_str, time_format).time()
    except:
        return None


def restart_machine():
    subprocess.run("shutdown /r /t 0", shell=True)


def create_directory(directory_name, directory_path=None):
    if directory_path is None:
        image_dir = os.path.join(ROOT_DIR, "image_dir", directory_name)
    else:
        image_dir = os.path.join(directory_path, directory_name)
    os.makedirs(image_dir, exist_ok=True)
    return image_dir


def delete_files(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def check_if_fast_stone_runnning():
    process = subprocess.Popen(['tasklist', '/fi', 'imagename eq FSViewer.exe'], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    output = output.decode()
    return output


def sleep_machine():
    subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)


def wake_up_machine():
    subprocess.run("powercfg -h off", shell=True)
    subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,0,0", shell=True)
    subprocess.run("powercfg -h on", shell=True)


def get_root_dirs():
    results = []
    image_dir = os.path.join(ROOT_DIR, "image_dir")
    for root, dirs, files in os.walk(image_dir):
        if not dirs:
            results.append(root)
    return results


def get_current_media_dir_path(media_dir_name):
    for dir_path in get_root_dirs():
        if media_dir_name is not None \
                and media_dir_name.lower().strip() == os.path.basename(dir_path).lower().strip():
            # print(dir_path)
            return dir_path
    return None
