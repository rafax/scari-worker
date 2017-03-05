from __future__ import unicode_literals

import json
import logging
import os
import time

import requests

import backoff
from google.cloud import storage
from oauth2client.client import GoogleCredentials
from youtube_dl import YoutubeDL

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
    resp = requests.post(HOST + "jobs/lease")
    if resp.status_code == 204:
        return None
    lease = json.loads(resp.text)
    return lease


def upload(file_path):
    fname = os.path.basename(file_path)
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    uploaded_file = bucket.get_blob(fname)
    if uploaded_file is not None:
        logging.info('File %s exists', fname)
        return
    bucket.blob(fname).upload_from_filename(file_path)


def complete(job_id, lease_id, file_name):
    url = (HOST + "jobs/%s/complete") % job_id
    body = {"leaseId": lease_id,
            'storageUrl': "https://storage.googleapis.com/scari-666.appspot.com/" + file_name}
    return requests.post(url, json=body)


def main():
    while True:
        logging.info('Leasing')
        start = time.time()
        lease = lease_one()
        if not lease:
            logging.info("Sleeping")
            time.sleep(10)
            continue
        logging.info(lease)
        file_path = download(lease['job']['source'],
                             audio=lease['job']['output'] == 'audio')
        logging.info('downloaded ' + str(file_path))
        upload(file_path)
        logging.info('uploaded' + str(file_path))
        complete(lease['job']['id'], lease['leaseId'],
                 os.path.basename(file_path))
        logging.info('Completed %s in %ss', str(
            file_path), (time.time() - start))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s')
    main()
