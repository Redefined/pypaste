#!/usr/bin/python
# Python file to monitor pastebin for pastes containing the passed regex
# Eventually this should be run by nagios every 5 mins

### TODO
### 1. allow more than one searchterm
### 2. implement exit codes (to be used as a nagios check)
### 3. implement distinct alert destinations based on each searchterm via config file sections
### 4. scrape other pastebin-like sites, as well as twitter(privatepaste.com, pastie.org, etc.)
### 5. best value would be to be able to use the search function of each site and scrape results (pastebin: http://pastebin.com/search?cx=partner-pub-7089230323117142%3A2864958357&cof=FORID%3A10&ie=UTF-8&q=lolwut&sa.x=-1284&sa.y=-33&sa=Search)
### 6. debug mode (which determines how verbose this crap gets, since nagios only needs an exit code [0,1,2,3,4] and a short status text); example  debug(0-nagios mode, 1-cli mode, 2-verbose mode like now)

import sys
import time
import urllib.request, urllib.parse, urllib.error
import re
import configparser
import argparse


###
# UTILITY FUNCTIONS SECTION
###
def debug(message):
    if args.debug:
        print("[DEBUG]: !" + message + "!")
        return
    else:
        return


def info(message):
    print("[INFO]: " + message)


def warn(message):
    print("[WARN]: " + message)


def crit(message):
    print("[CRIT]: " + message + " ... Bailing out ...")


def checkconfigfile():
    # sanity check for the existence of the config file
    if args.config != "":
        path = args.config
    else:
        path = "pypaste.cfg"  # defaults to this file in the same folder as the script
    try:
        tmpfile = open(path)
    except IOError as e:
        crit("cannot open configuration file ")
        debug("Opening the config file failed")
        sys.exit(e)
    if tmpfile:
        info("found config file: " + path)
        debug("Config file exists and we can open it")
        return tmpfile


def init_config():
    global config, args
    config = configparser.ConfigParser()
    config.read(args.config)
    return config


def checkconfig_value(val, config):
    debug("Testing configuration file critical keys...for key: " + val)
    found = False
    for section in config.sections():
        if config.has_option(section, val):
            found = True
    if not found:
        crit("one of the critical keys was not present in the config file: %s" % val)
        debug("\t%s value not found" % val)
        return False
    else:
        return True


def checkconfig_siteurls(site, config):
    url_list = [config.get(site, 'latest_url'), config.get(site, 'trends_now_url'), config.get(site, 'trends_week_url'),
                config.get(site, 'trends_month_url'), config.get(site, 'trends_year_url'),
                config.get(site, 'trends_all_url')]
    return url_list


def checkconfig_searchterms(config):
    searchterm_list = []
    for option in config.options('search'):
        searchterm_list.append(config.get('search', option)
    return searchterm_list

###
# SITE-SPECIFIC FUNCTIONS
###

def search_raw(needle, haystack, linkid):
    if re.search(r'' + needle, haystack):
        info('\t *** FOUND \'' + needle + '\' in link ' + linkid + '\n')


def read_site(url, matchstr, paste_ids_position):
    raw_paste = ''
    link_id = ''
    info('read_site() got called with url: ' + url)
    try:
        info("we're in the try open url block")
        lnk = urllib.request.urlopen(url)
        htm = lnk.read()
        lnk.close()
        htm_lines = htm.split('\n')
        for line in htm_lines:
            if re.search(matchstr, line):
                link_id = line[paste_ids_position]
                info('Link_id: ' + link_id)
                if re.search('pastebin', url):
                    info('we\'re on pastebin.com')
                    url_2 = urllib.request.urlopen("http://pastebin.com/raw.php?i=" + link_id)
                else:
                    url_2 = urllib.request.urlopen("http://pastie.org/pastes/" + link_id + "/text")
                raw_paste = url_2.read()
                url_2.close()
    except IOError:
        print("can\'t connect to url: %s" % url)
    return raw_paste, link_id


if __name__ == "__main__":
    global args, regex_weblink_string, paste_ids_position
    argparser = argparse.ArgumentParser(description='Pastebin&Co. string checker script')
    argparser.add_argument('-c', '--config', type=str, default='pypaste.cfg',
                           help='/path/to/config.cfg ; it defaults to \'pypaste.cfg\' in the same path as the script')
    argparser.add_argument('-d', '--debug', default=False, action='store_true',
                           help='Debug mode(1=True, 0=False), defaults to False')
    argparser.add_argument('-s', '--searchterm', type=str,
                           help='the search term you want to look for on these paste sites')
    args = argparser.parse_args()
    if not checkconfigfile():
        exit(2)
    cfg = init_config()

    if args.searchterm and not args.config:  # if you only specify -searchterm and don't specify explicitly a config file it means you want only that term searched, ignoring rest of terms in config.
        search_term = args.searchterm
        cliterm = True  # using this to let the logic know to only compare this to raw text, and not cycle through a bunch of terms expected from config.

    checkconfig_value('dryrun', config)
    checkconfig_value('debug', config)
    srch_terms = ''
    if not (args.searchterm or checkconfig_value('term1',
                                                 config): #  we should have at least one search term either coming from the config file or the command line, otherwise bail with crit exit(2)
        crit('no search terms specified')
    else:
        info('search terms are:')
        srch_terms = checkconfig_searchterms(config)
        for term in srch_terms:
            info('\t' + term)
    dryrun = config.get('system', 'dryrun')
    info('dryrun is: ' + dryrun)

    # main loop basically
    print('entered main loop')
    for url in checkconfig_siteurls('pastebin', config):
        time.sleep(10)
        info('main loop url read from config: ' + url)
        paste_ids_position = config.get('pastebin', 'paste_ids_position')
        matchstrings = '\'' + config.get('pastebin',
                                         'paste_ids_match_string') + '\''  # shit like '<td><img src=\"/i/t.gif\"  class=\"i_p0\" alt=\"\" border=\"0\" /><a href=\"/[0-9a-zA-Z]{8}">.*</a></td>' from config, site dependent, obviously
        raw, linkid = read_site(url, matchstrings, paste_ids_position)
        time.sleep(2)
        for item in srch_terms:
            search_raw(item, raw, linkid)
