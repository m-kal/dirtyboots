import logging

# internal logging configs - don't need anything fancy, can be just with a few 'consts'
LOG_DEFAULT_LVL = logging.INFO
LOG_BREAD_MAX   = 40
LOG_BREAD_CHR   = '='
LOG_LETTUCE_CHR = '-'
LOG_PIPE_CHAR   = '|'
LOG_CAT_LEN     = 9

def configFromArgs( args ):
    """
    Convert CLI args to a configured logger
    """
    filemode = None
    filename = None

    logFmt = '%(message)s'
    if not args.no_ts:
        logFmt = '[ %(asctime)s ] ' + logFmt

    level = getattr( logging, args.level.upper( ), None )
    if args.log:
        filemode = 'w' if ( args.log_mode == 'w' ) else 'a'
        filename = args.log

    # pass into logging's config
    logging.basicConfig( format = logFmt, level = level, filemode = filemode, filename = filename )

def logSandwich( str ):
    """
    Start log with a pretty initial entry / log-header
    """
    logBread( )
    logMeat( str )
    logBread( )

def logBread( fillChr = LOG_BREAD_CHR, level = LOG_DEFAULT_LVL ):
    """
    Log a divider string consisting of a single repeated char
    """
    logging.log( level, ''.ljust( LOG_BREAD_MAX + 4, fillChr ) )

def logMeat( meatStr, fillChr = LOG_BREAD_CHR, level = LOG_DEFAULT_LVL ):
    """
    Log a string centered between bread-chars
    """
    logging.log( level, '%s %s %s' % ( fillChr, meatStr[ :LOG_BREAD_MAX ].center( LOG_BREAD_MAX, ' ' ).upper( ), fillChr ) )

def logLettuce( level = LOG_DEFAULT_LVL ):
    """
    Log a mini-divider across the category & message sections
    """
    logStr = LOG_PIPE_CHAR \
             + ''.ljust( LOG_CAT_LEN, LOG_LETTUCE_CHR ) \
             + LOG_PIPE_CHAR \
             + ''.ljust( 1 + LOG_BREAD_MAX - LOG_CAT_LEN, LOG_LETTUCE_CHR )

    logging.log( level, logStr )

def log( cat, msg, level = LOG_DEFAULT_LVL ):
    """
    Log debug/info/error messages in a consistent manner
    """
    logStr = LOG_PIPE_CHAR \
             + cat[ :LOG_CAT_LEN ].center( LOG_CAT_LEN, ' ' ).lower( ) \
             + LOG_PIPE_CHAR \
             + ' ' + msg

    logging.log( level, logStr )