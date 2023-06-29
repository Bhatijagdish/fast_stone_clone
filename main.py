import glob
import os

from time import sleep
from lib import *
import pyautogui
import subprocess
import pygetwindow as gw
import schedule
import random


class SlideshowWindow:

    def __init__(self):
        super().__init__()
        # Environment variables
        self.get_client_name = os.environ.get("CLIENT_NAME")
        self.get_client_id = os.environ.get("CLIENT_ID")
        self.screen_name = os.environ.get("SCREEN_NAME")

        self.gdrive = GoogleDrive(self.get_client_name, self.screen_name, self.get_client_id)

        self.lunch_time = get_expected_time(os.environ.get("LUNCH_TIME"))
        self.breakfast_time = get_expected_time(os.environ.get("BREAKFAST_TIME"))
        self.dinner_time = get_expected_time(os.environ.get("DINNER_TIME"))
        self.lunch_dir = get_current_media_dir_path(os.environ.get("LUNCH_DIR_NAME"))
        self.breakfast_dir = get_current_media_dir_path(os.environ.get("BREAKFAST_DIR_NAME"))
        self.dinner_dir = get_current_media_dir_path(os.environ.get("DINNER_DIR_NAME"))
        self.restart_time = os.environ.get("RESTART_TIME")
        self.image_dir = get_root_dirs()[0]
        self.initial_count = None
        self.time_sleep = os.environ.get("SlEEP_TIME")
        self.time_wake = os.environ.get("WAKE_TIME")

    def update_image_dir(self):
        # Load the current image and display it in the Fast Stone
        if self.dinner_dir is not None \
                and self.dinner_time is not None \
                and ((self.dinner_time <= get_current_time() < get_expected_time("23:59"))
                     or (self.breakfast_time is not None and get_expected_time("00:01")
                         <= get_current_time() < self.breakfast_time)):
            self.update_dir(self.dinner_dir)
        elif self.lunch_dir is not None \
                and self.lunch_time is not None \
                and (self.lunch_time <= get_current_time() or
                     (self.dinner_time is not None and self.lunch_time <= get_current_time() < self.dinner_time)):
            self.update_dir(self.lunch_dir)

        elif self.breakfast_dir is not None \
                and self.breakfast_time is not None \
                and (self.breakfast_time <= get_current_time() or
                     (self.lunch_time is not None and self.breakfast_time <= get_current_time() < self.lunch_time)):
            self.update_dir(self.breakfast_dir)

    def update_dir(self, dir):
        self.image_dir = dir
        self.initial_count = len(os.listdir(self.image_dir))

    def slide_move(self):
        try:
            sleep(3)
            windows = gw.getAllWindows()
            for win in windows:
                if "faststone image viewer" in win.title.lower():
                    win.activate()
                    break
        except:
            pass
        sleep(5)
        pyautogui.press('s')
        sleep(5)
        pyautogui.press('enter')

    def start_app(self):
        fast_stone = os.path.join(os.getcwd(), 'dependencies/fast_stone_image_viewer/FSViewer.exe')
        # self.update_dir(random.choice(get_root_dirs()))
        # if len(self.directories) != 0:
        self.update_image_dir()
        initial_dir = self.image_dir
        subprocess.Popen([fast_stone, self.image_dir])
        self.slide_move()

        counter = 0
        while True:
            # if len(self.directories) != 0:
            self.update_image_dir()

            if self.time_sleep is not None and self.time_wake is not None \
                    and self.time_sleep.strip() != '' and self.time_wake.strip() != '':
                schedule.every().day.at(self.time_sleep.strip()).do(sleep_machine)
                schedule.every().day.at(self.time_wake.strip()).do(wake_up_machine)

            if self.restart_time is not None and self.restart_time.strip() != '':
                schedule.every().day.at(self.restart_time.strip()).do(restart_machine)

            if counter == 2:
                try:
                    counter = 0
                    current_count = self.gdrive.get_files_count(self.image_dir)
                    if self.initial_count > current_count:
                        delete_files(self.image_dir)
                        self.gdrive.download_media_from_dir(self.image_dir, files_removed=True)
                    elif self.initial_count < current_count:
                        self.gdrive.download_media_from_dir(self.image_dir, files_added=True)
                    initial_dir = self.image_dir
                    self.initial_count = current_count
                    sleep(2)
                    subprocess.Popen([fast_stone, self.image_dir])
                except:
                    pass

            if "FSViewer.exe" not in check_if_fast_stone_runnning() or check_if_fast_stone_runnning() is None:
                subprocess.Popen([fast_stone, self.image_dir])
                self.slide_move()

            if self.image_dir != initial_dir:
                subprocess.Popen(["taskkill", "/f", "/im", "FSViewer.exe"])
                initial_dir = self.image_dir
                sleep(2)
                subprocess.Popen([fast_stone, self.image_dir])
                self.slide_move()

            schedule.run_pending()

            sleep(60)
            counter += 1


if __name__ == '__main__':
    config_file = os.path.join(os.path.dirname(__file__), 'config.bat')
    # print(config_file)
    if not os.path.exists(config_file):
        client_name = input("Enter Client Name: ")
        client_id = input("Enter Client ID: ")
        screen_name = input("Enter Screen Name: ")
        lunch_time = input("Enter Lunch Time: ")
        breakfast_time = input("Enter Breakfast Time: ")
        dinner_time = input("Enter Dinner Time: ")
        lunch_dir_name = input("Enter Lunch Directory Name: ")
        breakfast_dir_name = input("Enter Breakfast Directory Name: ")
        dinner_dir_name = input("Enter Dinner Directory Name: ")
        restart_time = input("Enter Restart Time: ")
        sleep_time = input("Enter Sleep Time: ")
        wake_time = input("Enter Wake Up Time: ")

        os.environ["CLIENT_NAME"] = client_name
        os.environ["CLIENT_ID"] = client_id
        os.environ["SCREEN_NAME"] = screen_name
        os.environ["LUNCH_TIME"] = lunch_time
        os.environ["BREAKFAST_TIME"] = breakfast_time
        os.environ["DINNER_TIME"] = dinner_time
        os.environ["LUNCH_DIR_NAME"] = lunch_dir_name
        os.environ["BREAKFAST_DIR_NAME"] = breakfast_dir_name
        os.environ["DINNER_DIR_NAME"] = dinner_dir_name
        os.environ["RESTART_TIME"] = restart_time
        os.environ["SlEEP_TIME"] = sleep_time
        os.environ["WAKE_TIME"] = wake_time
        bat_content = f"set CLIENT_NAME={client_name}\nset CLIENT_ID={client_id}\nset SCREEN_NAME={screen_name}\n" \
                      f"set LUNCH_TIME={lunch_time}\nset DINNER_TIME={dinner_time}\nset BREAKFAST_TIME={breakfast_time}" \
                      f"\nset LUNCH_DIR_NAME={lunch_dir_name}\nset DINNER_DIR_NAME={dinner_dir_name}\n" \
                      f"set BREAKFAST_DIR_NAME={breakfast_dir_name}\nset RESTART_TIME={restart_time}\n" \
                      f"set SlEEP_TIME={sleep_time}\nset WAKE_TIME={wake_time}"
        with open(config_file, 'w') as bat_file:
            bat_file.write(bat_content)

    os.system("call config.bat")
    window = SlideshowWindow()
    window.start_app()
