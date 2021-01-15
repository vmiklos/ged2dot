OS = $(shell uname)
VERSION = $(shell git describe)

PYTHON_UNSAFE_OBJECTS = \
	libreoffice/base.py \
	libreoffice/dialog.py \
	libreoffice/importer.py \
	libreoffice/loader.py \
	qged2dot.py \

PYTHON_SAFE_OBJECTS = \
	ged2dot.py \
	inlineize.py \

PYTHON_TEST_OBJECTS = \
	tests/test_ged2dot.py \
	tests/test_inlineize.py \

PYTHON_OBJECTS = \
	$(PYTHON_UNSAFE_OBJECTS) \
	$(PYTHON_SAFE_OBJECTS) \
	$(PYTHON_TEST_OBJECTS) \

DOT = $(shell which dot)
all:

check: check-mypy check-flake8 check-pylint check-unit

check-mypy: $(patsubst %.py,%.mypy,$(PYTHON_OBJECTS))

check-flake8: $(patsubst %.py,%.flake8,$(PYTHON_OBJECTS))

check-pylint: $(patsubst %.py,%.pylint,$(PYTHON_OBJECTS))

check-unit:
	env PYTHONPATH=.:tests coverage run --branch --module unittest $(PYTHON_TEST_OBJECTS)
	env PYTHONPATH=.:tests coverage report --show-missing --fail-under=100 $(PYTHON_SAFE_OBJECTS)

%.mypy: %.py Makefile
	mypy --python-version 3.6 --strict --no-error-summary $< && touch $@

%.flake8: %.py Makefile
	flake8 $< && touch $@

%.pylint : %.py Makefile .pylintrc
	env PYTHONPATH=. pylint $< && touch $@

pack:
	rm -rf dist
	pyinstaller \
		-y \
		--clean \
		--windowed \
		$(if $(filter Darwin,$(OS)),--icon icon.icns,) \
		$(if $(filter Darwin,$(OS)),--osx-bundle-identifier hu.vmiklos.ged2dot,) \
		--add-data="placeholder-f.png:." \
		--add-data="placeholder-m.png:." \
		--add-data="placeholder-u.png:." \
		--add-binary="$(DOT):." \
		qged2dot.py
ifeq ($(OS),Darwin)
	hdiutil create dist/qged2dot-$(VERSION).dmg -srcfolder dist/qged2dot.app -ov
endif
