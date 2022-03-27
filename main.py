# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from xbmcvfs import translatePath

from urllib.parse import parse_qsl
from urllib.parse import urlencode, quote
import json
import codecs
import time
from datetime import date

from bs4 import BeautifulSoup
import re

import requests

_url = sys.argv[0]
if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

addon = xbmcaddon.Addon()

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_live_video_url(link, quality):
    soup = load_page(link)
    items = soup.find('div',{'class' : 'b-iframe-video'}).find_all('iframe')
    for item in items:
        embeded = item.get('src')
        soup = load_page(embeded)
        scripts = soup.find_all('script')
        urls = []
        for script in scripts:
            match = re.findall('https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(script))
            for url in match:
                print(url)
                if '.m3u8' in url:
                    urls.append(url.rstrip(',').rstrip('\''))
    link = None
    if len(urls) > 0:
        if quality == 'nízká':
            link = urls[0]
        else:
            link = urls[-1]
    return link

def get_video_url(link, quality):
    soup = load_page(link)
    items = soup.find('div',{'class' : 'b-iframe-video'}).find_all('iframe')
    for item in items:
        embeded = item.get('src')
        soup = load_page(embeded)
        scripts = soup.find_all('script')
        urls = []
        for script in scripts:
            match = re.findall('https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(script))
            for url in match:
                if '.mp4' in url:
                    urls.append(url.rstrip(',').rstrip('\''))
    link = None
    if len(urls) > 0:
        if quality == 'nízká':
            link = urls[0]
        else:
            link = urls[-1]
    return link

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

def set_scheduler(data):
    data = json.loads(data)
    scheduler_data = load_scheduler()
    scheduler_data.update(data)
    save_scheduler(scheduler_data)
    xbmc.executebuiltin('Container.Refresh')

def remove_scheduler(title):
    scheduler_data = load_scheduler()
    del scheduler_data[title]
    save_scheduler(scheduler_data)
    xbmc.executebuiltin('Container.Refresh')

def play_video_scheduler(link, label):
    import xbmc
    addon = xbmcaddon.Addon()
    link = get_live_video_url(link, addon.getSetting('quality'))
    addon = None
    if link is not None:
        playlist=xbmc.PlayList(1)
        playlist.clear()
        list_item = xbmcgui.ListItem(path = link)
        list_item.setProperty('inputstreamaddon','inputstream.adaptive')
        list_item.setProperty('inputstream.adaptive.manifest_type','hls')
        list_item.setInfo('video', {'title' : label}) 
        xbmc.PlayList(1).add(link, list_item)
        xbmc.Player().play(playlist)    

def play_live_video(link, label):
    link = get_live_video_url(link, addon.getSetting('quality'))
    if link is not None:
        list_item = xbmcgui.ListItem()
        list_item.setProperty('inputstreamaddon','inputstream.adaptive')
        list_item.setProperty('inputstream.adaptive.manifest_type','hls')
        list_item.setPath(link)
        xbmcplugin.setResolvedUrl(_handle, True, list_item)

def play_video(link, label):
    link = get_video_url(link, addon.getSetting('quality'))
    if link is not None:
        list_item = xbmcgui.ListItem()
        list_item.setPath(link)
        xbmcplugin.setResolvedUrl(_handle, True, list_item)

def list_items(link, label):
    xbmcplugin.setPluginCategory(_handle, label)
    soup = load_page(link)
    items = soup.find_all('article', {'class': 'b-article'})
    
    previous_page = soup.find('ul', {'class': 'pagination'}).find('a', {'aria-label' : 'Naspäť'})
    next_page = soup.find('ul', {'class': 'pagination'}).find('a', {'aria-label' : 'Ďalej'})

    if previous_page is not None:
        list_item = xbmcgui.ListItem(label = 'Předchozí strana')
        url = get_url(action='list_items', link = previous_page.get('href'), label = label)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    for item in items:
        a = item.find('h3', {'class' : 'title'}).find('a')
        title = a.get('title')
        a_sub = item.find('h4', {'class' : 'subtitle'}).find('a')
        subtitle = ''
        for row in a_sub.contents:
            subtitle = subtitle + str(row)
        if len(subtitle) > 0:
            title = title + ' (' + subtitle + ')'
        link = a.get('href')

        img = item.find('img').get('data-original')

        list_item = xbmcgui.ListItem(label = title)
        list_item.setInfo('video', {'title' : title}) 
        url = get_url(action='play_video', link = link, label = label + ' / ' + title) 
        list_item.setArt({'icon': img})
        list_item.setContentLookup(False)          
        list_item.setProperty('IsPlayable', 'true')        
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    if next_page is not None:
        list_item = xbmcgui.ListItem(label = 'Následující strana')
        url = get_url(action='list_items', link = next_page.get('href'), label = label)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle)

def list_submenu(link, label):
    xbmcplugin.setPluginCategory(_handle, label)    
    soup = load_page(link)
    navbar = soup.find('div', {'class': 'b-nav'}).find_all('a')
    for a in navbar:
        title = a.get('title')
        link = a.get('href')
        list_item = xbmcgui.ListItem(label = title)
        url = get_url(action='list_items', link = link, label = label + ' / ' + title)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)

