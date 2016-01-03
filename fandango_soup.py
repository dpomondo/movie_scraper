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


def get_colors(color_flag=True):
    """ Return object with color information.
    """
    class Colors:
        pass
    colors = Colors()
    # # else:
    #     # https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    #     # \033[_;__;__m     --> first:  character effect
    #     #                       second: foreground color
    #     #                       third:  background color
    #     # \033[38;5;___m    --> extended foreground color (0...255)
    #     # \033[48;5;___m    --> extended background color (0...255)
    color_info = {'bold':   "\033[1m",
                  'italic': "\033[3m",
                  #  'temp':   "\033[1;34;47m",
                  #  'wind':   "\033[38;5;199m\033[48;5;157m",
                  #  'high':   "\033[1;34;47m",
                  'early':   "\033[1;34;47m",
                  #  'low':    "\033[1;34;47m",
                  #  'cond':   "\033[3;36;47m",
                  'clear':  "\033[0m",
                  #  'hot':    "\033[38;5;160m\033[48;5;007m",
                  #  'cool':   "\033[38;5;020m\033[48;5;155m",
                  #  'night':  "\033[38;5;015m\033[48;5;017m",
                  #  'dusk':   "\033[38;5;015m\033[48;5;020m",
                  #  'dawn':   "\033[38;5;000m\033[48;5;172m",
                  #  'day':    "\033[38;5;000m\033[48;5;226m",
                  #  'cloud25':    "\033[38;5;015m\033[48;5;012m",
                  'hour':    "\033[38;5;015m\033[48;5;012m",
                  #  'cloud50':    "\033[38;5;015m\033[48;5;067m",
                  #  'cloud75':    "\033[38;5;015m\033[48;5;246m",
                  #  'cloud100':   "\033[38;5;018m\033[48;5;255m",
                  #  'precip25':   "\033[38;5;232m\033[48;5;255m",
                  #  'precip50':   "\033[38;5;238m\033[48;5;255m",
                  #  'precip75':   "\033[38;5;250m\033[48;5;232m",
                  #  'precip100':  "\033[38;5;255m\033[48;5;232m",
                  'grey_background': "\033[38;5;233m\033[48;5;251m"
                  }
    for key in color_info.keys():
        if color_flag is True:
            setattr(colors, key, color_info[key])
        elif color_flag is False:
            setattr(colors, key, '')
        else:
            raise KeyError("color_flag is unset")
    return colors


def today_formatted():
    today = datetime.date.today()
    return today.strftime("%b_%d_%y")


def parse_weird_fandango_date(dt):
    # dammit fandango, whats with the colon!
    # here we have the format string WITH timezone
    #  dt_n = dt[:-3] + dt[-2:]
    #  frmt = "%Y-%m-%dT%H:%M:%S%z"
    # here we have the format string WITHOUT timezone
    dt_n = dt.rsplit('-', 1)[0]
    frmt = "%Y-%m-%dT%H:%M:%S"
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
    COLOR = get_colors()
    now = datetime.datetime.today()
    soon = now + datetime.timedelta(hours=1)
    for th in results.keys():
        print('-' * 70)
        print(th)
        for m in results[th].keys():
            #  times = map(lambda x: x.strftime("%I:%M %p"), results[th][m])

            times_raw = results[th][m]
            times = []
            for tm in times_raw:
                t = tm.replace(tzinfo=None)
                if t < now:
                    c = COLOR.early + COLOR.italic
                elif t < soon:
                    c = COLOR.hour
                else:
                    c = COLOR.clear
                times.append("{}{}{}".format(c,
                                             t.strftime("%I:%M %p"),
                                             COLOR.clear))
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
