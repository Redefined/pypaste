#!/usr/bin/python
# Python file to monitor pastebin for pastes containing the passed regex
# Eventually this should be run by nagios every 5 mins

### TODO
### 1. allow more than one searchterm
### 2. implement exit codes (to be used as a nagios check)
### 3. implement distinct alert destinations based on each searchterm via config file sections
### 4. scrape other pastebin-like sites, as well as twitter(privatepaste.com, pastie.org, 
### 5. best value would be to be able to use the search function of each site and scrape results (pastebin: http://pastebin.com/search?cx=partner-pub-7089230323117142%3A2864958357&cof=FORID%3A10&ie=UTF-8&q=lolwut&sa.x=-1284&sa.y=-33&sa=Search)
### 6. debug mode (which determines how verbose this crap gets, since nagios only needs an exit code [0,1,2,3,4] and a short status text); example  debug(0-nagios mode, 1-cli mode, 2-verbose mode like now)

import sys
import time
import urllib
import re

# User-defined variables
time_between = 7       #Seconds between iterations (not including time used to fetch pages - setting below 5s may cause a pastebin IP block, too high may miss pasties)
error_on_cl_args = "Please provide a single regex search via the command line"   #Error to display if improper command line arguments are provided
archive_url = "http://pastebin.com/archive"    #whether you wanna scan the normal archive (you're lucky to grab the latest 10 minutes worth of pasties)
trending_url = "http://pastebin.com/trends"    #best to scan is the trending pasties page, since you can see the most 'popular' stuff which is more important anyway.
# Check for command line argument (a single regex)
if len(sys.argv) != 1:
    search_term = sys.argv[1]
else:
    print error_on_cl_args
    exit()

iterater = 1

counter = 0
print "This shoul be run once every 5-10 minutes, so we don't get IP-banned by pastebin"

#Open the recently posted pastes page
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
        	    if re.search(r''+search_term, raw_text):
        		print "\n !!!FOUND a reference to '" + search_term + "' in http://pastebin.com/raw.php?i=" + link_id + "\n"
        	    
        	    counter += 1
except(IOError):
	print "can't connect, haz you got networkz?"
except:
	print "Fatal exception. Bailing out..."
