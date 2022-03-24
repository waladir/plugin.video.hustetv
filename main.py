# -*- coding: utf-8 -*-
import os
import sys
import xbmcgui
import xbmcplugin
import xbmcaddon

from urllib.parse import parse_qsl
from urllib.parse import urlencode

from bs4 import BeautifulSoup
import re

import requests

_url = sys.argv[0]
if len(sys.argv) > 1:
    _handle = int(sys.argv[1])
addon = xbmcaddon.Addon()

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def play_video(link, label):
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
    if len(urls) > 0:
        if addon.getSetting('quality') == 'nízká':
            link = urls[0]
        else:
            link = urls[-1]
        list_item = xbmcgui.ListItem()
        list_item.setPath(link)
        xbmcplugin.setResolvedUrl(_handle, True, list_item)

def list_items(link, label):
    xbmcplugin.setPluginCategory(_handle, label)
    soup = load_page(link)
    items = soup.find_all('article', {'class': 'b-article'})
    
    previous_page = soup.find('ul', {'class': 'pagination'}).find('a', {'aria-label' : 'Naspäť'})
    next_page = soup.find('ul', {'class': 'pagination'}).find('a', {'aria-label' : 'Ďalej'})
    print(next_page)

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
            title = '[COLOR=gray]' + title + '[/COLOR]' + '\n' + (' / ').join(category_title)


            list_item = xbmcgui.ListItem(label = title)
            url = get_url(action='list_live', link = link, label = label)  
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)

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
        else:
            raise ValueError('Neznámý parametr: {0}!'.format(paramstring))
    else:
         list_menu()

if __name__ == '__main__':
    router(sys.argv[2][1:])

addon = None