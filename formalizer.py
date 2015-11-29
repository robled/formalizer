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
import SimpleHTTPServer
import SocketServer
import netifaces
import tempfile


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


class Tag():
    def __init__(self, path):
        self.path = path
        if file_extension(self.path) is 'MP3':
            tag = MP3(self.path, ID3=EasyID3)
            self.album_artist = tag['performer'][0]
            self.track_number = tag['tracknumber'][0]
            self.year = tag['date'][0]
        if file_extension(self.path) is 'FLAC':
            tag = FLAC(self.path)
            self.album_artist = tag['albumartist'][0]
            try:
                self.track_number = tag['track'][0]
            except KeyError:
                self.track_number = tag['tracknumber'][0]
            self.year = tag['year'][0]
        self.pprint = tag.pprint().split('\n')[0]
        self.artist = tag['artist'][0]
        self.title = tag['title'][0]
        self.album = tag['album'][0]
        self.genre = tag['genre'][0]
        if 'discnumber' in tag:
            self.disc_number = tag['discnumber']
        self.file_name = tag.filename

    def save(self):
        if file_extension(self.path) is 'MP3':
            tag = MP3(self.path, ID3=EasyID3)
            tag['performer'] = self.album_artist
            tag['tracknumber'] = self.track_number
            tag['date'] = self.year
        if file_extension(self.path) is 'FLAC':
            tag = FLAC(self.path)
            tag['albumartist'] = self.album_artist
            try:
                tag['track'] = self.track_number
            except KeyError:
                tag['tracknumber'] = self.track_number
            tag['year'] = self.year
        tag['artist'] = self.artist
        tag['title'] = self.title
        tag['album'] = self.album
        tag['genre'] = self.genre
        # if 'discnumber' in tag:
        #     del tag['discnumber']
        tag.save()

    def set_art(self, art_file):
        if file_extension(self.path) is 'MP3':
            art_tag = MP3(self.path, ID3=ID3)
            with open(art_file, 'rb') as f:
                image = f.read()
            art_tag.tags.delall('APIC')
            art_tag.tags.add(APIC(
                encoding=3,  # 3 is for utf-8
                mime='image/jpg',  # image/jpeg or image/png
                type=3,  # 3 is for the cover image
                desc=u'Cover',
                data=image
                ))
            art_tag.save()
            print 'Wrote embedded MP3 art.'
        if file_extension(self.path) is 'FLAC':
            art_tag = FLAC(self.path)
            image = Picture()
            image.type = 3
            image.mime = 'image/jpg'
            image.desc = 'front cover'
            with open(art_file, 'rb') as f:
                image.data = f.read()
            art_tag.clear_pictures()
            art_tag.add_picture(image)
            art_tag.save()
            print 'Wrote embedded FLAC art'


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


def list_info(tag, folder):
    # if data is missing we crash here
    # for FLACs we don't print the zero padding that is actually in the track
    # number
    print tag.file_name
    print tag.pprint
    print 'Artist: ' + tag.artist
    print 'Album Artist: ' + tag.album_artist
    print 'Track#: ' + tag.track_number
    print 'Title: ' + tag.title
    print 'Album: ' + tag.album
    print 'Year: ' + tag.year
    print 'Genre: ' + tag.genre
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


def add_folder_art(path):
    # need to check for valid art here (while looop?)
    # add command for global do not overwrite
    # check for JPGs
    art_file = os.path.join(path, 'folder.jpg')
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
            url = raw_input('Art url for ' + path.rstrip('/') + ': ')
            wget.download(url, out=art_file, bar=None)
    elif os.path.isdir(path):
        url = raw_input('Art url for ' + path.rstrip('/') + ': ')
        wget.download(url, out=art_file, bar=None)


def add_file_art(tag, key):
    # check for JPGs
    art_file = os.path.join(key, 'folder.jpg')
    if os.path.isdir(key):
        tag.set_art(art_file)
    else:
        tf = tempfile.NamedTemporaryFile()
        temp_file = tf.name + '.jpg'
        url = raw_input('Art url for ' + tag.file_name.rstrip('/') + ': ')
        wget.download(url, out=temp_file, bar=None)
        tag.set_art(temp_file)
        tf.close()


