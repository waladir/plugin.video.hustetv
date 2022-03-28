# -*- coding: utf-8 -*-
import os

import xbmc
import xbmcaddon
import xbmcgui
from xbmcvfs import translatePath

import json
import codecs
from datetime import datetime
import time

from bs4 import BeautifulSoup
import requests


from main import play_video_scheduler

addon = xbmcaddon.Addon()

def load_scheduler():
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'scheduler.txt')
    data = {}
    if os.path.exists(filename):
        try:
            with codecs.open(filename, 'r', encoding='utf-8') as file:
                for row in file:
                    data = json.loads(row[:-1])
        except IOError as error:
            if error.errno != 2:
                xbmcgui.Dialog().notification('Huste.tv', 'Chyba při načtení plánovače', xbmcgui.NOTIFICATION_ERROR, 5000)
    return data

def save_scheduler(data):
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    data = json.dumps(data)
    filename = os.path.join(addon_userdata_dir, 'scheduler.txt')
    try:
        with codecs.open(filename, 'w', encoding='utf-8') as file:
            file.write('%s\n' % data)
    except IOError:
        xbmcgui.Dialog().notification('Huste.tv', 'Chyba uložení plánovače', xbmcgui.NOTIFICATION_ERROR, 5000)       

def remove_scheduler(title):
    scheduler_data = load_scheduler()
    del scheduler_data[title]
    save_scheduler(scheduler_data)

tz_offset = int((time.mktime(datetime.now().timetuple())-time.mktime(datetime.utcnow().timetuple()))/3600)
time.sleep(10)
next = time.time()
interval = 30

if addon.getSetting('scheduler') == 'true':
    while not xbmc.Monitor().abortRequested():
        if(next < time.time()):
            scheduler_data = load_scheduler()
            for event in scheduler_data:
                if int(scheduler_data[event]['startts']) < int(time.mktime(datetime.now().timetuple())):
                    remove_scheduler(event)
                    r = requests.get('https://huste.joj.sk/live' , headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0'})
                    soup = BeautifulSoup(r.content, 'html.parser')
                    today = soup.find('div', {'class' : 'b-live-games'})
                    if today:
                        games = today.find_all('article', {'class' : 'b-article'})
                        for game in games:
                            if game.find('a', {'class' : 'label-live'}):
                                link = game.find('a', {'class' : 'label-live'}).get('href')
                                title = game.find('h3', {'class' : 'title'}).get_text()
                                titles = []
                                for row in title.split('\n'):
                                    if len(row.strip()) > 0: 
                                        titles.append(row.strip())
                                title = (' - ').join(titles)
                                if title in event:
                                    play_video_scheduler(link, title)
            next = time.time() + float(interval)
        time.sleep(10)
addon = None