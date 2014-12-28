import random
from datetime import *
import dateutil.parser

import logging
import dblog

class historian( ):
    """
    Manage searching / fetching of the url/browser history database
    """
    # class consts
    MAX_SEED_RESULTS = 100
    SUB_SEED_RESULTS =  50
    DAY_FACTOR = 0.75
    HHR_FACTOR = 1.25

    # select all url-instances since a specified time
    SQL_SELECT_URL_HISTORY = 'SELECT timestamp, url, guid FROM history WHERE timestamp > ? ORDER BY timestamp ASC'

    # select all url-instances since a specified time and matching a specified pattern
    SQL_SELECT_URL_HISTORY_PATTERN = 'SELECT timestamp, url, guid FROM history WHERE url like ? AND timestamp > ? ORDER BY timestamp ASC'

    def __init__( self, db ):
        self.db = db

    # shortcut / helper functions
    def log( self, msg, level = logging.INFO ):
        """
        Shortcut to DB's logger
        """
        dblog.log( 'history', msg, level = level )

    def executeSql( self, sql, args ):
        """
        Shortcut to SQL functions
        """
        self.db.dataMgr.executeSql( sql, args )

    def sqlResults( self ):
        """
        Shortcut to SQL functions
        """
        return self.db.dataMgr.curs( ).fetchall( )

    def getUrlHistory( self, days, urlPattern = '' ):
        """
        Fetches all url-instances since a date, and optionally matching a pattern
        """
        dtm = date.today( ) - timedelta( days )
        if len( urlPattern ):
            self.executeSql( self.SQL_SELECT_URL_HISTORY_PATTERN, (urlPattern, dtm,) )
        else:
            self.executeSql( self.SQL_SELECT_URL_HISTORY, (dtm,) )

        # do the fetch
        histRows = self.sqlResults( )

        # log the size of the results
        msg = 'Found %d records' % len( histRows )
        if len( urlPattern ):
            msg += ' [pattern: %s]' % urlPattern

        self.log( msg )

        return histRows

    def getDoWUrlData( self, dayOfWeek ):
        self.log( 'Fetching day[%d] results' % dayOfWeek, level = logging.DEBUG )

        sql = '''
            SELECT  *,
                    date( timestamp) as dayBucket,
                    strftime("%s",timestamp) as dateStr,
                    count( guid ) as guidCount
            FROM    history H
            WHERE   dateStr == ?
            GROUP BY dateStr, dayBucket, url
            ORDER BY guidCount DESC
            LIMIT   %d
        ''' % ( '%w', self.MAX_SEED_RESULTS )
        self.executeSql( sql, (str( dayOfWeek ),) )

        return self.sqlResults( )

    def getHalfHrlyUrlData( self, hour, minBlock ):
        fmt = '%02d:%02d'
        self.log( 'Fetching .5-hr[%s] results' % ( fmt % ( hour, minBlock ) ), level = logging.DEBUG )
        minTime = fmt % ( hour, minBlock )
        maxTime = fmt % ( hour, 30 ) if not minBlock else fmt % ( ((hour + 1) % 24), 0 )
        sql = '''
            SELECT  *,
                    date(timestamp) as dayBucket,
                    strftime("%s",timestamp) as timeBucket,
                    count(guid) as guidCount
            FROM    history H
            WHERE   ( timeBucket >= ? ) AND ( timeBucket <= ? )
            GROUP BY dayBucket, timeBucket, url
            ORDER BY guidCount DESC
            LIMIT   %d
        ''' % ( '%H:%m', self.MAX_SEED_RESULTS )
        self.executeSql( sql, (minTime, maxTime) )

        return self.sqlResults( )

    def getSeedUrlData( self, seedDtm = datetime.now( ) ):
        """
        Examines urls in the past that match time / day of week / etc. today
        """
        self.log( 'Generating Seed URLs for [ %s ]' % seedDtm )
        level = logging.INFO
        # use current 30-min period and day of week to build 'seed' data set
        # every 30-min of browsing we can reseed the data set, so we'll be working
        # with time-relevant data but smaller memory footprint and smaller DB hits
        day = seedDtm.weekday( )
        hour = seedDtm.hour

        # get the daily results
        self.log( 'Fetching day-of-week results [%d]' % day, level = level )
        dailyRows = self.getDoWUrlData( day )

        # and now the half-hourly
        minBlock = 30 * round( seedDtm.minute / 60, 0 )
        self.log( 'Fetching 1/2-hourly results [%02d:%02d]' % ( hour, minBlock ), level )
        halfHourlyRows = self.getHalfHrlyUrlData( hour, minBlock )

        # merge them together
        merged = self.mergeSeedUrlSegments( dailyRows, halfHourlyRows )

        # do some stats in 30-min blocks
        dailyRate = self.getUrlRate( 48, dailyRows )
        perHalfHourRate = self.getUrlRate( 48, halfHourlyRows )

        # average between the two rates, then give a 25% fuzz factor
        mergedRate  = 0.5 * ( ( self.DAY_FACTOR * dailyRate ) + ( self.HHR_FACTOR * perHalfHourRate ) )
        fuzzFactor  = random.choice([-1,1]) * ( random.uniform( 0, mergedRate ) / 8 )
        mergedRate += fuzzFactor

        # log it all as debug, essentials as info, and return a tuple of the merged list and visit-rate
        self.log( '%d url/30min on day %d' % ( dailyRate, day ), level  )
        self.log( '%d url/30min on block %02d:%02d' % ( perHalfHourRate, hour, minBlock ), level )
        self.log( '%d url/30min weighted' % mergedRate, level )

        self.log( 'Generated %d Seed URLs, browsing rate = %d/30min' % ( len( merged ), mergedRate ) )

        return list( merged ), mergedRate

    def getUrlRate( self, duration, urlRows = [ ], rateKey = 'visit_count' ):
        """
        For a list of URLs, determine the about how many URLs per time period are visited
        """
        if len( urlRows ) == 0:
            return 0

        # sum for daily rate / quota
        # start with daily groupings and then use duration to adjust daily/30min
        uniqueDays = list( )
        total = 0
        for urlRow in urlRows:
            total += urlRow[ rateKey ]
            dateStr = dateutil.parser.parse( str( urlRow[ 'timestamp' ] ) ).date( ).isoformat( )
            if dateStr not in uniqueDays:
                uniqueDays.append( dateStr )

        avgDaily = total / len( uniqueDays )

        return round( avgDaily / duration, 2 )

    def mergeSeedUrlSegments( self, daily, halfHourly ):
        """
        Merge daily and 30min seed samples, weighting 30min samples
        more favorably than daily samples.
        """
        # get 25 unique choices, picked randomly w/ weights
        dayChoices = self.getNRandWeightedChoices( daily, self.SUB_SEED_RESULTS, weightKey = 'guidCount' )

        print( 'hi %d' % len ( dayChoices ) )
        # get 25 unique choices, picked randomly w/ weights
        hrChoices = self.getNRandWeightedChoices( halfHourly, self.SUB_SEED_RESULTS, weightKey = 'guidCount' )
        # merge the 2 arrays together with their visit-weights multiplied by the bucket-factors
        choices = { }
        for dc in dayChoices:
            url = dc[ 'url' ]
            if url not in choices:
                choices[ url ] = dict( zip( dc.keys( ), dc ) )
                choices[ url ][ 'count' ] = 0
            choices[ url ][ 'count' ] += self.DAY_FACTOR * dc[ 'guidCount' ]

        print( 'hi %d' % len ( hrChoices ) )
        for hc in hrChoices:
            url = hc[ 'url' ]
            if url not in choices:
                choices[ url ] = dict( zip( hc.keys( ), hc ) )
                choices[ url ][ 'count' ] = 0
            choices[ url ][ 'count' ] += self.HHR_FACTOR * hc[ 'guidCount' ]

        # now merged and weighted appropriately, pick a subset
        return self.getNRandWeightedChoices( choices.values( ), self.SUB_SEED_RESULTS, weightKey = 'count' )

    def getNRandWeightedChoices( self, urlRows, numChoices, weightKey = 'visit_count', uniqueKey = 'url' ):
        """
        Get N random choices among weighted-values, no duplicates will be returned
        """
        if not len( urlRows ):
            return { }.values( )

        usedChoices = { }
        numChoices  = min( len( urlRows ), numChoices )
        for i in range( numChoices ):
            urlValid = False
            j = 0
            while not urlValid:
                choice = self.weightedUrlChoice( urlRows, weightKey )
                j += 1
                if j == numChoices:
                    urlValid = True

                if choice[ uniqueKey ] not in usedChoices:
                    urlValid = True
                    usedChoices[ choice[ uniqueKey ] ] = choice

        return usedChoices.values( )

    def weightedUrlChoice( self, urlRows, key = 'visit_count' ):
        """
        Return a random choice from the urlRows based on a weighted key-value
        """
        # sum the key, pick a random uniform point from 0-total
        random.seed( )
        total = sum( ur[ key ] for ur in urlRows )
        randV = random.uniform( 0, total )
        count = 0
        for ur in urlRows:
            if count + ur[ key ] > randV:
                return ur
            count += ur[ key ]
        print( 'returning none %d' % len( urlRows ) )
        return None