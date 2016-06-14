"""run_sackler.py
A unified script to run Sackler RSS to iCal conversion updates from the
command line.
"""
import pprint
from sackler import read_all_rss

ICS = read_all_rss()
PP = pprint.PrettyPrinter(indent=4)
PP.pprint(ICS)
