import re
import os
import string
import urllib
import glob
import time
import logging
from moviepy.editor import *
import moviepy.video.fx.all as vfx

import conf
import dblog

# selfie consts
SELFIE_WIDTH = 1280
SELFIE_HEIGHT = 720
SELFIE_CODEC = 'mpeg4'
SELFIE_EXT = 'mp4'

def selfieName( url ):
    """
    Converts a URL into an appropriate filename for saving (no extension)
    """
    # parse the URL, strip the scheme and divide the segments
    parsed = urllib.parse.urlparse( url )
    tmpStr = parsed.netloc + '-' + parsed.path + '-' + parsed.params + '-' + parsed.query
    tmpStr = urllib.parse.unquote_plus( tmpStr )

    # remove undesireable characters
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join( c for c in tmpStr if c in valid_chars )

    # replace all whitespace with hyphens
    filename = filename.replace( ' ', '-' )

    # trim down repeated hyphens
    return re.sub( r'(\-)\1+', r'\1', filename.rstrip( '-' ) )

def takeSelfie( db, url ):
    """
    Captures a screenshot of the browser, the url is what was sent to handleUrl(),
    thus the browser may have fired an action handler, so we shouldn't expect a screenshot
    to always be the same as browser.get(url).
    """
    # build a unique filename for this running instance
    filename = '%s-%s.png' % ( time.time( ), selfieName( url ) )

    # determine where we are putting these selfies
    dir = db.getConf( conf.conf.OPTIONS, conf.conf.OPTION_SELFIES_DIR )

    # ensure this directory actually exists
    if not os.path.isdir( dir ):
        os.makedirs( dir )

    # ensure we're only working with an absolute path here
    dir = os.path.abspath( dir )

    # put them together and what do we get? a nice consistent dir of filenames with timestamps
    # that can be scanned and used as frames in a movie / sequence
    fileFull = dir + '/' + filename
    if db.browser( ).get_screenshot_as_file( fileFull ):
        dblog.log( 'selfie', 'Saved [ %s ]' % fileFull )
    else:
        dblog.log( 'selfie', 'Failed to save [ %s ]' % fileFull, level = logging.WARNING )

def compileSelfies( dir, filenameNoExt ):
    """
    Concat *.png images in dir to create a 1-sec-per-url/frame movie
    with the output being the filename (+ the extension). Cropping is handled
    """
    # load all selfie files in order
    selfies = glob.glob( dir.rstrip( '/' ) + '/*.png' )
    clip = ImageSequenceClip( selfies, fps = 1 )

    # build frame array
    frames = [ ]
    for frame in clip.iter_frames( fps = 1, dtype = "uint8" ):
        frames.append( frame )

    # helper func for VideoClip
    def make_frame( t ):
        return frames[ int( t ) ]

    # recreate the video by loading the RGB arrays through make_frame, and then crop to our movie size
    durSec = len( selfies )
    vclip = VideoClip( make_frame, duration =durSec  ).fx( vfx.crop, x2 = SELFIE_WIDTH, y2 = SELFIE_HEIGHT )

    # set filename and codec and write out the movie
    filename = filenameNoExt + '.' + SELFIE_EXT
    vclip.write_videofile( filename = filename, codec = SELFIE_CODEC, fps = 1 )

    return os.path.abspath( filename )