SHELL := bash
PYFILES := ged2dot.py inlineize.py test/test.py libreoffice/base.py libreoffice/loader.py libreoffice/filter.py libreoffice/dialog.py

test.png: test.dot
	dot -Tpng -o test.png test.dot

test.svg: test-noinline.svg inlineize.py
	./inlineize.py test-noinline.svg test.svg

test-noinline.svg: test.dot
	dot -Tsvg -o test-noinline.svg test.dot

test.dot: test.ged ged2dot.py ged2dotrc Makefile
	./ged2dot.py > test.dot

%.mypy : %.py
	mypy --strict $< && touch $@

check: $(patsubst %.py,%.mypy,$(PYFILES))
	cd test && PYTHONPATH=$(PWD) ./test.py
	pycodestyle $(PYFILES)
	! pylint $(PYFILES) 2>&1 | egrep -i 'unused|indent'

# In case ged2dotrc or test.dot is missing, create a copy based on the
# screenshot sample.

test.ged :| test/screenshot.ged
	cat test/screenshot.ged > test.ged

ged2dotrc :| test/screenshotrc
	sed 's/screenshot.ged/test.ged/' test/screenshotrc > ged2dotrc
