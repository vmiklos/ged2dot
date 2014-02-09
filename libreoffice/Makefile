# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

NAME = gedcom
VERSION = $(shell git describe)
OXT = $(NAME)-$(VERSION).oxt
PACKAGE = hu.vmiklos.libreoffice.Draw.GedcomImportFilter

PARENTFILES = inlineize.py ged2dot.py placeholder-m.png placeholder-f.png placeholder-u.png
MYFILES = loader.py base.py filter.py dialog.py Config.xcs Config.xcu Filter.xcu Type.xcu description.xml META-INF/manifest.xml

PARENTFILES_SRC = $(foreach FILE,$(PARENTFILES),../$(FILE))

$(OXT): $(PARENTFILES_SRC) $(MYFILES) Makefile
	echo '[build OXT] $(NAME)'
	cp $(PARENTFILES_SRC) .
	zip -q $(OXT) $(PARENTFILES) $(MYFILES)
	rm -f $(PARENTFILES)

description.xml: description.in.xml ../.git/refs/heads/master
	echo '[build XML] description'
	sed 's/@VERSION@/$(VERSION)/' description.in.xml > description.xml

install: $(OXT)
	echo '[pkg   REM] $(NAME)'
	"$(UNOPKG_PREFIX)unopkg" remove $(PACKAGE) || :
	echo '[pkg   ADD] $(NAME)'
	"$(UNOPKG_PREFIX)unopkg" add -s $(OXT)

.PHONY : install

# vim: set sw=4 ts=4:
