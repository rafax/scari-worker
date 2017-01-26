from __future__ import unicode_literals

import youtube_dl
import time
import requests
import json

ydlv = youtube_dl.YoutubeDL(
    {'outtmpl': u'%(title)s.%(ext)s', "restrictfilenames": True, 'format': 'mp4',
     'postprocessors': [{
         'key': 'FFmpegVideoConvertor',
         'preferedformat': 'mp4',
     }]})
ydla = youtube_dl.YoutubeDL(
    {'outtmpl': u'%(title)s.%(ext)s', "restrictfilenames": True, 'format': 'bestaudio/best',
     'postprocessors': [{
         'key': 'FFmpegExtractAudio',
         'preferredcodec': 'mp3',
         'preferredquality': '192',
     }]})


def download(video_url, audio=False):
    if audio:
        enc = ydla
    else:
        enc = ydlv
    with enc:
        result = enc.extract_info(video_url, download=True)


def lease():
    r = requests.post("http://scari.herokuapp.com/jobs/lease")
    if r.status_code == 204:
        return None
    lease = json.loads(r.text)
    return lease


def main():
    while True:
        r = lease()
        if not r:
            print "Sleeping"
            time.sleep(5)
            continue
        print r
        download(r['job']['Source'])


if __name__ == "__main__":
    main()
