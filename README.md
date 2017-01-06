#cmus-scrobble

A last.fm scrobbler for [cmus](https://cmus.github.io/).

###Dependencies
- Python >= 2.6, 3.3
- Requires [requests](https://github.com/kennethreitz/requests) for HTTP communication with last.fm servers. Follow the instructions therein.

###Installation

Place `cmus-scrobble.py` and `lastfm_auth` wherever convenient, preferably `/usr/local/bin` or similar.

Run `chmod 755 cmus-scrobble.py` to make it executable.

Run `cmus-scrobble.py` in the background, foreground, whichever tickles your fancy.

To shut down easily, run `pkill -f cmus-scrobble.py`

###Configuration

This is a very simple script, so the only possibly configuration is the scrobble duration threshold. Please keep
 it to within 50-99 % of the track duration. Can be changed in line **11** of `cmus-scrobble.py`

The authorization token and session token are stored in `~/.cmus-scrobble`

