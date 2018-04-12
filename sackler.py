""" Sackler Calendar RSS Parser
Daniel Wong 2016 Mar 04

The Tufts Sackler School website has a calendar for upcoming events and
seminars, but it is just an RSS newsfeed and not a true calendar that
conforms to iCal or other calendar standards.

This script is an effort to parse this RSS feed and generate a more useful
product.

One issue I found is that the RSS feed items are sparse, consisting only of
the event time, title, and web page URL. Therefore, it would be best to go
to the event page URL and parse the HTML from the page.

Once done, take this data and populate a new Google Calendar.

Might be nice to also do some basic analytics on accession data by using
access logs in /var/log/httpd/. As of Jun 8, ~47 users requested the
various calendars. Some of these only appear once, e.g. Google Calendar
though I suspect it is more than one user.
"""

# Import necessary libraries
from datetime import datetime # Date/time processing
from time import strptime # Date/time formatting
import re # Regular expression for search
import feedparser # Parse RSS feed
import requests # Grab HTML
from bs4 import BeautifulSoup # Process HTML
from icalendar import Calendar, Event, vDatetime # Make iCal
from pytz import timezone # Timezone info for iCal

# Define some global variables
CALENDAR_LIST = {
    'sackler': {
        'rss_url': 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed' \
                   '.ashx?cid={F3B13FCF-27A3-44A2-A1B9-4672F1034B91}',
        'cal_name': 'Sackler Website Calendar',
        'cal_suffix': ''
    },
    'cmdb': {
        'rss_url': 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed' \
                   '.ashx?cid={39BDBCE0-8589-432A-8B13-DB805688ADCA}',
        'cal_name': 'CMDB Calendar',
        'cal_suffix': '_cmdb'
    },
    'gene': {
        'rss_url': 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed' \
                   '.ashx?cid={9B68062A-159E-4A1F-BDD6-2B1E061021E2}',
        'cal_name': 'Genetics Calendar',
        'cal_suffix': '_gene'
    },
    'immuno': {
        'rss_url': 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed' \
                   '.ashx?cid={47196DC1-83BE-4130-9460-C1DCA35ED6C8}',
        'cal_name': 'Immunology Calendar',
        'cal_suffix': '_immuno'
    },
    'micro': {
        'rss_url': 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed' \
                   '.ashx?cid={99F45320-2EA7-4996-B9D0-32B367C82440}',
        'cal_name': 'Molecular Microbiology Calendar',
        'cal_suffix': '_micro'
    },
    'neuro': {
        'rss_url': 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed' \
                   '.ashx?cid={E8AA928B-3EB7-49B8-9DE4-4909DFA5D732}',
        'cal_name': 'Neuroscience Calendar',
        'cal_suffix': '_neuro'
    },
    'ppet': {
        'rss_url': 'http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed' \
                   '.ashx?cid={265339A2-4E3D-4BC0-A4DE-B4E9786BEA1F}',
        'cal_name': 'PPET Calendar',
        'cal_suffix': '_ppet'
    },
}

def grab_rss(url='http://sackler.tufts.edu/Sites/Common/Data/CalendarFeed' \
'.ashx?cid={F3B13FCF-27A3-44A2-A1B9-4672F1034B91}'):
    """grab_rss(url)
    Break out the different small functions, like pulling the RSS feed
    Can be re-used to read any feed, but will read the full Sackler calendar by
    default.
    """
    feed = feedparser.parse(url) # Grab and parse the feed by item
    events = feed['items'] # Read the events into a list variable
    return events # Return the list for further processing

def grab_page(url):
    """grab_page(url)
    Much of the event detail is not actually supplied by the RSS feed.
    However, the URL for the event-specific page that does have all the detail
    is present, so we'll need to grab that.
    There are many elements on the page, but thankfully, the event information
    is contained within several HTML DIV elements all with the class "vevent".
    We'll want just those sections of the page, an not everything else.
    """
    page = requests.get(url) # Grab HTML
    vevent = None # Initialize an empty variable
    try: # Find the section of the page with the event information
        vevent = BeautifulSoup(page.text, 'html.parser').find(class_='vevent')
    except IndexError:
        pass
    finally:
        return vevent

def read_all_rss():
    """read_all_rss()
    Read all defined calendars in CALENDAR_LIST
    """
    results = []
    for calendar_name in CALENDAR_LIST:
        results.append(read_rss(calendar=calendar_name))

    return results

