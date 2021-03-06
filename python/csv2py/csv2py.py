#!/usr/bin/env python
# encoding: utf-8
'''
csv2py.csv2py -- converts a CSV file into a python dictionary using pystache with regular expression mapping

@author:     Eric Lindahl
			
@copyright:  2013 Sciumo Inc. All rights reserved.
			
@license:    LGPL v3

@contact:    eric.lindahl.tab@gmail.com
@deffield    updated: 2013-08-16
'''

import sys
import os

from optparse import OptionParser

__all__ = []
__date__ = '2013-08-16'
__updated__ = '2013-08-16'
__author__ = "Eric Lindahl"
__copyright__ = "Copyright 2013, Sciumo, Inc"
__credits__ = ["Eric Lindahl"]
__license__ = "LGPL v3"
__version__ = "0.0.1"
__maintainer__ = "Eric Lindahl"
__email__ = "eric.lindahl.tab@gmail.com"
__status__ = "Alpha"

DEBUG = 1
TESTRUN = 0
PROFILE = 0

def csv2py( opts_ ):
	print( str(opts_) )
	
def main(argv=None):
	'''Command line options.'''
	
	program_name = os.path.basename(sys.argv[0])
	program_version = __version__
	program_build_date = "%s" % __updated__
	
	program_version_string = '%%prog %s (%s)' % (program_version, program_build_date)
	#program_usage = '''usage: spam two eggs''' # optional - will be autogenerated by optparse
	program_longdesc = '''''' # optional - give further explanation about what the program does
	program_license = "%s                                            \
				Author %s (%s)                                                      \
				Licensed under the %s" % (__copyright__,__author__,__email__,__license__)
	
	if argv is None:
		argv = sys.argv[1:]
	try:
		# setup option parser
		parser = OptionParser(version=program_version_string, epilog=program_longdesc, description=program_license)
		parser.add_option("-i", "--csv", dest="infile", help="set input path [default: %default]", metavar="CSVFILE")
		parser.add_option("-o", "--out", dest="outfile", help="set output path [default: %default]", metavar="STDOUT")
		parser.add_option("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %default]")
		
		# set defaults
		parser.set_defaults(outfile="./(file_name).py", infile="./data.csv")
		
		# process options
		(opts, args) = parser.parse_args(argv)
		
		if opts.verbose > 0:
			print("verbosity level = %d" % opts.verbose)
		if opts.infile:
			print("infile = %s" % opts.infile)
		if opts.outfile:
			print("outfile = %s" % opts.outfile)
			
		# MAIN BODY #
		
	except Exception as e:
		sys.stderr.write( "Args: %s\n" % (sys.argv[1:]) )
		indent = len(program_name) * " "
		sys.stderr.write(program_name + ": " + repr(e) + "\n")
		sys.stderr.write(indent + "  for help use --help")
		return 2
	except:
		sys.stderr.write( "Unexpected error: %s\n" % (str(sys.exc_info()[0])) )
		sys.stderr.write( "Args: %s\n" % (sys.argv[1:]) )
		return 3


if __name__ == "__main__":
	if DEBUG:
		sys.argv.append("-h")
	if TESTRUN:
		import doctest
		doctest.testmod()
	if PROFILE:
		import cProfile
		import pstats
		profile_filename = 'csv2py.csv2py_profile.txt'
		cProfile.run('main()', profile_filename)
		statsfile = open("profile_stats.txt", "wb")
		p = pstats.Stats(profile_filename, stream=statsfile)
		stats = p.strip_dirs().sort_stats('cumulative')
		stats.print_stats()
		statsfile.close()
		sys.exit(0)
	status = main()
	sys.exit(status)