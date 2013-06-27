#!/usr/bin/env python

import re
import csv
import sys
import getopt
import types
import pprint


_author__ = "Eric Lindahl"
__copyright__ = "Copyright 2012, Sciumo, Inc"
__credits__ = ["Eric Lindahl"]
__license__ = "LGPL"
__version__ = "0.0.1"
__maintainer__ = "Eric Lindahl"
__email__ = "eric.lindahl.tab@gmail.com"
__status__ = "Alpha"


Metadata = None
cur_line = 0
pp = pprint.PrettyPrinter(indent=4)

def integer(s_):
	"""Parse a string to an Integer or None on error"""
	try:
		return int(s_)
	except ValueError:
		return None
		
def dmsToDD( dms_ ):
	"""DMS to degrees dictionary update"""
	sign = 1.0;
	if dms_['dir'] == "S" or dms_['dir'] == "W":
		sign = -1.0
	dd = dms_['min']*60.0 + dms_['sec']
	dd = sign * (dms_['deg'] + dd/3600.0)
	return dd


def latI180(dms_):
	"""Normalize dms_.lat.dec into 180.0 degrees"""
	lat = Math.floor( dms_['lat']['dec'] + 90.0 )
	return lat

#Regular expression for DMS
regDMS = re.compile("([0-9]{2})([0-9]{2})([0-9X]{2})([nsNS])([0-9]{3})([0-9]{2})([0-9X]{2})([ewEW])")

def parseDMS(str_):
	"""Parse a DMS string and return a dictionary with DMS and deg entries"""
	mdms = regDMS.match(str_)
	if mdms is None:
		print "!error parse DMS :" + str_
		return None
	d = mdms.groups()
	seclat = d[2].replace("X","0")
	seclon = d[6].replace("X","9")
	latlon = { 
		"lat": {
			"deg": integer(d[0]), "min": integer(d[1]), "sec":integer(seclat), "dir": d[3].upper() 
		},
		"lon": { 
			"deg": integer(d[4]), "min": integer(d[5]), "sec":integer(seclon), "dir": d[7].upper()
		}
	}
	
	latlon['lat']['dec'] = dmsToDD(latlon['lat'])
	latlon['lon']['dec'] = dmsToDD(latlon['lon'])
	return latlon

#Rechandlers registry for specific SFAF specific handlers. 
recHandlers = {}

#Frequency multiples for normalizing frequency to megahertz 
freqMultiple = { 'K': 0.001, 'M': 1.0, 'G':1000.0, 'T':1000000.0 }

regCenterF = re.compile("([KMGT])([0-9]+)")
regBand = re.compile("([KMGT])([0-9]+)\-([KMGT])([0-9]+)")
regDefBand = re.compile("([KMGT])([0-9]+)\-([0-9]+)")

def onHandleFreqMulti(rec_,recNum_,recSup_,recVal_):
	band = regDefBand.match(recVal_)
	if band is None:
		return None
	d = band.groups()

	mult = freqMultiple[d[0]]
	res = str(mult * float(d[1])) + ", " + str(mult * float(d[2]))
	
	#b = 1
	#while 	str(recNum_) + "_" + str(b) + "_band" in rec_.keys():
	#	b = b + 1
	#recId = str(recNum_) + "_" + str(b) + "_band"
	recId = str(recNum_)
	rec_[recId] = res
	return res
	
def onHandleDouble(rec_,recNum_,recSup_,recVal_):
	try:
		val = float(recVal_)
		if not val is None:
			recId = str(recNum_)
			rec_[recId] = str(val)
			return val
	except:
		return None
	return None
	
def onHandleFreq(rec_,recNum_,recSup_,recVal_):
	band = regBand.match(recVal_)
	if band is None:
		band = regDefBand.match(recVal_)
		if band is None:
			freq = regCenterF.match(recVal_)
			if freq is None:
				return None
			d = freq.groups()
			recId = str(recNum_) + "_freq"
			res = freqMultiple[d[0]] * float(d[1])
		else:
			d = band.groups()
			recId = str(recNum_) + "_band"
			mult = freqMultiple[d[0]]
			res = str(mult * float(d[1])) + ", " + str(mult * float(d[2]))
			#print recNum_, recVal_, recId, res

		rec_[recId] = res
	else:
		d = band.groups()
		recId = str(recNum_) + "_band"
		#res = [freqMultiple[d[0]] * float(d[1]),freqMultiple[d[2]] * float(d[3])]
		res = str(freqMultiple[d[0]] * float(d[1])) + ", " + str(freqMultiple[d[2]] * float(d[3]))
		rec_[recId] = res
		#print recNum_, recVal_, recId, res

	return res
	
def onHandleDMS(rec_,recNum_,recSup_,recVal_):
	try:
		recId = str(recNum_) + "_ll"
		res = parseDMS(recVal_)
		rec_[recId] = str(res['lat']['dec']) + "," + str(res['lon']['dec'])
		return res
	except:
		print "Error on DMS parse:" + recVal_ + " Line:" + str(cur_line)
		return None

