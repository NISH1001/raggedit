#!/usr/bin/env python3

import re
import time
import urllib.parse as urlparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pprint import pprint

import praw
from praw.models import MoreComments

import config
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
    return list(comments)


def get_cfg_value(key):
    key = key.upper()
    if key in ["CLIENT_ID", "CLIENT_SECRET"]:
        if not hasattr(config, key):
            raise ValueError("config file doesn't have CLIENT_ID or CLIENT_SECRET")
        elif key == "CLIENT_ID":
            return config.CLIENT_ID
        elif key == "CLIENT_SECRET":
            return config.CLIENT_SECRET
    if key == "LOOKBACK_DAYS":
        return 5 if not hasattr(config, key) else config.LOOKBACK_DAYS
    if key == "LIMIT":
        return 30 if not hasattr(config, key) else config.LIMIT
    return None


def main():
    client_id = get_cfg_value("CLIENT_ID")
    client_secret = get_cfg_value("CLIENT_SECRET")
    lookback_days = get_cfg_value("LOOKBACK_DAYS")
    limit = get_cfg_value("LIMIT")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost:8000",
        user_agent="testscript by u/fakebot3",
    )
    # print(reddit.auth.url(["identity read subscribe mysubreddits"], "...", "permanent"))

    today = time.time()
    week = today - (60 * 60 * 24 * 2)

    print(f"LOOKBACK_DAYS = {lookback_days}")
    lookback_days = datetime.utcnow() - timedelta(days=lookback_days)
    print(f"Fetching links from date: {lookback_days}")

    subr = reddit.subreddit("connectedbymusicNEPAL")
    # subr = reddit.subreddit("NepaliMusic")

    print(f"Submission limit = {limit}")
    submissions = subr.hot(limit=limit)
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

    print(f"Total URLs extracted from comments: {len(comment_urls)}")
    comment_urls = map(lambda url: (induce_type(url), url), comment_urls)
    comment_urls = filter(lambda url: url[0] is not None, comment_urls)
    comment_urls = list(comment_urls)
    print(f"After validation, URLs extracted from comments: {len(comment_urls)}")
    print(comment_urls)


if __name__ == "__main__":
    main()
