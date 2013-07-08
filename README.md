SFAF
====

Tools for processing MCEB Pub 7 or SFAF data files.


SFAF2SQL
========

sfaf2sql uses a Python dictionary mapping tool py2sql with a modified version of pystache to map a SFAF file to a configurable database SQL script.

Database configuration is done though a .json file and a pystache configuration directory.
The pystache directory has two subdirectories:
1. ./ddl contains Data Definition Language templates
2. ./dml contains Data Manipulation Language templates

New DB Configuration
--------------------
To create a new DB configuration, copy an existing DB configuration directory and modify the DDL and DML for your target database.


Usage
-----

   python sfaf2db.py --dbconf=mcebpub7 ../../data/sfaf_sample_byfreq.txt > sqlite.sql
   
Contents of mcebpub7.json
  {
    "array_subtables" : true,
	  "dbdir" : "./sqlite",
	  "array_template": "list_{{name}}"
  }
  
Creating SQLite database
  sqlite3 sfaf < sqlite.sql
