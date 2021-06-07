import tweepy
import re
import json
import sys
sys.path.append('/app/waldren/base')
import CONFIG

auth = tweepy.AppAuthHandler(CONFIG.TW_API_KEY, CONFIG.TW_SECRET)
#auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

whitespace = re.compile(r"\s+")
web_address = re.compile(r"(?i)http(s):\/\/[a-z0-9.~_\-\/]+")
user = re.compile(r"(?i)@[a-z0-9_]+")

def clean_tweet(tweet):
    tweet = whitespace.sub(' ', tweet)
    tweet = web_address.sub('', tweet)
    tweet = user.sub('', tweet)
    return tweet

for tweet in tweepy.Cursor(api.search, q='$DXC', tweet_mode='extended',lang='en-us', result_type='recent', count=10).items(10):
    print(tweet.user.name)