# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0

NAME = gedcom
ifeq ($(VERSION),)
VERSION = $(shell git describe)
endif
OXT = $(NAME)-$(VERSION).oxt
PACKAGE = hu.vmiklos.libreoffice.Draw.GedcomImportFilter

PARENTFILES = inlineize.py ged2dot.py placeholder-m.svg placeholder-f.svg placeholder-u.svg marriage.svg
MYFILES = loader.py base.py importer.py dialog.py Config.xcs Config.xcu Filter.xcu Type.xcu description.xml META-INF/manifest.xml

PARENTFILES_SRC = $(foreach FILE,$(PARENTFILES),../$(FILE))

$(OXT): $(PARENTFILES_SRC) $(MYFILES) Makefile
	echo '[build OXT] $(NAME)'
	cp $(PARENTFILES_SRC) .
	zip -q $(OXT) $(PARENTFILES) $(MYFILES)
	rm -f $(PARENTFILES)

description.xml: description.in.xml
	echo '[build XML] description'
	sed 's/@VERSION@/$(VERSION)/' description.in.xml > description.xml

install: $(OXT)
	echo '[pkg   REM] $(NAME)'
	"$(UNOPKG_PREFIX)unopkg" remove $(PACKAGE) || :
	echo '[pkg   ADD] $(NAME)'
	"$(UNOPKG_PREFIX)unopkg" add -s $(OXT)

.PHONY : install

# vim: set sw=4 ts=4:
