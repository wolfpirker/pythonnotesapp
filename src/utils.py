"""some logic used in GUI"""
"""relies on cboxt_notebook, txb_note and txv_note from GUI class"""

# utils.py
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

import uuid
import notesapp
import filesys, mongo

class LOGIC():
	def __init__(self, cboxt_notebook, txb_note, txv_note, target):
		self.mongo = mongo.APP()
		self.io = {'mongo': self.mongo, 'filesys': filesys}[target]
		self.export = {'mongo': filesys, 'filesys': self.mongo}[target]
		self.cboxt_notebook = cboxt_notebook
		self.txb_note = txb_note
		self.txv_note = txv_note

	def save_note (self, filename, text, password=None, export=None):
		"""saves textbuffer to file or db"""
		current_cursor = self.txb_note.get_property('cursor-position')
		iter_at_cursor = self.txb_note.get_iter_at_offset(current_cursor)
		self.txv_note.set_sensitive(0) # maybe optional
		self.txb_note.set_modified (False) # in API recommended
		if not export:
                        if not self.io.write_object(filename, text, password):
                                print("writing process failed!!!")
                else:
                        if not self.export.write_object(filename, text, password):
                                print("export failed")
		self.txb_note.set_modified (True) 
		self.txv_note.set_sensitive(1) # maybe optional
		self.txv_note.grab_focus()
		self.txb_note.place_cursor(iter_at_cursor)

	def fetch_notebooktitles(self): 
		"""gets all notebooknames and puts it into the cboxt"""		
		file_list = self.io.get_all_note_filenames()
		notebook_list = []
		if not file_list: # when MongoDB connection is wrong
                        return False
		for i, item in enumerate(file_list):
			notebook_list.insert(i, item.split('_')[0])			
		notebook_set = set(notebook_list)
		self.cboxt_notebook.remove_all()
		# insert entries in cboxt_notebook
		for item in notebook_set:
			self.cboxt_notebook.insert(0, "", item)
		#print "The notebookset used is: " + str(notebook_set)
		return notebook_set

	def create_title_filename_dict(self, notebook, password=None):
		"""creates a dictionary with note title as keys, and filenames as values"""
		title_filename_dict = {}
		notes_list = self.io.get_notebook_filenames(notebook)
		for filename in notes_list:
			title = self.io.get_title(filename, password)
			print "the used title is: " + title
			try: 
				title_filename_dict[title]
				title_filename_dict[title+" (2)"] = filename					
				print("Same Title exists several times!")
			except KeyError: # usual case
				title_filename_dict[title] = filename 
		return title_filename_dict
