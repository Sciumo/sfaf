SFAF
====

This SFAF repository is a collection of tools for processing MCEB Pub 7 or SFAF data files.
* `sfaf.py`  Parses a SFAF file parameter into an array Python dictionaries using a CSV configuration file for mapping SFAF record types.
* `sfaf2db.py` Uses `sfaf.py` and `py2sql.py` to parse a SFAF file and transform the results into DDL and DML configured by `pystache` moustache templates

These SFAF tools demonstrates the concept of `Convetion over Configuration over Code` design approach through the use of JSON, CSV, and Templating.  
Like the Spring `Configuration over Code`approach, this approach focuses on externalizing all configuration outside of code to reuse/redeploy using configuration only.  
In addtion, like the `Convention over Configuration` design approach, there is only a loose coupling between code structure and configuration.   

Pystache
--------
Pystache is a Python implementation of the logic-less string template library Moustache (http://mustache.github.io/)  
The local 'sfaf' repository version is a fork of the original https://github.com/defunkt/pystache  

Pystache extensions:
* New operator {{%obj}}  implies an infix `separator` which is a property of the obj (e.g. obj.separator)
* The new separator property allows easy comma seprated lists. `{{%cols}}{{.}}{{/cols}}` will produce something like `col1,col2,col3`
* New {{>obj}} Object Specialization behavior which leverages Python Classes to dynamically lookup class associated template files.  
* For example `{{%cols}}{{>column}}{{/cols}}` will dynamically lookup subclasses of the `Column` python class


SFAF2DB
========

`sfaf2db.py` uses a Python dictionary mapping tool py2sql with a modified version of   
pystache to map a SFAF file to a configurable database SQL script.

Database configuration is done though a .json file and a pystache configuration directory.  
The pystache directory has two subdirectories:    
1. ./ddl contains Data Definition Language templates  
2. ./dml contains Data Manipulation Language templates  

New DB Configuration
--------------------
To create a new DB configuration, copy an existing DB configuration directory   
and modify the DDL and DML for your target database.


Usage
-----
This example demonstrates the usage of `sfaf2db` targeting 'SQLite' database.  

>python sfaf2db.py --dbconf=mcebpub7 ../../data/sfaf_sample_byfreq.txt > sqlite.sql  

This uses the default MCEB CSV configuration file:   
> DEFAULTSFAF="../MCEBPub7.csv"  

Pass in a '--format=' option to change the format file.    
>  --format=../mypub7formats.csv

Contents of mcebpub7.json
> {  
>   "array_subtables" : true,  
>	  "dbdir" : "./sqlite",  
>	  "array_template": "list_{{name}}"  
> }  
  
Creating SQLite database  
> sqlite3 sfaf < sqlite.sql
