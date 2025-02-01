OS = $(shell uname)
VERSION = 25.2

PYTHON_UNSAFE_OBJECTS = \
	libreoffice/base.py \
	libreoffice/dialog.py \
	libreoffice/importer.py \
	libreoffice/loader.py \
	qged2dot.py \
	tools/pack.py \
	tools/requirements.py \

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

all:

check: check-mypy check-flake8 check-pylint check-unit
	@echo "make check: ok"

check-mypy: $(PYTHON_OBJECTS) Makefile requirements.txt
	env PYTHONPATH=.:tests mypy --python-version 3.11 --strict --no-error-summary $(PYTHON_OBJECTS) && touch $@

check-flake8: $(patsubst %.py,%.flake8,$(PYTHON_OBJECTS))

check-pylint: $(patsubst %.py,%.pylint,$(PYTHON_OBJECTS))

check-unit:
	env PYTHONPATH=.:tests coverage run --branch --module unittest $(PYTHON_TEST_OBJECTS)
	env PYTHONPATH=.:tests coverage report --show-missing --fail-under=100 $(PYTHON_SAFE_OBJECTS)

%.flake8: %.py Makefile requirements.txt
	flake8 $< && touch $@

%.pylint : %.py Makefile .pylintrc requirements.txt
	env PYTHONPATH=. pylint -v $< && touch $@

pack:
	rm -rf dist
	make -C libreoffice VERSION=$(VERSION)
	mkdir -p dist
	cp libreoffice/*.oxt dist/

run-guide:
	cd guide && mdbook serve --hostname 127.0.0.1

fuzz:
	env PYTHONPATH=. tools/fuzz.py
