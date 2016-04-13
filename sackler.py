# Sackler Calendar RSS Parser
# Daniel Wong 2016 Mar 04

# The Tufts Sackler School website has a calendar for upcoming events and seminars, but it is just an RSS newsfeed and not a true calendar that conforms to iCal or other calendar standards.
# This script is an effort to parse this RSS feed and generate a more useful product.
# One issue I found is that the RSS feed items are sparse, consisting only of the event time, title, and web page URL. Therefore, it would be best to go to the event page URL and parse the HTML from the page.
# Once done, take this data and populate a new Google Calendar

# Import necessary libraries

import feedparser # Parse RSS feed
import requests # Grab HTML
from bs4 import BeautifulSoup # Process HTML
from icalendar import Calendar, Event # Make iCal
from datetime import datetime # Date/time processing
from pytz import timezone # Timezone info for iCal
import pytz # Timezone info for iCal
from time import strptime, strftime # Date/time formatting
import re # Regular expression for search

def GrabRSS(url="http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed.ashx?cid={F3B13FCF-27A3-44A2-A1B9-4672F1034B91}"):
    feed = feedparser.parse(url) # Parse the feed
    events = feed['items'] # Read the events into a list variable
    return events

def GrabPage(url):
    page = requests.get(url) # Grab HTML
    vevent = None
    try:
        vevent = BeautifulSoup(page.text, 'html.parser').find(class_='vevent')
    except IndexError:
        pass
    finally:
        return vevent

