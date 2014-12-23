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

* argparse
* selenium
* scikit-learn
* pandas

## Usage

    init     Creates database for browsing history and stats
    clear    Clears existing browsing history database
    importdb Imports a web browser's history
    config   Create a default configuration file
    run      Run the program

All commands support the following options

    -h, --help                      Show this help message and exit
    --log [LOG]                     Log file location, default to stdout
    --level [{debug,info,warning,error,critical}]
                                    Logging level

### Quick-Start

    # init database with default filename [history.sqlite]
    dirtyboots.py init

    # create conf with defaults [boots.conf]
    dirtyboots.py config

    # import Firefox profile's browsing history
    dirtyboots.py importdb --browser firefox --location /Path/To/Firefox/Profile/History.sqlite

    # import Chrome profile's browsing history
    dirtyboots.py importdb --browser chrome --location /Path/To/Chrome/Profile/History

    # start browsing
    dirtyboots.py run

### Init

Creates database for browsing history and stats

    --location [LOCATION]           Location to create the database

### Clear

Clears existing browsing history database

    --location [LOCATION]           Location to create the database

### ImportDB

Import database for browsing history and stats

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
    --no-fuzz                       No fuzzy typing, no errors
    --skip-urls                     Skip all URLs (still bootstraps and runs stats)

## License

DirtyBoots is licensed under GNU GPL v3.  Please see LICENSE for more information.

https://github.com/m-kal

&copy; 2014