#!/usr/bin/env python

from __future__ import print_function, division
import subprocess
import time
from lastfm_auth import LastFMInstance, TokenRequestException, \
    AuthenticationException, NotAuthenticatedException, ScrobbleException
from math import floor

#
# Change the scrobble percentage here
SCROBBLE_THRESHOLD = 50 # percent
#

LOOP_DURATION = 1

class CMUSStatus:
    def __init__(self):
        self.scrobbleThreshold = SCROBBLE_THRESHOLD
        if self.scrobbleThreshold < 50: self.scrobbleThreshold = 50
        if self.scrobbleThreshold > 99: self.scrobbleThreshold = 99
        self.lastFMInstance = LastFMInstance()
        self.status = ""
        self.duration = -1
        self.position = -1
        self.artist = ""
        self.album = ""
        self.title = ""
        self.elapsed = -1
        self.started = ""
        self.scrobbledTrack = False

    def scrobble(self):
        self.scrobbledTrack = True
        try:
            self.lastFMInstance.scrobble(
                artist=self.artist,
                album=self.album,
                title=self.title,
                started=self.started
            )
        except AuthenticationException:
            print("Error retrieving Last.fm session")
            exit(1)
        except NotAuthenticatedException as e:
            print("Please allow cmus-scrobble to access your account")
            print(e)
            exit(1)
        except TokenRequestException:
            print("Error retrieving access token")
        except ScrobbleException:
            print("Error scrobbling track to Last.fm")
        except ValueError:
            print("Error parsing JSON from Last.fm server")

    def reset(self):
        self.elapsed = 0
        self.scrobbledTrack = False
        self.started = str(time.time())
        pass

    def apply(self, remoteOutput): # called every LOOP_DURATION seconds
        for line in remoteOutput.splitlines():
            if line.startswith("status "):
                self.status = line[7:]
                if self.status != "playing":
                    return

            if line.startswith("duration "):
                if int(line[9:]) != self.duration:
                    self.reset()
                    self.duration = int(line[9:])

            if line.startswith("position "):
                self.position = int(line[9:])

            if line.startswith("tag artist "):
                if line[11:] != self.artist:
                    self.reset()
                    self.artist = line[11:]

            if line.startswith("tag album "):
                if line[10:] != self.album:
                    self.reset()
                    self.album = line[10:]

            if line.startswith("tag title "):
                if line[10:] != self.title:
                    self.reset()
                    self.title = line[10:]

        self.elapsed += LOOP_DURATION

        if self.percentagePlayed >= self.scrobbleThreshold and not self.scrobbledTrack:
            self.scrobble()

    @property
    def percentagePlayed(self):
        return floor( (self.elapsed * 100.0) / self.duration)

    def __str__(self):
        return "{0} - {1} ({2}) {3} : {4}%".format(self.artist, self.title, self.album, self.position, self.percentagePlayed)

def scrobblerLoop():
    status = CMUSStatus()
    while True:
        try:
            res = subprocess.check_output(["cmus-remote", "-Q"], stderr=subprocess.STDOUT)
            status.apply(res.decode(encoding="utf-8"))
        except subprocess.CalledProcessError:
            print("cmus is not running")
            exit(0)
            pass

        time.sleep(LOOP_DURATION)

if __name__ == "__main__":
    scrobblerLoop()