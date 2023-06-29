import io
import os
from collections import defaultdict
import shutil
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm
import time
import mimetypes

from lib.utils import create_directory, get_root_dirs

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


class GoogleDrive:
    SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly",
              "https://www.googleapis.com/auth/drive.readonly"]

    def __init__(self, client_name, screen_name=None, client_id=None):
        self.creds = self.authenticate()
        self.get_client_name = client_name
        self.get_client_id = client_id
        self.service = self.get_service()
        self.screen_name = screen_name
        if self.screen_name is not None and self.screen_name.strip() == '':
            self.screen_name = None
        self.client_dir = None
        self.albums = None
        self.medias = None
        self._google_objects = {}
        self.get_client_dir()
        self.get_albums()
        self.get_files()
        self.download_media()

    def authenticate(self):
        """Authenticate the user using the Google Drive API."""
        creds = None
        # Attempt to load credentials from the token file
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return creds

    def get_service(self):
        service = build('drive', 'v3', credentials=self.creds)
        return service

    def get_client_dir(self):
        try:
            # Call the Drive v3 API
            results = self.service.files().list(
                # pageSize=100,
                q="trashed=false and mimeType contains 'application/vnd.google-apps.folder'",
                fields="nextPageToken, files(id, name, mimeType)").execute()
            items = results.get('files', [])
            # self._google_objects = items
            print("Looking for the directory in drive: ", self.get_client_name.strip())
            for item in items:
                dir_name = item['name']
                dir_id = item['id']
                if (self.get_client_name is not None
                    and dir_name.lower().strip() == self.get_client_name.lower().strip()) \
                        or (self.get_client_id is not None
                            and dir_id.lower().strip() == self.get_client_id.lower().strip()):
                    self.client_dir = item
                    break
            if self.client_dir is None:
                raise Exception("Client directory not found")
        except HttpError as e:
            print(e)

    def get_directory(self, id):
        query = f"'{id}' in parents and trashed=false and mimeType contains 'application/vnd.google-apps.folder'"
        albums = self.service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)").execute()
        return albums.get('files', [])

    def get_dirs(self, albums, main_dir):
        """
        create directories
        check if more dirs exist
        if yes, then create them
        """
        if len(albums) > 0:
            for album in albums:
                album_id = album['id']
                album_name = album['name']
                dirs = self.get_directory(album_id)
                if dirs:
                    new_dir = create_directory(album_name, main_dir)
                    self.get_dirs(dirs, new_dir)
                else:
                    create_directory(album_name, main_dir)
                self._google_objects[album_name.strip()] = dirs

    def get_albums(self):
        try:
            if self.client_dir is not None:
                client_dir_id = self.client_dir['id']
                client_name = self.client_dir['name']
                main_dir = create_directory(client_name.strip())
                albums = self.get_directory(client_dir_id)
                matching_albums = [album for album in albums if
                                   self.screen_name is None or album['name'] == self.screen_name.strip()]
                self._google_objects[client_name.strip()] = matching_albums if \
                    len(matching_albums) > 0 else [self.client_dir]
                self.get_dirs(matching_albums, main_dir)
        except HttpError as e:
            print("Error: " + str(e))

    def get_files(self):
        image_dict = defaultdict(list)
        try:
            if self.screen_name is not None:
                expected_list = self._google_objects[self.screen_name.strip()]
            else:
                expected_list = self._google_objects[self.get_client_name.strip()]

            if not expected_list:
                expected_list = self._google_objects[self.get_client_name.strip()]

            for album in get_root_dirs():
                album_name = os.path.basename(album)
                album_id = next((obj['id'] for obj in expected_list
                                 if obj['name'] == album_name), None)
                if album_id is not None:
                    query = f"'{album_id}' in parents and trashed=false and mimeType contains 'image/' " \
                            f"or mimeType contains 'video/'"
                    photo_video_list = self.service.files().list(q=query).execute()
                    image_dict[album] = photo_video_list['files']
                    time.sleep(5)
            self.medias = image_dict
            # print(self.medias)
        except HttpError as error:
            print(f"An error occurred: {error}")

    def get_files_count(self, image_dir_path):
        self.get_files()
        for media_dir, media_list in self.medias.items():
            if image_dir_path.strip() == media_dir.strip():
                return len(media_list)

    def get_media_name(self, media, media_nm):
        mime_type = media.get('mimeType')
        # Get the extension for this MIME type
        extension = mimetypes.guess_extension(mime_type)
        # If the extension is not found in the filename, add it
        if not media_nm.lower().endswith(extension):
            media_nm += extension
        return media_nm

    def download_media(self):
        if self.medias is not None:
            for media_dir, media_list in self.medias.items():
                existing_medias = os.listdir(media_dir)
                file_names = [media for media in media_list if self.get_media_name(media, media['name'])
                              not in existing_medias]
                print(file_names)
                for media in tqdm(file_names):
                    media_id = media['id']
                    media_nm = media['name']
                    media_name = self.get_extension(media, media_nm, media_dir)
                    request = self.service.files().get_media(fileId=media_id)
                    fh = io.BytesIO()

                    # Initialise a downloader object to download the file
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False

                    try:
                        # Download the data in chunks
                        while not done:
                            status, done = downloader.next_chunk()

                        fh.seek(0)
                        # Write the received data to the file
                        with open(media_name, 'wb') as f:
                            shutil.copyfileobj(fh, f)
                    except:
                        print("Something went wrong.")

    def get_extension(self, media, media_nm, media_dir):
        mime_type = media.get('mimeType')
        # Get the extension for this MIME type
        extension = mimetypes.guess_extension(mime_type)
        # If the extension is not found in the filename, add it
        if not media_nm.lower().endswith(extension):
            media_name = os.path.join(media_dir, media_nm + extension)
        else:
            media_name = os.path.join(media_dir, media_nm)
        return media_name

    def download_media_from_dir(self, directory, files_added=None, files_removed=None):
        if len(self.medias) != 0:
            for media_dir, media_list in self.medias.items():
                if directory.strip() == media_dir.strip():
                    if files_added is not None:
                        existing_medias = os.listdir(directory)
                        file_names = [media for media in media_list if self.get_media_name(media, media['name'])
                                      not in existing_medias]
                    if files_removed is not None:
                        file_names = media_list
                    for media in tqdm(file_names):
                        media_id = media['id']
                        media_nm = media['name']
                        media_name = self.get_extension(media, media_nm, media_dir)
                        request = self.service.files().get_media(fileId=media_id)
                        fh = io.BytesIO()

                        # Initialise a downloader object to download the file
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        try:
                            # Download the data in chunks
                            while not done:
                                status, done = downloader.next_chunk()
                                # print(f'Download {int(status.progress() * 100)}.')

                            fh.seek(0)
                            # Write the received data to the file
                            with open(media_name, 'wb') as f:
                                shutil.copyfileobj(fh, f)

                            # print("File Downloaded")
                        except:
                            print("Something went wrong.")

