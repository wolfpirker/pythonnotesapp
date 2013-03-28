## Process this file with automake to produce Makefile.in
## Created by Anjuta

SUBDIRS = src 

notesappdocdir = ${prefix}/doc/notesapp
notesappdoc_DATA = \
	README\
	COPYING\
	AUTHORS\
	ChangeLog\
	INSTALL\
	NEWS


EXTRA_DIST = $(notesappdoc_DATA)


# Remove doc directory on uninstall
uninstall-local:
	-rm -r $(notesappdocdir)
