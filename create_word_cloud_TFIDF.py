#!/usr/bin/env python
# coding: utf-8

#script that makes a word cloud of the top 50 words tweeted in a city

import wordcloud
from wordcloud import WordCloud
import psycopg2,psycopg2.extras,ppygis
from collections import defaultdict
import string, argparse, math
#--for mask stuff--
#from scipy.misc import imread
#from os import path
#import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument('--city','-c',default='pgh',help="cities are: austin," +
"chicago,cleveland,dallas,detroit,houston,london,miami,minneapolis,ny,pgh," + 
"sanantonio,seattle,sf,whitehouse")
args = parser.parse_args()

psql_conn = psycopg2.connect("dbname='tweet'")
psycopg2.extras.register_hstore(psql_conn)
pg_cur = psql_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
pg_cur.execute("SELECT text,user_screen_name FROM tweet_" + args.city + ";")

cities = ['austin','chicago','cleveland','dallas','detroit','houston', 
          'london','miami','minneapolis','ny','pgh','sanantonio', 
          'seattle','sf','whitehouse']
freqs = defaultdict(int)
IDF = defaultdict(int)
TFIDF = {}
uniq_users_per_word = defaultdict(set)
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
    exclude.remove('-')
    exclude.remove("'")
    exclude.remove("@")
    for punct in exclude:
        tweet = tweet.replace(punct,"") 
    wordList = tweet.split(" ")

    for word in wordList:
        word = word.lower()
        #don't include if a single letter
        if len(word)<=1: continue
        #don't include if it's all punctation marks
        if all(char in string.punctuation for char in word): continue
        #if the entire string is non-ascii (emojis)
        if all(ord(i)>=128 for i in word): continue
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
        if non_ascii_count >= 4: continue
        #take out top english words + random twitter junk
        if word in stop_words: continue
        #remove any usernames and html urls
        if word.startswith('@') or word.startswith('http'): continue
        freqs[word] += 1
        uniq_users_per_word[word].add(username)

#take out words tweeted by less than 10 people
for word in uniq_users_per_word:
    if len(uniq_users_per_word[word]) < 10:
        del freqs[word]

#since this word shows up in the city, increment each word's IDF        
for word in freqs:
    IDF[word] += 1    

#look at other cities to further increase IDF values
for city in cities:
    users_per_word = defaultdict(set)
    if city == args.city: continue
    print "looking at " + city
    pg_cur.execute("SELECT text,user_screen_name FROM tweet_" + city + 
                    " ORDER BY RANDOM() LIMIT 1000000;")
    for row in pg_cur:
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
            #don't need to do all that word filtering above because
            #those words will be ignored here
            if word in IDF:
                users_per_word[word].add(username) 
    #if a word was tweeted by at least 10 people, increment that word's IDF
    for word in users_per_word:
        if len(users_per_word[word]) < 10: continue
        IDF[word] += 1

#TF = # of times a word appears in list/total # of words in list 
#   but not doing the division because it makes the numbers 
#   too small and everything becomes 0.0 
#IDF = log_e(total num of cities/# of cities with word w in it)
for word in freqs:
    TFIDF[word] = freqs[word] *  math.log(float(len(cities))/IDF[word])

TFIDF = sorted(TFIDF.items(), key=lambda item:item[1], reverse=True)
TFIDF = TFIDF[:100]

print "creating word cloud"

#read the mask image
#pgh_outline = imread(path.join('pgh_outline.png'))
#WordCloud(mask=pgh_outline).fit_words(freqs).to_file(args.city + "_word_cloud_skyline.jpg")

WordCloud(width=800,height=400).fit_words(TFIDF).to_file(args.city + "_word_cloud_TFIDF.jpg")

for item in TFIDF:
    print item[0],
    print " count:" + str(freqs[item[0]]) + " #nghds:" + str(IDF[item[0]]),
    print " TFIDF:" + str(item[1])

