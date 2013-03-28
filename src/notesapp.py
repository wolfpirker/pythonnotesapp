#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# notesapp.py
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

from gi.repository import Gtk, GdkPixbuf, Gdk
import sys
import uuid, glob, re
import cPickle as pickle

# program modules
import mongo # mongodb support
import filesys # file I/O operations
import utils
import encryption
from settings import SETTINGS
from settings import CONFIG_FILE


#Comment the first line and uncomment the second before installing
#or making the tarball (alternatively, use project variables)
UI_FILE = "src/notesapp.ui"
#UI_FILE = "/usr/local/share/notesapp/ui/notesapp.ui"
	
class STATE:
	def __init__(self):
	# when the programm starts load the configuration file
        # FIXME: better exception handling when file doesn't exist
		try:
			file_object = open(CONFIG_FILE, 'r')
			settings = pickle.load(file_object)
			self.target_settings = self.target(settings)
			settings = pickle.load(file_object)
			self.encryption_settings = self.encryption(settings)
			settings = pickle.load(file_object)
			self.saving_settings = self.saving(settings)
			settings = pickle.load(file_object)
			self.font_settings = self.font(settings)
			file_object.close()
		except IOError:
                        print 'IOEerror'
			self.target_settings = self.target({'fcbtn': '', 'rbtn': (1,0)
				, 'cbtn': (0,0)})
			self.encryption_settings = self.encryption({'rbtn': (1,0)})
			self.saving_settings = self.saving({'rbtn': (0,1,0)})
			self.font_settings = self.font({'rbtn': (True, False, True
                                , False, False), 'e': (), 'cbtn': (False, True)
                                , 'fbtn': ('DejaVu Sans Ultra-Light 12',)
                                , 'clbtn': ('#e9e9b9b96e6e', '#5c5c35356666'
                                , '#fffff86ebe4a', '#1d4d0e9b3777'), 'fcbtn': ()})

		except EOFError:
                        print 'EOFEerror'
			file_object.close()
			self.target_settings = self.target({'fcbtn': '', 'rbtn': (1,0)
				, 'cbtn': (0,0)})
			self.encryption_settings = self.encryption({'rbtn': (1,0)})
			self.saving_settings = self.saving({'rbtn': (0,1,0)})
			self.font_settings = self.font({'rbtn': (True, False, True
                                , False, False), 'e': (), 'cbtn': (False, True)
                                , 'fbtn': ('DejaVu Sans Ultra-Light 12',)
                                , 'clbtn': ('#e9e9b9b96e6e', '#5c5c35356666'
                                , '#fffff86ebe4a', '#1d4d0e9b3777'), 'fcbtn': ()})			

	def target(self, settings):
		"""this method yields target settings in following order: 
			1th target, 2nd file_path, 3rd export, 4rd connection info list;
			it's required that it first gets the settings dictionary"""
		file_path = settings['fcbtn']#[0]
		mongo_connection_info = None
		if settings['rbtn'][1]:
			target = 'mongo'
			export = settings['cbtn'][1]
		else:
			target = 'filesys'	
			export = settings['cbtn'][0]
		if export or (target == 'mongo'):
			mongo_connection_info = settings['e']
		print ("target method called")
		while True:
			yield (target, file_path, export, mongo_connection_info)

	def encryption(self, settings):
		"""this method yields encryption settings in following order: 
			1th encryption, 2nd migration;
			it's required that it first gets the settings dictionary"""
		ask_migration = False
		encryption = settings['rbtn'][1]
		if encryption: 
			ask_migration = settings['cbtn'][0]
		print ("encryption method called")
		while True:
			yield (encryption, ask_migration)

	def saving(self, settings):
		"""this method yields the saving behaviour setting"""
		if settings['rbtn'][0]: # instant auto saving
			behaviour = 0
		elif settings['rbtn'][1]: # newline saving
			behaviour = 1
		else: # manual saving
			behaviour = 2
		print ("saving method called")
		while True:
			yield behaviour

	# font
	def font(self, settings):
		"""this method yields the font and color settings"""
		font = False
		bool_btn_font = False
		if settings['rbtn'][1]: # app font
                        font = settings['fbtn'][0]
                        bool_btn_font = settings['cbtn'][0]

                color = ()
                bool_btn_color = False
                if settings['rbtn'][3]: # 1 color
                        color = (settings['clbtn'][0],)
                        bool_btn_color = settings['cbtn'][1]
                elif settings['rbtn'][4]: # 3 colors
                        color = (settings['clbtn'][1], settings[
                                'clbtn'][2], settings['clbtn'][3])
		while True:
			yield (font, bool_btn_font, color, bool_btn_color)

