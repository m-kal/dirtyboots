# libs
import re
import urllib
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

import dblog

def log( text ):
    """
    For consistent logging format within all handler functions
    """
    dblog.log( 'handlers', text )

def skipUrl( db, url, matches ):
    """
    Does nothing - handler to literally do nothing at all
    """
    pass

def watchYoutube( db, url, matches ):
    """
    Visits a YouTube video and pauses for the duration of the video
    """
    db.visitUrl( url )
    # duration may not exist if the Youtube video has been taken down
    try:
        durStr = db.browser( ).find_element_by_xpath( "//meta[@itemprop='duration']" ).get_attribute( "content" )
    except NoSuchElementException:
        return

    # https://stackoverflow.com/questions/16742381/how-to-convert-youtube-api-duration-to-seconds
    ISO_8601_period_rx = re.compile(
        'P'   # designates a period
        '(?:(?P<years>\d+)Y)?'   # years
        '(?:(?P<months>\d+)M)?'  # months
        '(?:(?P<weeks>\d+)W)?'   # weeks
        '(?:(?P<days>\d+)D)?'    # days
        '(?:T' # time part must begin with a T
        '(?:(?P<hours>\d+)H)?'   # hourss
        '(?:(?P<minutes>\d+)M)?' # minutes
        '(?:(?P<seconds>\d+)S)?' # seconds
        ')?'   # end of time part
    )
    dur = ISO_8601_period_rx.match( durStr ).groupdict( )
    # wait on the page, watch it, then end
    durSec = int( dur[ 'seconds' ] or 0 )           \
             + 60 * int( dur[ 'minutes' ] or 0 )    \
             + 60 * 60 * int( dur[ 'hours' ] or 0 )

    title = db.browser().find_element_by_id('eow-title').get_attribute( "title" )
    log( 'Watching [ %s ] for %s seconds' % ( title, durSec ) )
    db.user.idle( durSec )
    log( 'Finished watching youtube' )

def searchGoogle( db, url, matches ):
    """
    Visits Google and searches manually via typeKeys
    """
    # search Google "manually"
    searchTerm = urllib.parse.unquote_plus( matches[ 0 ] )
    # remove extra query string params from regex match
    searchTerm = searchTerm.split( '&' )[ 0 ]
    log( 'Searching Google for [ %s ]' % searchTerm )
    db.user.react( )
    db.visitUrl( 'https://google.com/' )
    elem = db.browser( ).find_element_by_name( 'q' )
    db.typeKeys( elem, searchTerm )
    elem.send_keys( Keys.RETURN )
    db.user.pause( )

def searchDuckDuckGo( db, url, matches ):
    """
    Visits DuckDuckGo and searches manually via typeKeys
    """
    # search DDG "manually"
    searchTerm = urllib.parse.unquote_plus( matches[ 0 ] )
    log( 'Searching DuckDuckGo for [ %s ]' % searchTerm )
    db.user.react( )
    db.visitUrl( 'https://duckduckgo.com/' )
    elem = db.browser( ).find_element_by_name( 'q' )
    db.typeKeys( elem, searchTerm )
    elem.send_keys( Keys.RETURN )
    db.user.pause( )

# handlers array containing regex-rules -> handler associations
handlers = [
    # skip media
    ( r'(.*).(mp3|mp4|mkv|jpg|png|jpeg|gif)', skipUrl ),
    ( r'(.*).(css|js)', skipUrl ),
    # youtube
    ( r'youtube.com/watch\?v=(\w+.*)', watchYoutube ),
    # search list
    ( r'duckduckgo.com/\?q=(\w+.*)', searchDuckDuckGo ),
    ( r'duckduckgo.com/html/\?q=(\w+.*)', searchDuckDuckGo ),
    ( r'google.com/search\?q=(\w+.*)', searchGoogle )
]