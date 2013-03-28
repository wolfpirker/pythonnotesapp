#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# main.py
# Copyright (C) 2012 Wolfgang Pirker <wolfj@localhost.f17-wolfis-comp>
# 
# settings is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# settings is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GdkPixbuf, Gdk
import os, sys
import cPickle as pickle

#Comment the first line and uncomment the second before installing
#or making the tarball (alternatively, use project variables)
UI_FILE = "src/settings.ui"
#UI_FILE = "/usr/local/share/notesapp/ui/settings.ui"

#DEFAULT_CONFIG_FILE = 'settings_default.cfg'
CONFIG_FILE = 'settings.cfg'

class SETTINGS:
	def __init__(self):

		self.not_applied_set = set(self.SETTING_TABS)
		self.temp_file_o = None
		self.pickled_objects_order = []
		self.all_settings_dict = {}
		self.migration = False

		self.builder = Gtk.Builder()
		self.builder.add_from_file(UI_FILE)
		self.builder.connect_signals(self)

		self.widgets_visibility_and_first_settings()

	@property
	def SETTING_TABS(self):
		return ['target', 'encryption', 'saving', 'font']

	def widgets_visibility_and_first_settings(self):
		window = self.builder.get_object('window_settings')	
		self.infbar_target = self.builder.get_object('infbar_target')
		self.infbar_encryption = self.builder.get_object('infbar_encryption')
		self.infbar_saving = self.builder.get_object('infbar_saving')
		self.infbar_font = self.builder.get_object('infbar_font')
		self.infbar_hints = self.builder.get_object('infbar_hints')
		self.infbar_show_hints = self.builder.get_object('infbar_show_hints')
		self.lbl_hint = self.builder.get_object('lbl_hint')
		self.statusbar_applied = self.builder.get_object('statusbar_applied')
		self.statusbar_applied.push(0, "status: not applied any settings yet")

		#self.builder.get_object('rbtn_save').set_inconsistent(True)


		window.show_all()
		window.present()
		
		# load all recently saved settings
		self.load_settings_from_file(CONFIG_FILE, None)