class COUNTER:
	@property 
	def opened_windows_counter(self):
		"""opened_windows_counter is used to determine wheter a notes window
		should be destroyed or hided"""
		return 1	
	@property
	def opened_settings(self):
		"""used to find out when to apply settings"""
		return 0
		
class GUI:
	def __init__(self):
		self.save_button = False

		# used module, for either filesystem IO or DB IO
		self.mongo = mongo.APP()
		self.IO_DICT = {'mongo': self.mongo, 'filesys': filesys}
		self.number_of_lines = False
		self.migrated = False
		self.password = None
		self.settings_to_set = False

		self.__cboxe_note_editable = False
		self.initial_notebook = "Notebook"
		self.notebookcount = 1

		self.builder = Gtk.Builder()
		self.builder.add_from_file(UI_FILE)
		self.builder.connect_signals(self)

		self.window_main = self.builder.get_object('window')
		
		self.txv_note = self.builder.get_object('txv_note')
		self.txb_note = self.txv_note.get_buffer()
		self.cboxt_note = self.builder.get_object('cboxt_note')
		self.cboxt_selection = self.builder.get_object('cboxt_selection')
		self.cboxt_notebook = self.builder.get_object('cboxt_notebook')
		self.cboxe_note = self.builder.get_object('cboxe_note')
		self.cboxe_notebook = self.builder.get_object('cboxe_notebook')
		self.cboxe_note.set_max_length(self.max_title_len)

		self.grid_innerleft = self.builder.get_object('grid_innerleft')

		# load all settings
		self.state = STATE() 
		self.target = self.state.target_settings.next()[0]
		self.check_color_button()
		self.check_font_button()
		self.check_export_buttons()

		self.window_manage = self.builder.get_object('window_manage')

		if self.target == 'mongo': 
                        try:
                                self.mongo.check_connection()
                        except AttributeError:
                                # not correct MongoDB connection settings!
                                self.message_dialog(self.window_manage, Gtk.ButtonsType.OK,
				"MongoDB connection failed! Please correct settings.")
                                self.on_settings_activate(0)
			
		self.on_manage_notebook(0) # integrates utils.LOGIC

		self.set_style(self.state.font_settings.next()[0]
                               , self.state.font_settings.next()[2])
		self.window_main.show_all()
		  
	@property # TODO later: possibility to change it in the settings window
	def max_title_len(self):
		"""get the maximum title length"""
		return 48

	@property
	def initial_notetitle(self):
		return "Note"
		
	@property
	def notecount(self): # TODO: count notes somewhere
		return 1

	@notecount.setter
	def initial_notecount(self, value):
		self.notecount = value	

	@property
	def initial_notebook(self):
		return "Notes Collection"
		
	@property
	def notebookcount(self): # TODO: count notes somewhere 
		return 1

	@notebookcount.setter # TODO: test this
	def notebookcount(self, value):
		self.notebookcount = value

	def set_style(self, font, color=None):
		"""set style settings from the css file,
                the color argument can be a hex string color,
                None or Gtk.Color"""
		provider = Gtk.CssProvider.new()
		display = Gdk.Display.get_default()
		screen = Gdk.Display.get_default_screen(display)

		Gtk.StyleContext.add_provider_for_screen(
			screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

		# colors support worked on: red, yellow, blue, bright, dark
		css_win = "GtkWindow{"
		css_first = ""
		css_rest = ""
		if color:
                        css_btn = ".button{"
			if len(color) == 1:
                                greyish = False
                                css_first = '@define-color bg_color #' + color[0][1:13:2] + ';\n'
                                
                                red_share = int(color[0][1:4:2], 16)
                                green_share = int(color[0][5:8:2], 16)
                                blue_share = int(color[0][9:12:2], 16)
                                c = (red_share, green_share, blue_share)
                                # create a color used in widget, similar to the main color
                                # but more contrast to the font color, and less colorful
                                diff = 128*3 - c[0] - c[1] - c[2]
                                c_base = self.more_contrast(c, diff, False, 6)
                                css_first += '@define-color base_color rgb(' + str(
                                        c_base[0]) + ',' + str(c_base[1]) +',' + str(
                                                c_base[2]) + ');\n'
                                
                                
                                # find approbiate font color -> assume it should
                                # have a good contrast to other colors
                                min_val = min(red_share, green_share, blue_share)
                                max_val = max(red_share, green_share, blue_share)

                                if max_val - min_val < 35:
                                        greyish = True
                                        
                                new_c = [0, 0, 0]
                                #diff = 128*3 - c[0] - c[1] - c[2]
                                if not greyish:
                                        for i,share in enumerate(
                                                (red_share, green_share, blue_share)):
                                                if share==min_val:
                                                        new_c[i] = max_val
                                                elif share==max_val:
                                                        new_c[i] = min_val
                                                else:
                                                        new_c[i] = 256-c[i] # CHECK if this makes sense!
                                                #new_c[i] = str(hex(new_c[i]))[2:]
                                                #if len(new_c[i]) < 2: # if any share less than 10
                                                #         new_c[i] = '0' +  new_c[i]
                                        c_font = self.more_contrast(new_c, diff, True, 3) # third bool True for
                                                                                # hight contrast to main color,
                                                                                # otherwise high contrast to font
                                        
                                if greyish:
                                        if diff > 140: # bright color for font
                                                c_font = [0, 255, 255] # aqua                                                     
                                        else: # darker font
                                                c_font = [0, 0, 128] # navy blue
                                css_first += '@define-color text_color rgb(' + str(c_font[0]) + ', ' + str(
                                        c_font[1]) + ', ' + str(c_font[2]) + ');'
			elif len(color) == 3:
                                # FIXME: order of colors is confusing
                                css_first = '@define-color bg_color #' + color[0][1:13:2] + ';\n'
                                css_first += '@define-color text_color #' + color[1][1:13:2] + ';\n'
                                css_first += '@define-color base_color #' + color[2][1:13:2] + ';\n'
                        css_win += ' background-color: @bg_color;'
                        css_win += ' color: @text_color;'
                        css_win += ' -Clearlooks-colorize-scrollbar: true;'
                        css_win += ' -Clearlooks-style: classic;'
                        css_rest = """
.button{
        background-color: shade(@bg_color, 1.04);
}
.button:hover{
        background-color: shade(@bg_color, 1.08);
}
.button:active{
        background-color: shade(@bg_color, 0.85);
}
.entry{
        background-color: @base_color;
        color: @text_color;
}
.entry:selected{
        background-color: mix (@bg_color, @base_color, 0.4);
        -Clearlooks-focus-color: shade (0.65, @bg_color);
}
GtkTextView{
        padding: 2px;
        background-color: @base_color;
        color: @text_color;
}
GtkTextView:selected{
        background-color: @text_color;
        color: @base_color;
}
GtkMenuItem{
        background-color: @base_color;
        color: @text_color;
}
GtkPaned{
        background-color: @base_color;
}
"""
                if font:
                        css_win += ' font: ' + font + ';'
                css_win += '}'
                provider.load_from_data(css_first + '\n' + css_win + '\n' + css_rest)

	def more_contrast(self, c, diff, font, scale=5):
                """method returns a new color, takes rgb values as list,
                a indicator if it's a bright or dark color, and a bool to
                determine wheter it's a background or font color,
                the fourth argument gives a adjustment possiblity"""
                if font:
                        scale = (-scale)
                if diff > 140:
                        c_base = [int(c[0]-scale*15), int(c[1]-scale*15), int(c[2]-scale*15)]
                        for i, value in enumerate(c_base):
                                if value<0:
                                        c_base[i] = 0
                else: # make it brighter
                        c_base = [int(c[0])/2+scale*20, int(c[1])/2+scale*20
                                , int(c[2])/2+scale*20]
                        for i, value in enumerate(c_base):
                                if value>255:
                                        c_base[i] = 255
                return c_base
                
	def on_window_focus_in_event (self, widget, event):		
		"""update all settings, when the window gets the focus and Settings 
		Window was or is opened"""
		try:
			self.preferences_GUI.on_btn_close_clicked(0)
		except AttributeError:
			return
		if not self.settings_to_set:
                        return
		self.state = STATE()
		print "-> use new settings"
		self.set_style(self.state.font_settings.next()[0]
			, self.state.font_settings.next()[2])
		self.window_main.show_all()
		self.check_color_button()
		self.check_font_button()
		self.check_export_buttons()
		if self.preferences_GUI.migration and not self.migrated:
			# initiate migration
			self.preferences_GUI = None
			self.let_migration_happen()
			self.migrated = True
		self.settings_to_set = False

	def check_color_button(self):
                if len(self.state.font_settings.next()[2]) == 1:
                        if self.state.font_settings.next()[3]:
                                self.add_color_button()

        def check_font_button(self):
                if self.state.font_settings.next()[1]:
                        self.add_font_button()

        def check_export_buttons(self):
                if self.state.target_settings.next()[2]: # enable export
                        self.add_export_button(self.state.target_settings.next()[0])

	def let_migration_happen(self):
		self.builder.get_object('box_migration').show()
		print ("here here")
		# add all notebooks with checkboxes to the grid
		# get notebooks names, for each determine wheter it's encrypted, set
		# appropriate icon	
		grid_migration = self.builder.get_object('grid_migration')

		all_filenames = self.IO_DICT[self.target].get_all_note_filenames() 
		# at first only one filename per notebook is needed
		file_in_notebook_dict = {}
		print "all filenames: " + str(all_filenames)
		for item in all_filenames:
			file_in_notebook_dict[item.split('_')[0]] = [item.split('_')[1]]
		print file_in_notebook_dict
		for i, notebook in enumerate(file_in_notebook_dict.keys()):
			# add notebook to the Viewport
			cbtn = Gtk.CheckButton.new()
			grid_migration.attach(cbtn, 0, i, 1, 1)
			entry = Gtk.Entry.new()
			entry.set_text(notebook)
			# is it encrypted?
			print file_in_notebook_dict[notebook][0]
			text = self.IO_DICT[self.target].read_object( 
				notebook + '_' + file_in_notebook_dict[notebook][0], self.password)
			print "der text ist" + str(text)
			if encryption.check_if_encrypted(text):
				# add key icon
				entry.set_icon_from_stock(0, Gtk.STOCK_DIALOG_AUTHENTICATION)
			else:
				# add file icon
				entry.set_icon_from_stock(0, Gtk.STOCK_FILE)
			grid_migration.attach(entry, 1, i, 1, 1)
			i+=1
			entry.set_can_focus(False)
			entry.set_icon_activatable(0, False)			
		grid_migration.show_all()		

	def on_btn_migration_proceed_clicked (self, button):
		grid_migration = self.builder.get_object('grid_migration')

		# check if new passwords match
		new_password = self.builder.get_object('e_migration_new').get_text()
		if new_password != self.builder.get_object(
			'e_migration_confirm').get_text():
			self.builder.get_object('infbar_warning').show()
			return False
			
		i = 0
		while True:
			cbtn = grid_migration.get_child_at(0,i)
			if not cbtn:
				break
			if cbtn.get_active():
				entry = grid_migration.get_child_at(1,i)
				notebook = entry.get_text()
				failed = False # failed should be True, if validation of just
							# recently encrypted notes fails!
				none_text_skipped = False # True, if the decrypt_text method
							# returns False and therefore it doesn't change a file
				notefiles = self.IO_DICT[
					self.target].get_notebook_filenames(notebook)
				if entry.get_icon_stock(0) == 'gtk-file': 
					# not encrypted, use of new password, and encrypt notes 
					for notefile in notefiles:
						text = self.IO_DICT[self.target].read_object(notefile)	
						self.IO_DICT[self.target].write_object(notefile, text, new_password)	
						
						# Note: following validation maybe redundant 
						# -> makes it a bit slower
						#encrypted_text = self.IO_DICT[self.target].read_object(notefile)
						#if not encryption.decrypt_text(encrypted_text, new_password):
						#	failed = True
						#	self.builder.get_object('infbar_error').show()
							
					# change left icon 
					entry.set_icon_from_stock(0, Gtk.STOCK_DIALOG_AUTHENTICATION)

				else: # already encrypted notebook 
					# use of current password, validate password and then
					# decrypt using current and encrypt using new password
					for notefile in notefiles:
						encrypted_text = self.IO_DICT[self.target].read_object(
							notefile)
						current_pw = self.builder.get_object(
							'e_migration_current').get_text()
						if not encryption.decrypt_text(
							encrypted_text, current_password):
								# so entered password must be wrong!
								entry.set_icon_from_stock(1, Gtk.STOCK_WARNING)
						else: # password validation worked
							text = encryption.decrypt_text(encrypted_text, current_pw)
							if text:
								self.IO_DICT[self.target].write_object(
									notefile, text, new_password)
								#entry.set_icon_from_stock(1, Gtk.STOCK_APPLY)
							else:
								none_text_skipped = True

						# Note: following validation maybe redundant 
						# -> makes it a bit slower
						#encrypted_text = self.IO_DICT[self.target].read_object(notefile)
						#if not encryption.decrypt_text(encrypted_text, new_password):
						#	failed = True
						#	self.builder.get_object('infbar_error').show()

				# set the second icon of a notebook
				if failed:
					entry.set_icon_from_stock(1, Gtk.STOCK_ERROR)
				elif none_text_skipped:
					entry.set_icon_from_stock(1, Gtk.STOCK_WARNING)
				else:
					entry.set_icon_from_stock(1, Gtk.STOCK_APPLY)
		
				entry.set_icon_activatable(1, False)
			i += 1
		grid_migration.show_all()	

	def on_btn_migration_close_clicked (self, button):
		self.builder.get_object('box_migration').hide()		

	def entry_hide(self, widget, tooltip):
		if widget.get_visibility():
			widget.set_visibility(False)
			widget.set_tooltip_text(tooltip)
			widget.set_text('')

	def on_btn_check_clicked (self, button):
		password = self.builder.get_object('e_encryption_pw1').get_text()
		e_encryption_pw2 = self.builder.get_object('e_encryption_pw2')
		infbar = self.builder.get_object('infbar_pw_warning')
		infbar.hide()
		infbar_success = self.builder.get_object('infbar_pw_success')
		infbar_success.hide()
		infbar_label = self.builder.get_object('lbl_pw_warning')
		if e_encryption_pw2.get_visible():
			password2 = e_encryption_pw2.get_text()
			if password2 != password:
				infbar_label.set_text('Passwords do not match! Please correct it.')
				infbar.show()
				return False
		try:
                        filename = self.IO_DICT[self.target].get_notebook_filenames(
			self.notebook)[0]
                except IndexError: # happens with new and encrypted notes
                        self.add_note(self.filename) # self.filename is already set correctly here!
                        filename = self.filename
		enc_text = self.IO_DICT[self.target].read_object(filename)
		try:
			decryption_success = encryption.decrypt_text(enc_text, password)
		except TypeError: # TODO: could need more Testing!
			decryption_success = encryption.decrypt_text(enc_text[:-1], password)
		if not decryption_success:
			infbar_label.set_text('Password wrong! Please try again!')
			infbar.show()
			return False
		else:
			infbar_success.show()
			self.password = password
			# update the title_filename dict with decrypted titles
			# and show it in the notes combobox
			self.title_filename_dict = self.logic.create_title_filename_dict(
				self.notebook, password)
			self.builder.get_object('grid_encrypted_notebook').hide()
			# put it into the combo box text
			for title in self.title_filename_dict:
				self.cboxt_note.insert(0,"", title)
				self.cboxt_selection.insert(0,"", title)						
			
	def on_e_encryption_pw1_activate (self, entry):
		e_encryption_pw2 = self.builder.get_object('e_encryption_pw2')
		if e_encryption_pw2.get_visible():
			e_encryption_pw2.grab_focus()
		else:
			self.on_btn_check_clicked (True)
			
	def on_e_encryption_pw2_activate (self, entry):	
		self.on_btn_check_clicked (True)
			
	def on_e_migration_current_grab_focus (self, widget):
		self.entry_hide(widget, 'enter current password')

	def on_e_migration_new_grab_focus (self, widget):
		self.entry_hide(widget, 'enter new password')

	def on_e_migration_confirm_grab_focus (self, widget):
		self.entry_hide(widget, 'confirm new password')

	def message_dialog(self, window, buttons, message):
		error_message = Gtk.MessageDialog(window, 
		Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING, 
		buttons, message)
		error_message.set_default_response(1)
		error_message.run()
		error_message.destroy()

	def on_txb_note_changed (self, txb_note): 
		text = self.txb_note.get_property('text')
		if not self.filename:
                        self.txb_note.set_text(self.title_filename_dict.keys()[0]) # ???????
                        self.filename = self.title_filename_dict.values()[0]
		if self.state.saving_settings.next() ==0: # -> instant save
			self.logic.save_note(self.filename, text, self.password)
			#try: # FIXME: doesn't work!!!
			#	self.save_button.destroy()
			#except AttributeError:
			#	None
		elif self.state.saving_settings.next() ==1: # save when linecount changes
			lines = self.txb_note.get_line_count()
			if self.number_of_lines != lines:
				self.logic.save_note(self.filename, text, self.password)
				self.number_of_lines = lines
			#try: # FIXME: doesn't work!!!
			#	self.save_button.destroy()
			#except AttributeError:
			#	None
		else: # manual save
			self.add_save()
				
	# rename notes:
	def on_cboxe_note_icon_press (self, entry, entryiconposition, event):
		if entryiconposition == 0:
			self.active = self.cboxt_note.get_active() 
			self.cboxe_note.set_can_focus(1)
			self.cboxe_note.grab_focus()
			self.cboxt_selection.set_can_focus(0)
			self.cboxt_selection.set_can_focus(0)
		else: 
			can_focus = self.cboxe_note.get_can_focus()
			# 1st: can_focus, 2nd: duplicate_title
			CASE_DICT = {(1,1):3, (1,0):2, (0,1):1, (0,0):0}
			duplicate_title = self.title_filename_dict.has_key(
				self.cboxe_note.get_text())
			if CASE_DICT[(can_focus, duplicate_title)] == 2:
				self.cboxe_note.set_can_focus(0)
				self.txv_note.grab_focus()
				# update title-file dict 
				try:
					del(self.title_filename_dict[self.notetitle])
				except KeyError: # can happen when new notebook with note was created
					None
				self.notetitle = self.cboxe_note.get_text()	
				self.title_filename_dict[self.notetitle] = self.filename
				# update cboxt_note
				self.cboxt_note.remove (self.active)
				self.cboxt_note.insert_text(self.active, self.notetitle)
				# set title in textbuffer
				iterstart = self.txb_note.get_iter_at_line(0)
				iterend = self.txb_note.get_iter_at_line(1)
				self.txb_note.delete(iterstart, iterend)
				self.txb_note.insert(iterstart, self.notetitle+'\n', len(self.notetitle+'\n'))
				# write whole text to file
				current_cursor = self.txb_note.get_property('cursor-position')
				iter_at_cursor = self.txb_note.get_iter_at_offset(current_cursor)
				self.txv_note.set_sensitive(0) # maybe optional
				self.txb_note.set_modified (False) # in the API recommended
				#io_o = self.IO_DICT[self.target].io_o_open(self.filename, 'w')
				text = self.txb_note.get_property('text')
				if not self.IO_DICT[self.target].write_object(
					self.filename, text):
						print("writing process failed!!!")
				self.txb_note.set_modified (True) 
				self.txv_note.set_sensitive(1) # maybe optional
				self.txb_note.place_cursor(iter_at_cursor)
				self.txv_note.grab_focus()
					
			elif CASE_DICT[(can_focus, duplicate_title)] == 3:
				question_dialog = Gtk.MessageDialog(self.window_main, 
					Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION, 
					Gtk.ButtonsType.YES_NO,
					"Title exists already!\nShould it really be used?")
					# FIXME: only works if it's the same note
				if question_dialog.run() == Gtk.ResponseType.YES:
					self.cboxe_note.set_can_focus(0)
					self.txv_note.grab_focus()
				question_dialog.destroy()
			else:
				print("ups, click edit first")

	def on_cboxe_note_activate (self, entry):
		self.on_cboxe_note_icon_press (0, 1, 0)	


	def on_cboxe_notebook_activate (self, entry):
		self.on_cboxe_notebook_icon_press (0, 1, 0)

	# rename notebooks:
	def on_cboxe_notebook_icon_press (self, entry, entryiconposition, event):
		if entryiconposition == 0:
			self.notebook = self.cboxt_notebook.get_active_text()
			self.cboxe_notebook.set_can_focus(1)
			self.cboxe_notebook.grab_focus()		
		else: 
			notebook_set = self.logic.fetch_notebooktitles()
			new_title = self.cboxe_notebook.get_text()
			if new_title in notebook_set:
				question_dialog = Gtk.MessageDialog(self.window_main, 
					Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION, 
					Gtk.ButtonsType.YES_NO,
					"Title exists already! Should it really be used?\n"
					"Hint: Notes can be merged to one\nsingle Notebook"
					" via the rename mechanism")
					# FIXME: doesn't check if note titles of different notebooks
					# are the same -> in this case it must be handled somehow
				if question_dialog.run() == Gtk.ResponseType.YES:
					# rename notebook files
					self.IO_DICT[self.target].rename_notebook_files(
						self.notebook, new_title)
					# update title_filename dict and cboxt_notebook
					self.logic.fetch_notebooktitles()
					self.cboxe_notebook.set_can_focus(0)
					self.title_filename_dict = (
						self.logic.create_title_filename_dict(new_title, self.password) )
					self.cboxt_selection.grab_focus()
					# self.notetitle = self.cboxe_notebook.get_text()
				question_dialog.destroy()
			else: # Note: doesn't include the case when a new notebook was created!
					# this must be handled in the IO module
				# rename notebook files
				self.IO_DICT[self.target].rename_notebook_files(
					self.notebook, new_title)
				# update title_filename dict and cboxt_notebook
				self.logic.fetch_notebooktitles()
				self.cboxe_notebook.set_can_focus(0)
				self.title_filename_dict = (
					self.logic.create_title_filename_dict(new_title, self.password) )
				self.cboxt_selection.grab_focus()
				self.notetitle = self.cboxe_notebook.get_text()

	# create new notebook
	def on_btn_new_clicked (self, button):
		self.builder.get_object('infbar_pw_warning').hide()
		self.builder.get_object('infbar_pw_success').hide()
		self.notebook = None
		self.password = None
		self.on_cboxe_notebook_icon_press(-1, 0, 0)	
		if self.state.encryption_settings.next()[0]:
			self.builder.get_object('grid_when_new_notebook').show()

	def add_save(self):
		self.add_button_to_grid(self.grid_innerleft, 
			Gtk.STOCK_SAVE, 0, 0, 'save')
		self.save_button = True

	def add_color_button(self):
                self.add_button_to_grid(self.grid_innerleft, 
			Gtk.STOCK_SELECT_COLOR, 2, 0, 'color')

        def add_font_button(self):
                self.add_button_to_grid(self.grid_innerleft,
                        Gtk.STOCK_SELECT_FONT, 3, 0, 'font')

        def add_export_button(self, target):
                if target == 'filesys':
                        self.add_button_to_grid(self.grid_innerleft,
                                Gtk.STOCK_FLOPPY, 1, 0, 'export to MongoDB')
                else:
                        self.add_button_to_grid(self.grid_innerleft,
                                Gtk.STOCK_FLOPPY, 1, 0, 'export to File')
                        

	def add_button_to_grid (self, grid, stock, x, y, tooltip):
		if stock == 'save':
                        if self.save_button:
                                return
		button = Gtk.Button.new()
		image = Gtk.Image()
		image.set_from_stock(stock,4)
		button.set_alignment(0.0, 0.0)
		button.set_tooltip_text(tooltip)
		button.add(image)

		# add and show button
		self.grid_innerleft.attach(button, x, y, 1, 1)
		self.grid_innerleft.show_all()
		
		btn = grid.get_child_at(x,y)			
		# dictionary purpose: declaration of the button clicked signal
  		# add more to the dictionary, when more buttons are needed
		method = {'save': self.on_save_clicked
                         , 'color': self.on_color_clicked
                          , 'font': self.on_font_clicked
                          , 'export to MongoDB': self.on_export
                          , 'export to File': self.on_export}
		btn.connect_after('clicked', method[tooltip]) 

	def on_save_clicked (self, button):
		text = self.txb_note.get_property('text')
		self.logic.save_note(self.filename, text, self.password)

        def on_export(self, button):
                text = self.txb_note.get_property('text')
                self.logic.save_note(self.filename, text, self.password, True)

	def on_color_clicked (self, button):
                color_dialog = Gtk.ColorChooserDialog("main color chooser"
                                                      , self.window_main)
		color_dialog.run()
		color = color_dialog.get_property('rgba')
		color_dialog.destroy()
		self.set_style(0, (color.to_color().to_string(), ))
		# Note: second argument is a tuple, not a string!
		self.window_main.show_all()

        def on_font_clicked (self,button):
                font_dialog = Gtk.FontChooserDialog("font chooser"
                                                      , self.window_main)
		font_dialog.run()
		font = font_dialog.get_property('font')
		font_dialog.destroy()
		self.set_style(font, 0)
		self.window_main.show_all()
                
			
	# shared method: none	
	def on_add_note (self, button):
		uid = uuid.uuid4()
		#try:
		#	self.IO_DICT[self.target].io_o_close(io_o)
		#except AttributeError:
		#	None
		self.filename = self.notebook + '_' + str(uid) + '.note'
		self.add_note(self.filename)
		

	def add_note (self, filename):
                self.notetitle = self.initial_notetitle + ' ' + repr(self.notecount)
		# update title-file dict
		self.title_filename_dict[self.notetitle] = self.filename 
		
		self.cboxt_note.insert(0,"", self.notetitle)
		self.cboxt_note.set_active(0) 
		self.notecount+=1
		self.txb_note.set_text(self.notetitle)
		text = self.txb_note.get_property('text')
		if not self.IO_DICT[self.target].write_object(
					self.filename, text, self.password):
						print("writing process failed!!!")
		
	def on_cboxt_notebook_changed (self, combobox):
		self.builder.get_object('e_encryption_pw2').hide()
		self.builder.get_object('infbar_pw_warning').hide()
		self.builder.get_object('infbar_pw_success').hide()
		self.password = None
		self.builder.get_object('cboxt_selection').set_sensitive(True)
		self.notebook = self.cboxt_notebook.get_active_text()
		# get note titles
		self.title_filename_dict = self.logic.create_title_filename_dict(
			self.notebook, self.password)
		self.cboxt_note.remove_all()		
		self.cboxt_selection.remove_all()		
		if self.state.encryption_settings.next()[0]:
			try:
                                self.filename = self.title_filename_dict.values()[0] # get filename
                                text = self.IO_DICT[self.target].read_object(self.filename, self.password)
                        except IndexError: # happens with new notebooks! at least in fs mode
                                #self.on_add_note(0) # TODO: nicht hier rein! speichert sonst bei jeder kleinen Änderung neue Notiz!!
                                #filename = self.title_filename_dict.values()[0]
                                uid = uuid.uuid4()
                                self.filename = self.notebook + '_' + str(uid) + '.note'
                                return
			if encryption.check_if_encrypted(text):
				self.builder.get_object('grid_encrypted_notebook').show()
				return
		self.builder.get_object('grid_encrypted_notebook').hide()
		# put it into the combo box text
		for title in self.title_filename_dict:
			self.cboxt_note.insert(0,"", title)
			self.cboxt_selection.insert(0,"", title)

	def on_e_encryption_pw1_grab_focus (self, widget):
		if widget.get_text() == 'password':
			self.builder.get_object('btn_show').set_sensitive(True)
			widget.set_visibility(False)
			widget.set_text('')

	def on_e_encryption_pw2_grab_focus (self, widget):
		if widget.get_text() == 'confirm password':
			widget.set_visibility(False)
			widget.set_text('')
			
	def on_btn_show_clicked (self, button):
		e_encryption = self.builder.get_object('e_encryption_pw1')
		if not e_encryption.get_visibility():
			e_encryption.set_visibility(True)
			button.set_label('hide')
		else:
			e_encryption.set_visibility(False)
			button.set_label('show')
					

	def on_remove_note (self, button):
		current = self.cboxt_note.get_active()
		self.cboxt_note.remove(current) 
		self.IO_DICT[self.target].remove_file(self.filename) 
		self.cboxt_note.set_active(0)
		# TODO: now load the first note...
		
	def on_cboxt_note_changed (self, combobox):
		cbox_note_editable = self.cboxe_note.get_can_focus()
		self.number_of_lines = self.txb_note.get_line_count()
		if not cbox_note_editable: 
			self.notetitle = self.cboxe_note.get_text()
			print "the notetitle is: " + self.notetitle
			if self.notetitle:
				try:
                                        self.filename = self.title_filename_dict[self.notetitle]  
					text = self.IO_DICT[self.target].read_object(self.filename, self.password) 
					self.txb_note.set_text(text, len(text))
				except IOError, UnboundLocalError: # when new notebook was added
					None
				except KeyError: # FIXME: cmb_note locked until new note
                                        None #  is created; and previous note is in buffer
                                                

	def on_new_win_activate (self, menuitem):
		try:
			counter = COUNTER.opened_windows_counter.fget('opened_windows_counter')+1
		except AttributeError: # when a third window is opened
			counter = COUNTER.opened_windows_counter+1
		COUNTER.opened_windows_counter = counter
		GUI()		
					
	def on_manage_notebook (self, menuitem):
		# get LOGIC class components:
		self.logic = utils.LOGIC(self.cboxt_notebook, self.txb_note,
			self.txv_note, self.state.target_settings.next()[0])
		self.cboxt_note.set_sensitive(0)
		self.txv_note.set_sensitive(0)
		#self.title_filename_dict = {}
		self.window_manage.show_all()
		self.window_manage.set_keep_above(1)
		# now get the existing notebooks
		self.logic.fetch_notebooktitles()

	def on_settings_activate (self, menuitem):
		self.migrated = False
		self.settings_to_set = True
		try:
			self.preferences_GUI.widgets_visibility_and_first_settings()
		except AttributeError:
			self.preferences_GUI = SETTINGS()
		
		# delete notebook with all its notes
	def on_btn_delete_clicked (self, button):
		question_dialog = Gtk.MessageDialog(self.window_main, 
					Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION, 
					Gtk.ButtonsType.YES_NO,
					"Remove this notebook with all its notes, really?")
		
		if question_dialog.run() == Gtk.ResponseType.YES:
			file_list = glob.glob(self.notebook + '_*.note') # FIXME: outsource this IO 
			for item in file_list:							# specific code
				self.IO_DICT.remove_file(item)
		question_dialog.destroy()
		self.logic.fetch_notebooktitles()
		self.cboxt_notebook.set_active(0)
		
	def on_btn_ok_clicked (self, button):
		try: 
			self.notebook
		except AttributeError:
			# note: message dialog widget must be a Top Level Window, Not a Popup!
			self.message_dialog(self.window_manage, Gtk.ButtonsType.OK,
				"Please choose a notebook first!")
			return
		active = self.cboxt_selection.get_active() 
		self.window_manage.hide()
		self.txv_note.set_sensitive(1)
		self.cboxt_note.set_sensitive(1)
		self.cboxt_note.set_active(active)
		self.window_main.present()
		self.txv_note.grab_focus()
		self.builder.get_object('grid_when_new_notebook').hide()		

	def on_rbtn_yes_toggled (self, togglebutton):
		self.builder.get_object('grid_encrypted_notebook').show()

	def on_rbtn_no_toggled (self, togglebutton):
		self.builder.get_object('grid_encrypted_notebook').hide()

	def on_undo_step (self, menuitem):
		return

	def on_redo_step (self, menuitem):
		return

	def on_close_app (self, menuitem):
		try: # first time it takes the property like this:
			count = COUNTER.opened_windows_counter.fget(
				'opened_windows_counter')-1
		except AttributeError: # then it would raise a AttributeError
			count = COUNTER.opened_windows_counter-1
		COUNTER.opened_windows_counter = count
		if not COUNTER.opened_windows_counter: 
			Gtk.main_quit()
		self.window_main.hide()

	def on_quit_activate (self, menuitem):
		Gtk.main_quit()
		
	def destroy(window, self):
		window.on_close_app(0)

def main():
	app = GUI()
	Gtk.main()
		
if __name__ == "__main__":
    sys.exit(main())
