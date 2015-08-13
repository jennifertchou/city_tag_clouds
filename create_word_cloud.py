#!/usr/bin/env python
# coding: utf-8

#script that makes a word cloud of the top 50 words tweeted in a city

import wordcloud
from wordcloud import WordCloud
import psycopg2,psycopg2.extras,ppygis
from collections import defaultdict
import string, argparse

parser = argparse.ArgumentParser()
parser.add_argument('--city','-c',default='pgh',help="cities are: austin,chicago,cleveland,dallas,detroit,houston,london,miami,minneapolis,ny,pgh,sanantonio,seattle,sf,whitehouse")
args = parser.parse_args()

psql_conn = psycopg2.connect("dbname='tweet'")
psycopg2.extras.register_hstore(psql_conn)
pg_cur = psql_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
pg_cur.execute("SELECT text,user_screen_name FROM tweet_" + args.city + ";")

freqs = defaultdict(int)
stop_words = []
for line in open('stop_words.txt'):
    stop_words.append(line.rstrip('\n'))

counter = 0
for row in pg_cur:
    counter += 1
    if (counter % 100000) == 0:
        print str(counter) + ' tweets processed'
    tweet = row[0]
    username = row[1]
    #replace unicode special chars with ascii version
    tweet = tweet.replace('“','"').replace('”','"')
    tweet = tweet.replace('’',"'").replace('‘',"'")
    tweet = tweet.replace("…","...")
    tweet = tweet.replace("\n","")
    exclude = set(string.punctuation)
    exclude.remove('#')
    exclude.remove('-')
    exclude.remove("'")
    exclude.remove("@")
    for punct in exclude:
        tweet = tweet.replace(punct,"") 
    wordList = tweet.split(" ")

    for word in wordList:
        word = word.lower()
        #don't include if a single letter
        if len(word)<=1:
            continue
        #don't include if it's all punctation marks
        if all(char in string.punctuation for char in word):
            continue
        #if the entire string is non-ascii (emojis)
        if all(ord(i)>=128 for i in word):
            continue
        #emojis are 4 non-ascii chars, so get rid of those
        #if they're attached to words
        non_ascii_count = 0
        for i in word:
            if ord(i)>=128:
                non_ascii_count += 1
            else:
                non_ascii_count = 0
            if non_ascii_count >= 4:
                break
        if non_ascii_count >= 4:
            continue
        #take out top 100 english words
        if word in stop_words:
            continue
        #remove any usernames and html urls
        if word.startswith('@') or word.startswith('http'):
            continue
        freqs[word] += 1

freqs = sorted(freqs.items(), key=lambda item:item[1], reverse=True)
freqs = freqs[:50]

print "creating word cloud"
WordCloud().fit_words(freqs).to_file(args.city + "_word_cloud.jpg")
