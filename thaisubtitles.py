from cStringIO import StringIO
from urlparse import urljoin
import xml.etree.ElementTree as et
import string
import sys
import ElementSoup
import re
import urllib2
import urllib
from BeautifulSoup import BeautifulSoup

try:
    import xbmc
    DEBUG = False
except:
    DEBUG = False

MAIN_URL = "http://www.thaisubtitle.com"


def log(msg, lvel):
    pass


def prepare_search_string(s):
    s = string.strip(s)
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title
    return s


def geturl(url):
    log(__name__, "Getting url: %s" % url)
    try:
        response = urllib2.urlopen(url)
        content = response.read()
        #Fix non-unicode characters in movie titles
        strip_unicode = re.compile("([^-_a-zA-Z0-9!@#%&=,/'\";:~`\$\^\*\(\)\+\[\]\.\{\}\|\?<>\\]+|[^\s]+)")
        content = strip_unicode.sub('', content)
        return_url = response.geturl()
    except:
        log(__name__, "Failed to get url: %s" % url)
        content = None
        return_url = None
    return content, return_url


def search_movie(title, year, languages, filename):
    title = string.strip(title)
    search_string = prepare_search_string(title)

    log(__name__, "Search movie = %s" % search_string)
    url = MAIN_URL + "manage/search.php?movie_name=" + urllib.quote_plus(search_string)
    content, response_url = geturl(url)

    if content is not None:
        log(__name__, "Multiple movies found, searching for the right one ...")
        subspage_url = find_movie(content, title, year)
        if subspage_url is not None:
            log(__name__, "Movie found in list, getting subs ...")
            url = MAIN_URL + subspage_url
            content, response_url = geturl(url)
            if content is not None:
                getallsubs(content, languages, filename)
        else:
            log(__name__, "Movie not found in list: %s" % title)
            if string.find(string.lower(title), "&") > -1:
                title = string.replace(title, "&", "and")
                log(__name__, "Trying searching with replacing '&' to 'and': %s" % title)
                subspage_url = find_movie(content, title, year)
                if subspage_url is not None:
                    log(__name__, "Movie found in list, getting subs ...")
                    url = MAIN_URL + subspage_url
                    content, response_url = geturl(url)
                    if content is not None:
                        getallsubs(content, languages, filename)
                else:
                    log(__name__, "Movie not found in list: %s" % title)


def search_tvshow(tvshow, season, episode, languages, filename):
    tvshow = string.strip(tvshow)
    search_string = prepare_search_string(tvshow)
    search_string += " - " + seasons[int(season)] + " Season"

    log(__name__, "Search tvshow = %s" % search_string)
    url = MAIN_URL + "/subtitles/title?q=" + urllib.quote_plus(search_string) + '&r=true'
    content, response_url = geturl(url)

    if content is not None:
        log(__name__, "Multiple tv show seasons found, searching for the right one ...")
        tv_show_seasonurl = find_tv_show_season(content, tvshow, seasons[int(season)])
        if tv_show_seasonurl is not None:
            log(__name__, "Tv show season found in list, getting subs ...")
            url = MAIN_URL + tv_show_seasonurl
            content, response_url = geturl(url)
            if content is not None:
                search_string = "s%#02de%#02d" % (int(season), int(episode))
                getallsubs(content, languages, filename, search_string)


def search_manual(searchstr, languages, filename):
    search_string = prepare_search_string(searchstr)
    url = MAIN_URL + "/manage/search.php?movie_name=" + urllib.quote_plus(search_string)
    if DEBUG:
        content = open("test.html").read()
    else:
        content, response_url = geturl(url)

    if content is not None:
        return getallsubs(content, languages, filename)


def getallsubs(content, allowed_languages, filename="", search_string=""):

    #parser = HTMLParser()
#    parser = et.XMLParser(html=1)
#    html = et.fromstring(content, parser).getroot()
#    html = ElementSoup.parse(StringIO(content))

    soup = BeautifulSoup(content)
    #elements = html.findall(".//tr[./td/a/img[@title='Download Thai Subtitle']]")

    subtitles = []
    sub_list = soup.fetch("div", dict(id="subtitle_list"))
    if not sub_list:
        return []
    table = sub_list[0].fetch("table")[0]
    if table is None:
        return []

    for element in table.findAll("tr")[1:]:
        num, title, rating, translate, upload, download = element.findAll("td")
        subtitle_name = title.find('br').previousSibling.strip().strip(" [En]")
        rating = int(float(rating.getText().strip('%'))/100.0*5)
        th_link = download.fetch("img",{'title':'Download Thai Subtitle'})[0].parent['href']
        th_link = urljoin(MAIN_URL + "/manage/", th_link)
        en_link = download.fetch("img",{'title':'Download English Subtitle'})[0].parent['href']
        en_link = urljoin(MAIN_URL + "/manage/", en_link)
        th_code = ("Thai", "0", "th", "tha", "41", 30243)
        en_code = ("English", "2", "en", "eng", "11", 30212)

        sync = False
        if filename != "" and string.lower(filename) == string.lower(subtitle_name):
            sync = True

        for code, link in [(th_code, th_link), (en_code, en_link)]:
            lang_name, _, let2, let3, _, _  = code
            if let3 in allowed_languages:
                lang = {'name': lang_name, '2let': let2, '3let': let3}

                subtitles.append({'rating': str(rating),
                                  'filename': subtitle_name,
                                  'sync': sync,
                                  'link': link,
                                  'lang': lang,
                                  'hearing_imp': False})

#    subtitles.sort(key=lambda x: [not x['sync']])
    return subtitles

if __name__ == "__main__":
    print search_manual(sys.argv[1], "tha", sys.argv[2])
