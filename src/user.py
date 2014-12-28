# includes
import conf
import dblog

# libs
import time
import random
import string
from datetime import datetime
import dateutil.parser

from selenium.webdriver.common.keys import Keys

class user( ):
    """
    Simulates a user through typing, pausing, and randomization
    """
    DRUNK_WPM_FACTOR = .75
    DRUNK_ERR_FACTOR = 1.5

    def __init__( self, typingWpm=conf.conf.OPTION_TYPING_WPM_DEFAULT, typingRand=conf.conf.OPTION_TYPING_ERR_DEFAULT ):
        self.typingWpm = float( typingWpm )
        self.typingRand = float( typingRand )

    def idle( self, seconds ):
        """
        Sleep for a given duration (in seconds)
        """
        time.sleep( seconds )

    def waitUntil(self, whenStr):
        startDtm = dateutil.parser.parse(str(whenStr))
        nowDtm   = datetime.now()
        diff     = (startDtm-nowDtm)
        diffSec  = round(diff.total_seconds(),0)
        if diffSec > 0:
            dblog.log('wait','Waiting %s before starting, resuming at %s' % ( diff, startDtm ) )
            self.idle( diffSec )
            dblog.log('wait','Finished waiting, target time = %s' % ( diff, startDtm ) )

    def pause( self ):
        """
        Uses 3 react()s for a semi-random pause
        """
        self.react( )
        self.react( )
        self.react( )

    def react( self ):
        """
        Sleeps for the duration of a reactionSec()
        """
        self.idle( self.reactionSec( ) )

    def reactionSec( self ):
        """
        Returns a random time between 0.1 - 0.5 seconds
        """
        random.seed( )
        return random.uniform( .1, .5 )

    def reactKeyPress( self, speed=None ):
        if not speed:
            speed = self.typingWpm
        self.idle( self.postKeyPause( speed ) )

    def perterb( self ):
        """
        Using the randomization factor, return a fuzz factor to perturb key pauses
        """
        return float( (self.typingRand / 100) * (random.choice( [ -1, 1 ] )) )

    def secPerKey( self, wpm ):
        """
        Assuming 5 chars per word, return how many seconds to wait per key press
        """
        return pow( ( ( wpm * 5 ) / 60 ), -1 )

    def postKeyPause( self, wpm ):
        """
        Returns a fuzzied duration that can be used between key presses
        to simulate typing consistent with a user's WPM
        """
        return abs( round( self.secPerKey( wpm ) + self.perterb( ), 5 ) )

    def sloppify( self, text, errRate=None ):
        """
        Given text, inject incorrect characters and `backspace` to produce a mangled string
        which when simulated with as keystrokes, matches the original text.
        """
        sloppy = ''
        if not errRate:
            errRate = self.typingRand
        for c in text:
            if ( 2 * self.reactionSec( ) ) > ( 1 - errRate ):
                sloppy += random.choice( string.ascii_letters[ :26 ] )
                sloppy += Keys.BACKSPACE
            sloppy += c
        return sloppy

    def typeKeys( self, db, inputElem, text, sloppify = True, enableDrunkRate = False ):
        """
        Types keys as if the user did it themselves, also has fuzz-factor
        """
        errRate = self.typingRand
        speedWpm = self.typingWpm
        if enableDrunkRate:
            errRate  *= self.DRUNK_ERR_FACTOR
            speedWpm *= self.DRUNK_WPM_FACTOR

        if sloppify:
            # mangle and sloppify the string to a more drunk-like string
            str = self.sloppify( text, errRate )
            # log original and sloppy text, replace unicode backspace with '\b' for easier reading in log output
            dblog.log( 'user', 'Sloppifying [ %s ] -> [ %s ]' % ( text, str.replace( Keys.BACKSPACE, '\\b' ) ) )
            text = str

        # send each character and wait a fuzzed duration
        for c in text:
            inputElem.send_keys( c )
            self.reactKeyPress( speedWpm )

    def insideDrunkTimeFrame( self ):
        """
        Returns True if within a valid "drunk" time period
        [ Friday & Saturday from 8pm - Midnight ]
        """
        dtm = datetime.now( )
        d = dtm.isoweekday( )
        t = dtm.time( )
        validDay = ( d == 5 ) or ( d == 6 )
        tsStart = datetime.now( ).replace( hour = 20, minute = 0, second = 0 )
        tsEnd   = datetime.now( ).replace( hour = 23, minute = 59, second = 59 )
        validTime = ( t > tsStart.time( ) ) and ( t < t > tsEnd.time( ) )

        return validDay and validTime