def ReadRSS(calendar="sackler", output_path="/var/www/sackler/public"):
    # Process incoming parameters
    # Make a dictionary list of the calendars, with dictionary of dependent variables
    calendar_list = { 
        'sackler': {
            'rss_url': 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed.ashx?cid={F3B13FCF-27A3-44A2-A1B9-4672F1034B91}',
            'cal_name': 'Sackler Website Calendar',
            'cal_suffix': ''
        },
        'micro': {
            'rss_url': 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed.ashx?cid={99F45320-2EA7-4996-B9D0-32B367C82440}',
            'cal_name': 'Molecular Microbiology Calendar',
            'cal_suffix': '_micro'
        },
    }

    if calendar in calendar_list:
        rss_url = calendar_list[calendar]['rss_url']
        cal_name = calendar_list[calendar]['cal_name']
        cal_suffix = calendar_list[calendar]['cal_suffix']

    cal = Calendar() # Initialize a blank calendar

    calendar_properties = {
        'prodid':       '-//' + cal_name + ', parsed (Daniel Senh Wong)//sackler.tufts.edu//EN', # Must be unique, per iCal standard
        'version':      '2.0', # Must be 2.0 per iCal standard
        'calscale':     'GREGORIAN',
        'method':       'PUBLISH',
        'x-wr-calname': cal_name,
        'x-wr-timezone':        'America/New_York',
        'x-wr-caldesc':  "This is the iCal-formatted version of the calendar presented on the Tufts Sackler school website (sackler.tufts.edu). It is generated every morning at 4 AM by a Python script that reads the calendar's RSS feed, then retrieves the event details from the individual event pages.\n\nThe script feeding this calendar was written and is maintained by Daniel Wong (daniel_s.wong@tufts.edu / danielsenhwong@gmail.com), and not by the Sackler Dean's Office. Please direct any questions, suggestions, or requests to me directly.",
     }

    for field, value in calendar_properties.items():
        cal.add(field, value)

    START_DATE_FORMATS = [ # Different events have different formats
        '%B %d, %Y<br />%I:%M %p ', # Start and end the same day
        '%B %d, %Y %I:%M %p ', # Multiple day event
        '%B %d, %Y<br />%I:%M %p<br />', # No end time
    ]

    #sackler_rss_url = 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed.ashx?cid={F3B13FCF-27A3-44A2-A1B9-4672F1034B91}' # Sackler calendar RSS feed URL

    events = GrabRSS(rss_url) # Grab events from the RSS

    for event in events: # Loop through each individual event found
        tz_et = timezone('America/New_York') # Set our timezone
        e = Event() # Initialize a blank event
        description = '' # Initialize the description string

        summary_str = event['title'] # Start with the given title for the event

        start_str = event['summary'].split('&')[0] # Break up the time string to find the start time
        for date_format in START_DATE_FORMATS:
            try: # Try each format
                start_dt = strptime(start_str, date_format)
            except ValueError: # If one fails, go back and try the next
                pass
            else: # Once one works, exit the loop
                dtstart = datetime(*start_dt[:6], tzinfo=tz_et) # Give the event a start date and time
                break

        end_str = event['summary'].split(';') # Break up the time string to find the end time
 
        try: # Events starting and ending on the same day have one format
            end_dt = strptime(end_str[1], ' %I:%M %p<br />')
            dtend = datetime(start_dt[0], start_dt[1], start_dt[2], *end_dt[3:5], tzinfo=tz_et) # Date information is missing, so borrow from start
        except ValueError: # Events spanning multiple days have another
            end_dt = strptime(end_str[1], '<br /> %B %d, %Y %I:%M %p<br />')
            dtend = datetime(*end_dt[:6], tzinfo=tz_et) # Has its own date
        except IndexError: # Events without an end time or date have another
            dtend = None # Has nothing

        page = requests.get(event['link']) # Now grab more details from the event page
        try: # Try to find the div containing the event details
            vevent = BeautifulSoup(page.text, 'html.parser').find(class_='vevent') # Just parse the div that has the event info
            eg = vevent.find_all(class_='event-group') # Find the event-group divs

            try: # If there is event info, see if there is a speaker
                speaker =  vevent.find_all(class_='event-speaker')[0].h4.text.strip()
            except IndexError:
                speaker = None
            finally:
                if speaker:
                    description = '%sSpeaker(s): %s\n' % (description, speaker)

            try: # See if there is an affiliation listed
                affiliation = vevent.find_all(class_='affiliation')[0].text
            except IndexError:
                    affiliation = None
            finally:
                if affiliation:
                    description = '%sAffiliation: %s\n' % (description, affiliation)

            try: # See if there is a seminar title
                talk_title = vevent.find_all('p', {'id' : re.compile('.*seminarTitle')})[0].text
            except IndexError:
                talk_title = None
            finally:
                if talk_title:
                    description = '%s"%s"\n' % (description, talk_title) # Add the talk title to the description
                    summary_str = '%s, "%s"' % (summary_str, talk_title) # Also add the talk title to the event name

            description = '%s\n' % description # add another new line
            
            # Start checking for more detail
            indicies = list(range(-3,0)) # Make a list of reverse indices
            description_original = None
            room = None
            contact = None
            location = ''
            for i in indicies:
                try: # See if there is a room number and/or contact info
                    check_string = eg[i].contents[1].text
                    if check_string == 'Contact Information':
                        contact = eg[i].contents[3].text.replace('\t', '').replace('\n\r\n', '\n').strip() # Remove all \r and \n from the ends, \t from the middle if there are any
                    elif check_string == 'Directions & Parking':
                        room = str(eg[i].contents[2]).strip()
                    elif check_string == 'Description':
                        description_original = ''.join(str(d).strip() for d in eg[i].contents[3:len(eg[i].contents)])
                except (IndexError, AttributeError):
                    pass
                finally:
                    if room:
                        location = '(%s)' % room
                    if description_original:
                        description = '%s%s\n\n' % (description.decode, description_original.decode)
                    if contact:
                        description = '%sContact: %s\n\n' % (description.decode, contact)
            
            try: # If there is event info, check to see if there is location info
                loc = ''.join(str(l).strip() for l in vevent.find_all(class_='location')[0].span.contents).replace('<br/>',', ') # try and find location information and make it presentable
            except IndexError: # If there's not, that's ok
                loc = None
            finally:
                location = '%s %s' % (location, loc)

            e.add('location', location) # Pass the location, if there is one, to the iCal event

        except AttributeError: # In case some pages can't be loaded or don't have the vevent div, skip
            pass

        if dtend:
            dtdelta = dtend - dtstart # Check the start and end times, and convert to an all-day event if applicable
            if dtdelta.days > 0:
                dtstart = dtstart.date() # Convert to a date only
                dtend = dtend.date() # Convert to a date only

        e.add('dtstart', dtstart) # Add the start time to the Event() object
        if dtend:
            e.add('dtend', dtend) # Give the event an end date and time if there is anything to add
        e.add('summary', summary_str) # Give the event a title
        e.add('description', '%s%s' % (description, event['link'])) # Put the event page URL in the description of the event
        if location:
            e.add('location', location)
        cal.add_component(e) # Add the event to the calendar

    # Export resulting calendar
    result = cal.to_ical()
    destination = '%s/%s' % (output_path, 'calendar' + cal_suffix + '.ics')
    f = open(destination, 'wb')
    f.write(result)
    f.close()

    return result
