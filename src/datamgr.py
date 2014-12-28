import uuid
import sqlite3
from datetime import date, timedelta

import logging
import dblog

class datamgr( object ):
    """
    Handles database creation/setup, queries, and importation
    """
    _dbConn = { }
    _dbCurs = { }
    _db = None

    # default name/location of the merged history database
    DEF_DB_LOC = 'history.sqlite'

    # create SQL for imported/original history records
    SQL_CREATE_IMPORTED = '''
        DROP TABLE IF EXISTS "imported_history";
        CREATE TABLE imported_history (
            browser TEXT,
            guid TEXT,
            seq INTEGER DEFAULT 0,
            type TEXT,
            url LONGVARCHAR,
            from_url LONGVARCHAR,
            root_url LONGVARCHAR,
            visit_count INTEGER DEFAULT 0,
            timestamp DATETIME
        );
        '''

    # create SQL for massaged/active history records
    SQL_CREATE_HISTORY = '''
        DROP TABLE IF EXISTS "history";
        CREATE TABLE history (
            browser TEXT,
            guid TEXT,
            seq INTEGER DEFAULT 0,
            type TEXT,
            url LONGVARCHAR,
            from_url LONGVARCHAR,
            root_url LONGVARCHAR,
            visit_count INTEGER DEFAULT 0,
            timestamp DATETIME
        );
        '''

    # clear working history table
    SQL_CLEAR_URL_HISTORY = 'DELETE FROM history'

    # clear imported history table
    SQL_CLEAR_URL_IMPORT_HISTORY = 'DELETE FROM imported_history'

    # import url data into history database for a specified table
    SQL_INSERT_URL_HISTORY = 'INSERT INTO %s (browser,guid,seq,type,url,from_url,root_url,visit_count,timestamp) VALUES (?,?,?,?,?,?,?,?,?)'

    # select url data from chrome history database to be used for import
    SQL_SELECT_CHROME_HISTORY_FOR_IMPORT = '''
         SELECT V.*,
            datetime((visit_time/10000000),'unixepoch') AS timestamp,
            U.visit_count,
            U.url AS url_str,
            datetime((U.last_visit_time/10000000),'unixepoch') AS last_visit_date
        FROM visits AS V
        JOIN urls U ON ( U.id = V.url )
        '''

    # select url data from firefox history database to be used for import
    SQL_SELECT_FIREFOX_HISTORY_FOR_IMPORT = '''
        SELECT MHI.*,
            datetime((visit_date/1000000),'unixepoch') AS timestamp,
            MP.url,
            MP.rev_host,
            MP.visit_count,
            MP.frecency,
            datetime((MP.last_visit_date/1000000),'unixepoch') AS last_visit_date,
            MP.guid
        FROM moz_historyvisits AS MHI
        JOIN moz_places MP ON ( MP.id = MHI.place_id )
    '''

    # select visit counts per url, returns all url-instances
    SQL_SELECT_URL_VISIT_COUNT = 'SELECT *, count(guid) AS visit_count FROM imported_history GROUP BY url, timestamp'

    def __init__(self,db):
        self._db = db

    def db(self):
        return self._db

    def closeConn( self ):
        """
        Close the database connection
        """
        self.curs( ).close( )
        self.conn( ).close( )

    def conn( self ):
        return self._dbConn

    def curs( self ):
        return self._dbCurs

    def log( self, msg, level = logging.INFO ):
        """
        For consistent logging format within all handler functions
        """
        dblog.log( 'SQL', msg, level = level )

    # DB Setup Functions
    def openDb( self, location = DEF_DB_LOC ):
        """
        Open and connect to a database
        """
        self._dbConn = sqlite3.connect( location, detect_types = sqlite3.PARSE_COLNAMES )
        self.conn( ).row_factory = sqlite3.Row
        self._dbCurs = self.conn( ).cursor( )

    def clearDb( self, location = DEF_DB_LOC ):
        """
        Clears all tables in a history database
        """
        self.openDb( location )
        self.log( 'Clearing database' )
        self.executeSql( self.SQL_CLEAR_URL_HISTORY )
        self.executeSql( self.SQL_CLEAR_URL_IMPORT_HISTORY )
        self.conn( ).commit( )

    def initDb( self, location = DEF_DB_LOC ):
        """
        Create a database at a given location/filename
        """
        self.openDb( location )
        self.createDbTables( )

    def createDbTables( self ):
        """
        Execute creation SQL for DB
        """
        self.executeSqlScript( self.SQL_CREATE_IMPORTED )
        self.executeSqlScript( self.SQL_CREATE_HISTORY )
        self.log( 'Executed creation commands' )
        self.conn( ).commit( )

    def lcdVisitType( self, browser, typeFromDb ):
        """
        Match a visit type int for a browser to a generic/shared visit type
        """
        firefox = [ '', 'link', 'typed', 'bookmark', 'embed', 'redirect_perm', 'redirect_temp', 'download',
                    'framed_link' ]
        chrome = [ 'link', 'typed', 'bookmark', 'frame_auto', 'frame_man', 'generated', 'start_page', 'form', 'reload',
                   'keyword_url', 'keyword_gen' ]
        if browser == 'firefox':
            return firefox[ max( max( 0, typeFromDb ), min( -typeFromDb, 0 ) ) ]
        else:
            return chrome[ max( 0, typeFromDb ) ]

    # Import / Insert Functions
    def importDatabase( self, browser, filename ):
        """
        Import a browser database into the generic history database
        """
        self.log( '[%s] Loading Database' % browser.title( ) )
        if browser == 'firefox':
            self.importFirefoxDatabase( filename )
        else:
            self.importChromeDatabase( filename )

        self.log( 'Rebuilding the working history table' )
        self.rebuildUrlHistoryTable( )
        self.conn( ).commit( )

    def importChromeDatabase( self, filename ):
        """
        Imports a Chrome database into the generic history database
        """
        self.log( '[ChromeDB] Loading database from %s' % filename )
        conn = sqlite3.connect( filename )
        conn.row_factory = sqlite3.Row
        curs = conn.cursor( )
        self.executeSql( self.SQL_SELECT_CHROME_HISTORY_FOR_IMPORT, curs = curs )
        urlsToImport = curs.fetchall( )
        self.log( '[ChromeDB] Importing %d urls into database' % len( urlsToImport ) )
        for urlRecord in urlsToImport:
            transCode = 0xFF & urlRecord[ 'transition' ]
            visitType = self.lcdVisitType( 'chrome', transCode )
            formattedRow = {
                'browser': 'chrome',
                'guid': str( uuid.uuid1( ) ),
                'seq': urlRecord[ 'id' ],
                'type': visitType,
                'url': urlRecord[ 'url_str' ],
                'visit_count': urlRecord[ 'visit_count' ],
                'from_url': '',
                'root_url': '',
                'timestamp': urlRecord[ 'timestamp' ]
            }
            self.insertFormattedHistoryRow( formattedRow )

    def importFirefoxDatabase( self, filename ):
        """
        Imports a Firefox database into the generic history database
        """
        self.log( '[FirefoxDB] Loading database from %s' % filename )
        conn = sqlite3.connect( filename )
        conn.row_factory = sqlite3.Row
        curs = conn.cursor( )
        self.executeSql( self.SQL_SELECT_FIREFOX_HISTORY_FOR_IMPORT, curs = curs )
        urlsToImport = curs.fetchall( )
        self.log( '[FirefoxDB] Importing %d urls into database' % len( urlsToImport ) )
        for urlRecord in urlsToImport:
            visitType = self.lcdVisitType( 'firefox', urlRecord[ 'visit_type' ] )
            formattedRow = {
                'browser': 'firefox',
                'guid': str( uuid.uuid1( ) ),
                'seq': urlRecord[ 'id' ],
                'type': visitType,
                'url': urlRecord[ 'url' ],
                'visit_count': urlRecord[ 'visit_count' ],
                'from_url': '',
                'root_url': '',
                'timestamp': urlRecord[ 'timestamp' ]
            }
            self.insertFormattedHistoryRow( formattedRow )

    def insertFormattedHistoryRowHelper( self, table, formattedRow ):
        """
        Inserts a row for the history database into one of the *history tables
        """
        self.executeSql( self.SQL_INSERT_URL_HISTORY % table, [
            formattedRow[ 'browser' ],
            formattedRow[ 'guid' ],
            formattedRow[ 'seq' ],
            formattedRow[ 'type' ],
            formattedRow[ 'url' ],
            formattedRow[ 'from_url' ],
            formattedRow[ 'root_url' ],
            formattedRow[ 'visit_count' ],
            formattedRow[ 'timestamp' ]
        ] )

    def insertFormattedHistoryRow( self, formattedRow ):
        """
        Inserts formatted url-rows into imported_history
        """
        self.insertFormattedHistoryRowHelper( 'imported_history', formattedRow )

    def rebuildUrlHistoryTable( self ):
        """
        Inserts formatted url-rows into history after updating their count
        """
        self.log( 'Recalculating visit counts and records for all browsers' )
        self.executeSql( self.SQL_CLEAR_URL_HISTORY )
        self.executeSql( self.SQL_SELECT_URL_VISIT_COUNT )
        urlsToUpdate = self.curs( ).fetchall( )

        self.log( 'Importing results into emptied `history` table' )
        for urlToUpdate in urlsToUpdate:
            self.insertFormattedHistoryRowHelper( 'history', urlToUpdate )

        self.log( 'Finished import into working `history` table' )

    # SQL Execution Functions
    def _execute( self, sql, args = None, curs = None, single = True ):
        """
        Execute SQL command (w/ optional args) and log in debug log
        """
        if not curs:
            curs = self.curs( )

        # log the query/queries and execute it/them
        self.log( 'SQL: %s | args: [%s]' % ( sql, args ), level=logging.DEBUG )
        if single:
            if args:
                curs.execute( sql, args )
            else:
                curs.execute( sql )
        else:
            curs.executescript( sql )

    def executeSql( self, sql, args = None, curs = None ):
        """
        Execute SQL command (w/ optional args) and log in debug log
        """
        self._execute( sql, args, curs )

    def executeSqlScript( self, sql, curs = None ):
        """
        Execute SQL command (w/ optional args) and log in debug log
        """
        self._execute( sql, args=None, curs = curs, single = False )