from sackler import ReadRSS
import pprint

ics = ReadRSS()
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(ics)