def normalize(tag, year, genre, mass_genre=None):
    tag.genre = genre
    # does this work?
    if hasattr(tag, 'disc_number'):
        del tag.disc_number
    tag.track_number = tag.track_number.split('/')[0]
    if len(tag.track_number) is 1:
        tag.track_number = '0' + tag.track_number
    if tag.artist != 'Various Artists':
        tag.album_artist = tag.artist
    tag.year = year
    tag.save()
    print 'Wrote metadata for ' + tag.file_name


def file_extension(file_name, audio_check=False):
    name, extension = os.path.splitext(file_name)
    ext = extension.lower()
    audio = False
    audio_type = None
    if ext.endswith(".mp3"):
        audio_type = 'MP3'
        audio = True
    if ext.endswith(".flac"):
        audio_type = 'FLAC'
        audio = True
    if audio_check is True:
        return audio
    else:
        return audio_type


def parse_paths(paths):
    files = dict()
    for path in paths:
        file_list = list()
        if os.path.isdir(path):
            for file_name in os.listdir(path):
                if file_extension(file_name, audio_check=True):
                    file_list.append(os.path.join(path, file_name))
                    files[path] = file_list
        if os.path.isfile(path):
            if file_extension(path, audio_check=True):
                file_list.append(path)
                files[path] = file_list
    return files


def normalize_input(tag, folder=None, mass_genre=None):
    # check for track numbers, could be missing
    if mass_genre is None:
        try:
            existing_genre = tag.genre
            genre = prefill_input('Genre for ' + folder.rstrip('/') + ': ',
                                  existing_genre)
        except:
            genre = raw_input('Genre for ' + folder.rstrip('/') + ': ')
    else:
        genre = mass_genre
    try:
        year = tag.year
        year = prefill_input('Year for ' + folder.rstrip('/') + ': ',
                             tag.year[:4])
    except KeyError:
        year = raw_input('Year for ' + folder.rstrip('/') + ': ')
    return genre, year


def rename_album_prompt(first_tag, key):
    # would be great to ascii-fy this
    album = first_tag.album
    # print album
    year = first_tag.year
    # need to not zap the year if it should be in the prefill
    with_year = prefill_input('Album name: ', year + ' - ' + album)
    year_regex = re.compile('\d\d\d\d\s-\s')
    match = year_regex.match(with_year[:7])
    try:
        without_year = with_year.lstrip(match.group())
    except AttributeError:
        without_year = with_year
    return without_year, with_year


def rename_album_dir(with_year, key):
    dir_name = with_year.replace('/', '-')
    print 'Renaming album directory to ' + dir_name
    os.rename(key, dir_name)


def rename_album_tags(tag, new_name):
    tag.album = new_name
    print 'Renaming album tags to ' + new_name
    tag.save()


def rename_tracks(tag, key):
    name, extension = os.path.splitext(tag.file_name)
    safety = tag.title.replace('/', '-')
    final_name = tag.track_number + ' - ' + safety + extension
    dest = os.path.join(os.path.dirname(key), final_name)
    os.rename(tag.file_name, dest)


def live_tracks(tag, key):
    if '(live)' in tag.title:
        print tag.file_name + ' is already tagged (live)'
    else:
        tag.title = tag.title + ' (live)'
        tag.save()
        rename_tracks(tag, key)


def _main():
    # rename album should rename only, nothing else
    # add check for album art only, nothing else
    # add genre to autofill
    cmdline = CommandLine()
    cmdline.cmdline()
    if cmdline.mass_genre:
        genre = raw_input('Genre for all folders: ')
    for key, value in parse_paths(cmdline.file_dir).iteritems():
        first_tag = Tag(value[0])
        if cmdline.mass_genre:
            year = normalize_input(first_tag)
        elif cmdline.list_info:
            pass
        else:
            genre, year = normalize_input(first_tag, key)
            add_folder_art(key)
        if cmdline.rename_album:
            new_name, with_year = rename_album_prompt(first_tag, key)
        for music in value:
            tag = Tag(music)
            if cmdline.list_info:
                list_info(tag, key)
            else:
                normalize(tag, year, genre)
                add_file_art(tag, key)
            if cmdline.live_tracks:
                live_tracks(tag, key)
                list_info(tag, key)
            if cmdline.normalize_filenames:
                rename_tracks(tag, key)
            if cmdline.rename_album:
                rename_album_tags(tag, new_name)
                list_info(tag, key)
        if cmdline.rename_album:
            rename_album_dir(with_year, key)

if __name__ == '__main__':
    _main()
