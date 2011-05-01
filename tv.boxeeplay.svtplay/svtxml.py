﻿#encoding:utf-8
#author:Mats Boisen
#project:boxeeplay
#repository:https://bitbucket.org/hesapesa/boxeeplay
#license:Creative Commons GNU GPL v2
# (http://creativecommons.org/license/GPL/2.0/)

import threading
from urllib import quote_plus
import urllib2
import xml.dom.minidom
import re
import time
import calendar
import mc
from logger import BPLog,BPTraceEnter,BPTraceExit,Level

def GetDirectory(url, maxResults=0):
    BPTraceEnter(url)
    start = 1
    
    if (maxResults <= 0):
        maxResults = 9999
    
    BPLog("svtxml: %s" % url, Level.DEBUG)
    root = RetrieveXmlStream(url)
    
    totalResults = int(root.getElementsByTagName("opensearch:totalResults")[0].childNodes[0].data)
    if (totalResults > maxResults):
        totalResults = maxResults
        
    listItems = ProcessDirectoryPage(root)

    noOfItems = len(listItems)
    start = start + noOfItems
    while (start <= totalResults):
        pageUrl = url + "&start=" + str(start)
        pageListItems = GetDirectoryPage(pageUrl)
        start = start + len(pageListItems)
        for pageListItem in pageListItems:
            listItems.append(pageListItem)
        
    BPLog("svtxml: Loaded %s items." % str(len(listItems)), Level.DEBUG)
    BPTraceExit("Returning %s" % listItems)
    return listItems
        
def ProcessDirectoryPage(root) :
    BPTraceEnter(root)
    items = mc.ListItems()
        
    for node in root.getElementsByTagName("item"):
        item = AddItem(items, node)

    BPTraceExit("Returning %s" % items)
    return items

def GetDirectoryPage(url) :
    BPTraceEnter(url)
    BPLog("svtxml: %s" %url, Level.DEBUG)
    root = RetrieveXmlStream(url)
    r = ProcessDirectoryPage(root)
    BPTraceExit("Returning %s" % r)
    return r

def SetItemImages(node, item) :
    BPTraceEnter("%s, %s" % (node, item))
    imageNo = 0
    mediaContentNodes = node.getElementsByTagName("media:content")
    for mediaContentNode in mediaContentNodes:
        if (mediaContentNode.getAttribute("medium").encode("utf-8") == "image"):
            imageUrl = mediaContentNode.getAttribute("url").encode("utf-8")
            if (imageNo == 0):
                item.SetIcon(imageUrl)
                item.SetThumbnail(imageUrl)
            item.SetImage(imageNo, imageUrl)
            imageNo = imageNo + 1
    BPTraceExit()
    
def AddItem(items, node):
    BPTraceEnter("%s, %s" % (items, node))
    videoType = mc.ListItem.MEDIA_VIDEO_CLIP
    try:
        episode = int(GetElementAttribute(node, "svtplay:programInfo", "episodeNo"))
        videoType = mc.ListItem.MEDIA_VIDEO_EPISODE
    except:
        episode = 0

    item = mc.ListItem(videoType)

    try:
        item.SetPath(GetElementData(node, "link"))
        item.SetContentType("text/html")
        title = GetElementData(node, "title")
        item.SetTitle(title)
        item.SetLabel(title)
        show = GetElementData(node, "svtplay:titleName")
        item.SetTVShowTitle(show)
        if len(show) > 0:
            item.SetLabel("%s - %s" %(show,title))
        item.SetDescription(GetElementData(node, "description"))
        item.SetAuthor(GetElementData(node, "author"))
        item.SetProviderSource(GetElementData(node, "svtplay:broadcastChannel"))
        item.SetThumbnail(GetElementAttribute(node, "media:thumbnail", "url"))
        item.SetIcon(GetElementData(node, "svtplay:logotype"))
        SetItemImages(node, item)
        item.SetProperty("id", GetElementData(node, "svtplay:titleId"))
        item.SetGenre(LookupCategory(str(GetElementData(node, "svtplay:category"))))
        item.SetReportToServer(False)
        item.SetAddToHistory(False)
        #if episode > 0:
        #    item.SetEpisode(episode) #Funkar dåligt i Boxees interface med SVT

        SetDate(item, node)

        SetAlternatePaths(item, node)

        SetGuiInfo(item)

        items.append(item)
    except Exception, e:
        BPLog("svtxml: List item creation failed, url =%s, Exception: %s" % (item.GetPath(),str(e)), Level.ERROR)
    BPTraceExit()

