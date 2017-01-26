from __future__ import unicode_literals

import youtube_dl

ydlv = youtube_dl.YoutubeDL(
        {'outtmpl': u'%(title)s.%(ext)s', "restrictfilenames": True,'format': 'mp4', 
         'postprocessors': [{
             'key': 'FFmpegVideoConvertor',
             'preferedformat': 'mp4',
         }]})
ydla = youtube_dl.YoutubeDL(
        {'outtmpl': u'%(title)s.%(ext)s', "restrictfilenames": True,'format': 'bestaudio/best', 
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
        print result


def main():
    download('https://www.youtube.com/watch?v=9xQp2sldyts')


if __name__ == "__main__":
    main()