def read_rss(calendar="sackler", output_path="/var/www/sackler/public"):
    """read_rss(calendar, output_path)
    Read a specific RSS feed, parse it, and write the output to an iCal file.
    """
    #####
    # Process incoming parameters
    #####
    # Check to see which calendar is being requested.
    # Set up variables accordingly.
    if calendar in CALENDAR_LIST:
        rss_url = CALENDAR_LIST[calendar]['rss_url']
        cal_name = CALENDAR_LIST[calendar]['cal_name']
        cal_suffix = CALENDAR_LIST[calendar]['cal_suffix']

    #####
    # Start building the calendar
    #####
    cal = Calendar() # Initialize a blank calendar

    # The iCal standard provides space for some identifying information
    # Let's populate it so that the calendar looks pretty when people import
    # it into programs that use the fields. The calendar name in 'x-wr-calname'
    # is most important, closely followed by time zone as 'x-wr-timezone' so
    # events are properly scheduled, and then we'll put supporting info in
    # 'x-wr-caldesc'.
    calendar_properties = {
        # Must be unique, per iCal standard
        'prodid':       '-//'
                        + cal_name
                        + ', parsed (Daniel Senh Wong)//sackler.tufts.edu//EN',
        'version':      '2.0', # Must be 2.0 per iCal standard
        'calscale':     'GREGORIAN',
        'charset':      'UTF-8',
        'method':       'PUBLISH',
        'x-wr-calname': cal_name,
        'x-wr-timezone': 'America/New_York',
        'x-wr-caldesc': "This is the iCal-formatted version of the calendar" \
                        "presented on the Tufts Sackler school website (sac" \
                        "kler.tufts.edu). It is generated every morning at " \
                        "4 AM by a Python script that reads the calendar's " \
                        "RSS feed, then retrieves the event details from th" \
                        "e individual event pages.\n\nThe script feeding th" \
                        "is calendar was written and is maintained by Danie" \
                        "l Wong (PhD Candidate, Jay Lab/CMP) (daniel_s.wong" \
                        "@tufts.edu / danielsenhwong@gmail.com), and not by" \
                        "the Sackler Dean's Office. Please direct any quest" \
                        "ions, suggestions, or requests to me directly.",
    }

    # Add all of these calendar properties to the calendar object
    for field, value in calendar_properties.items():
        cal.add(field, value)

    ######
    # Prepare to interpret event data
    #####
    start_date_formats = [ # Different events have different formats
        '%B %d, %Y<br />%I:%M %p ', # Start and end the same day
        '%B %d, %Y %I:%M %p ', # Multiple day event
        '%B %d, %Y<br />%I:%M %p<br />', # No end time
    ]

    # Read the RSS feed of whichever calendar was requested.
    # Sackler calendar is default.
    events = grab_rss(rss_url) # Grab events from the RSS

    for event in events: # Loop through each individual event found
        # Prepare some variables
        tz_et = timezone('America/New_York') # Set our timezone
        e_tmp = Event() # Initialize a blank event
        description = '' # Initialize the description string

        # Pull the event information
        summary_str = event['title'] # Start with the given title for the event

        # Break up the time string to find the start time.
        # Input formats vary, see START_DATE_FORMATS variable above.
        start_str = event['summary'].split('&')[0]
        for date_format in start_date_formats:
            try: # Try each format
                start_dt = strptime(start_str, date_format)
            except ValueError: # If one fails, go back and try the next
                pass
            else: # Once one works, exit the loop
                # Give the event a start date and time
                dtstart = datetime(*start_dt[:6], tzinfo=tz_et)
                break

        # Break up the time string to find the end time
        end_str = event['summary'].split(';')[1].split('<br />')

        try: # Events starting and ending on the same day have one format
            end_dt = strptime(end_str[0], ' %I:%M %p')
            # Date information is missing, so borrow from start
            dtend = datetime(start_dt[0], start_dt[1], \
                    start_dt[2], *end_dt[3:5], tzinfo=tz_et)
        except ValueError: # Events spanning multiple days have another
            end_dt = strptime(end_str[1], ' %B %d, %Y %I:%M %p')
            dtend = datetime(*end_dt[:6], tzinfo=tz_et) # Has its own date
        except IndexError: # Events without an end time or date have another
            dtend = None # Has nothing
            
        # Grab the UID for this event
        # UID is encoded between curly braces in URL for event, presented as 'base' element in 'title_detail'
        event_uid_src = event['title_detail']['base']
        event_uid = re.split('[{}]', event_uid_src)[1]

        #####
        # Read event details from event-specific page
        #####
        # Now grab more details from the event page
        page = requests.get(event['link'])

        # The event details are wrapped in HTML DIV tags with the class
        # "vevent" within the "vevent" DIVs, there are child DIVs with
        # specific info
        try: # Try to find the div containing the event details
            # Just parse the div that has the event info
            vevent = BeautifulSoup(page.text, 'html.parser') \
                .find(class_='vevent')
            # Find the event-group divs
            e_group = vevent.find_all(class_='event-group')

            #####
            # Event speaker
            #####
            try: # If there is event info, see if there is a speaker
                speaker = vevent.find_all(class_='event-speaker')[0] \
                          .h4.text.strip()
            except IndexError:
                speaker = None
            finally:
                if speaker:
                    description = '%sSpeaker(s): %s\n' % (description, speaker)

            #####
            # Event speaker affiliation
            #####
            try: # See if there is an affiliation listed
                affiliation = vevent.find_all(class_='affiliation')[0].text
            except IndexError:
                affiliation = None
            finally:
                if affiliation:
                    description = '%sAffiliation: %s\n' % (description, affiliation)

            #####
            # Seminar title
            #####
            try: # See if there is a seminar title
                talk_title = vevent.find_all('p', {'id' : re.compile('.*seminarTitle')})[0].text
            except IndexError:
                talk_title = None
            finally:
                if talk_title:
                    # Add the talk title to the description
                    description = '%s"%s"\n' % (description, talk_title)
                    # Also add the talk title to the event name
                    summary_str = '%s, "%s"' % (summary_str, talk_title)

            #####
            # Detailed event description
            #####
            # The iCal standard doesn't have fields for the event speaker, etc.
            # So we'll put all of this both in the title of the calendar event
            # and the description, along with the full description, etc.
            #
            # The BeautifulSoup4 library is great. We can search through each
            # HTML element group to look for information.
            # Not every event has contact information, a room number,
            # or full description, but if present, these will be contained
            # within the last three HTML elements

            description = '%s\n' % description # add another new line

            # Start checking for more detail
            indicies = list(range(-3, 0)) # Make a list of reverse indices
            description_original = None # Initialize a blank variable
            room = None # Initialize a blank variable
            contact = None # Initialize a blank variable
            location = '' # Initialize a blank variable

            for i in indicies:
                try: # See if there is a room number and/or contact info
                    check_string = e_group[i].contents[1].text
                    if check_string == 'Contact Information': # Contact
                        # Remove all \r and \n from the ends, \t from the
                        # middle if there are any
                        contact = e_group[i].contents[3].text \
                                  .replace('\t', '') \
                                  .replace('\n\r\n', '\n').strip()
                    elif check_string == 'Directions & Parking':
                        # Building & room number are stored in Directions and
                        # Parking, not sure why
                        room = str(e_group[i].contents[2]).strip()
                    elif check_string == 'Description': # Full description
                        description_original = ''.join(str(d).strip() \
                                               for d in e_group[i] \
                                               .contents[3:len(e_group[i].contents)])
                except (IndexError, AttributeError):
                    pass
                finally:
                    if room:
                        # Google Maps will ignore information in parentheses,
                        # so we'll want the room number to be present but
                        # ignored if people try to map it
                        location = '(%s)' % room
                    if description_original:
                        description = '%s%s\n\n' % \
                                      (description, description_original)
                    if contact:
                        description = '%sContact: %s\n\n' % \
                                      (description, contact)

            # Sometimes the building address is given, so let's grab that
            try:
                # If there is event info, check to see if there is location info
                # try and find location information and make it presentable
                loc = ''.join(str(l).strip() for l in \
                      vevent.find_all(class_='location')[0].span.contents) \
                      .replace('<br/>', ', ')
            except IndexError: # If there's not, that's ok
                loc = None
            finally:
                location = '%s %s' % (location, loc)

            # Pass the location, if there is one, to the iCal event
            e_tmp.add('location', location)

        except AttributeError:
            # In case some pages can't be loaded or don't have the vevent div,
            # skip
            pass

        # Check for multi-day events that are scheduled by hour,
        # instead of daily
        # We don't want these events being giant blocks spanning all day
        # for multiple days, just marked as "all day events".
        if dtend:
            # Check the start and end times, and convert to an all-day event
            # if applicable
            dtdelta = dtend - dtstart
            if dtdelta.days > 0:
                dtstart = dtstart.date() # Convert to a date only
                dtend = dtend.date() # Convert to a date only

        #####
        # Populate the event item
        #####
        # add DTSTAMP property
        e_tmp.add('dtstamp', vDatetime(datetime.now(timezone('America/New_York'))).to_ical())
        e_tmp.add('uid', event_uid)
        e_tmp.add('dtstart', vDatetime(dtstart).to_ical()) # Add the start time to the Event() object
        if dtend:
            # Give the event an end date and time if there is anything to add
            e_tmp.add('dtend', vDatetime(dtend).to_ical())
        e_tmp.add('summary', summary_str) # Give the event a title
        # Put the event page URL in the description of the event
        e_tmp.add('description', '%s%s' % (description, event['link']))
        cal.add_component(e_tmp) # Add the event to the calendar

    # Export resulting calendar
    result = cal.to_ical()
    destination = '%s/%s' % (output_path, 'calendar' + cal_suffix + '.ics')
    f_tmp = open(destination, 'wb')
    f_tmp.write(result)
    f_tmp.close()

    return result
