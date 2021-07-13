# scraper.py

import requests
import lxml
from bs4 import BeautifulSoup
import json
from youtube_dl import YoutubeDL

def fpsb_discourse_scraper():
	article_list = []
	try:
		r = requests.get('https://forum.penspinning-france.fr/c/videos/projets/30.rss')
		soup = BeautifulSoup(r.content, 'xml')
		articles = soup.find_all('item')
		for a in articles:
			title = a.title.text
			link = a.link.text
			author = a.find('dc:creator').text
			article_list.append({'title':title, 'link':link, 'author': author})
		return article_list
	except Exception as e:
		print(e)


def get_new_discourse_posts():
	with open('/home/discord/fpsb_bot/json/projets_cv.json') as old_posts_file:
		old_posts = json.load(old_posts_file)
	scraped_posts = fpsb_discourse_scraper()
	new_posts = [p for p in scraped_posts if (p not in old_posts)]
	with open('/home/discord/fpsb_bot/json/projets_cv.json', 'w') as old_posts_file:
		json.dump(scraped_posts, old_posts_file)
	return new_posts

def ps_academy_scraper():
	with YoutubeDL({'quiet':True}) as ydl:
		videos = ydl.extract_info('https://www.youtube.com/channel/UC5chm7XPK_snAZYgG7c6srg/videos', download=False)['entries']
		video_list = [{'title':v['title'], 'link':v['webpage_url']} for v in videos]
		return video_list

def get_new_ps_academy_posts():
	with open('/home/discord/fpsb_bot/json/ps_academy.json') as old_videos_file:
		old_videos = json.load(old_videos_file)
	scraped_videos = ps_academy_scraper()
	new_videos = [v for v in scraped_videos if (v not in old_videos)]
	with open('/home/discord/fpsb_bot/json/ps_academy.json', 'w') as old_videos_file:
		json.dump(scraped_videos, old_videos_file)
	return new_videos
