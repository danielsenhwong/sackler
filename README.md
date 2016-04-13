# sackler #

Projects related to the Sackler school.

Site currently running Python apps via Flask and Passenger.

## Calendar ##
A script to parse the Sackler school calendar RSS feed and output an iCal calendar file. Accessible at http://sackler.danielsenhwong.com/calendar (runs script and generates new file) and http://sackler.danielsenhwong.com/calendar.ics (target address for calendar subscriptions and file created by previous script run)

### Recent updates ###
_2016 Apr 13_ Added the ability to parse specific calendars from the Sackler website. Currently only enabled for Microbiology, which was specifically requested. Enabling this function for additional calendars just requires adding a new dictionary entry to `calendar_list` dictionary in `sackler/ReadRSS()`. Necessary items are the RSS feed URL as `rss_url`, a proper name/title for the calendar as `cal_name`, and a suffix for naming the ICS file as `cal_suffix`.

Modified the URL routing in `passenger_wsgi.py` to handle subcalendars.The subcalendar stub should match the short name used as the dictionary key for that calendar in `sackler.py`.

Modified `run_sackler.py` to also run an update to the `micro` calendar.

Also solved an issue with an unnecessary and erroneous `.decode` call when trying to pull more detail from the event page and populate the iCal fields. The code would probably be tightened up a bit and also need to properly sort out the `try`/`except`/`finally` syntax. Current usage is not quite right.

### Future plans ###
- Improve performance. The script takes a minute or so to run because it pulls the HTML from the Sackler website to get all of the details for each event. One possible way to improve this is to enter all retrieved URLs along with processed data into a database table, then check for new URLs that are not in the database at the beginning of the next run. The HTML for each new URL would be fetched, while existing information would just be drawn from the database. This should reduce the runtime significantly.
