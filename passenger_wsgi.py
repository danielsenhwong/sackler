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
def sackler():
	return Response(response=ReadRSS(), mimetype='text/calendar')


if __name__ == "__main__":
	application.run()
