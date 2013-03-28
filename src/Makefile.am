## Process this file with automake to produce Makefile.in
## Created by Anjuta


uidir = $(pkgdatadir)/ui
ui_DATA = notesapp.ui


## The main script
bin_SCRIPTS = notesapp.py

## Directory where .class files will be installed
notesappdir = $(pythondir)/notesapp


notesapp_PYTHON = \
	notesapp.py


EXTRA_DIST = $(ui_DATA)


# Remove ui directory on uninstall
uninstall-local:

	-rm -r $(uidir)

	-rm -r $(pkgdatadir)