def SetAlternatePaths(item, node):
    BPTraceEnter("%s, %s" % (item, node))
    item.SetProperty("replacedPath", "0")
    for mediaGroup in node.getElementsByTagName("media:group"):
        mediaNodes = mediaGroup.getElementsByTagName("media:content")
        AddFlowplayerPaths(item, mediaNodes)
    #DumpAlternateMediaPaths(item, node)
    BPTraceExit()
		
def DumpAlternateMediaPaths(item, node):
    BPTraceEnter("%s, %s" %(item, node))
    if item.GetProperty("replacedPath") == "0":
        for mediaGroup in node.getElementsByTagName("media:group"):
            mediaNodes = mediaGroup.getElementsByTagName("media:content")
            if (len(mediaNodes) > 0):
                BPLog("svtxml: No playable media path was found! Alternative paths listed below.")
                for mediaNode in mediaNodes:	
                    mediaLabel = GetElementData(mediaNode, "svtplay:videoIdentifier")
                    mediaPath = mediaNode.getAttribute("url").encode("utf-8")
                    mediaType = mediaNode.getAttribute("type").encode("utf-8")
                    BPLog("svtxml: %s - %s - %s" %(mediaLabel, mediaType, mediaPath))
    BPTraceExit()
        
def AddFlowplayerPaths(item, mediaNodes):
    BPTraceEnter("%s, %s" %(item, mediaNodes))
    AddFlowplayerPath(item, mediaNodes, "mp4-e-v1", "HD-kvalitet, 720p, 2400 kbs.", "http://svt.se/content/1/c8/01/39/57/98/play-hd-webb-tv.gif")
    AddFlowplayerPath(item, mediaNodes, "mp4-d-v1", "Hög kvalitet, 1400 kbs.", "http://svt.se/content/1/c8/01/39/57/98/play-high-webb-tv.gif")
    AddFlowplayerPath(item, mediaNodes, "mp4-c-v1", "Medelkvalitet, 850 kbs.", "http://svt.se/content/1/c8/01/39/57/98/play-medium-webb-tv.gif")
    AddDirectPath(item, mediaNodes, "wmv-a-v1", "Låg kvalitet, 340 kbs.", "http://svt.se/content/1/c8/01/39/57/98/play-low-webb-tv.gif")
    AddDirectPath(item, mediaNodes, "video/x-ms-asf", "Låg kvalitet, 340 kbs.", "http://svt.se/content/1/c8/01/39/57/98/play-low-webb-tv.gif")
    BPTraceExit()
    
def CreateRtmpPath(path):
    BPTraceEnter(path)
    domain = re.compile('^(.*?)/kluster', re.DOTALL + re.IGNORECASE).search(str(path)).group(1)
    id = re.compile(domain + '/(.*?)$', re.DOTALL + re.IGNORECASE).search(str(path)).group(1)
    url = 'http://boxeeplay.tv/flowplayer/index.html?net=' + str(domain) + '&id=mp4:' + str(id)
    url = quote_plus(url)
    jsActions = quote_plus('http://boxeeplay.tv/flowplayer/flow.js')
    path = 'flash://boxeeplay.tv/src=' + str(url) + '&bx-jsactions=' + str(jsActions)
    BPLog("svtxml: Media path converted to: %s" % path, Level.DEBUG)
    BPTraceExit("Returning %s" % path)
    return path
    