def list_archiv(link, label):
    xbmcplugin.setPluginCategory(_handle, label)
    soup = load_page(link)
    archiv_list = soup.find('div', {'class': 'e-filter'}).find_all('a')
    for a in archiv_list:
        title = a.get('title')
        link = a.get('href')
        list_item = xbmcgui.ListItem(label = title)
        url = get_url(action='list_items', link = link, label = label + ' / ' + title)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)

def list_live(link, label):
    xbmcplugin.setPluginCategory(_handle, label)
    soup = load_page(link)
    if addon.getSetting('scheduler') == 'true':
        scheduler_data = load_scheduler()

    today = soup.find('div', {'class' : 'b-live-games'})
    datum = date.today().strftime('%d.%m.%Y')
    if today:
        games = today.find_all('article', {'class' : 'b-article'})
        for game in games:
            if game.find('a', {'class' : 'label-live'}):
                link = game.find('a', {'class' : 'label-live'}).get('href')
                cas = 'LIVE'
            else:
                cas = game.find('div', {'class' : 'date'}).get_text()
            title = game.find('h3', {'class' : 'title'}).get_text()
            titles = []
            for row in title.split('\n'):
                if len(row.strip()) > 0: 
                    titles.append(row.strip())
            categories = game.find('ul', {'class' : 'e-breadcrumbs'}).find_all('a')
            category_title = []
            for category in categories:
                category_title.append(category.get_text())

            title = (' - ').join(titles) + ' (' + datum + ' ' + cas + ')'

            if addon.getSetting('scheduler') == 'true' and title in scheduler_data:
                title_colored = '[COLOR=darkgreen]' + title + '[/COLOR]' + '\n' + (' / ').join(category_title)
            else:
                title_colored = '[COLOR=gray]' + title + '[/COLOR]' + '\n' + (' / ').join(category_title)
            list_item = xbmcgui.ListItem(label = title_colored)
            if cas == 'LIVE':
                list_item.setInfo('video', {'title' : title}) 
                url = get_url(action='play_live_video', link = link, label = label + ' / ' + title) 
                list_item.setContentLookup(False)          
                list_item.setProperty('IsPlayable', 'true')        
                xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
            else:
                if addon.getSetting('scheduler') == 'true':
                    startts = int(time.mktime(time.strptime(datum + ' ' + cas, '%d.%m.%Y %H:%M')))
                    data = {title : {'title' : title, 'startts' : startts}}
                    if title in scheduler_data:
                        list_item.addContextMenuItems([('Zrušit naplánování spuštění', 'RunPlugin(plugin://plugin.video.hustetv?action=remove_scheduler&title=' + quote(title) + ')')])       
                    else:
                        list_item.addContextMenuItems([('Naplánovovat spuštění', 'RunPlugin(plugin://plugin.video.hustetv?action=set_scheduler&data=' + quote(json.dumps(data)) + ')')])       

                url = get_url(action='list_live', link = link, label = label)  
                xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    future = soup.find_all('div', {'class' : 'b-live-calendar'})
    for day in future:
        datum = day.find('h3', {'class' : 'title'}).get_text()
        games = day.find_all('div', {'class' : 'b-l-game'})
        for game in games:
            cas = game.find('div', {'class' : 'date'}).get_text()
            hrefs = game.find_all('a')
            titles = []
            for href in hrefs:
                if href.get('class') and href.get('class')[0] == 'i':
                    titles.append(href.get('title'))
            categories = game.find('ul', {'class' : 'e-breadcrumbs'}).find_all('a')
            category_title = []
            for category in categories:
                category_title.append(category.get_text())

            title = (' - ').join(titles) + ' (' + datum + ' ' + cas + ')'

            if addon.getSetting('scheduler') == 'true' and title in scheduler_data:
                title_colored = '[COLOR=darkgreen]' + title + '[/COLOR]' + '\n' + (' / ').join(category_title)
            else:
                title_colored = '[COLOR=gray]' + title + '[/COLOR]' + '\n' + (' / ').join(category_title)
            list_item = xbmcgui.ListItem(label = title_colored)
            if addon.getSetting('scheduler') == 'true':
                startts = int(time.mktime(time.strptime(datum + ' ' + cas, '%d.%m.%Y %H:%M')))
                data = {title : {'title' : title, 'startts' : startts}}
                if title in scheduler_data:
                    list_item.addContextMenuItems([('Zrušit naplánování spuštění', 'RunPlugin(plugin://plugin.video.hustetv?action=remove_scheduler&title=' + quote(title) + ')')])       
                else:
                    list_item.addContextMenuItems([('Naplánovovat spuštění', 'RunPlugin(plugin://plugin.video.hustetv?action=set_scheduler&data=' + quote(json.dumps(data)) + ')')])       
 
            url = get_url(action='list_live', link = link, label = label)  
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def list_menu():
    list_item = xbmcgui.ListItem(label = 'Live a budoucí')
    url = get_url(action='list_live', link = 'https://huste.joj.sk/live', label = 'Live')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Archív')
    url = get_url(action='list_archiv', link = 'https://huste.joj.sk/archiv', label = 'Archív')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    soup = load_page('https://huste.joj.sk/')
    navbar = soup.find_all('div', {'class' : 'w-more'})
    for item in navbar:
        a = item.find('a')
        title = a.get('title')
        link = a.get('href')
        list_item = xbmcgui.ListItem(label = title)
        url = get_url(action='list_submenu', link = link, label = title)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)

def load_page(url):
    r = requests.get(url , headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0'})
    soup = BeautifulSoup(r.content, 'html.parser')
    return soup

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'list_live':
            list_live(params['link'], params['label'])
        elif params['action'] == 'list_archiv':
            list_archiv(params['link'], params['label'])
        elif params['action'] == 'list_submenu':
            list_submenu(params['link'], params['label'])
        elif params['action'] == 'list_items':
            list_items(params['link'], params['label'])
        elif params['action'] == 'play_video':
            play_video(params['link'], params['label'])
        elif params['action'] == 'play_live_video':
            play_live_video(params['link'], params['label'])
        elif params['action'] == 'set_scheduler':
            set_scheduler(params['data'])
        elif params['action'] == 'remove_scheduler':
            remove_scheduler(params['title'])
        else:
            raise ValueError('Neznámý parametr: {0}!'.format(paramstring))
    else:
         list_menu()

if __name__ == '__main__':
    router(sys.argv[2][1:])

addon = None