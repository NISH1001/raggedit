#!/usr/bin/env python3

import re
import time
import urllib.parse as urlparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pprint import pprint

import praw
from praw.models import MoreComments

from config import CLIENT_ID, CLIENT_SECRET
from validators import SpotifyValidator, StreamType, TrackType, YouTubeValidator


def extract_urls(text):
    matches = re.finditer("(?P<url>https?://[^\s]+)", text)
    res = []
    for m in matches:
        url = m.group("url")
        if url:
            res.append(url)
    return res


@dataclass
class URLMeta:
    idx: str
    upvotes: int
    url: str
    title: str
    created_utc: datetime = None
    parent_idx: str = None
    upvote_ratio: float = None


def get_all_urls_from_submission(submission):
    post_urls = []

    url = submission.url
    title = submission.title
    upvotes = submission.ups
    content = submission.selftext

    # first append post url
    post_urls.append(
        URLMeta(
            idx=submission.id,
            upvotes=upvotes,
            upvote_ratio=submission.upvote_ratio,
            title=title,
            url=url,
            created_utc=datetime.utcfromtimestamp(submission.created_utc),
            parent_idx=submission.id,
        )
    )

    # then add all the urls from the content
    urls = extract_urls(content)
    post_urls.extend(
        [
            URLMeta(
                idx=submission.id,
                upvotes=upvotes,
                upvote_ratio=submission.upvote_ratio,
                title=title,
                url=url,
                created_utc=datetime.utcfromtimestamp(submission.created_utc),
                parent_idx=submission.id,
            )
            for url in urls
        ]
    )

    return post_urls


def get_comment_urls(submission):
    comments = submission.comments.list()
    comments = filter(None, comments)
    to_add = []
    for comment in comments:
        urls = extract_urls(comment.body)
        for url in urls:
            to_add.append(
                URLMeta(
                    idx=comment.id,
                    upvotes=comment.ups,
                    title=comment.body,
                    url=url,
                    created_utc=datetime.utcfromtimestamp(comment.created_utc),
                    parent_idx=submission.id,
                )
            )

    comments = filter(lambda x: x.url is not None, to_add)
    return comments


def main():

    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="http://localhost:8000",
        user_agent="testscript by u/fakebot3",
    )
    # print(reddit.auth.url(["identity read subscribe mysubreddits"], "...", "permanent"))

    today = time.time()
    week = today - (60 * 60 * 24 * 2)

    lookback_days = datetime.utcnow() - timedelta(days=5)
    print(f"Fetching links from date: {lookback_days}")

    subr = reddit.subreddit("connectedbymusicNEPAL")
    # subr = reddit.subreddit("NepaliMusic")

    submissions = subr.hot(limit=10)
    submissions = filter(
        lambda s: datetime.utcfromtimestamp(s.created_utc) >= lookback_days, submissions
    )

    post_urls = []
    comment_urls = []
    for submission in submissions:
        post_urls.extend(get_all_urls_from_submission(submission))
        comment_urls.extend(get_comment_urls(submission))

    yt_validator = YouTubeValidator()
    spotify_validator = SpotifyValidator()
    url_validators = [yt_validator, spotify_validator]

    def induce_type(url):
        if isinstance(url, URLMeta):
            url = url.url
        res = map(lambda v: v.induce_type(url), url_validators)
        res = filter(lambda v: v[0] != StreamType.VOID and v[1] != TrackType.VOID, res)
        res = list(res)
        return res[0] if res else None

    print(f"Total URLs extracted from post: {len(post_urls)}")
    post_urls = map(lambda url: (induce_type(url), url), post_urls)
    post_urls = filter(lambda url: url[0] is not None, post_urls)
    post_urls = list(post_urls)
    print(f"After validation, URLs extracted from post: {len(post_urls)}")
    print(post_urls)


if __name__ == "__main__":
    main()
