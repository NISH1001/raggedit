# raggedit
Aggregate music streaming site links from any sub-reddit (including post content and all the comments).

For now it aggregates YouTube/Spotify links including single track, playlist and album.

## Configuration

You should have `config.py` with following variables/values:

- `CLIENT_ID` (`str`) : your application client id for Reddit api (compulsary)
- `CLIENT_SECRET` (`str`) : your application client secret for Reddit api  (compulsary)
- `LOOKBACK_DAYS` (`int`): delta days from current time, from which links are to be aggregated (default=`5`)
- `LIMIT` (`int`): Total number of reddit posts/submissions from which lijnks are to be aggregated (default=`30`)

## Run

Just run `aggregator.py`. Make sure you have proper configuration!
