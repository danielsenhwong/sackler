from sackler import ReadRSS
import pprint

ics = ReadRSS()
ics_micro = ReadRSS('micro')
ics_cmdb = ReadRSS('cmdb')
ics_neuro = ReadRSS('neuro')
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(ics)
pp.pprint(ics_micro)
