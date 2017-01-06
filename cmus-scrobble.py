#!/usr/bin/env python

from __future__ import print_function, division

import subprocess
import time
from math import floor

from lastfm_auth import LastFMInstance, TokenRequestException, \
    AuthenticationException, NotAuthenticatedException, \
    ScrobbleException, NowPlayingException

#
# Change the scrobble percentage here
SCROBBLE_THRESHOLD = 50  # percent
#

LOOP_DURATION = 1


class MusicInfo:
    def __init__(self):
        self.artist = ""
        self.status = ""
        self.album = ""
        self.title = ""
        self.duration = -1
        self.position = -1
        self.elapsed = 0
        self.started = str(time.time())
        self.scrobbledTrack = False

    def __eq__(self, other):
        return self.artist == other.artist \
               and self.album == other.album \
               and self.title == other.title \
               and self.duration == other.duration

    def __cmp__(self, other):  # Python 2 exclusive
        return self.__cmp__(other)

    def __ne__(self, other):
        return not self == other

    @property
    def percentagePlayed(self):
        return floor((self.elapsed * 100.0) / self.duration)


class CMUSStatus:
    def __init__(self):
        self.scrobbleThreshold = SCROBBLE_THRESHOLD
        if self.scrobbleThreshold < 50: self.scrobbleThreshold = 50
        if self.scrobbleThreshold > 99: self.scrobbleThreshold = 99

        self.nowPlayingInfo = MusicInfo()

        try:
            self.lastFMInstance = LastFMInstance()
        except AuthenticationException:
            print("Error retrieving last.fm session")
            exit(1)
        except NotAuthenticatedException as exception:
            print("Please allow cmus-scrobble to access your account")
            print(exception)
            exit(1)
        except TokenRequestException:
            print("Error retrieving access token. Please check your internet connection.\nExiting program..")
            exit(1)
        except ValueError:
            print("Error parsing JSON from last.fm server")

    def scrobble(self):
        self.nowPlayingInfo.scrobbledTrack = True
        try:
            self.lastFMInstance.scrobble(
                artist=self.nowPlayingInfo.artist,
                album=self.nowPlayingInfo.album,
                title=self.nowPlayingInfo.title,
                started=self.nowPlayingInfo.started
            )
        except ScrobbleException:
            print("Could not scrobble track to last.fm")
        except ValueError:
            print("Error parsing JSON from last.fm server")

    def updateNowPlaying(self):
        try:
            self.lastFMInstance.updateNowPlaying(
                artist=self.nowPlayingInfo.artist,
                album=self.nowPlayingInfo.album,
                title=self.nowPlayingInfo.title
            )
        except NowPlayingException:
            print("Could not send now playing info to last.fm")
        except ValueError:
            print("Error parsing JSON from last.fm server")

    def reset(self, newMusicInfo=None):
        if newMusicInfo is None:
            self.nowPlayingInfo = MusicInfo()
        else:
            self.nowPlayingInfo = newMusicInfo
            self.updateNowPlaying()

    def apply(self, remoteOutput):  # called every LOOP_DURATION seconds
        newMusicInfo = MusicInfo()
        for line in remoteOutput.splitlines():
            if line.startswith("status "):
                newMusicInfo.status = line[7:]
                if newMusicInfo.status != "playing":
                    return

            if line.startswith("duration "):
                newMusicInfo.duration = int(line[9:])

            if line.startswith("position "):
                newMusicInfo.position = int(line[9:])

            if line.startswith("tag artist "):
                newMusicInfo.artist = line[11:]

            if line.startswith("tag album "):
                newMusicInfo.album = line[10:]

            if line.startswith("tag title "):
                newMusicInfo.title = line[10:]

        if newMusicInfo != self.nowPlayingInfo:
            self.reset(newMusicInfo)
            return

        self.nowPlayingInfo.elapsed += LOOP_DURATION

        if not self.nowPlayingInfo.scrobbledTrack and self.nowPlayingInfo.duration > 30:  # Scrobble minimum length is 30s according to last.fm api rules
            if self.nowPlayingInfo.percentagePlayed >= self.scrobbleThreshold \
                    or self.nowPlayingInfo.elapsed >= 4 * 60:  # Scrobble if elapsed duration reaches 4m according to last.fm api rules
                self.scrobble()

    def __str__(self):
        return "{0} - {1} ({2}) {3} : {4}%" \
            .format(self.nowPlayingInfo.artist,
                    self.nowPlayingInfo.title,
                    self.nowPlayingInfo.album,
                    self.nowPlayingInfo.position,
                    self.nowPlayingInfo.percentagePlayed)


def scrobblerLoop():
    status = CMUSStatus()
    while True:
        try:
            res = subprocess.check_output(["cmus-remote", "-Q"], stderr=subprocess.STDOUT)
            status.apply(res.decode(encoding="utf-8"))
        except subprocess.CalledProcessError:
            print("cmus is not running")

            """
            # This doesn't really work if it's run as a background process
            # so it'd be better to not do it at all
            #

            try:
                if sys.version_info[0] == 2:
                    inp = raw_input("Enter q to quit or any other key to retry.")
                else:
                    inp = input("Enter q to quit or any other key to retry.")

                if inp == 'q':
                    exit(0)
            except SyntaxError:
                pass
            """

        time.sleep(LOOP_DURATION)


if __name__ == "__main__":
    scrobblerLoop()
