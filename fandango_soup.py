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
import os
import shelve
from bs4 import BeautifulSoup as bs


def today_formatted():
    today = datetime.date.today()
    return today.strftime("%b_%d_%y")


def parse_weird_fandango_date(dt):
    # dammit fandango, whats with the colon!
    dt_n = dt[:-3] + dt[-2:]
    frmt = "%Y-%m-%dT%H:%M:%S%z"
    return datetime.datetime.strptime(dt_n, frmt)


def get_html(targets):
    try:
        r = requests.get(targets)
    except requests.exceptions.RequestException as e:
        raise e
    if r is None:
        raise requests.exceptions.ConnectionError("no response from server")
    soup = bs(r.text, "lxml")
    next_links = soup.find_all("link", rel="next")
    return soup, list(map(lambda x: x["href"], next_links))


def do_the_work(soup):
    res = {}
    theaters = soup.find_all("div",
                             itemtype="http://schema.org/MovieTheater")
    if theaters is None:
        raise AttributeError("No theaters found")
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


def main(zips, verbose=False):
    res = {}
    targs = []
    if isinstance(zips, str):
        zips = [zips]
    for z in zips:
        assert isinstance(z, str)
        assert len(z) == 5
        assert z.isdecimal()
    # check the db file:
    if not os.path.exists(os.path.join(os.curdir, '.db')):
        os.mkdir('.db')
    db_target = os.path.join(os.curdir, '.db',
                             "{}.db".format(today_formatted()))
    if verbose:
        print("trying to open {}".format(db_target))
    try:
        db = shelve.open(db_target)
        #  with shelve.open(db_target) as db:
        for z in zips:
            if z in db.keys():
                if verbose:
                    print("reading {} from database...".format(z))
                for key in db[z].keys():
                    res[key] = db[z][key]
            else:
                targs.append("http://www.fandango.com/{}_movietimes".format(z))
                # add new zip code to db:
                #  db[z] = {}
                #  assert z in db.keys()
                while targs:
                    if verbose:
                        print("getting html from {}".format(targs[0]))
                    soup, new_targs = get_html(targs[0])
                    temp = do_the_work(soup)
                    if new_targs is not None:
                        targs.extend(new_targs)
                    targs = targs[1:]
                    # add the new results to the current results
                    for key in temp.keys():
                        if verbose > 2:
                            print("writing {} to {}".format(temp[key],
                                                            key))
                        res[key] = temp[key]
                db[z] = res
    # there gotta be a try/finally in there somewhere so we always hit this:
    finally:
        db.close()
    return res


if __name__ == '__main__':
    import sys
    zips = sys.argv[1:]
    #  if zips is None:
    if zips == []:
        zips = ["80521"]
    thunder = main(zips, verbose=True)
    printer(thunder)
