#! /usr/local/bin/python3
# coding=utf-8
#
# -----------------------------------------------------------------------------
#   file:       fandango_soup.py
#   use:
#
#   author:     dpomondo
#   site:       
# -----------------------------------------------------------------------------

import requests
from bs4 import BeautifulSoup as bs

targs = ["http://www.fandango.com/80521_movietimes",
         "http://www.fandango.com/80521_movietimes?pn=2"
         ]


def main(targets=targs):
    res = {}
    for t in targets:
        r = requests.get(t)
        soup = bs(r.text, "lxml")
        theaters = soup.find_all("div",
                                 itemtype="http://schema.org/MovieTheater")
        for th in theaters:
            name = th.find("meta", itemprop="name")["content"]
            #  res[nam] = {}
            dic = {}
            movies = th.find_all("span",
                                 itemtype="http://schema.org/TheaterEvent")
            for m in movies:
                nam = m.find("meta", itemprop="name")["content"]
                temp = m.find_all("meta", itemprop="startDate")
                dic[nam] = []
                for t in temp:
                    dic[nam].append(t["content"])
            res[name] = dic
    return res


if __name__ == '__main__':
    thunder = main()
    for th in thunder.keys():
        print(th)
        for m in thunder[th].keys():
            print('\t', m, thunder[th][m])
