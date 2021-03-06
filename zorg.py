#!/usr/bin/python

# pip install --upgrade google-api-python-client

import urllib2
import json
import time 
from time import gmtime, strftime
import subprocess
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import ConfigParser
import csv
import re 

conf = ConfigParser.ConfigParser()
conf.read('./config.ini')

YOUTUBE_DEVELOPER_KEY = conf.get("config", "youtube_api_key")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
LAST_FM_API_KEY = conf.get("config", "lastfm_api_key")
# LAST_FM_TIME = str(0)
LAST_FM_TIME = str(time.time()-4000)
# overall | 7day | 1month | 3month | 6month | 12month
LAST_FM_TOP = "7day" 
CSV_DB = conf.get("config", "csv_database")
USERS = ["intel17", "under_your_tree"]
DOWNLOAD_PATTERN = "./downloads/%(id)s.%(ext)s"
LOG_FILE = conf.get("config", "log_file")
KEYWORDS_WANTED = ["official", "OFFICIAL"]
KEYWORDS_IGNORE = ["live", "remix", "full", "album"]

def youtube_search(query, max_results):
	# Build up the query.
	query += '|'.join(KEYWORDS_WANTED)
	for k in KEYWORDS_IGNORE:
		query += " -"+k

	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_DEVELOPER_KEY)

	search_response = youtube.search().list(
		q=query,
		part="id,snippet",
		videoDefinition="high",
		type="video",
		order="rating",
		maxResults=max_results
	).execute()

	for search_result in search_response.get("items", []):
		print "[Y] Result Video ", search_result["snippet"]["title"].encode('utf-8')
		if youtube_filter(search_result["snippet"]["title"].encode('utf-8')):
			return("%s" % (search_result["id"]["videoId"]))
	print ("[Y] No result for: \n>\t%s" % query)
			
def youtube_filter(title):
	for ignore in KEYWORDS_IGNORE:
		if re.search(ignore, title, re.I):
			return False
	return True

def lastfm_top(period):
	rtn = []
	url_base = "http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks&period="+period
	for username in USERS:
		res = urllib2.urlopen(url_base+"&user="+username+"&limit=200"+"&api_key="+LAST_FM_API_KEY+"&format=json").read()
		tracks = json.loads(res)

		for track in tracks['toptracks']['track']:
			name   = track['name'].encode('utf-8')
			artist = track['artist']['name'].encode('utf-8')
			nice   = name + " by " + artist + " "
			print "[L] ", nice, " From ", username
			rtn.append([name, artist, nice, username])
	return rtn 

def lastfm_latest():
	rtn = []
	url_base = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks"
	for username in USERS:
		res = urllib2.urlopen(url_base+"&user="+username+"&limit=200&from="+LAST_FM_TIME+"&api_key="+LAST_FM_API_KEY+"&format=json").read()
		# TODO: Check those errors.
		recent_played = json.loads(res)

		for track in recent_played['recenttracks']['track']:
				name   = track['name'].encode('utf-8')
				artist = track['artist']['#text'].encode('utf-8')
				nice   = name + " by " + artist + " "
				print "[L] ", nice, " From ", username
				rtn.append([name, artist, nice, username])
	return rtn

def download_track_id(id):
	return subprocess.call(["/usr/bin/youtube-dl", "-o", DOWNLOAD_PATTERN, id, "--write-info-json", "--add-metadata", "-x", "--audio-format", "mp3"])

def insert_track(id, track):
	date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
	with open(CSV_DB, 'ab') as db:
		writer = csv.writer(db)
		writer.writerow([id, track[0], track[1], date, track[3]])

def track_exists(track):
	with open(CSV_DB, 'rb') as db:
		reader = csv.reader(db)
		for row in reader:
			if row[1] == track[0] and row[2] == track[1]:
				return True
	return False

def proccess_tracks(tracks):
	for track in tracks:
		if not track_exists(track):
			id = youtube_search(track[2], "50")
			if id and download_track_id(id) == 0:
				insert_track(id, track)
			else:
				print "Unable to download track - ", track[2], id
		else: 
			print "Track exists - ", track[2]

print "[----] Last FM Top "+LAST_FM_TOP
top = lastfm_top(LAST_FM_TOP) 
print "[----] Last FM Latest"
latest = lastfm_latest()

print "[----] Downlading Latest"
proccess_tracks(latest)
print "[----] Downlading Top"
proccess_tracks(top)

