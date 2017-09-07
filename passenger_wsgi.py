#import sys
"""passenger_wsgi.py
Provides support to run sackler as a Passenger application.
"""
from flask import Flask, Response, render_template
import os
from sackler import read_rss
application = Flask(__name__)

#def application(environ, start_response):
#	start_response('200 OK', [('Content-Type', 'text/plain')])
#	v = sys.version_info
#	str = 'hello world from %d.%d.%d!\n' % (v.major, v.minor, v.micro)
#	return [bytes(str, 'UTF-8')]

@application.template_filter(name='autoversion')
def autoversion_filter(filename):
    # From https://ana-balica.github.io/2014/02/01/autoversioning-static-assets-in-flask/
    # determining fullpath might be project specific
    fullpath = os.path.join('', filename[1:])
    try:
        timestamp = str(os.path.getmtime(fullpath))
    except OSError:
        return filename
    newfilename = "{0}?v={1}".format(filename, timestamp)
    return newfilename

@application.route("/")
def index():
    """index()
    Content to show if index page requested.
    """
    return render_template('index.html')

@application.route("/calendar", defaults={'subcalendar': 'sackler'})
@application.route("/calendar/<subcalendar>")
def sackler(subcalendar):
    """sackler(subcalendar)
    Run an update for one specific RSS calendar.
    """
    return Response(response=("The calendar script is scheduled to run every" \
                              "day at 4 AM and generate a new iCal file acce" \
                              "ssible at http://sackler.danielsenhwong.com/c" \
                              "alendar.ics and other sub-calendars like cale" \
                              "ndar_micro.ics.\n\nAccessing this page genera" \
                              "ted a new iCal file, which is presented below" \
                              "in plain text.\n\n", \
                              read_rss(subcalendar)), mimetype='text/plain')

if __name__ == "__main__":
    application.run()
