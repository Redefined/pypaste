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
import urllib
import re
import ConfigParser
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
        path = "pypaste.cfg"
    try:
        tmpfile = open(path)
    except IOError, e:
        crit("cannot open configuration file ")
        debug("Opening the config file failed")
        sys.exit(e)
    if tmpfile:
        info("found config file")
        debug("Config file exists and we can open it")
        return tmpfile


def checkconfig_value(val):
    global config
    config = ConfigParser.ConfigParser()
    config.read(args.config)
    debug("Testing configuration file critical keys...for key: " + val)
    found = False
    for section in config.sections():
        if config.has_option(section, val):
            found = True
    if found == False:
        crit("one of the critical keys was not present in the config file")
        debug("    %s value not found" % val)
        return False
        sys.exit(1)
    else:
        return True


###
#
###


if __name__ == "__main__":
    ConfigParser.RawConfigParser()
    argparser = argparse.ArgumentParser(description='Pastebin&Co. string checker script')
    argparser.add_argument('-c', '--config', type=str, default='pypaste.cfg', help='/path/to/config.cfg ; it defaults to \'pypaste.cfg\' in the same path as the script')
    argparser.add_argument('-d', '--debug', default=False, action='store_true', help='Debug mode(1=True, 0=False), defaults to False')
    argparser.add_argument('-s', '--searchterm', type=str, help='the search term you want to look for on these paste sites')
    args = argparser.parse_args()
    if not checkconfigfile():
        exit(2)

    # User-defined variables, to be moved in config file under [system] section, and urls under [pastebin.com] and so on sections.
    error_on_cl_args = "Please provide a single regex search via the command line"   # Error to display if improper command line arguments are provided
    archive_url = "http://pastebin.com/archive"    # whether you wanna scan the normal archive (you're lucky to grab the latest 10 minutes worth of pasties)
    trending_url = "http://pastebin.com/trends"    # best to scan is the trending pasties page, since you can see the most 'popular' stuff which is more important anyway.

    if args.expression and not args.config:  # if you only specify -searchterm and don't specify explicitly a config file it means you want only that term searched, ignoring rest of terms in config.
        search_term = args.expression

    dryrun = True
    counter = 0

    #Open the recently posted pastes page
    if not dryrun:
        try:
            url = urllib.urlopen(trending_url)
            html = url.read()
            url.close()
            html_lines = html.split('\n')
            for line in html_lines:
                if counter < 10:
                    if re.search(r'<td><img src=\"/i/t.gif\"  class=\"i_p0\" alt=\"\" border=\"0\" /><a href=\"/[0-9a-zA-Z]{8}">.*</a></td>', line):
                        link_id = line[72:80]
                        print "Link id: " + link_id
    
                        #Begin loading of raw paste text
                        url_2 = urllib.urlopen("http://pastebin.com/raw.php?i=" + link_id)
                        raw_text = url_2.read()
                        url_2.close()
                        print "\tLength of raw text in this pastie is: %d" % len(raw_text)
    
                        #if search_term in raw_text:
                        if re.search(r'' + search_term, raw_text):
                            print "\n !!!FOUND a reference to '" + search_term + "' in http://pastebin.com/raw.php?i=" + link_id + "\n"
    
                        counter += 1
        except(IOError):
            print "can't connect, haz you got networkz?"
        except:
            print "Fatal exception. Bailing out..."
