#!/usr/bin/env python

from __future__ import print_function
import requests
import hashlib
import re
import os
import sys

API_KEY = "0d9c21f4af919c86946abbe45e226713"
SHARED_SECRET = "d59f49d7997ac6254a05355e60a8ec45"
APP_NAME = "cmus-scrobble"
REGISTERED_TO = "drooool"

URL_API_ROOT = "http://ws.audioscrobbler.com/2.0/"
URL_AUTHORIZATION = "http://www.last.fm/api/auth/"

CONFIG_DIR = os.path.expanduser("~/.cmus-scrobble/")
SESSION_KEY_PATH = os.path.join(CONFIG_DIR, "session")
TOKEN_KEY_PATH = os.path.join(CONFIG_DIR, "token")


class TokenRequestException(Exception):
    pass


class NotAuthenticatedException(Exception):
    pass


class AuthenticationException(Exception):
    pass


class ScrobbleException(Exception):
    pass


class NowPlayingException(Exception):
    pass


class LastFMInstance:
    def __init__(self):
        self.sessionKey = None
        self.checkSession()

    def checkSession(self):
        if self.sessionExists:  # User authenticated and session key obtained
            self.sessionKey = open(SESSION_KEY_PATH).read()
        elif self.tokenExists:  # User possibly has authenticated and session key hasn't been obtained yet
            self.fetchSession()
        else:  # User has definitively not authenticated. Ask and quit
            self.requestAuthorization()

        print("Starting cmus-scrobble")

    def scrobble(self, artist=None, album=None, title=None, started=None):
        if self.sessionExists:
            self.postScrobble(artist, album, title, started)
        else:
            self.checkSession()

    def postScrobble(self, artist, album, title, started):
        args = {
            'method': 'track.scrobble',
            'artist': artist,
            'album': album,
            'track': title,
            'timestamp': started,
            'api_key': API_KEY,
            'sk': self.sessionKey
        }
        self.addSignature(args)
        try:
            scrobbleResponse = requests.post(URL_API_ROOT, args)
            if scrobbleResponse.status_code == 200:
                print("Scrobbled:", artist, "-", title, "(" + album + ")")
        except requests.RequestException:
            raise ScrobbleException

    def updateNowPlaying(self, artist=None, album=None, title=None):
        if self.sessionExists:
            self.postNowPlaying(artist, album, title)
        else:
            self.checkSession()

    def postNowPlaying(self, artist, album, title):
        args = {
            'method': 'track.updateNowPlaying',
            'artist': artist,
            'album': album,
            'track': title,
            'api_key': API_KEY,
            'sk': self.sessionKey
        }
        self.addSignature(args)
        try:
            nowPlayingResponse = requests.post(URL_API_ROOT, args)
        except requests.RequestException:
            raise NowPlayingException


    ## Authentication methods
    ##


    def requestToken(self):
        try:
            args = {
                'method': 'auth.gettoken',
                'api_key': API_KEY,
                'format': 'json'
            }
            self.addSignature(args)
            tokenResponse = requests.get(URL_API_ROOT, args)
            if tokenResponse.status_code != 200:
                raise TokenRequestException
            token = tokenResponse.json()["token"]

            if not self.configDirExists:
                os.makedirs(CONFIG_DIR)
            tokenFile = open(TOKEN_KEY_PATH, "w+")
            tokenFile.write(token)
            tokenFile.close()

        except requests.RequestException:
            raise TokenRequestException

    def requestAuthorization(self):  # Exits the programs
        print("Please allow cmus-scrobble to access your Last.fm account")
        print(self.authorizationURL)
        print("Exiting program..")
        exit(0)

    def fetchSession(self):
        args = {
            'method': 'auth.getSession',
            'api_key': API_KEY,
            'token': self.token,
        }
        self.addSignature(args)
        try:
            sessionResponse = requests.get(URL_API_ROOT, args)
            sessionResponse = sessionResponse.content.decode()
        except requests.RequestException:
            raise AuthenticationException

        if "<lfm status=\"ok\">" in sessionResponse:
            pattern = re.compile("<key>([0-9a-f]+)</key>")
            sessionKey = pattern.search(sessionResponse).group(1)
            if not self.configDirExists:
                os.makedirs(CONFIG_DIR)
            sessionFile = open(SESSION_KEY_PATH, "w+")
            sessionFile.write(sessionKey)
            sessionFile.close()

            if self.tokenExists:
                os.remove(TOKEN_KEY_PATH)

        else:
            pattern = re.compile("<error code=\"([0-9]+)\">")
            errorCode = pattern.search(sessionResponse).group(1)
            if errorCode == "14":  # Not authorized yet by user
                self.requestAuthorization()
            elif errorCode == "15" or errorCode == "4":  # Token has expired or is invalid
                if self.tokenExists:
                    os.remove(TOKEN_KEY_PATH)
                self.checkSession()
            else:
                raise AuthenticationException


    ## Helper methods
    ##


    @staticmethod
    def addSignature(args):
        signatureStr = ""
        for key in sorted(args.keys()):
            signatureStr += key
            signatureStr += args[key]
        signatureStr += SHARED_SECRET

        args['api_sig'] = hashlib.md5(signatureStr.encode("utf-8")).hexdigest()

    @property
    def token(self):
        token = ""
        if self.tokenExists:
            tokenFile = open(TOKEN_KEY_PATH, "r+")
            token = tokenFile.read()
        return token if len(token) > 1 else None

    @property
    def authorizationURL(self):
        if not self.tokenExists:
            self.requestToken()
        return "{0}?api_key={1}&token={2}".format(URL_AUTHORIZATION, API_KEY, self.token) \
            if self.token is not None else None

    @property
    def tokenExists(self):
        return os.path.exists(TOKEN_KEY_PATH)

    @property
    def sessionExists(self):
        return os.path.exists(SESSION_KEY_PATH)

    @property
    def configDirExists(self):
        return os.path.exists(CONFIG_DIR)
