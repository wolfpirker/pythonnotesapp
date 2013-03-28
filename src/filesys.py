"""filesys - support of io file operations"""

# filesys.py
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

import os, glob, sys
import notesapp, encryption

# FIXME: the setting working directory is ignored!

def read_object(filename, password=None): 
	"""read a file, return text"""
	
	f_o = open(filename, 'r')
	text = f_o.read()
	
	f_o.close()
	if password:
		text = encryption.decrypt_text(text, password)
	return text

def write_object(filename, text, password=None): 
	"""write text to a file"""
	if password:
		text = encryption.encrypt_text(text, password)
	f_o = open(filename, 'w')
	print >>f_o, text
	f_o.close()
	return True

def get_notebook_filenames(notebook):
	"""return filenames with the notebook_*.note pattern"""
	return glob.glob(notebook + '_*.note')

def get_all_note_filenames():
	"""return filenames with the *_*.note pattern"""
	# FIXME: only each notebook title must be returned
	# this method is not consistent with mongo.py
	return glob.glob('*_*.note')
	
def rename_notebook_files(notebook, notebook_new):
	"""rename of files when a notebook title changes"""
	filenames = get_notebook_filenames(notebook)
	for note_file in filenames:
		uid_of_file = note_file[len(notebook)+1:] 
		os.rename(note_file, notebook_new+uid_of_file)

def remove_file(f):
	"""remove a particular note file"""
	os.remove(f)

def get_title(f, password=None):
	"""get the title of a note"""
	file_o = open(f, 'r')
	first_line = file_o.readline()
	file_o.close()
	max_title_len = notesapp.GUI.max_title_len.fget('max_title_len')
	if password: 
		first_line = encryption.decrypt_text(first_line, password)
	title = first_line[0:max_title_len].split('\n')[0]
	return str(title.encode('utf-8')) 

		
