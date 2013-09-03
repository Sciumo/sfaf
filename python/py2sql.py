#!/usr/bin/env python
"""SQL Map transforms results of an array of dictionaries such as produced 
	via sfaf.py reader into an SQL output via JSON configuration file."""

import re
import getopt
import json
import pystache
import os
import types
import inspect

__author__ = "Eric Lindahl"
__copyright__ = "Copyright 2012, Sciumo, Inc"
__credits__ = ["Eric Lindahl"]
__license__ = "LGPL v3"
__version__ = "0.0.2"
__maintainer__ = "Eric Lindahl"
__email__ = "eric.lindahl.tab@gmail.com"
__status__ = "Alpha"

DEFDB = "oracle"
PatString = re.compile("str(\((?P<len>\d+)\))?")
PatDouble = re.compile("doubl?e?")
PatName = re.compile("[_a-zA-Z][_a-zA-Z0-9]*$")
PatKey = re.compile("[_a-zA-Z0-9]+$")
PatJSON = re.compile(".+\.json$")
LONGOPTIONS = ["dbconf=","dbdir=","noddl"]

COLTYPES = {}

class Data(object):
	def __init__(self, sql_, data_):
		self.sql = sql_
		self.data = data_
		self.name = data_['name']
	def separator(self):
		return ", "

class Module(Data):
	def __init__(self, sql_, data_):
		super(Module,self).__init__(sql_,data_)

class Insert(Data):
	def __init__(self, sql_, table_):
		super(Insert,self).__init__(sql_,table_.data)
		self.table = table_
	def cols(self):
		cols = filter( lambda c: c.value() is not None, self.table.cols )
		return cols

def newCol(sql_,col_):
	typeinfo = col_['typeinfo']
	if inspect.isclass(typeinfo):
		return typeinfo(sql_,col_,None)
	m = PatDouble.match(typeinfo)
	if m is not None:
			return Double(sql_,col_,m)
	else:
		m = PatString.match(typeinfo)
		if m is not None:
			return String(sql_,col_,m)
	raise Exception("No column type for " + typeinfo )
				
class Table(Data):
	def __init__(self, sql_, data_):
		super(Table,self).__init__(sql_,data_)
		self.cols = []
		self.colsByName = {}
		self.insert = Insert(sql_,self)
	def registerCol(self,col_):
		col = newCol(self.sql,col_)
		if col.name in self.colsByName:
			raise Exception("Duplicate column name: table '%s' col '%s' attr '%s'" % (self.name,col.name,col.attr))
		self.cols.append( col )
		self.colsByName[col.name]=col
	def render(self,renderer_):
		return renderer_.render(self.insert)

class ArrayTable(Table):
	def __init__(self, sql_, primary_, data_):
		super(ArrayTable,self).__init__(sql_,data_)
		self.primary = primary_
		self.primaryCol = primary_.primaryCol
		self.foreign = Foreign(sql_,self.primary)
		self.index = Index(sql_,self.primaryCol.data)
	def render(self,renderer_):
		self.index.index = 0
		dml = ""
		col = self.col = self.cols[0]
		vals = self.sql.value(col.attr)
		if vals is None:
			return "";
		if len(vals) > 0 and isinstance(vals, types.StringTypes):
			raise Exception("Unexpected non-list")
		for val in vals:
			self.col.val = val
			dml += renderer_.render(self) + "\n"
			self.index.index += 1
		return dml
	
class Column(Data):
	def __init__(self, sql_, data_, matchinfo_):
		super(Column,self).__init__(sql_,data_)
		self.match = matchinfo_
		self.table = data_['table']
		self.attr = data_['attr']
		if PatKey.match(self.attr) is None:
			raise Exception("Invalid attr name: table '%s' col '%s' attr '%s'" % (self.table,self.name,self.attr))
		if PatName.match(self.name) is None:
			raise Exception("Invalid column name: table '%s' col '%s' attr '%s'" % (self.table,self.name,self.attr))
		self.val = None
	def value(self):
		if self.val is not None:
			return self.val
		return self.sql.value(self.attr)

	
class Double(Column):
	def __init__(self, sql_, data_, matchinfo_):
		super(Double,self).__init__(sql_,data_,matchinfo_)

class String(Column):
	def __init__(self, sql_, data_, matchinfo_):
		super(String,self).__init__(sql_,data_,matchinfo_)
		self.len = matchinfo_.group("len")
		if self.len is None:
			self.len = "32"


class LatLon(Column):
	def __init__(self, sql_, data_, matchinfo_):
		super(LatLon,self).__init__(sql_,data_,matchinfo_)
		self.name_ddl = self.name + "_lat REAL, " + self.name + "_lon REAL"
		self.name = self.name + "_lat, " + self.name + "_lon"
	def value(self):
		if self.val is not None:
			return self.val
		return self.sql.value(self.attr)

