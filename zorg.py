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

conf = ConfigParser.ConfigParser()
conf.read('./config.ini')

YOUTUBE_DEVELOPER_KEY = conf.get("config", "youtube_api_key")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
LAST_FM_API_KEY = conf.get("config", "lastfm_api_key")
LAST_FM_TIME = time.time()-15000 # about an hour
CSV_DB = conf.get("config", "csv_database")
USERS = ["intel17"]
DOWNLOAD_PATTERN = "./downloads/%(id)s.%(ext)s"
LOG_FILE = conf.get("config", "log_file")

def youtube_search(track, max_results):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_DEVELOPER_KEY)

	search_response = youtube.search().list(
		q=track,
		part="id,snippet",
		maxResults=max_results
	).execute()

	videos = []

	for search_result in search_response.get("items", []):
		if search_result["id"]["kind"] == "youtube#video":
			print "[Y] ",search_result["id"]["videoId"], track
			# Return the first found video id.
			return("%s" % (search_result["id"]["videoId"]))

def lastfm_search():
	rtn = []
	for username in USERS:
		res = urllib2.urlopen("http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user="+username+"&from="+str(LAST_FM_TIME)+"&api_key="+LAST_FM_API_KEY+"&format=json").read()
		# TODO: Check those errors.
		recent_played = json.loads(res)
		tracks = recent_played['recenttracks']['track']

		for t in tracks: 
				rtn.append([t['name'],t['artist']['#text']])
				print rtn[-1][0], "by", rtn[-1][1]
	return rtn

def download_track_id(id):
	return subprocess.call(["/usr/bin/youtube-dl", "-o", DOWNLOAD_PATTERN, id, "--write-info-json", "--add-metadata", "-x", "--audio-format", "mp3"])


def insert_track(id, track, artist):
	date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
	with open(CSV_DB, 'ab') as db:
		writer = csv.writer(db)
		writer.writerow([id, track, artist, date])

def track_exists(track):
	with open(CSV_DB, 'rb') as db:
		reader = csv.reader(db)
		for row in reader:
			if row[1] == track[0] and row[2] == track[1]:
				return True
	return False

# Main
tracks = lastfm_search()
for track in tracks:
	track_nice = track[0] + " by " + track[1]
	print track_nice
	if not track_exists(track):
		id = youtube_search(track_nice, "1") 
		if download_track_id(id) == 0:
			insert_track(id, track[0], track[1])
		else:
			print "Unable to download track - ", track_nice, id
	else: 
		print "Track exists - ", track_nice