recHandlers[110] = onHandleFreq
recHandlers[111] = onHandleFreqMulti
recHandlers[303] = onHandleDMS
recHandlers[306] = onHandleDouble
recHandlers[403] = onHandleDMS

p7line = re.compile("([0-9]+)(\/([0-9]+))?\s*\.\s*(.*)")

def parsep7(line_, lastRec, lastRecNum, fmts_):
	mrec = p7line.match(line_)
	if mrec is None:
		print "No Match Fail on:'" + line_ + "'" + "Line:" + str(cur_line)
		return None
	groups = len(mrec.groups())
	if groups < 4:
		print "Fail groups on: " + line_ + "Line:" + str(cur_line)
		return None
	rec = {}
	recVal = mrec.group(4)
	recNum = integer(mrec.group(1))
	recSup = mrec.group(3)
	fmt = ['000','Unknown','UNK','','','','','','FALSE',str(recNum)]
	
	if not recNum in fmts_.keys():
		print "!!No format for: ", recNum
	else:
		fmt = fmts_[recNum]
	recId = fmt[9]
	
	if recNum < 10 and recNum < lastRecNum:
		rec[recId] = recVal
		return rec, lastRec, recNum, True
		
	isArray = not (fmt[8] == "FALSE")
	
	if recSup is not None and len(recSup) > 0:
		recSup = integer(recSup)
	
	if isArray:
		recsuplist = []
		if recNum not in lastRec.keys():
			lastRec[recId] = recsuplist
		else:
			lastRecVal = lastRec[recNum]
			if type(lastRecVal) is not list:
				recsuplist.append( lastRecVal )
				lastRec[recId] = recsuplist
			else:
				recsuplist = lastRecVal
				
		recsuplist.append(recVal)
	else:
		if recId in lastRec.keys():
			if recNum is not 5:
				lastRec[recId] = lastRec[recId] + "\n" + recVal
			else:
				lastRec[recId] = recVal
		else:
			lastRec[recId] = recVal
	
	if recNum in recHandlers.keys():
		#print "Rec handler", recNum
		recHandler = recHandlers[recNum]
		if type(recHandler) is types.FunctionType:
			recHandler(lastRec, recNum, recSup, recVal)
	return rec, lastRec, recNum, False

DEFAULTSFAF="../MCEBPub7.csv"

def read_sfaf_fmts( file_=DEFAULTSFAF, dometa = False ):
	"""Read SFAF column format information"""
#	print "sfaf formats:",file_, "metadata:", dometa
	sfmts={}
	meta = []
	with open(file_, 'rbU') as csvfile:
		fmts = csv.reader(csvfile, dialect='excel', delimiter=',')
		fmts.next() #skip header
		for fmt in fmts:
			meta.append(fmt)
			code = integer(fmt[0])
			if code is None:
				print "Unknown row:",fmt
			else:
				sfmts[code] = fmt
	return sfmts, meta

def recprint(recs_,cnt_):
	"""Print all records"""
	pp.pprint(recs_)
	
def readAllRecs( file_, fmts_, batch=1000, callback=recprint ):
	global cur_line
	recs = []
	id = "sfaf:" + file_
	cnt = 1
	cur_line = 0
	with open(file_, "rtU") as f:
		lastRec = {}
		lastRecNum = 0
		for line in f:
			cur_line = cur_line + 1
			rec, lastRec, lastRecNum, isnew = parsep7(line, lastRec, lastRecNum, fmts_)
			if isnew:
				#print rec
				recid = id + "_" + str(cnt)
				lastRec['id'] = recid
				recs.append( lastRec )
				cnt = cnt + 1
				lastRec = rec
				if cnt % batch == 0:
					callback(recs,cnt)
					recs = []
		callback(recs,cnt)
	return recs

sfaf_fmts = {}

def readSFAF(argv,batch=1000,callback=recprint,metadata=False):
	"""Read all records from file using SFAF format CSV for column information.
	Batch the results and call callback every batch records and flush to limit memory.
	"""
	cur_line = 0
	readMeta = False
	fmtfile = DEFAULTSFAF
	meta = None
	optlist, args = getopt.getopt(argv, "", ["format=","metadata"])
	
	for opt,arg in optlist:
		if opt == "--format":
			print "SFAF Formats:", arg
			fmtfile=arg
		elif opt == "--metadata":
			readMeta = True

	sfaf_fmts, meta = read_sfaf_fmts(fmtfile,metadata)
	if readMeta:
		return None, meta

	if len(args) < 1:
		print "no input file. usage 'sfaf [--format] inputfile'"
		return
	infile = args[0]
#	print "Reading input: ", infile, "Batch:", batch
	recs = readAllRecs(infile,sfaf_fmts,batch,callback)
	return recs, meta

	
if __name__ == "__main__":
	recs, Metadata = readSFAF(sys.argv[1:],80,callback=recprint)