class Primary(Column):
	def __init__(self, sql_, data_, table_):
		super(Primary,self).__init__(sql_,data_,None)
		self.table = table_

class Foreign(Column):
	def __init__(self, sql_, table_):
		super(Foreign,self).__init__(sql_,table_.primaryCol.data,None)
		self.foreigntable = table_
		self.primary = table_.primaryCol
		self.key = self.foreigntable.name + "_" + self.primary.name
	def keyname(self):
		return self.foreigntable.name + "_" + self.primary.name

class Index(Column):
	def __init__(self, sql_, data_):
		super(Index,self).__init__(sql_,data_,None)
		self.name = "idx"
		self.index = 0
	
class Py2SQL(object):
	def __init__(self,argv,cols_):
		self.db = DEFDB
		self.noddl = False
		self.dbdir = None
		self.tables = {}
		self.tableList = []
		optlist, _ = getopt.getopt(argv, "", LONGOPTIONS)
		for opt,arg in optlist:
			if opt == "--dbconf":
				self.dbconfFile = arg
			elif opt == "--dbdir":
				self.dbdir = arg
			elif opt == "--noddl":
				self.noddl = True
		if self.dbconfFile is None:
			raise Exception( "Missing required --dbconf file.")
		if PatJSON.match( self.dbconfFile ) is None:
			self.dbconfFile += ".json"
		if not os.path.isfile(self.dbconfFile):
			raise Exception( "Missing DBConf file. %s" % (self.dbconfFile) )
		with open (self.dbconfFile, "r") as f:
			self.dbconf = json.load(f)
		if self.dbdir is None:
			if "dbdir" not in self.dbconf:
				raise Exception("Missing required --dbdir parameter or dbconf parameter.")
			self.dbdir = self.dbconf["dbdir"]
		if not os.path.isdir(self.dbdir):
			raise Exception("DBDir doesn't exists %s" % (self.dbdir) )
		self.ddldbdir = self.dbdir + "/ddl"
		if not os.path.isdir(self.ddldbdir):
			raise Exception("DBDir/ddl doesn't exists %s" % (self.ddldbdir) )
		self.dmldbdir = self.dbdir + "/dml"
		if not os.path.isdir(self.dmldbdir):
			raise Exception("DBDir/dml doesn't exists %s" % (self.dmldbdir) )
		self.ddlrenderer = pystache.Renderer(search_dirs=[self.ddldbdir])
		self.dmlrenderer = pystache.Renderer(search_dirs=[self.dmldbdir])
		self.arraySubtables = self.dbconf["array_subtables"]
		if self.arraySubtables:
			if (not "array_template" in self.dbconf):
				self.dbconf["array_template"] = "arraytablename"
				self.arrayTemplate = self.ddlrenderer.load_template(self.dbconf["array_template"])
			else:
				self.arrayTemplate = pystache.parse(self.dbconf["array_template"])
			if self.arrayTemplate is None:
				raise Exception("Array table name template unable to load. %s" % (self.dbconf["array_template"]))
		for col in cols_.keys():
			self.registerCol( col, cols_[col] )
		self.genddl()
	def value(self,attr_):
		val = self.currec.get(attr_,None)
		return val
	def dml(self,recs_,cnt_):
		dml = ""
		rend = self.dmlrenderer
		for rec in recs_:
			self.currec = rec
			for table in self.tableList:
				dml += table.render(rend)
		return dml
	def registerCol(self, name_, col_):
		isArray = self.arraySubtables and ("IsArray" in col_) and col_["IsArray"]
		tableName = col_["table"]
		if isArray:
			master = tableName
			tableName = self.ddlrenderer.render(self.arrayTemplate,col_)	
		if PatName.match(tableName) is None:
			raise Exception("Invalid table name '%s' col '%s' attr '%s'" % (tableName,col_['name'],col_['attr']))
		table = self.tables.get(tableName)
		if table is None:
			if isArray:
				masterTable = self.tables.get(master)
				if masterTable is None:
					raise Exception( "Unable to find primary table %s for array subtable %s" % (master,tableName))
				if not hasattr(masterTable,'primaryCol'):
					masterTable.primaryCol = Primary( self, {'name':'id', 'attr':'None', 'table':master}, masterTable )
					masterTable.cols.insert(0,masterTable.primaryCol)
					masterTable.colsByName["id"] = masterTable.primaryCol
				table = ArrayTable(self, masterTable, {'name':tableName })
			else:
				table = Table(self, { 'name':tableName })
			self.tables[tableName] = table
			self.tableList.append(table)
		table.registerCol(col_)
	def genddl(self):	
		self.ddl = None
		rend = self.ddlrenderer
		if self.noddl:
			return
		ddl = ""
		for table in self.tableList:
			ddl += rend.render(table) + "\n"
		self.ddl = ddl
		return ddl
