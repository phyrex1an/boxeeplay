﻿#encoding:utf-8
#author:Mats Boisen
#project:boxeeplay
#repository:https://bitbucket.org/hesapesa/boxeeplay
#license:Creative Commons GNU GPL v2
# (http://creativecommons.org/license/GPL/2.0/)

import mc
from urllib import quote_plus
import tv4xml
from logger import BPLog,BPTraceEnter,BPTraceExit,Level

def GetCategories() :
    return tv4xml.GetCategories()

def GetCategoryId(item) :
    return item.GetProperty("id")

def GetTitles(id) :
    return tv4xml.GetTitles(id)

def GetTitleId(item) :
    return item.GetProperty("id")

def GetEpisodes(id) :
    return tv4xml.GetEpisodes(id, False)

def GetSamples(id) :
    return tv4xml.GetEpisodes(id, True)

def SearchEpisodes(searchTerm) :
    return tv4xml.SearchEpisodes(searchTerm, False)

def SearchSamples(searchTerm) :
    return tv4xml.SearchEpisodes(searchTerm, True)

def DumpAllEpisodes():
    BPTraceEnter()
    categories = GetCategories()
    for category in categories:
        categoryId = GetCategoryId(category)
        titles = GetTitles(categoryId)
        for title in titles:
            titleId = GetTitleId(title)
            episodes = GetEpisodes(titleId)
    BPTraceExit()

def DumpAllSamples():
    BPTraceEnter()
    categories = GetCategories()
    for category in categories:
        categoryId = GetCategoryId(category)
        titles = GetTitles(categoryId)
        for title in titles:
            titleId = GetTitleId(title)
            episodes = GetSamples(titleId)
    BPTraceExit()