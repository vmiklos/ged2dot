test.png: test.dot
	dot -Tpng -o test.png test.dot

test.svg: test-noinline.svg inlineize.py
	./inlineize.py test-noinline.svg test.svg

test-noinline.svg: test.dot
	dot -Tsvg -o test-noinline.svg test.dot

test.dot: test.ged ged2dot.py ged2dotrc Makefile
	./ged2dot.py > test.dot

check:
	cd test && ./test.py
	pep8 --ignore=E501 ged2dot.py inlineize.py test/test.py libreoffice/loader.py libreoffice/filter.py libreoffice/dialog.py

# In case ged2dotrc or test.dot is missing, create a copy based on the
# screenshot sample.

test.ged :| test/screenshot.ged
	cat test/screenshot.ged > test.ged

ged2dotrc :| test/screenshotrc
	sed 's/screenshot.ged/test.ged/' test/screenshotrc > ged2dotrc
