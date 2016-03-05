# sackler

Projects related to the Sackler school.

Site currently running Python apps via Flask and Passenger.

## Calendar##
A script to parse the Sackler school calendar RSS feed and output an iCal calendar file. Accessible at http://sackler.danielsenhwong.com/calendar (runs script and generates new file) and http://sackler.danielsenhwong.com/calendar.ics (target address for calendar subscriptions and file created by previous script run)

Future plans:
- Improve performance. The script takes a minute or so to run because it pulls the HTML from the Sackler website to get all of the details for each event. One possible way to improve this is to enter all retrieved URLs along with processed data into a database table, then check for new URLs that are not in the database at the beginning of the next run. The HTML for each new URL would be fetched, while existing information would just be drawn from the database. This should reduce the runtime significantly.
