#import sys
from flask import Flask, Response
from sackler import ReadRSS
application = Flask(__name__)

#def application(environ, start_response):
#	start_response('200 OK', [('Content-Type', 'text/plain')])
#	v = sys.version_info
#	str = 'hello world from %d.%d.%d!\n' % (v.major, v.minor, v.micro)
#	return [bytes(str, 'UTF-8')]

@application.route("/")
def hello():
	return "Hello World!"

@application.route("/calendar")
@application.route("/calendar/<subcalendar>")
def sackler(subcalendar=''):
#	return Response(response=ReadRSS(), mimetype='text/calendar')
	return Response(response=("The calendar script is scheduled to run every day at 4 AM and generate a new iCal file accessible at http://sackler.danielsenhwong.com/calendar.ics and other sub-calendars like calendar_micro.ics\n\nAccessing this page generated a new iCal file, which is presented below in plain text.\n\n", ReadRSS(subcalendar)), mimetype='text/plain')

if __name__ == "__main__":
	application.run()