def AddFlowplayerPath(item, mediaNodes, label, title, thumbnailPath):
    BPTraceEnter("%s, %s, %s, %s, %s" % (item, mediaNodes, label, title, thumbnailPath))
    for mediaNode in mediaNodes:
        mediaLabel = GetElementData(mediaNode, "svtplay:videoIdentifier")
        mediaPath = mediaNode.getAttribute("url").encode("utf-8")
        mediaType = mediaNode.getAttribute("type").encode("utf-8")
        if mediaType == "video/mp4" and mediaLabel == label:
            if mediaPath[:5] == "rtmp:" or mediaPath[:6] == "rtmpe:":
                mediaPath = CreateRtmpPath(mediaPath)
                item.AddAlternativePath(title, mediaPath, "text/html", thumbnailPath) 
                try:
                    duration =  int(mediaNode.getAttribute("duration").encode("utf-8"))
                except:
                    duration = 0
                if duration > 0:
                    item.SetDuration(duration)
                    item.SetProperty("duration",str(duration)) #forall GetDuration() == 0 ...
                item.SetReportToServer(True)
                item.SetAddToHistory(True)
                if item.GetProperty("replacedPath") == "0":
                    item.SetProperty("replacedPath", "1")
                    item.SetPath(str(mediaPath))
    BPTraceExit()
                
def AddDirectPath(item, mediaNodes, label, title, thumbnailPath):
    BPTraceEnter("%s, %s, %s, %s, %s" % (item, mediaNodes, label, title, thumbnailPath))
    for mediaNode in mediaNodes:
        mediaLabel = GetElementData(mediaNode, "svtplay:videoIdentifier")
        mediaPath = mediaNode.getAttribute("url").encode("utf-8")
        mediaType = mediaNode.getAttribute("type").encode("utf-8")
        if mediaLabel == label:
			item.AddAlternativePath(title, mediaPath, mediaType, thumbnailPath) 
			try:
				duration =  int(mediaNode.getAttribute("duration").encode("utf-8"))
			except:
				duration = 0
			if duration > 0:
				item.SetDuration(duration)
                                item.SetProperty("duration", str(duration)) #forall GetDuration() == 0 ...
			item.SetReportToServer(True)
			item.SetAddToHistory(True)
			if item.GetProperty("replacedPath") == "0":
				item.SetProperty("replacedPath", "1")
				item.SetPath(str(mediaPath))
				item.SetContentType(mediaType)
    BPTraceExit()

def RetrieveXmlStream(url):
    BPTraceEnter(url)
    try:
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        data = response.read()
        response.close()
        root = xml.dom.minidom.parseString(data)
        BPTraceExit("Returning %s" % root)
        return root
    except:
        root = xml.dom.minidom.parseString("<error>error</error>")
        BPLog("svtxml: http download failed, url=%s" % url, Level.ERROR)
        BPTraceExit("Returning %s" % root)
        return  root

def GetElementData(node, name):
    #BPTraceEnter("%s, %s" % (node, name))
    try:
        #BPTraceExit()
        return node.getElementsByTagName(name)[0].childNodes[0].data.encode("utf-8")
    except:
        #BPTraceExit()
        return str("")

def GetElementAttribute(node, name, attribute):
    #BPTraceEnter("%s, %s, %s" % (node, name, attribute))
    try:
        #BPTraceExit()
        return node.getElementsByTagName(name)[0].getAttribute(attribute).encode("utf-8")
    except:
        #BPTraceExit()
        return str("")

