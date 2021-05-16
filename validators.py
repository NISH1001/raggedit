#!/usr/bin/env python3

import enum
import re
import urllib.parse as urlparse
from abc import ABC, ABCMeta, abstractmethod

import requests


def unshorten_url(url):
    print(f"Unshortening the url = {url}")
    return requests.head(url, allow_redirects=True).url


@enum.unique
class TrackType(enum.Enum):
    SINGLE = 0
    PLAYLIST = 1
    ALBUM = 2
    VOID = 666


@enum.unique
class StreamType(enum.Enum):
    YOUTUBE = 0
    SPOTIFY = 1
    VOID = 666


class URLValidator(ABC):
    _VOID = (StreamType.VOID, TrackType.VOID)

    @abstractmethod
    def validate(self, url: str) -> bool:
        pass

    @abstractmethod
    def _induce(self, url: str) -> (StreamType, TrackType):
        raise NotImplementedError

    def induce_type(self, url: str) -> (StreamType, TrackType):
        if not self.validate_url(url):
            return self._VOID
        return self._induce(url)

    def validate_url(self, url: str) -> bool:
        if not isinstance(url, str):
            return False
        val = self.validate(url)
        return val


class YouTubeValidator(URLValidator):
    def _induce(self, url: str) -> (StreamType, TrackType):
        def _induce(url):
            url_obj = urlparse.urlparse(url)
            params = urlparse.parse_qs(url_obj.query)
            if "v" in params:
                return TrackType.SINGLE
            if "list" in params:
                return TrackType.PLAYLIST
            return TrackType.VOID

        res = _induce(url)
        if res == TrackType.VOID:
            res = _induce(unshorten_url(url))
        return (StreamType.YOUTUBE, res)

    def validate(self, url: bool) -> bool:
        bools = []
        bools.append(
            bool(
                re.findall(
                    r"^(?:https?(?:\:\/\/)?)?(?:www\.)?(?:youtu\.be|youtube\.com)",
                    url,
                )
            )
        )
        bools.append(bool(re.search(r"^(https?://)?music.youtube.com/watch.*?", url)))
        return any(bools)


class SpotifyValidator(URLValidator):
    def _induce(self, url: str) -> (StreamType, TrackType):
        res = re.search(
            r"^(spotify:|https://[a-z]+\.spotify\.com/)(?P<type>(playlist|album|track))",
            url,
        )
        ret = TrackType.VOID
        if not res:
            ret = TrackType.VOID
        elif res.group("type").lower() == "track":
            ret = TrackType.SINGLE
        elif res.group("type").lower() == "playlist":
            ret = TrackType.PLAYLIST
        elif res.group("type").lower() == "album":
            ret = TrackType.ALBUM
        return (StreamType.SPOTIFY, ret)

    def validate(self, url):
        bools = []
        bools.append(
            bool(
                re.findall(
                    r"^(spotify:|https://[a-z]+\.spotify\.com/)",
                    url,
                )
            )
        )
        return any(bools)


def main():
    # url_validator = URLValidator()
    yt_validator = YouTubeValidator()
    spt_validator = SpotifyValidator()

    url = "https://www.youtube.com/watch?v=40d0p_Wb2no"
    url = "https://www.youtube.com/watch?v=CoTGzy51IjA"
    url = "https://www.youtube.com/playlist?list=PLwg22VSCR0W5TcCcyhymD6g_a_6-DY74r"
    print(yt_validator.validate_url(url))
    print(yt_validator.induce_type(url))

    url = "https://open.spotify.com/album/2aoSpTAjFaMvaZeruqnCVv?si=j0cn_uKJRg6nvC1lqv35UA)"
    url = "https://open.spotify.com/track/6s5BwPPzz4bdY5aUHWzqAE?si=31cd6f90f3cc4825"
    url = "google.com"
    # url = "https://open.spotify.com/playlist/0NMsSrtXFTtRieF0kkxZxT?si=878bfbeb25754855"
    print(spt_validator.validate_url(url))
    print(spt_validator.induce_type(url))


if __name__ == "__main__":
    main()
