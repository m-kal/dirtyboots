# DirtyBoots

DirtyBoots drives/automates web browsing to mimic your browsing habits, so your network traffic and online activity can appear normal while away from keyboard / home.

Online, many people focus on what they explicitly post, upload, or share.  This ignores privacy from a traffic and network perspective.  Gaps in browsing activity can indicate sleep patterns, habitual periods away from one's keyboard or home, and more.  DirtyBoots is a simple solution to import existing browsing history database files, and drive a real-time probability-based browsing sequence.  In addition to obscuring 'genuine' network traffic, third-party trackers will be flooded with excess requests, obscuring

## Features

* Statistical analysis w/ SciKit-Learn
* Fuzzy/error-prone typing
* Firefox, Chrome, and Internet Explorer support
* Website filtering and exclusion with white/black lists
* Site plugins to expand per-site features and abilities
* Delayed/timer-triggered browsing
* Increased errors / slower typing between 8pm-midnight Friday/Saturday
* Easy logging and configuration

## Dependencies

* python 3
* selenium
* ffmpeg
* moviepy
* pygame
* argparse

## Usage

### Quick-Start

    # setup / install
    python setup.py install

    # init database with default filename [history.sqlite]
    dirtyboots.py init

    # create conf with defaults [boots.conf]
    dirtyboots.py config

    # import Firefox profile's browsing history
    dirtyboots.py importdb /Path/To/Firefox/Profile/places.sqlite --browser firefox

    # import Chrome profile's browsing history
    dirtyboots.py importdb /Path/To/Chrome/Profile/History --browser chrome

    # start browsing
    dirtyboots.py run

The main commands are,

    initsb   Creates database for browsing history and stats
    clearsb  Clears existing browsing history database
    importdb Imports a web browser's history
    config   Create a default configuration file
    run      Run the program
    txt      Run the program from a newline-delimited text file of urls

All commands support the following options

    -h, --help                      Show this help message and exit
    --log [LOG]                     Log file location, default to stdout
    --level                         Logging level
        [{debug,info,warning,error,critical}]

    --no-ts                         Disable timestamps during logging
    --log-mode                      Which mode to open log files with
        [{w,a}]

### InitDB

Creates database for browsing history and stats

    --location [LOCATION]           Location to create the database

### ClearDB

Clears existing browsing history database

    --location [LOCATION]           Location to create the database

### ImportDB

Import database for browsing history and stats

    dirtyboots.py importdb [database] [options]

    database                        Browser database file (places.sqlite/History)
    --browser [{firefox,chrome}]    Browser database type
    --location [LOCATION]           Location to create the database

### Config

Create a default configuration file

    --config [CONFIG]               Config file load (.conf)

### Run

Launch cruise-control for websites

    --config [CONFIG]               Config file load (.conf)
    --location [LOCATION]           Location to create the database
    --https                         Skip not-HTTPS links
    --browser [{firefox,chrome,ie}] Which browser to browse with
    --start [START]                 Start time to begin browsing
    --end [END]                     Time to finish browsing
    --whitelist [WHITELIST]         File containing regex of websites to include
    --blacklist [BLACKLIST]         File containing regex of websites to exclude
    --drunk                         Enable drunk typing regardless of day/time
    --selfies                       Capture a screenshot on every site and produce a video
    --no-fuzz                       No fuzzy typing, no errors
    --no-repeats                    Do not revisit any URLs during a browsing session
    --skip-urls                     Skip all URLs (still bootstraps and runs stats)

### Txt

Run the program from a newline-delimited text file of urls rather than a sqlite database.

Text-file mode has a required argument `txtfile` and has the same command line options as `run`

## Help

### Locating Browser History Databases

#### Firefox

**Windows XP**

`C:\Documents and Settings\<user>\Application Data\Mozilla\Firefox\Profiles\<profile.id>\places.sqlite`

**Windows Vista/7**

`C:\Users\<user>\AppData\Roaming\Mozilla\Firefox\Profiles\<profile.id>\places.sqlite`

**GNU/Linux**

`/home/<user>/.mozilla/firefox/<profile folder>/places.sqlite`

**Mac OS X**

`/Users/<user>/Library/Application Support/Firefox/Profiles/default.lov/places.sqlite`

#### Chrome

**Windows XP**

`C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Default\History`

`C:\Users\<user>\AppData\Roaming\Mozilla\Firefox\Profiles\<profile.id>\places.sqlite`
`C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Default\History`


**Windows XP**

**Windows Vista/7**

`C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Default\History`


## License

DirtyBoots is licensed under GNU GPL v3.  Please see LICENSE for more information.

https://github.com/m-kal

&copy; 2014