#!/usr/bin/env python

import sfaf
import py2sql
import sys
import re
import types
import inspect

def cleanargs(list_): return lambda a_: (not (a_[2:a_.find('=')+1] in list_))

sfafargs = filter(cleanargs(py2sql.LONGOPTIONS), sys.argv[1:]) 

meta = sfaf.readSFAFFormats(sfafargs)

coldefs = {}
for coldef in meta.keys():
	col = meta[coldef]
	if col[11] is None or len(col[11]) < 1:
		continue
	tcol = col[11].split(".")
	if len(tcol) < 2:
		raise Exception("Column definition table.column at: " + str(coldef) )
	typeinfo = col[12]
	isarray = False
	if col[8] == "TRUE":
		isarray = True
	coldefs[coldef] = { 'table': tcol[0], 'attr':str(coldef), 'name' : tcol[1], 'typeinfo' : typeinfo, "IsArray":isarray }

ll = py2sql.LatLon
llt = inspect.isclass(ll)

coldefs['303_ll'] = { 'table': 'sfaf', 'attr':'303_ll', 'name' : 'tx_coords', 'typeinfo' : py2sql.LatLon, "IsArray": False }
coldefs['110_rej_freq'] = { 'table': 'sfaf', 'attr':'110_rej_freq', 'name' : 'rejected_freq', 'typeinfo' : py2sql.Double, "IsArray": False }
coldefs['110_freq'] = { 'table': 'sfaf', 'attr':'110_freq', 'name' : 'assigned_freq', 'typeinfo' : py2sql.Double, "IsArray": False }

sql = py2sql.Py2SQL(filter(cleanargs(sfaf.LONGOPTIONS),sys.argv[1:]),coldefs)

if sql.ddl:
	print sql.ddl
	
def dml(recs_,cnt_):
	print sql.dml(recs_,cnt_)
	
sfaf.readSFAFRecs(sfafargs,meta,dml)
