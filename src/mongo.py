"""mongodb - MongoDB support"""

# mongo.py
# Copyright (C) 2012 Wolfgang Pirker <w_pirker@gmx.de>
# 
# notesapp is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# notesapp is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

#HOST = 'alex.mongohq.com'
#'mongo1.mongood.com,mongo2.mongood.com,mongo3.mongood.com'
# c = ReplicaSetConnection('mongo1.mongood.com:27017,mongo2.mongood.com:27017,mongo3.mongood.com:27017,mongo4.mongood.com:27017' ,replicaSet='cluster')

MODE = 'single' # 'replica' not implemented yet!

import os
import uuid 
from datetime import datetime
import notesapp 
import filesys
import time
import encryption

try:
	import pymongo
	from pymongo import uri_parser
	from pymongo import collection
	from pymongo import Connection
	from pymongo import database
	from pymongo import ReplicaSetConnection
except ImportError: 
	print("pymongo module not found!")

class MONGO:
	"""methods to handle connections to MongoDB Databases"""
	def __init__(self):
		print "initialize MONGO"
		self.settings = notesapp.STATE()
		try:
                        self.host = self.settings.target_settings.next()[3][0]
                        self.port = int(self.settings.target_settings.next()[3][1])
                        self.db_name = self.settings.target_settings.next()[3][2]
                        self.user = self.settings.target_settings.next()[3][3]
                        self.pw = self.settings.target_settings.next()[3][4]
                except TypeError:
                        print "MongoDB settings not found."

	def connect(self):
		"""Connects to the database and returns the DB connection,
		if successful"""
		mode_dict = {'replica': ReplicaSetConnection, 'single': Connection, 
			'local': Connection} # local assumed to be without authentification
		# Note: only 'single' mode with authentification works!
		try:
                        self.connection = mode_dict[MODE](self.host, self.port)
                except TypeError:
                        print "connection settings seem to be wrong! Correct it."
                        return False
		self.connected_db = self.connection[self.db_name] 
		if self.connected_db.connection.is_locked:
			print "DB was locked" # to see if this happens regulary
			self.connected_db.connection.unlock

		mode = MODE # FIXME: this line not nice code
		if not mode=='local':
			if self.connected_db.authenticate(self.user, self.pw):
				print("authentication happened")
			else:
				print("Authentification failed")
				return False
		return self.connected_db			

        # TODO: fix rename feature, does not work
	def rename_collection(self, collection_old=None, collection_new=None):
		if not self.connected_db:
			self.connect()
		if self.connection.is_locked:
			self.connection.unlock
		try:
			collection = self.connected_db[collection_old]
			collection.rename(collection_new)
			return True
		# in following cases a new note must be added below the calling method
		except pymongo.errors.OperationFailure: # when db[notebook] is missing
			return False		
		except pymongo.errors.InvalidName: # when db[notebook] is empty
			return False

	def get_collections(self):
		if not self.connected_db:
			db_connected = self.connect()
		collections = self.connected_db.collection_names()
		return (collections, self.connected_db)
		
class HELPER:	
	"""methods not called in notesapp.py directly, but used in APP class"""
	def __init__(self):
		None
		
	def split_filename(self, filename):
		"""splits filename into its components"""
		splitted = filename[:-5].split("_")
		notebook = splitted[0]
		# rare case when '_' was used in notebooktitle
		if len(splitted)>2:
			for i, item in enumerate(splitted):
				if i == (len(splitted)-1):
					break
				notebook = notebook + splitted
				# needs testing
				# maybe works here, but not in whole program
		uid = splitted[len(splitted)-1]
		return (notebook, uid)
	
	def add_note(self, collection, uid, password):
		"""adds a note with default title to a collection"""
		if uid == 0:
			uid = uuid.uuid4()
		notesapp.GUI.notecount = collection.count()+1
		title = notesapp.GUI.initial_notetitle.fget('initial_notetitle') + (
			repr(notesapp.GUI.notecount) )
		if password:
                        encry_title = encryption.encrypt_text(title, password)
                        collection.insert({'_id': str(uid),'title': encry_title, 'body': '', 
			'created_at': datetime.now().isoformat(' ')})
                else:
                        collection.insert({'_id': str(uid),'title': title, 'body': '',
                                'created_at': datetime.now().isoformat(' ')})
		return (title, uid) # used in get_title 

