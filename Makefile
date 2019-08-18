SHELL := bash
PYFILES := ged2dot.py inlineize.py test/test.py libreoffice/base.py libreoffice/loader.py libreoffice/filter.py libreoffice/dialog.py

check-type: $(patsubst %.py,%.mypy,$(PYFILES))

check-lint: $(patsubst %.py,%.lint,$(PYFILES))

test.png: test.dot
	dot -Tpng -o test.png test.dot

test.svg: test-noinline.svg inlineize.py
	./inlineize.py test-noinline.svg test.svg

test-noinline.svg: test.dot
	dot -Tsvg -o test-noinline.svg test.dot

test.dot: test.ged ged2dot.py ged2dotrc Makefile
	./ged2dot.py > test.dot

%.mypy : %.py Makefile
	mypy --python-version 3.5 --strict $< && touch $@

%.lint : %.py Makefile
	pylint \
		--max-line-length=120 \
		--disable=import-error,redefined-builtin,unidiomatic-typecheck,pointless-statement,too-many-instance-attributes,attribute-defined-outside-init,missing-docstring,no-self-use,invalid-name,too-many-branches,too-many-statements,fixme,len-as-condition,line-too-long,superfluous-parens,too-many-arguments,unused-import,protected-access,too-few-public-methods,too-many-locals \
		$< && touch $@

check: check-type check-lint
	cd test && PYTHONPATH=$(PWD) ./test.py
	pycodestyle $(PYFILES)

clean:
	rm -f $(patsubst %.py,%.mypy,$(PYFILES))

# In case ged2dotrc or test.dot is missing, create a copy based on the
# screenshot sample.

test.ged :| test/screenshot.ged
	cat test/screenshot.ged > test.ged

ged2dotrc :| test/screenshotrc
	sed 's/screenshot.ged/test.ged/' test/screenshotrc > ged2dotrc
