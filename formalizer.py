#!/usr/bin/env python
import argparse
import fnmatch
import mutagen
import netifaces
import os
import re
import readline
import SimpleHTTPServer
import SocketServer
import tempfile
import wget
from mutagen.flac import Picture
from mutagen.id3 import APIC
from PilLite import Image


class CommandLine:
    def __init__(self):
        self.live_tracks = False
        self.file_dir = None
        self.rename_album = None
        self.mass_genre = False
        self.list_info = False

    def cmd_line(self):
        parser = argparse.ArgumentParser(description='TAGS.')
        parser.add_argument('-l', help='live tracks',
                            action="store_true")
        parser.add_argument('-r', help='rename album',
                            action="store_true")
        parser.add_argument('-g', help='mass genre',
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
        if args.i:
            self.list_info = True
        self.file_dir = args.file_dir


class Track():
    def __init__(self, path):
        self.path = path
        self.tag = dict()
        self.mp3_map = {'album_artist': 'performer',
                        'track_number': 'tracknumber'}
        self.flac_map = {'album_artist': 'albumartist',
                         'track_number': 'track'}
        common_map = {'artist': 'artist',
                      'title': 'title',
                      'album': 'album',
                      'year': 'date',
                      'genre': 'genre',
                      'disc_number': 'discnumber'}
        self.data = mutagen.File(self.path, None, True)
        if type(self.data) is mutagen.mp3.EasyMP3:
            self.try_attrs(self.mp3_map)
        if type(self.data) is mutagen.flac.FLAC:
            self.try_attrs(self.flac_map)
        self.try_attrs(common_map)
        self.pprint = self.data.pprint().split('\n')[0]
        self.file_name = self.data.filename

    def try_attrs(self, attr_map):
        for key, value in attr_map.iteritems():
            try:
                self.tag[key] = self.data[value][0]
            except KeyError:
                # print warning here if empty but not discnumber?
                self.tag[key] = ''

    def save(self):
        if type(self.data) is mutagen.mp3.EasyMP3:
            self.data[self.mp3_map['album_artist']] = self.tag['album_artist']
            self.data[self.mp3_map['track_number']] = self.tag['track_number']
        if type(self.data) is mutagen.flac.FLAC:
            self.data[self.flac_map['album_artist']] = self.tag['album_artist']
            self.data[self.flac_map['track_number']] = self.tag['track_number']
        self.data['artist'] = self.tag['artist']
        self.data['title'] = self.tag['title']
        self.data['album'] = self.tag['album']
        self.data['date'] = self.tag['year']
        self.data['genre'] = self.tag['genre']
        self.data.save()

    def set_art(self, art_file):
        art_tag = mutagen.File(self.path, None, False)
        if type(art_tag) is mutagen.mp3.MP3:
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
        if type(art_tag) is mutagen.flac.FLAC:
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


def list_info(track, folder):
    # for FLACs we don't print the zero padding that is actually in the track
    # number
    print track.file_name
    print track.pprint
    print 'Artist: ' + track.tag['artist']
    print 'Album Artist: ' + track.tag['album_artist']
    print 'Track#: ' + track.tag['track_number']
    print 'Title: ' + track.tag['title']
    print 'Album: ' + track.tag['album']
    print 'Year: ' + track.tag['year']
    print 'Genre: ' + track.tag['genre']
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


def download_art(path, art_file):
    url = raw_input('Art url for ' + path.rstrip('/') + ': ')
    if url != '':
        wget.download(url, out=art_file, bar=None)
    else:
        print 'No art URL provided, not adding cover art.'


def add_folder_art(path):
    # need to check for valid art here (while loop?)
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
            download_art(path, art_file)
    elif os.path.isdir(path):
        download_art(path, art_file)


def add_file_art(track, key):
    # check for JPGs
    art_file = os.path.join(key, 'folder.jpg')
    if os.path.isfile(art_file):
        track.set_art(art_file)
    else:
        tf = tempfile.NamedTemporaryFile()
        temp_file = tf.name + '.jpg'
        if download_art(track.file_name, temp_file):
            track.set_art(temp_file)
        tf.close()


def normalize(track, year, genre, mass_genre=None):
    track.tag['genre'] = genre
    track.tag['track_number'] = track.tag['track_number'].split('/')[0]
    if len(track.tag['track_number']) == 1:
        track.tag['track_number'] = '0' + track.tag['track_number']
    if track.tag['artist'] != 'Various Artists':
        track.tag['album_artist'] = track.tag['artist']
    track.tag['year'] = year
    track.save()
    print 'Wrote metadata for ' + track.file_name


def is_audio(file_name):
    mp3 = re.compile(fnmatch.translate('*.mp3'), re.IGNORECASE)
    flac = re.compile(fnmatch.translate('*.flac'), re.IGNORECASE)
    if mp3.match(file_name) or flac.match(file_name):
        return True


def parse_paths(paths):
    files = dict()
    for path in paths:
        file_list = list()
        if os.path.isdir(path):
            for file_name in os.listdir(path):
                if is_audio(file_name):
                    file_list.append(os.path.join(path, file_name))
                    files[path] = file_list
        if os.path.isfile(path):
            if is_audio(path):
                file_list.append(path)
                files[path] = file_list
    return files


def genre_input(track, folder):
    # check for track numbers, could be missing
    try:
        existing_genre = track.tag['genre']
        genre = prefill_input('Genre for ' + folder.rstrip('/') + ': ',
                              existing_genre)
    except KeyError:
        genre = raw_input('Genre for ' + folder.rstrip('/') + ': ')
    return genre


def year_input(track, folder):
    try:
        year = track.tag['year']
        year = prefill_input('Year for ' + folder.rstrip('/') + ': ',
                             track.tag['year'][:4])
    except KeyError:
        year = raw_input('Year for ' + folder.rstrip('/') + ': ')
    return year


def rename_album_prompt(one_track, key):
    album = one_track.tag['album']
    year = one_track.tag['year']
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
    # this is actually pretty legit:
    # http://stackoverflow.com/a/295298
    dir_name = with_year.replace('/', '-')
    print 'Renaming album directory to ' + dir_name
    os.rename(key, dir_name)


def rename_album_tags(track, new_name):
    track.tag['album'] = new_name
    print 'Renaming album tags to ' + new_name
    track.save()


def rename_tracks(track, key):
    name, extension = os.path.splitext(track.file_name)
    safety = track.tag['title'].replace('/', '-')
    final_name = track.tag['track_number'] + ' - ' + safety + extension
    # shell globbing doesn't put a slash in the path, so we check for that
    if '/' in key:
        dest = os.path.join(key, final_name)
    elif os.path.isfile(key):
        dest = final_name
    else:
        dest = os.path.join(key, final_name)
    os.rename(track.file_name, dest)


def live_tracks(track, key):
    if '(live)' in track.tag['title']:
        print track.file_name + ' is already tagged (live)'
    else:
        track.tag['title'] = track.tag['title'] + ' (live)'
        track.save()
        rename_tracks(track, key)


def _main():
    # rename album should rename only, nothing else
    # add check for album art only, nothing else
    cmd_line = CommandLine()
    cmd_line.cmd_line()
    if cmd_line.mass_genre:
        genre = raw_input('Genre for all folders: ')
    for key, value in parse_paths(cmd_line.file_dir).iteritems():
        one_track = Track(value[0])
        if cmd_line.mass_genre:
            year = year_input(one_track, key)
            add_folder_art(key)
        elif cmd_line.list_info:
            pass
        else:
            genre = genre_input(one_track, key)
            year = year_input(one_track, key)
            add_folder_art(key)
        if cmd_line.rename_album:
            new_name, with_year = rename_album_prompt(one_track, key)
        for music in value:
            track = Track(music)
            if cmd_line.list_info:
                list_info(track, key)
            else:
                normalize(track, year, genre)
                add_file_art(track, key)
            if cmd_line.live_tracks:
                live_tracks(track, key)
                list_info(track, key)
            if cmd_line.rename_album:
                rename_album_tags(track, new_name)
                list_info(track, key)
            if not cmd_line.live_tracks and not cmd_line.rename_album:
                rename_tracks(track, key)
        if cmd_line.rename_album:
            rename_album_dir(with_year, key)
            # would be cool to list just one file as a summary
        if not cmd_line.list_info:
            # this has some stale data in it
            print 'Summary example track for ' + key + ':'
            list_info(one_track, key)

if __name__ == '__main__':
    _main()
