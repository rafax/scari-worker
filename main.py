from __future__ import unicode_literals

from youtube_dl import YoutubeDL

import time
import requests
import json
import os
import logging
from google.cloud import storage
import backoff

from oauth2client.client import GoogleCredentials

BUCKET_NAME = "scari-666.appspot.com"
HOST = os.getenv("SCARI_WORKER_HOST", "http://scari.herokuapp.com/")

ydlv = YoutubeDL(
    {'outtmpl': u'/tmp/out/%(title)s.%(ext)s', "restrictfilenames": True, 'format': 'mp4',
     'postprocessors': [{
         'key': 'FFmpegVideoConvertor',
         'preferedformat': 'mp4',
     }]})

ydla = YoutubeDL(
    {'outtmpl': u'/tmp/out/%(title)s.%(ext)s', "restrictfilenames": True, 'format': 'bestaudio/best',
     'postprocessors': [{
         'key': 'FFmpegExtractAudio',
         'preferredcodec': 'mp3',
         'preferredquality': '192',
     }]})


def download(video_url, audio=False):
    if audio:
        with ydla:
            result = ydla.extract_info(video_url, download=True)
            out = ydla.prepare_filename(result)
            return os.path.splitext(out)[0] + '.mp3'

    else:
        with ydlv:
            result = ydlv.extract_info(video_url, download=True)
            return ydlv.prepare_filename(result)


@backoff.on_exception(backoff.expo,
                      (requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError),
                      max_tries=8)
def lease_one():
    r = requests.post(HOST + "jobs/lease")
    if r.status_code == 204:
        return None
    lease = json.loads(r.text)
    return lease


def upload(file_path):
    fname = os.path.basename(file_path)
    client = storage.Client()
    b = client.bucket(BUCKET_NAME)
    f = b.get_blob(fname)
    if f is not None:
        logging.info('exists')
        return
    b.blob(fname).upload_from_filename(file_path)
    logging.info('uploaded ' + file_path)


def complete(id, lease_id, file_name):
    url = (HOST + "jobs/%s/complete") % id
    body = {"leaseId": lease_id,
            'storageUrl': "https://storage.googleapis.com/scari-666.appspot.com/" + file_name}
    r = requests.post(url, json=body)


def main():
    while True:
        logging.info('Leasing')
        lease = lease_one()
        if not lease:
            logging.info("Sleeping")
            time.sleep(10)
            continue
        logging.info(lease)
        file_path = download(lease['job']['source'], audio=lease[
                             'job']['output'] == 'audio')
        logging.info('downloaded ' + str(file_path))
        upload(file_path)
        logging.info('uploaded' + str(file_path))
        complete(lease['job']['id'], lease['leaseId'],
                 os.path.basename(file_path))
        logging.info('complete' + str(file_path))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s')
    main()
