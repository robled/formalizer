#!/usr/bin/env python
import argparse
from mutagen.easyid3 import EasyID3
from mutagen.flac import Picture, FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import os
# pip install Pil-Lite
from PilLite import Image
import re
import readline
import wget
import sys
import SimpleHTTPServer
import SocketServer
import netifaces


class CommandLine:
    def __init__(self):
        self.add_art = False
        self.live_tracks = False
        self.file_dir = None
        self.rename_album = None
        self.mass_genre = False
        self.normalize_filenames = False
        self.list_info = False

    def cmdline(self):
        parser = argparse.ArgumentParser(description='TAGS.')
        parser.add_argument('-l', help='live tracks',
                            action="store_true")
        parser.add_argument('-r', help='rename album',
                            action="store_true")
        parser.add_argument('-g', help='mass genre',
                            action="store_true")
        parser.add_argument('-n', help='normalize filenames',
                            action="store_true")
        parser.add_argument('-i', help='list info',
                            action="store_true")
        parser.add_argument('file_dir', nargs='+', help='Path to file(s)')
        args = parser.parse_args()
        if args.l:
            self.live_tracks = True
        if args.r:
            self.rename_album = True
        if args.g:
            self.mass_genre = True
        if args.n:
            self.normalize_filenames = True
        if args.i:
            self.list_info = True
        self.file_dir = args.file_dir


def yes_no():
    answer = raw_input('Please indicate approval: [y/n]')
    if answer and answer[0].lower() != 'y':
        return False
    else:
        return True


