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
import datetime
from bs4 import BeautifulSoup as bs


def parse_weird_fandango_date(dt):
    frmt = "%Y-%m-%dT%H:%M:%S-07:00"
    return datetime.datetime.strptime(dt, frmt)


def do_the_work(targets):
    res = {}
    for t in targets:
        try:
            r = requests.get(t)
        except requests.exceptions.RequestException as e:
            raise e
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
                    dic[nam].append(parse_weird_fandango_date(t["content"]))
            res[name] = dic
    return res


def printer(results):
    for th in results.keys():
        print('-' * 70)
        print(th)
        for m in results[th].keys():
            times = map(lambda x: x.strftime("%I:%M %p"), results[th][m])
            res = "\t{}:".format(m)
            for t in times:
                res = "{} {}".format(res, t)
            print(res)
            #  print('\t', m, times)
        print()


def main():
    targs = ["http://www.fandango.com/80521_movietimes",
             "http://www.fandango.com/80521_movietimes?pn=2"
             ]
    res = do_the_work(targs)
    return res


if __name__ == '__main__':
    thunder = main()
    printer(thunder)
