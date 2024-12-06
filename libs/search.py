# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from libs.api import call_graphql
from libs.utils import get_url, plugin_id, get_kodi_version

_handle = int(sys.argv[1])

def list_search(label):
    xbmcplugin.setPluginCategory(_handle, label)
    list_item = xbmcgui.ListItem(label='Nové hledání')
    url = get_url(action='program_search', query = '-----', label = label + ' / ' + 'Nové hledání')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    history = load_search_history()
    for item in history:
        list_item = xbmcgui.ListItem(label=item)
        url = get_url(action='program_search', query = item, label = label + ' / ' + item)  
        list_item.addContextMenuItems([('Smazat', 'RunPlugin(plugin://' + plugin_id + '?action=delete_search&query=' + quote(item) + ')')])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle,cacheToDisc = False)

def program_search(query, label):
    kodi_version = get_kodi_version()
    xbmcplugin.setPluginCategory(_handle, label)
    if query == '-----':
        input = xbmc.Keyboard('', 'Hledat')
        input.doModal()
        if not input.isConfirmed(): 
            return
        query = input.getText()
        if len(query) == 0:
            xbmcgui.Dialog().notification('iVysíláni', 'Je potřeba zadat vyhledávaný řetězec', xbmcgui.NOTIFICATION_ERROR, 5000)
            return   
        else:
            save_search_history(query)
            
    data = call_graphql(operationName = 'SearchShows', variables = '{"limit":30,"offset":0,"search":"' + query + '","onlyPlayable":true}')            
    if data is None:
        xbmcgui.Dialog().notification('iVysíláni', 'Chyba načtení pořadů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        if 'items' in data and len(data['items']) > 0:
            for item in data['items']:
                print(item)
                list_item = xbmcgui.ListItem(label = item['title'])
                url = get_url(action='play_external', id = item['id'])  
                if kodi_version >= 20:
                    infotag = list_item.getVideoInfoTag()
                    infotag.setMediaType('movie')
                else:
                    list_item.setInfo('video', {'mediatype' : 'movie'})      
                if 'imageUrl' in item and item['imageUrl'] is not None:
                    list_item.setArt({'thumb': item['imageUrl'], 'poster' : item['imageUrl']})
                list_item.setProperty('IsPlayable', 'true')       
                list_item.setContentLookup(False)          
                xbmcplugin.addDirectoryItem(_handle, url, list_item, False)        
            xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)                  
        else:
            xbmcgui.Dialog().notification('iVysíláni','Nic nenalezeno', xbmcgui.NOTIFICATION_INFO, 3000)

def save_search_history(query):
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile')) 
    max_history = 10
    cnt = 0
    history = []
    filename = addon_userdata_dir + 'search_history.txt'
    try:
        with open(filename, 'r') as file:
            for line in file:
                item = line[:-1]
                history.append(item)
    except IOError:
        history = []
    history.insert(0,query)
    with open(filename, 'w') as file:
        for item  in history:
            cnt = cnt + 1
            if cnt <= max_history:
                file.write('%s\n' % item)

def load_search_history():
    history = []
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile')) 
    filename = addon_userdata_dir + 'search_history.txt'
    try:
        with open(filename, 'r') as file:
            for line in file:
                item = line[:-1]
                history.append(item)
    except IOError:
        history = []
    return history

def delete_search(query):
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile')) 
    filename = addon_userdata_dir + 'search_history.txt'
    history = load_search_history()
    for item in history:
        if item == query:
            history.remove(item)
    try:
        with open(filename, 'w') as file:
            for item in history:
                file.write('%s\n' % item)
    except IOError:
        pass
    xbmc.executebuiltin('Container.Refresh')