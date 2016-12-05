---
layout: default
title: DirtyBoots
description: Web browser automation to obscure between genuine and fake browsing sessions
---

DirtyBoots drives/automates web browsing to mimic your browsing habits, so your network traffic and online activity can appear normal while away from keyboard / home.

Online, many people focus on what they explicitly post, upload, or share.  This ignores privacy from a traffic and network perspective.  Gaps in browsing activity can indicate sleep patterns, habitual periods away from one's keyboard or home, and more.  DirtyBoots is a simple solution to import existing browsing history database files, and drive a real-time probability-based browsing sequence.  In addition to obscuring 'genuine' network traffic, third-party trackers will be flooded with excess requests, obscuring 'genuine' network traffic, third-party trackers will be flooded with excess requests, distorting your actual browsing patterns.

## Features

* Fuzzy/error-prone typing
* Firefox, Chrome, and Internet Explorer support
* Website filtering and exclusion with white/black lists
* Site plugins to expand per-site features and abilities
* Delayed/timer-triggered browsing
* Increased errors / slower typing between 8pm-midnight Friday/Saturday
* Easy logging and configuration

## Usage

Getting started with DirtyBoots is simple and only requires a couple commands.  Initialize configuration and database, import browser databases if needed, and launch DirtyBoots.  Beow is a quick-start guide to get you up and running, followed by documentation on each command.

### Quick-Start

<pre class="code-txt">
# setup / install
python setup.py install

# create conf with defaults [boots.conf]
dirtyboots config

# init database with default filename [history.sqlite]
dirtyboots initdb

# import a Firefox profile's browsing history
dirtyboots importdb /Path/To/Firefox/Profile/places.sqlite --browser firefox

# import a Chrome profile's browsing history
dirtyboots importdb /Path/To/Chrome/Profile/History --browser chrome

# start browsing
dirtyboots run

# alternative run (from text file)
dirtyboots txt /Path/To/Text/File/of/Urls.txt
</pre>

The main commands are,

<pre class="code-txt">
run                         Run the program
txt                         Run the program from a newline-delimited text file of urls
initdb                      Creates database for browsing history and stats
cleardb                     Clears existing browsing history database
importdb                    Imports a web browser's history
config                      Create a default configuration file
</pre>

All commands support the following options

<pre class="code-txt">
-h, --help                  Show this help message and exit
--no-ts                     Disable timestamps during logging
--log       [LOG]           Log file location, default to stdout
--level     [LEVEL]         Logging level [{debug,info,warning,error,critical}]
--log-mode  [MODE]          Which mode to open log files with [{w,a}]
</pre>

### Run

Launch cruise-control for websites

<pre class="code-txt">
--https                     Skip not-HTTPS links
--drunk                     Enable drunk typing regardless of day/time
--selfies                   Capture a screenshot on every site and produce a video
--no-fuzz                   No fuzzy typing, no errors
--no-repeats                Do not revisit any URLs during a browsing session
--skip-urls                 Skip all URLs (still bootstraps and runs stats)
--config    [CONFIG]        Config file load (.conf)
--location  [LOCATION]      Location to create the database
--browser   [BROWSER]       Which browser to browse with [{firefox,chrome,ie}]
--start     [START]         Start time to begin browsing
--end       [END]           Time to finish browsing
--whitelist [WHITELIST]     File containing regex of websites to include
--blacklist [BLACKLIST]     File containing regex of websites to exclude
</pre>

### Txt

Run the program from a newline-delimited text file of urls rather than a sqlite database.

<pre class="code-txt">
txtFile                     Newline delimited text file of URLs
--https                     Skip not-HTTPS links
--drunk                     Enable drunk typing regardless of day/time
--selfies                   Capture a screenshot on every site and produce a video
--no-fuzz                   No fuzzy typing, no errors
--no-repeats                Do not revisit any URLs during a browsing session
--skip-urls                 Skip all URLs (still bootstraps and runs stats)
--config    [CONFIG]        Config file load (.conf)
--location  [LOCATION]      Location to create the database
--browser   [BROWSER]       Which browser to browse with [{firefox,chrome,ie}]
--start     [START]         Start time to begin browsing
--end       [END]           Time to finish browsing
--whitelist [WHITELIST]     File containing regex of websites to include
--blacklist [BLACKLIST]     File containing regex of websites to exclude
</pre>

Text-file mode has a required argument `txtfile` and has the same command line options as `run`

### InitDB

Creates database for browsing history and stats

<pre class="code-txt">
dirtyboots initdb [OPTIONS]

--location  [LOCATION]      Location to create the database
</pre>

### ClearDB

Clears existing browsing history database

<pre class="code-txt">
dirtyboots cleardb [OPTIONS]

--location  [LOCATION]      Location to create the database
</pre>

### ImportDB

Import database for browsing history and stats

<pre class="code-txt">
dirtyboots importdb [DATABASE] [OPTIONS]

database                    Browser database file (ex: places.sqlite or History)
--browser   [BROWSER]       Browser database type [{firefox,chrome}]
--location  [LOCATION]      Location to create the database
</pre>

### Config

Create a default configuration file

<pre class="code-txt">
dirtyboots config [OPTIONS]

--config    [CONFIG]        Config file load (.conf)
</pre>

## Website

The official website is hosted at http://m-kal.com/dirtyboots

## License

DirtyBoots is licensed under GNU GPL v3.  Please see LICENSE for more information.

https://github.com/m-kal

&copy; 2016