def LookupCategory(id):
    BPTraceEnter(id)
    if (id == "96240"):
        r = "Barn"
    elif (id == "96242"):
        r = "Film"
    elif (id == "96247"):
        r = "Drama"
    elif (id == "96243"):
        r = "Kultur"
    elif (id == "96245"):
        r = "Nöje"
    elif (id == "96246"):
        r = "Samhälle"
    elif (id == "96241"):
        r = "Fakta"
    elif (id == "96244"):
        r = "Nyheter"
    elif (id == "96248"):
        r = "Sport"
    elif (id == "98382"):
        r = "Öppet arkiv"
    else:
        r = "Okänd (" + str(id) + ")"
    BPTraceExit("Returning %s" % r)
    return r
        
def SetDate(item, node):
    BPTraceEnter("%s, %s" % (item, node))
    try:
        dateString = GetElementData(node, "pubDate")
        dayString = dateString[0:3]
        day = dateString[5:7]
        monthString = dateString[8:11]
        year = dateString[12:16]

        dayNrMap   = { "Mon" : 0
                     , "Tue" : 1
                     , "Wed" : 2
                     , "Thu" : 3
                     , "Fri" : 4
                     , "Sat" : 5
                     , "Sun" : 6
                     }

        daySEMap   = ["måndag"
                     ,"tisdag"
                     ,"onsdag"
                     ,"torsdag"
                     ,"fredag"
                     ,"lördag"
                     ,"söndag"
                     ]

        monthNrMap = { "Jan" : 1
                     , "Feb" : 2
                     , "Mar" : 3
                     , "Apr" : 4
                     , "May" : 5
                     , "Jun" : 6
                     , "Jul" : 7
                     , "Aug" : 8
                     , "Sep" : 9
                     , "Oct" : 10
                     , "Nov" : 11
                     , "Dec" : 12
                     }

        monthSEMap = ["undefined"
                     ,"januari"
                     ,"februari"
                     ,"mars"
                     ,"april"
                     ,"maj"
                     ,"juni"
                     ,"juli"
                     ,"augusti"
                     ,"september"
                     ,"oktober"
                     ,"november"
                     ,"december"
                     ]

        item.SetDate(int(year), monthNrMap[monthString], int(day))
        
        try:
            hour = dateString[17:19]
            minute = dateString[20:22]
            second = dateString[23:25]
            tstruct = time.struct_time((int(year)
                                      , monthNrMap[monthString]
                                      , int(day)
                                      , int(hour)
                                      , int(minute)
                                      , int(second)
                                      , dayNrMap[dayString]
                                      , 0
                                      , -1
                                      ))
            t = calendar.timegm(tstruct)
            lt = time.localtime(t)
       
            
            #Fulhack för GUI -.-
            #Format: "Sändes måndag den 2 april, 17:30"
            item.SetProperty("airtime-se","Sändes %s den %d %s, %02d:%02d"
                %(daySEMap[lt.tm_wday], lt.tm_mday, monthSEMap[lt.tm_mon], lt.tm_hour, lt.tm_min))
        except Exception, e:
            BPLog("svtxml: Failed to set GUI air date. Exception: %s" %e, Level.ERROR)
    except Exception, e:
        BPLog("svtxml: Failed to set item date. Exception: %s" %e ,Level.ERROR)
    BPTraceExit()

def SetGuiInfo(item):
    BPTraceEnter()
    try:
        info = ""
        airtime = item.GetProperty("airtime-se")
        if len(airtime) > 0:
            info += airtime + '\n'
        cat = item.GetGenre()
        chan = item.GetProviderSource()
        if len(cat) > 0:
            info += "Kategori: %s" %cat
            if len(chan) > 0:
                info += ", "
        if len(chan) > 0:
            info += "Kanal: %s" %chan
        if len(cat) or len(chan):
            info += '\n'
        dur = item.GetProperty("duration")
        if len(dur) > 0:
            info += "Längd: %s minuter" %(int(dur)//60)
        item.SetStudio(info)
    except Exception, e:
        BPLog("svtxml: Could not set GUI info, Exception: %s" %e, Level.ERROR)
    BPTraceExit()