class APP:
	"""methods called in notesapp.py"""
	def __init__(self):
                self.mongo = MONGO()
		self.helper = HELPER()

        def check_connection(self):
                """return the db if MongoDB connection works, otherwise False"""
                try:
                        return self.db 
		except AttributeError:
                        self.db = self.mongo.connect()
                        # FIXME: when connection fails, there could be one or 2
                        # reconnection attempts
                        return self.db
	
	
	def read_object(self, filename, password = None): 
		"""read a note, return text"""
		self.db = self.check_connection()
		notebookplusuid = self.helper.split_filename(filename)
		notebook = notebookplusuid[0]
		uid = notebookplusuid[1]
		collection = self.db[notebook]
		all_note_data = collection.find_one({'_id' : uid })
		try: 
			title = all_note_data['title']
			if password:
                                title = encryption.decrypt_text(title, password)
		except TypeError:
			notedata = self.helper.add_note(collection, uid, password)
			if all_note_data: # happens when a notebook has no notes
				all_note_data = collection.find_one({'_id' : notedata[1] })
				title = all_note_data['title']
				if password:
                                        title = encryption.decrypt_text(title, password)
			else: False
		try:
                        main = all_note_data['body']
                except TypeError:
                        print "empty note body"
		if password:
                        main = encryption.decrypt_text(main, password)
		try:
                        text = title+'\n'+ main
                        return text
                except UnboundLocalError: # when a note was created
                        None # FIXME

	def write_object(self, filename, text, password = None):
                """write text to a db collection""" 
		self.db = self.check_connection()
		notebookplusuid = self.helper.split_filename(filename)
		notebook = notebookplusuid[0]
		uid = notebookplusuid[1]
		collection = self.db[notebook]
		title = self.get_title(filename, password) 
		main = text[len(title)+1:] 
		max_title_len = notesapp.GUI.max_title_len.fget('max_title_len')
		new_title = str(text)[0:max_title_len].split('\n')[0]
		if password:
                        main = encryption.encrypt_text(main, password)
		collection.update({'_id': uid}, {"$set": {
			'body': main}}) 
		# only set title when really needed; otherwise possible bug with multiple titles
		if new_title and new_title != title:
                        if password:
                                new_title = encryption.encrypt_text(new_title, password)                              
			collection.update({'_id': uid}, {"$set": {
			'title': new_title}}) 
		return True

	def get_notebook_filenames(self, notebook):
		"""return would-be filenames with the notebook_*.note pattern"""
		self.db = self.check_connection()
		collection = self.db[notebook] 
		uids = collection.find().distinct('_id')
		file_list = []
		for noteid in uids:
			file_list.append(notebook+'_'+str(noteid)+'.note') 
		return file_list		

	def get_all_note_filenames(self):
		"""return would-be filenames with the *_*.note pattern"""
                self.db = self.check_connection()	
		if self.db:
			collections_plus_db = self.mongo.get_collections()
			nb_collections = collections_plus_db[0]
			self.db = collections_plus_db[1]
			if not nb_collections: # add note
				notesapp.GUI.notebookcount = 1
				title = notesapp.GUI.initial_notebook.fget('initial_notebook') + (
					repr(notesapp.GUI.notebookcount) )
				notesapp.GUI.notebookcount += 1
				nb_collections = []
				nb_collections.append(title)
			all_files = []
			for notebook in nb_collections:
				files_of_nb = self.get_notebook_filenames(notebook)
				all_files.extend(files_of_nb)
			return all_files		

	# TODO: fix rename feature
	def rename_notebook_files(self, notebook, notebook_new, password=None): 
		"""rename a notebook"""
		# unlike the filesys rename method it should create the notebook_new collection
		# when notebook is empty!
		if not self.mongo.rename_collection(notebook, notebook_new):
			# when db[notebook] is empty
			collection = self.db[notebook_new]
			self.helper.add_note(collection, 0, password)		

	def remove_file(self, filename):
		"""remove a particular note"""
		self.db = self.check_connection()
		
		notebookplusuid = self.helper.split_filename(filename)
		notebook = notebookplusuid[0]
		uid = notebookplusuid[1]
		collection = self.db[notebook]
		collection.remove({'_id': uid}) 	

	def get_title(self, filename, password = None): 
		"""get the title of a note"""
		self.db = self.check_connection()
	
		notebookplusuid = self.helper.split_filename(filename)
		notebook = notebookplusuid[0]
		uid = notebookplusuid[1]
		collection = self.db[notebook]
		try: 
			title = collection.find_one({'_id' : uid })['title']
			if password:
                                title = encryption.decrypt_text(title, password)
		except TypeError: # a new note
			notedata = self.helper.add_note(collection, uid, password) 
			title = notedata[0]
		return str(title.encode('utf-8'))