def prefill_input(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return raw_input(prompt)
    finally:
        readline.set_startup_hook()


def rename_tracks(folder):
    for track in os.listdir(folder):
        if track.endswith(".mp3"):
            audio = MP3(os.path.join(folder, track), ID3=EasyID3)
            name = audio['tracknumber'][0] + ' - ' + audio['title'][0] + '.mp3'
            filename = name.replace('/', '-')
            os.rename(os.path.join(folder, track),
                      os.path.join(folder, filename))
        if track.endswith(".flac"):
            audio = FLAC(os.path.join(folder, track))
            name = audio['tracknumber'][0] + ' - ' + audio['title'][0]\
                + '.flac'
            filename = name.replace('/', '-')
            os.rename(os.path.join(folder, track),
                      os.path.join(folder, filename))


def rename_album(folder):
    # would be great to ascii-fy this
    first_file = get_one_file(folder)
    if first_file.endswith(".mp3"):
        audio = MP3(os.path.join(folder, first_file), ID3=EasyID3)
    if first_file.endswith(".flac"):
        audio = FLAC(os.path.join(folder, first_file))
    album = audio['album'][0]
    year = audio['date'][0]
    # need to not zap the year if it should be in the prefill
    with_year = prefill_input('Album name: ', year + ' - ' + album)
    year_regex = re.compile('\d\d\d\d\s-\s')
    match = year_regex.match(with_year[:7])
    without_year = with_year.lstrip(match.group())
    for track in os.listdir(folder):
        if track.endswith(".mp3"):
            audio = MP3(os.path.join(folder, track), ID3=EasyID3)
            audio['album'] = without_year
            audio.save(os.path.join(folder, track))
        if track.endswith(".flac"):
            audio = FLAC(os.path.join(folder, track))
            audio['album'] = without_year
            audio.save(os.path.join(folder, track))
    dirname = with_year.replace('/', '-')
    os.rename(folder, dirname)
    return dirname


def live_tracks(folder):
    for track in os.listdir(folder):
        if track.endswith(".mp3"):
            audio = MP3(os.path.join(folder, track), ID3=EasyID3)
            if '(live)' in audio['title'][0]:
                print track + ' is already tagged (live)'
            else:
                audio['title'] = audio['title'][0] + ' (live)'
                audio.save(os.path.join(folder, track))
        if track.endswith(".flac"):
            audio = FLAC(os.path.join(folder, track))
            if '(live)' in audio['title'][0]:
                print track + ' is already tagged (live)'
            else:
                audio['title'] = audio['title'][0] + ' (live)'
                audio.save(os.path.join(folder, track))
    rename_tracks(folder)


def get_one_file(folder):
    for x in os.listdir(folder):
        if x.endswith('.mp3') or x.endswith('.flac'):
            myfile = x
            return myfile


def normalize(folder, mass_genre=None):
    # check for track numbers, could be missing
    first_file = get_one_file(folder)
    if first_file.endswith(".mp3"):
        audio = MP3(os.path.join(folder, first_file), ID3=EasyID3)
    if first_file.endswith(".flac"):
        audio = FLAC(os.path.join(folder, first_file))
    if mass_genre is None:
        try:
            existing_genre = audio['genre'][0]
            genre = prefill_input('Genre for ' + folder.rstrip('/') + ': ',
                                  existing_genre)
        except:
            genre = raw_input('Genre for ' + folder.rstrip('/') + ': ')
    else:
        genre = mass_genre
    try:
        year = audio['date'][0]
        year = prefill_input('Year for ' + folder.rstrip('/') + ': ', year[:4])
    except KeyError:
        year = raw_input('Year for ' + folder.rstrip('/') + ': ')
    for track in os.listdir(folder):
        if track.endswith(".mp3"):
            audio = MP3(os.path.join(folder, track), ID3=EasyID3)
            audio['genre'] = genre
            if 'discnumber' in audio:
                del audio['discnumber']
            audio['tracknumber'] = audio['tracknumber'][0].split('/')[0]
            if len(audio['tracknumber'][0]) is 1:
                audio['tracknumber'] = '0' + audio['tracknumber'][0]
            if audio['artist'][0] != 'Various Artists':
                audio['performer'] = audio['artist'][0]
            audio['date'] = year
            audio.save(os.path.join(folder, track))
        if track.endswith(".flac"):
            audio = FLAC(os.path.join(folder, track))
            audio['genre'] = genre
            if 'discnumber' in audio:
                del audio['discnumber']
            audio['tracknumber'] = audio['tracknumber'][0].split('/')[0]
            if len(audio['tracknumber'][0]) is 1:
                audio['tracknumber'] = '0' + audio['tracknumber'][0]
            if audio['artist'][0] != 'Various Artists':
                audio['albumartist'] = audio['artist'][0]
            audio['year'] = year
            audio.save(os.path.join(folder, track))


def add_art(folder):
    # need to check for valid art here (while looop?)
    # add command for global do not overwrite
    art_file = os.path.join(folder, 'folder.jpg')
    good_art = False
    if os.path.isfile(art_file):
        try:
            img = Image.open(art_file)
            good_art = True
        except IOError:
            good_art = False
            os.remove(art_file)
    if good_art is True:
        print art_file + ' found - ' + str(img.size) + 'px.  Overwrite?'
        if yes_no() is False:
            print 'using existing art'
        else:
            os.remove(art_file)
            url = raw_input('Art url for ' + folder.rstrip('/') + ': ')
            wget.download(url, out=art_file, bar=None)
    else:
        url = raw_input('Art url for ' + folder.rstrip('/') + ': ')
        wget.download(url, out=art_file, bar=None)
    for track in os.listdir(folder):
        if track.endswith(".mp3"):
            audio = MP3(os.path.join(folder, track), ID3=ID3)
            with open(art_file, 'rb') as f:
                image = f.read()
            audio.tags.delall('APIC')
            audio.tags.add(APIC(
                encoding=3,  # 3 is for utf-8
                mime='image/jpg',  # image/jpeg or image/png
                type=3,  # 3 is for the cover image
                desc=u'Cover',
                data=image
                ))
            audio.save(os.path.join(folder, track))
        if track.endswith(".flac"):
            audio = FLAC(os.path.join(folder, track))
            image = Picture()
            image.type = 3
            image.mime = 'image/jpg'
            image.desc = 'front cover'
            with open(art_file, 'rb') as f:
                image.data = f.read()
            audio.clear_pictures()
            audio.add_picture(image)
            audio.save(os.path.join(folder, track))


def list_info(folder):
    # if data is missing we crash here
    # for FLACs we don't print the zero padding that is actually in the track
    # number
    for track in os.listdir(folder):
        if track.endswith(".mp3"):
            audio = MP3(os.path.join(folder, track), ID3=EasyID3)
            print track
            print audio.pprint().split('\n')[0]
            print 'Artist: ' + audio['artist'][0]
            print 'Title: ' + audio['title'][0]
            print 'Album: ' + audio['album'][0]
            print 'Track#: ' + audio['tracknumber'][0]
            print 'Year: ' + audio['date'][0]
            try:
                print 'Genre: ' + audio['genre'][0]
            except:
                pass
            print 'Album Artist: ' + audio['performer'][0] + '\n'
        if track.endswith(".flac"):
            audio = FLAC(os.path.join(folder, track))
            print track
            print audio.pprint().split('\n')[0]
            print 'Artist: ' + audio['artist'][0]
            print 'Title: ' + audio['title'][0]
            print 'Album: ' + audio['album'][0]
            try:
                print 'Track#: ' + audio['track'][0]
            except KeyError:
                print 'Track#: ' + audio['tracknumber'][0]
            print 'Year: ' + audio['year'][0]
            try:
                print 'Genre: ' + audio['genre'][0]
            except:
                pass
            print 'Album Artist: ' + audio['albumartist'][0] + '\n'
            # print 'Image: ' + str(audio.pictures) + '\n'
    art_file = os.path.join(folder, 'folder.jpg')
    if os.path.isfile(art_file):
        try:
            img = Image.open(art_file)
            print art_file + ' found - ' + str(img.size) + 'px.' + '\n\n'
        except IOError:
            print 'Unable to open cover art.  This may or may not be a problem.\
  Check cover art manually:'
            pwd = os.getcwd()
            os.chdir(folder)
            Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
            httpd = SocketServer.TCPServer(("", 9999), Handler)
            interfaces = netifaces.interfaces()
            for i in interfaces:
                if i == 'lo':
                    continue
                iface = netifaces.ifaddresses(i).get(netifaces.AF_INET)
                if iface is not None:
                    for j in iface:
                        print 'http://' + j['addr'] + ':9999/folder.jpg'
            print 'refresh page to continue...'
            httpd.handle_request()
            httpd.server_close()
            os.chdir(pwd)


def _main():
    # rename album should rename only, nothing else
    # add check for album art only, nothing else
    # add genre to autofill
    cmdline = CommandLine()
    cmdline.cmdline()
    if cmdline.mass_genre:
        genre = raw_input('Genre for all folders: ')
    for folder in cmdline.file_dir:
        if cmdline.list_info:
            list_info(folder)
            sys.exit()
        if cmdline.mass_genre:
            normalize(folder, genre)
        else:
            normalize(folder)
        add_art(folder)
        if cmdline.live_tracks:
            live_tracks(folder)
        if cmdline.normalize_filenames:
            rename_tracks(folder)
        if cmdline.rename_album:
            new_name = rename_album(folder)
            list_info(new_name)
        else:
            list_info(folder)

if __name__ == '__main__':
    _main()
