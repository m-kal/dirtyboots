# libraries
import argparse
import logging
import re
import sys
import os.path
import time
import random
from datetime import *
from selenium import webdriver

# prog imports
import user
import dblog
import conf
import datamgr
import handlers
import selfies
import historian

class dirtyboots( ):
    """
    Management and execution for browsing the internet
    in a similar manner to existing browsing history
    """
    commands = {
        'initdb':   'Creates database for browsing history and stats',
        'cleardb':  'Clears existing browsing history database',
        'importdb': 'Imports a web browser\'s history',
        'config':   'Create a default configuration file',
        'run':      'Run %(prog)s',
        'txt':      'Run %(prog)s from a newline-delimited text file of urls'
    }

    # program consts
    PROG_NAME = 'dirtyboots'

    def __init__( self ):
        """
        Do argument setup / description, and execute subcommand
        """
        cmdStr = ''
        for cmd, desc in sorted( self.commands.items() ):
            cmdStr += '  %s%s\n' % ( cmd.ljust( 10, ' ' ), desc )

        parser = argparse.ArgumentParser( prog = self.PROG_NAME, description = '', usage = '''%(prog)s <command> [<args>]

The most commonly used %(prog)s commands are:

''' + cmdStr )

        parser.add_argument( 'command', help = 'Subcommand to run' )
        args = parser.parse_args( sys.argv[ 1:2 ] )
        if ( not hasattr( self, args.command ) ) or ( args.command not in self.commands.keys() ):
            print( 'Unrecognized command' )
            parser.print_help( )
            exit( 1 )

        # setup our default member vars
        self.user = user.user( )
        self.processedUrls = { }
        self.historian = historian.historian( self )
        self.configParser = conf.conf( ).genDefault( )
        self.txtFile = False
        self.skipHandling = False
        self.browsers = { }
        self.urllist = [ ]
        self.blacklist = [ ]
        self.whitelist = [ ]
        self.stats = {
            'tick': datetime.now( ),
            'tock': None,
            'visited': 0,
            'skipped': 0,
            'handled': 0
        }

        # use CLI command == function name, use it
        getattr( self, args.command )( )

    # Top Level Commands
    def initdb( self ):
        """
        Creates database for browsing history and stats
        """
        parser = argparse.ArgumentParser( description = 'Creates database for browsing history and stats',
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                          usage = '%(prog)s init' )
        self.addConfigParserArgs( parser )
        self.addLocationParserArgs( parser )
        self.addLogParserArgs( parser )
        args = self.parseAndMergeArgs( parser )
        self.dataMgr.initDb( args.location )
        self.shutdown( )

    def importdb( self ):
        """
        Import database for browsing history and stats
        """
        c = conf.conf
        parser = argparse.ArgumentParser( description = 'Import database for browsing history and stats',
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                          usage = '%(prog)s importdb [database]' )
        parser.add_argument( 'database', action = 'store', help = 'Browser database file (places.sqlite/History)' )
        parser.add_argument( '--browser', action = 'store', choices = [ 'firefox', 'chrome' ],
                             help = 'Browser database type', default = c.OPTION_DEFAULT_BROWSER_DEFAULT )
        self.addConfigParserArgs( parser )
        self.addLocationParserArgs( parser )
        self.addLogParserArgs( parser )
        args = self.parseAndMergeArgs( parser )
        self.dataMgr.openDb( self.getConf( c.OPTIONS, c.OPTION_HISTORY_DB ) )
        self.dataMgr.importDatabase( args.browser, args.database )
        self.shutdown( )

    def cleardb( self ):
        """
        Clears existing browsing history database
        """
        parser = argparse.ArgumentParser( description = 'Clears existing browsing history database',
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                          usage = '%(prog)s clear' )
        self.addConfigParserArgs( parser )
        self.addLocationParserArgs( parser )
        self.addLogParserArgs( parser )
        args = self.parseAndMergeArgs( parser )
        self.dataMgr.clearDb( args.location )
        self.shutdown( )

    def config( self ):
        """
        Create a config file with default values
        """
        parser = argparse.ArgumentParser( description = 'Create a config file with default values',
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                          usage = '%(prog)s config' )
        self.addConfigParserArgs( parser )
        self.addLogParserArgs( parser )
        args = self.parseAndMergeArgs( parser )
        conf.conf( ).initConf( args.config )
        print( 'Generated default configuration file: %s' % args.config )

    def txt( self ):
        """
        Browse the internet similar to run(), except do not use the history database,
        load from a flat text file
        """
        # save time and effort by just setting a flag and piggy-backing off of run()
        self.txtFile = True

        # hand-off to the main function
        self.run( )

    def run( self ):
        """
        Browse the internet in a similar manner to the history database
        """
        # handle all the arg setup / parsing
        parser = argparse.ArgumentParser( description = 'Launch cruise-control for websites',
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter,
                                          usage = '%(prog)s run' if not self.txtFile else '%(prog)s txt [txtFile]')
        self.addConfigParserArgs( parser )
        self.addLocationParserArgs( parser )
        self.addRunParserArgs( parser )
        self.addLogParserArgs( parser )
        args = self.parseAndMergeArgs( parser )
        self.skipHandling = args.skip_urls

        # setup data manager and browser
        self.runBootstrap( )

        if self.txtFile:
            self.urllist = self.loadList( args.txtFile )

        # wait until out start dtm
        self.user.waitUntil( args.start )

        # begin magic
        # self.urlHistory( )
        # self.urlHistory( '%duckduckgo.com/%' )
        self.simulateRealtime( )

        # memories to last a lifetime
        if self.getConf( conf.conf.OPTIONS, conf.conf.OPTION_SELFIES ) == 'True':
            dir = self.getConf( conf.conf.OPTIONS, conf.conf.OPTION_SELFIES_DIR )
            nameNoExt = '%s-selfies' % str( time.time( ) ).split( '.' )[ 0 ]
            outputFileName = selfies.compileSelfies( dir, nameNoExt )
            dblog.log( 'selfie', 'Compiled selfie movie at [ %s ]' % outputFileName )

        # Shuuuut iiit doooooown
        self.shutdown( )

    def runBootstrap( self ):
        """
        Setup configs, args, users, and browsers based on CLI args and .conf files
        """
        c = conf.conf

        # load white/black lists
        self.loadLists( )

        # load database with data manager
        self.dataMgr.openDb( self.getConf( c.OPTIONS, c.OPTION_HISTORY_DB ) )

        # set the browser
        self.setBrowser( self.getConf( c.OPTIONS, c.OPTION_DEFAULT_BROWSER ) )

    def shutdown( self ):
        """
        Close the active browsers and shut down database connections
        """
        self.stats[ 'tock' ] = datetime.now( )
        for browserStr in self.browsers:
            self.browser( browserStr ).quit( )
        self.dataMgr.closeConn( )

        # debugging purposes
        # dblog.logSandwich( 'visited/handled urls' )
        # self.dumpProcessedUrls( )

        # starting line / bread + gooey stat center / meat + bread again
        dblog.logSandwich( 'stats' )
        self.logStats( )
        dblog.logBread( )

        # time to exit, make it so!
        logging.shutdown( )

    # Shared Argument Functions
    def addLocationParserArgs( self, parser ):
        """
        Add history database file location CLI arguments
        """
        parser.add_argument( '--location', action = 'store', help = 'Location of the %(prog)s database',
                             default = conf.conf.OPTION_HISTORY_DB_DEFAULT )

    def addConfigParserArgs( self, parser ):
        """
        Add configuration file location CLI arguments
        """
        parser.add_argument( '--config', action = 'store', help = 'Name of the config file',
                             default = conf.conf.FILENAME_DEFAULT )

    def addLogParserArgs( self, parser ):
        """
        Add the logging level and file location CLI arguments
        """
        parser.add_argument( '--log', action = 'store', help = 'Log file location', default = False )
        parser.add_argument( '--level', action = 'store', choices = [ 'debug', 'info', 'warning', 'error', 'critical' ],
                             help = 'Logging level', default = 'info' )
        parser.add_argument( '--no-ts', action = 'store_true', help = 'Disable timestamps during logging',
                             default = False )
        parser.add_argument( '--log-mode', action = 'store', choices = [ 'w', 'a' ],
                             help = 'Which mode to open log files with', default = 'a' )

    def addRunParserArgs( self, parser ):
        c = conf.conf
        if self.txtFile:
            parser.add_argument( 'txtFile', action='store', help = 'Newline delimited text file of URLs', default = None)

        parser.add_argument( '--browser', action = 'store', choices = [ 'firefox', 'chrome', 'ie' ],
                             help = 'Which browser to browse with', default = c.OPTION_DEFAULT_BROWSER_DEFAULT )
        parser.add_argument( '--https', action = 'store_true', help = 'Skip not-HTTPS links',
                             default = c.OPTION_HTTPS_FORCE_DEFAULT )
        parser.add_argument( '--start', action = 'store', help = 'Start time to begin browsing',
                             default = datetime.now( ), )
        parser.add_argument( '--end', action = 'store', help = 'Time to finish browsing', default = None )
        parser.add_argument( '--whitelist', action = 'store', help = 'File containing regex of websites to include',
                             default = c.OPTION_WHITELIST_DEFAULT )
        parser.add_argument( '--blacklist', action = 'store', help = 'File containing regex of websites to exclude',
                             default = c.OPTION_BLACKLIST_DEFAULT )
        parser.add_argument( '--drunk', action = 'store_true',
                             help = 'Enable drunk typing regardless of day/time',
                             default = False )
        parser.add_argument( '--selfies', action = 'store_true',
                             help = 'Capture a screenshot on every site and produce a video', default = False )
        parser.add_argument( '--no-fuzz', action = 'store_true',
                             help = 'No fuzzy typing, no errors',
                             default = False )
        parser.add_argument( '--no-repeats', action = 'store_true',
                             help = 'Do not revisit any URLs during a browsing session',
                             default = False )
        parser.add_argument( '--skip-urls', action = 'store_true',
                             help = 'Skip all URLs (still bootstraps and runs stats)',
                             default = False )

    def parseAndMergeArgs( self, parser ):
        """
        Parse the CLI args using the parser passed in.
        Configure logger, override loaded values with CLI args/values
        Return parsed args
        """
        c = conf.conf
        args = parser.parse_args( sys.argv[ 2: ] )

        # before we can do anything, config the logger
        dblog.configFromArgs( args )

        # start log a pretty initial entry / log-header
        dblog.logSandwich( self.PROG_NAME )

        # set config, args.config defaults to c.FILENAME_DEFAULT
        self.configParser = c.loadConf( args.config )

        # dump for debugging purposes
        self.dumpConf( )
        dblog.logLettuce( logging.DEBUG )
        self.dumpRunArgs( args )
        dblog.logLettuce( logging.DEBUG )

        # merge args into configs, will print at info level
        self.mergeArgsAndConfigs( args )

        # set data manager
        self.dataMgr = datamgr.datamgr( self )

        # set user preferences
        self.user = user.user( typingWpm = self.getConf( c.OPTIONS, c.OPTION_TYPING_WPM ),
                               typingRand = self.getConf( c.OPTIONS, c.OPTION_TYPING_ERR ) )

        return args

    def mergeArgsAndConfigs( self, args ):
        """
        Merge CLI args and config file values
        """
        c = conf.conf
        vArgs = vars( args )

        if 'location' in vArgs:
            self.setConf( c.OPTIONS, c.OPTION_HISTORY_DB, args.location )

        if 'browser' in vArgs:
            self.setConf( c.OPTIONS, c.OPTION_DEFAULT_BROWSER, args.browser )

        if 'https' in vArgs:
            self.setConf( c.OPTIONS, c.OPTION_HTTPS_FORCE, str( args.https ) )

        if 'whitelist' in vArgs:
            self.setConf( c.OPTIONS, c.OPTION_WHITELIST, str( args.whitelist ) )

        if 'blacklist' in vArgs:
            self.setConf( c.OPTIONS, c.OPTION_BLACKLIST, str( args.blacklist ) )

        if 'drunk' in vArgs and 'no_fuzz' not in vArgs:
            self.setConf( c.OPTIONS, c.OPTION_DRUNKEN_WEEKENDS, str( args.drunk ) )

        if 'no_fuzz' in vArgs:
            self.setConf( c.OPTIONS, c.OPTION_FUZZY_TYPING, str( not args.no_fuzz ) )

        if 'no_repeats' in vArgs:
            self.setConf( c.OPTIONS, c.OPTION_NO_REPEATS, str( args.no_repeats ) )

        if 'selfies' in vArgs:
            self.setConf( c.OPTIONS, c.OPTION_SELFIES, str( args.selfies ) )

        # always let the user know what our config values are before running
        # this is useful for reading through logs, regardless of errors/successes
        self.dumpConf( level = logging.INFO )
        dblog.logLettuce( )

    # Getters / Setters
    def getConf( self, section, key ):
        """
        Returns a configuration value for a section-key pair
        """
        return self.configParser.get( section, key )

    def setConf( self, section, key, value ):
        """
        Sets a configuration value for a section-key pair
        """
        self.configParser.set( section, key, value )

    def browser( self, browserOver = '' ):
        """
        Returns default browser or specified browser
        """
        browser = self.defaultBrowser
        if len( browserOver ):
            browser = browserOver
        return self.browsers[ browser ]

    def setBrowser( self, browserName ):
        """
        Creates a browser instance
        """
        self.defaultBrowser = browserName
        if browserName == 'firefox':
            self.browsers[ 'firefox' ] = webdriver.Firefox( )
        elif browserName == 'chrome':
            self.browsers[ 'chrome' ] = webdriver.Chrome( )
        elif browserName == 'ie':
            self.browsers[ 'ie' ] = webdriver.Ie( )

    def loadList( self, filename ):
        """
        Load white/black list from the location and read in each line as a new regex entry
        """
        list = [ ]
        # give lists an existential crisis test
        if os.path.isfile( filename ):
            with open( filename ) as f:
                list = [ x.strip( '\n' ) for x in f.readlines( ) ]
                dblog.log( 'list', 'Found %d records from %s' % ( len( list ), filename ) )

        return list

    def loadLists( self ):
        """
        Load the white and black lists
        """
        c = conf.conf
        self.blacklist = self.loadList( self.getConf( c.OPTIONS, c.OPTION_BLACKLIST ) )
        self.whitelist = self.loadList( self.getConf( c.OPTIONS, c.OPTION_WHITELIST ) )

    # Main 'Run' Actions
    def simulateRealtime( self ):
        """
        Use current date/time to build a "typical" browsing pattern
        """
        # continuously loop, refreshing the seed data as needed
        expiresDtm  = None
        processUrls = True
        while processUrls:
            # first up, get history if our time block is up
            now = datetime.now()
            if ( expiresDtm is None ) or ( now >= expiresDtm ):
                failures = 0
                expiresDtm = now + timedelta( minutes = 30 )
                dblog.log( 'sim', 'Refreshing seed data, valid until %s' % expiresDtm )
                if self.txtFile:
                    # refresh from the text file - don't need to actually reload all the URLs
                    # since they are cached.  Just change the rate at which we browse so there
                    # is a change in behavior at this period
                    urlRows = self.urllist.copy()
                    ratePerHalfHour = random.uniform( 150, 500 )
                else:
                    # refresh from the database
                    ( urlRows, ratePerHalfHour ) = self.historian.getSeedUrlData( now )

                # if there are no URL results foudn, we have to go home
                urlRowsOrigLen = len( urlRows )
                if not urlRowsOrigLen:
                    dblog.log( 'sim', 'No URLs found :-(' )
                    return

                # convert 30-min rate to secs/url
                secPerUrl = round( 60 / ( ratePerHalfHour / 30 ), 2 )

            # pick a random item in the urls
            idx = int( random.uniform( 0, len( urlRows ) ) )

            # remove it so it's not seen again
            urlRow = urlRows.pop( idx )
            url = urlRow[ 'url' ] if not self.txtFile else urlRow

            # handle it with our main handler / dispatcher
            if self.handleUrl( url ):
                # wait the appropriate amount of time; we'll fudge the time by +/- 25%
                sleepSec = abs( secPerUrl + round( random.choice( [-1,1] ) * ( secPerUrl / 4 ), 2 ) )
                dblog.log( 'sim', 'Finished URL, waiting %d seconds' % sleepSec )
                self.user.idle( sleepSec )
            else:
                failures += 1

            # reset the expiration time if we're out of URLs
            if not len( urlRows ):
                expiresDtm = None

            # only keep going if we haven't failed on every URL attempt
            processUrls = ( failures < urlRowsOrigLen )

    def urlHistory( self, urlPattern = '' ):
        """
        Use the full chronological url history (or just matching a pattern)
        to replay a sequence of urls
        """
        days = int( self.getConf( conf.conf.OPTIONS, conf.conf.OPTION_WINDOW_DAYS ) )
        histRows = self.historian.getUrlHistory( days, urlPattern )

        for histRow in histRows:
            self.handleUrl( histRow[ 'url' ] )

    # URL Handlers
    def handleUrl( self, url ):
        """
        Given a URL, check if the URL is valid for handling/visiting
        If it can be handled, execute the handler, otherwise visit the page
        """
        # no handling / skipping means no cleanup / postHandleUrl()
        if self.skipHandling:
            self.skipUrl( url )
            return False

        # check if we're concerned about repeated URLs
        if self.getConf( conf.conf.OPTIONS, conf.conf.OPTION_NO_REPEATS ) == 'True':
            if url in self.processedUrls:
                self.skipUrl( url, 'repeat' )
                return False

        # check secure/HTTPS enforcement
        if self.getConf( conf.conf.OPTIONS, conf.conf.OPTION_HTTPS_FORCE ) == 'True':
            if not url.startswith( 'https' ):
                self.skipUrl( url, '!https' )
                return False

        # check whitelist / blacklist
        if not self.urlPassesWhiteBlackLists( url ):
            self.skipUrl( url, '!list' )
            return False

        # check handlers
        for handler in handlers.handlers:
            if self.tryUrlHandler( url, handler ):
                return True

        # by default just visit the page
        self.visitUrl( url )
        self.user.pause( )
        self.postHandleUrl( url )

        return True

    def postHandleUrl( self, url ):
        """
        Do any post-url handling clean up or features that should be executed once we consider a url visit "done"
        """
        # check if we need to take any selfies
        if self.getConf( conf.conf.OPTIONS, conf.conf.OPTION_SELFIES ) == 'True':
            selfies.takeSelfie( self, url )

        # check if we're concerned about keeping a log of previous urls
        if self.getConf( conf.conf.OPTIONS, conf.conf.OPTION_NO_REPEATS ) == 'True':
            if url not in self.processedUrls:
                self.processedUrls[ url ] = list( )
                # guaranteed to have an initialized list, append the timestamp to represent this URL instance
            self.processedUrls[ url ].append( datetime.now( ) )

    def skipUrl( self, url, reason = 'skip' ):
        """
        Skip a URL and log it
        """
        dblog.log( reason, url )
        self.stats[ 'skipped' ] += 1

    def tryUrlHandler( self, url, handler ):
        """
        Try a regex-handleFunc pair for the URL
        """
        pattern = re.compile( handler[ 0 ] )
        match = pattern.findall( url )
        # do we have a match?
        if len( match ):
            handleFunc = handler[ 1 ]
            dblog.log( 'handler', "'%s' handling url [ %s ]" % ( handleFunc.__name__, url ) )
            # use the handler and the regex match for the URL
            handleFunc( self, url, match )
            # mark it handled and move on
            self.stats[ 'handled' ] += 1
            self.postHandleUrl( url )
            return True

        return False

    def visitUrl( self, url ):
        """
        Visit a url with the browser
        """
        dblog.log( 'visit', url )
        self.browser( ).get( url )
        self.stats[ 'visited' ] += 1

    # Utility Functions
    def urlHasListMatch( self, list, url ):
        """
        For a given list, return if a url matches an of the list regex patterns
        """
        for regex in list:
            pattern = re.compile( regex.strip( ) )
            match = pattern.findall( url )
            if len( match ):
                return True
        return False

    def urlPassesWhiteBlackLists( self, url ):
        """
        Check if a URL is valid when matched against white and blacklists
        A whitelist always overrides blacklists
        """
        # no lists equal insta-pass
        wLen = len( self.whitelist )
        bLen = len( self.blacklist )
        dblog.log( 'list', 'white: %d | black: %d' % ( wLen, bLen ), level = logging.DEBUG )
        if wLen + bLen == 0:
            dblog.log( 'list', 'Url [ %s ] didn\'t test, empty lists' % url, level = logging.DEBUG )
            return True

        # check if we pass the white/blacklist test
        wMatch = self.urlHasListMatch( self.whitelist, url )
        bMatch = self.urlHasListMatch( self.blacklist, url )
        dblog.log( 'list', 'Url [ %s ] tested on lists -> white[%d] = %s | black[%d] = %s ' % (
            url, wLen, wMatch, bLen, bMatch ), level = logging.DEBUG )

        # if we have white && black list, only pass if
        # url matches the whitelist and not the blacklist
        if wLen and bLen:
            return wMatch and not bMatch

        # return whitelist match if we have a list
        if wLen:
            return wMatch

        # matching a blacklist is bad, do not pass
        if bLen:
            return not bMatch

        # shouldn't ever get here ...
        return False

    def typeKeys( self, inputElem, text ):
        """
        Simulate typing keys based on a user's typing speed / error rate
        """
        drunk = False
        sloppy = self.getConf( conf.conf.OPTIONS, conf.conf.OPTION_FUZZY_TYPING ) == 'True'
        if sloppy:
            # check for "drunk typing" enabled day/time period
            if ( self.user.insideDrunkTimeFrame( )
                 and self.getConf( conf.conf.OPTIONS, conf.conf.OPTION_DRUNKEN_WEEKENDS ) == 'True' ):
                # we're within an "appropriate" time frame, modify typing stats as if inebriated
                drunk = True

        self.user.typeKeys( self, inputElem, text, sloppy, drunk )

    # Logging Functions
    def logStats( self ):
        """
        Log start-finish stats in a formatted manner
        """
        dur = self.stats[ 'tock' ] - self.stats[ 'tick' ]
        hrRate = float( ( 60 * 60 ) / dur.total_seconds( ) )
        total = self.stats[ 'skipped' ] + self.stats[ 'handled' ] + self.stats[ 'visited' ]
        dblog.log( 'stat', 'Skipped: %s [ %.2f url/hr ]' % ( self.stats[ 'skipped' ], hrRate * self.stats[ 'skipped' ] ) )
        dblog.log( 'stat', 'Handled: %s [ %.2f url/hr ]' % ( self.stats[ 'handled' ], hrRate * self.stats[ 'handled' ] ) )
        dblog.log( 'stat', 'Visited: %s [ %.2f url/hr ]' % ( self.stats[ 'visited' ], hrRate * self.stats[ 'visited' ] ) )
        dblog.log( 'stat', 'Total:   %s [ %.2f url/hr ]' % ( total, hrRate * total ) )
        dblog.log( 'stat', 'Elapsed: %s' % dur )

    # Debug Functions
    def dumpConf( self, level = logging.DEBUG ):
        """
        Dump all configuration variables and their values
        """
        for s in self.configParser.sections( ):
            for o in sorted( self.configParser.options( s ) ):
                dblog.log( 'conf', '%s: %s' % ( o.title( ), self.getConf( s, o ) ), level = level )

    def dumpRunArgs( self, args ):
        """
        Dump all command line arguments and their values
        """
        d = vars( args )
        for a in d:
            dblog.log( 'args', '%s: %s' % ( a, d[ a ] ), level = logging.DEBUG )

    def dumpProcessedUrls( self, level = logging.DEBUG ):
        """
        Dump all the URLs that have been processed and when they were processed
        """
        for url in self.processedUrls:
            for ts in reversed( self.processedUrls[ url ] ):
                dblog.log( 'urlhist', '%s %s %s' % ( ts.strftime( '%Y-%M-%d %H:%M:%S' ), dblog.LOG_PIPE_CHAR, url ),
                           level = level )

# Go go gadget "I'm not here right now but my network traffic says otherwise"
if __name__ == "__main__":
    dirtyboots( )