# not yet sure if following uncommented lines are needed!
		## if password below target is not "User Password", make it invisible
		#e_target05 = self.builder.get_object('e_target05')
		#if e_target05.get_text() == "User Password":
		#	e_target05.set_visibility(True)

		self.update_visibility('target', 5) # if pw is entered, hide it
		self.update_sensitivity()
		self.on_rbtn_target_grab_focus(0) # target tab is shown first
		self.active_tab = "target"

	def load_settings_from_file(self, file_name, category=None):
		"""loads settings from a config file, if category is given only settings 
		of this particular category are loaded"""
		try:
                        file_object = open(file_name, 'r')
                except IOError:
                        return
		for i, section in enumerate(self.SETTING_TABS):
			try:
				category_settings = pickle.load(file_object)
			except EOFError:
                                print "EOFError happended in section: " + str(section)
				category_settings = None
			if not category_settings: 
				print("config file is probably broken")
				print("affected category is " + self.SETTING_TABS[i])
				continue
			if i==0 and (category is None or category=='target'):
				self.set_settings('target', category_settings)
			elif i==1 and (category is None or category=='encryption'):
				self.set_settings('encryption', category_settings)
			elif i==2 and (category is None or category=='saving'):
				self.set_settings('saving', category_settings)
			elif i==3 and (category is None or category=='font'):
				self.set_settings('font', category_settings)
			else:
				continue
		file_object.close()
		# disable "ask about migration" always by default
		self.builder.get_object('cbtn_encryption01').set_active(0)

	def set_settings(self, category, pickled_dict):
		to_check_dict = {'target': ('rbtn', 'cbtn', 'fcbtn', 'e'), 
			'encryption': ('rbtn', 'cbtn'), 'saving': ('rbtn',), 
			'font': ('rbtn', 'cbtn', 'fbtn', 'clbtn')}

		for widget_type in to_check_dict[category]:
			i = 1
			while True:
				widget = self.builder.get_object(widget_type + '_' + category 
					+ '0' + str(i))
				if widget is None:
                                    break
				# set settings	
				if widget_type == 'rbtn' or widget_type == 'cbtn':
                                    widget.set_active(pickled_dict[widget_type][i-1])
				elif widget_type == 'e':
                                    widget.set_text(pickled_dict[widget_type][i-1])
				elif widget_type == 'fcbtn':
                                    try:
                                        widget.set_current_folder(pickled_dict[
                                            widget_type][i-1])
                                    except TypeError:
                                        print "it was not possible to set this folder"
				elif widget_type == 'fbtn':
                                    widget.set_font(pickled_dict[widget_type][i-1])
                                elif widget_type == 'clbtn':
                                    color = Gdk.color_parse(pickled_dict[widget_type][i-1])
                                    widget.set_rgba(Gdk.RGBA.from_color(color))
                                    # FIXME: GtkButton.set_rgba since Gtk 3.4 deprecated!
                                i +=1

	def on_btn_apply_clicked (self, button):
		settings_dict = self.check_settings(self.active_tab)
		if settings_dict:
			if self.active_tab == 'encryption':
				self.migration = self.builder.get_object(
					'cbtn_encryption01').get_active()
			try:
				self.not_applied_set.remove(self.active_tab)
			except KeyError:
				print "not anymore in not_applied_set, was already removed"
			self.all_settings_dict[self.active_tab] = settings_dict
			self.update_status()				
		
		# check all settings of a single category, and return these
	def check_settings(self, category):		
		# same for all categories
		widget_to_check = ('rbtn', 'cbtn', 'e', 'fcbtn', 'fbtn', 'clbtn')
		settings_dict = {}		
		for widget_type in widget_to_check:
			data = self.get_widget_data (category, widget_type)
			settings_dict.update({widget_type: data})			
		return settings_dict

		# get all the settings of one category and one widget type
		# widgets supported: rbtn, cbtn, e (entries), fcbtn, fbtn, clbtn
		# name of widgets must be like rbtn_target01
	def get_widget_data(self, category, abbreviation):
		# find out which type of widget it is...
		i = 1
		zero = '0' 
		setting_list = []
		while True:
			#if i>9: zero = '' # uncomment if widget numbers >9 are used
			widget = self.builder.get_object(abbreviation + '_' + category
				+ zero + str(i))
			if not widget:
				break
			if abbreviation == 'rbtn':
				method_dict = {'rbtn': widget.get_active()}
			elif abbreviation == 'cbtn':
				method_dict = {'cbtn': widget.get_active()}
			elif abbreviation == 'e':
				method_dict = {'e': widget.get_text()}
			elif abbreviation == 'fcbtn':
				# note: this widget type returns the current folder, not the file
				method_dict = {'fcbtn': widget.get_current_folder()}
			elif abbreviation == 'fbtn':
				method_dict = {'fbtn': widget.get_font()}
			elif abbreviation == 'clbtn':
                                method_dict = {'clbtn': widget.get_property( # get color as hex
                                        'rgba').to_color().to_string()}
			else:
				raise KeyError("widget type " + str(abbreviation) 
					+ ' is not supported')
			setting_list.append(method_dict[abbreviation])
			i += 1
		return tuple(setting_list)

	def update_status(self):
		status_string = ''
		if len(self.not_applied_set)>2: # show applied settings
			for item in self.SETTING_TABS:
				if item in self.not_applied_set:
					continue
				status_string = status_string + ', ' + item
			self.statusbar_applied.push(0, 'settings applied: '
				+ status_string.lstrip(", "))
		else:
			for item in self.not_applied_set: # show not applied settings
				status_string = status_string + ', ' + item
			self.statusbar_applied.push(0, 'status: settings not applied yet: '
				+ status_string.lstrip(", "))


	def on_e_target05_grab_focus (self, widget):
		e_target05 = self.builder.get_object('e_target05')
		e_target05.set_visibility(False)
		e_target05.set_text("")
		
	def hide_infbars(self):
		self.infbar_target.hide()
		self.infbar_encryption.hide()
		self.infbar_saving.hide()
		self.infbar_font.hide()

	def on_btn_yes_hints_clicked (self, button):
		self.infbar_show_hints.hide()
		self.infbar_hints.show()
	
	def on_btn_hint_hide_clicked (self, button):
		self.infbar_hints.hide()
		self.infbar_show_hints.show()

	def update_inconsistency(self, widget):
                try:
                        self.builder.get_object('rbtn_target').set_inconsistent(0)
                        self.builder.get_object('rbtn_encryption').set_inconsistent(0)
                        self.builder.get_object('rbtn_saving').set_inconsistent(0)
                        self.builder.get_object('rbtn_font').set_inconsistent(0)
                        widget.set_inconsistent(True)
                except AttributeError: # happens just after window opened
                        self.builder.get_object('rbtn_target').set_inconsistent(True)
                        

		# target
	def on_rbtn_target_grab_focus (self, widget):
		self.active_tab = "target"
		self.update_inconsistency(widget)		
		self.hide_infbars()
		self.infbar_target.show()
		self.lbl_hint.set_text(
		"Tip: if not sure, use the filesystem primarily.\n" 
		" → then you can still use MongoDB as extra option. \n"
		"(MongoDB Hosts include: www.mongohq.com, mongolab.com)\n"
		"Attention: The Password of the MongoDB connection is saved in cleartext!")
		# TODO: hash connection password or let user retype it at app start

		# encryption
	def on_rbtn_encryption_grab_focus (self, widget):
		self.active_tab = "encryption"
		self.update_inconsistency(widget)
		self.hide_infbars()
		self.infbar_encryption.show()
		self.lbl_hint.set_text(
		"Note: for encryption the blowfish cypher is used. This method of "
		"encoding is considered save and fast. The password is not saved! You will "
                "have to write it down or remember it!\n"
		"If \"ask about password migration\" is enabled you will get asked, if "
		"you wish to encrypt a particular notebook. It's also possible to change"
                " passwords.")

		#saving
	def on_rbtn_saving_grab_focus (self, widget):
		self.active_tab = "saving"
		self.update_inconsistency(widget)
		self.hide_infbars()			
		self.infbar_saving.show()
		self.lbl_hint.set_text(
		"instant auto save: automatically save the note, when changes happen\n"
		"\nnewline auto save: saves when the lines are added or removed\n"
		"\ndisable auto save: saving is then possible via a button")

	def on_rbtn_font_grab_focus (self, widget):
		self.active_tab = "font"
		self.update_inconsistency(widget)
		self.hide_infbars()
		self.infbar_font.show()
		self.lbl_hint.set_text(
		"'use system default font': if selected, the OS default font will be "
		"used"
		"\n'set app specific font': if selected, a app specific font can be "
		"chosen.\n"
		"\n'disable app colors': if selected default app theme colors will "
		"be used."
		"\n'set just one color': if selected, you may choose one main color."
		"\n'set three colors': then you can set background, font and "
		"widget color.")

	def update_visibility(self, category, number):
                '''password entries should only be visible if 'Password' is included in
                it'''
                entry_field =self.builder.get_object('e_' + category + '0' + str(number))
                if 'Password' not in entry_field.get_text():
                        entry_field.set_visibility(False)

	def update_sensitivity(self): 
		'''some widgets should be insensitive or sensitive depending on which
		rbtn is active; for this purpose exists this method'''

		# check category 'target'
		sensitivity = self.builder.get_object('rbtn_target02').get_active()
		self.builder.get_object('cbtn_target01').set_sensitive(not sensitivity)
		self.builder.get_object('cbtn_target02').set_sensitive(sensitivity)
		self.set_sensitivity('e', 'target', 1, sensitivity)
		if not sensitivity: # check cbtn_target01
			activate = self.builder.get_object('cbtn_target01').get_active()
			self.set_sensitivity('e', 'target', 1, activate)

		# check category 'encryption'
		sensitivity = self.builder.get_object('rbtn_encryption02').get_active()
		self.builder.get_object('cbtn_encryption01').set_sensitive(sensitivity)

		# check category 'font'
		sensitivity = self.builder.get_object('rbtn_font02').get_active()
		self.builder.get_object('cbtn_font01').set_sensitive(sensitivity)
		self.builder.get_object('fbtn_font01').set_sensitive(sensitivity)

	def on_rbtn_target01_toggled (self, togglebutton):
		self.builder.get_object('cbtn_target01').set_sensitive(True)
		self.builder.get_object('cbtn_target02').set_sensitive(False)
		self.builder.get_object('rbtn_saving01').set_sensitive(True)
		if not self.builder.get_object('cbtn_target01').get_active():
			self.set_sensitivity('e', 'target', 1, 0)

	def on_cbtn_target01_toggled (self, togglebutton):
		if togglebutton.get_active():
			self.set_sensitivity('e', 'target', 1, 1)
		else:
			self.set_sensitivity('e', 'target', 1, 0)
			self.builder.get_object('e_target05').set_text("User Password")
			self.builder.get_object('e_target05').set_visibility(True)

	def on_rbtn_target02_toggled (self, togglebutton):
		self.builder.get_object('cbtn_target02').set_sensitive(1)
		self.builder.get_object('cbtn_target01').set_sensitive(0)
		self.set_sensitivity('e', 'target', 1, 1)
		# if MongoDB is primarily used, disable instant save option
		rbtn_saving01 = self.builder.get_object('rbtn_saving01')
		rbtn_saving01.set_sensitive(False)
		if rbtn_saving01.get_active():
			self.builder.get_object('rbtn_saving02').set_active(True)
			self.active_tab = 'saving'
			self.on_btn_apply_clicked(0)

	def on_rbtn_encryption01_toggled (self, togglebutton):
		cbtn_migrate = self.builder.get_object('cbtn_encryption01')
		cbtn_migrate.set_active(False)
		cbtn_migrate.set_sensitive(0)
			
	def on_rbtn_encryption02_toggled (self, togglebutton):
		self.builder.get_object('cbtn_encryption01').set_sensitive(1)	

	def on_rbtn_font02_toggled (self, togglebutton):
		if togglebutton.get_active():
                        self.builder.get_object('cbtn_font01').set_sensitive(1)
                        self.builder.get_object('fbtn_font01').set_sensitive(1)
		else:
                        self.builder.get_object('cbtn_font01').set_sensitive(0)
                        self.builder.get_object('fbtn_font01').set_sensitive(0)
		
	def set_sensitivity(self, abbreviation, category, start, sensitive):
		"""makes several widgets of one type sensitive or insensitive"""
		# to avoid repetition
		i = start
		zero = '0' 
		while True:
			#if i>9: zero = '' # uncomment if numbers >9 are used
			widget_identity = abbreviation + '_' + category + zero + str(i) 
			widget = self.builder.get_object(widget_identity)
			if not widget:
				break
			widget.set_sensitive(sensitive)
			i += 1
		
	def on_btn_close_clicked (self, button):
		self.write_config_file()
		self.builder.get_object('window_settings').hide()			

	def write_config_file(self):
		if len(self.not_applied_set) > 0:
			copied = list(self.not_applied_set)
			for not_applied in copied:
				# restore previously saved settings
				self.load_settings_from_file(CONFIG_FILE, not_applied)
				self.active_tab = not_applied
				settings_dict = self.check_settings(self.active_tab)
				self.all_settings_dict[self.active_tab] = settings_dict
		config_file = open(CONFIG_FILE, 'w')
		for category in self.SETTING_TABS:
			print category
			print self.all_settings_dict[category]
			pickle.dump(self.all_settings_dict[category], config_file)
		config_file.close()				
		
	def destroy(window, self):
		Gtk.main_quit()
