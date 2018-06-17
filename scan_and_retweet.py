import json
import time
import os
import sys

import requests
import twitter
import config
from dateutil import parser

# Number of home timeline tweets to fetch in each batch of pagination
BATCH_SIZE = 200


def tweet_matches_rule(tweet):
    # If tweet is a retweet, skip it
    if tweet.retweeted:
        print('    -- tweet already retweeted')
        return False
    # Tweet must be within our defined date range
    date = parser.parse(tweet.created_at).date()
    if config.START_DATE <= date <= config.END_DATE:
        full_text = tweet.full_text.lower()
        # Tweet must feature one of our hashtags
        for hashtag in config.HASHTAGS:
            if hashtag in full_text:
                return True
        print('    -- tweet did not match a hashtag')
        return False
    else:
        print('    -- tweet date is not in range')
        return False


def get_tweets(api, num_pages_to_fetch=1):
    # Fetch BATCH_SIZE recent tweets from users we follow
    max_id = None
    tweets = []
    for i in range(num_pages_to_fetch):
        print 'max_id: %r' % max_id
        tweets.extend(
            api.GetListTimeline(
                count=BATCH_SIZE,
                owner_screen_name=config.LIST_OWNER_SCREEN_NAME,
                slug=config.LIST_SLUG,
                max_id=max_id,
            )
        )
        max_id = min([tweet.id for tweet in tweets]) - 1
    print "FETCHED %d tweets" % len(tweets)
    print
    return tweets


def scan_and_retweet(tweets):
    # For every tweet, see if it matches a rule
    for tweet in reversed(tweets):
        print "CONSIDER @%s \"%r\"" % (tweet.user.screen_name, tweet.full_text)

        # Have we retweeted this already?
        if tweet.retweeted:
            print "...  SKIPPING, we have retweeted already"
            continue

        # Does it match a rule?
        elif tweet_matches_rule(tweet):
            print "...  TWEETING Matched a rule! Gonna retweet it"
            # Retweet it!
            print api.PostRetweet(tweet.id)
            # Sleep before next possible retweet
            time.sleep(2.5)
        else:
            print "...  IGNORING"


if __name__ == '__main__':
    api = twitter.Api(
        tweet_mode='extended',
        consumer_key=os.environ['CONSUMER_KEY'],
        consumer_secret=os.environ['CONSUMER_SECRET'],
        access_token_key=os.environ['ACCESS_TOKEN_KEY'],
        access_token_secret=os.environ['ACCESS_TOKEN_SECRET'],
    )
    num_pages_to_fetch = 1

    if '--backfill' in sys.argv:
        print "Running backfill (last 800 tweets)"
        num_pages_to_fetch = 4

    tweets = get_tweets(api, num_pages_to_fetch)
    scan_and_retweet(tweets)
