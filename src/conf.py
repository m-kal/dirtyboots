import configparser

class conf( ):
    """
    Handles configuration files, read/write, and options/values.
    """
    # keys
    OPTIONS = 'Options'
    OPTION_HISTORY_DB = 'HistoryDb'
    OPTION_HTTPS_FORCE = 'Https'
    OPTION_NO_REPEATS = 'NoRepeats'
    OPTION_DEFAULT_BROWSER = 'DefaultBrowser'
    OPTION_DRUNKEN_WEEKENDS = 'DrunkenWeekends'
    OPTION_SELFIES = 'Selfies'
    OPTION_SELFIES_DIR = 'SelfiesDir'
    OPTION_FUZZY_TYPING = 'FuzzyTyping'
    OPTION_TYPING_WPM = 'TypingWPM'
    OPTION_TYPING_ERR = 'TypingErrRate'
    OPTION_WINDOW_DAYS = 'HistoryWindowDays'
    OPTION_BLACKLIST   = 'BlackListFile'
    OPTION_WHITELIST   = 'WhiteListFile'

    # default values
    FILENAME_DEFAULT = 'boots.conf'
    OPTION_HTTPS_FORCE_DEFAULT = False
    OPTION_NO_REPEATS_DEFAULT = False
    OPTION_HISTORY_DB_DEFAULT = 'history.sqlite'
    OPTION_DEFAULT_BROWSER_DEFAULT = 'firefox'
    OPTION_DRUNKEN_WEEKENDS_DEFAULT = True
    OPTION_SELFIES_DEFAULT = False
    OPTION_SELFIES_DIR_DEFAULT = './selfies'
    OPTION_FUZZY_TYPING_DEFAULT = True
    OPTION_TYPING_WPM_DEFAULT = 80
    OPTION_TYPING_ERR_DEFAULT = .15
    OPTION_WINDOW_DAYS_DEFAULT = 31
    OPTION_BLACKLIST_DEFAULT = 'blacklist.txt'
    OPTION_WHITELIST_DEFAULT = 'whitelist.txt'

    def initConf( self, filename = FILENAME_DEFAULT ):
        """
        Create a configuration file at a given location and return the ConfigParser
        """
        confParser = self.genDefault( )
        configfile = open( filename, 'w' )
        confParser.write( configfile )

        return confParser

    def loadConf( self, filename = FILENAME_DEFAULT ):
        """
        Load a configuration file and return the ConfigParser
        """
        config = configparser.ConfigParser( )
        if ( not config.read( filename ) ):
            config = self.initConf( filename )

        return config

    def genDefault( self ):
        """
        Generate a ConfigParser with the default values
        """
        config = configparser.ConfigParser( )

        config[ self.OPTIONS ] = {
            self.OPTION_HISTORY_DB: self.OPTION_HISTORY_DB_DEFAULT,
            self.OPTION_HTTPS_FORCE: self.OPTION_HTTPS_FORCE_DEFAULT,
            self.OPTION_NO_REPEATS: self.OPTION_NO_REPEATS_DEFAULT,
            self.OPTION_DEFAULT_BROWSER: self.OPTION_DEFAULT_BROWSER_DEFAULT,
            self.OPTION_DRUNKEN_WEEKENDS: self.OPTION_DRUNKEN_WEEKENDS_DEFAULT,
            self.OPTION_SELFIES: self.OPTION_SELFIES_DEFAULT,
            self.OPTION_SELFIES_DIR: self.OPTION_SELFIES_DIR_DEFAULT,
            self.OPTION_FUZZY_TYPING: self.OPTION_FUZZY_TYPING_DEFAULT,
            self.OPTION_TYPING_WPM: self.OPTION_TYPING_WPM_DEFAULT,
            self.OPTION_TYPING_ERR: self.OPTION_TYPING_ERR_DEFAULT,
            self.OPTION_WINDOW_DAYS: self.OPTION_WINDOW_DAYS_DEFAULT,
            self.OPTION_WHITELIST: self.OPTION_WHITELIST_DEFAULT,
            self.OPTION_BLACKLIST: self.OPTION_BLACKLIST_DEFAULT,
        }

        return config
