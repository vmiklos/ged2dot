OS = $(shell uname)
VERSION = 7.3

PYTHON_UNSAFE_OBJECTS = \
	libreoffice/base.py \
	libreoffice/dialog.py \
	libreoffice/importer.py \
	libreoffice/loader.py \
	qged2dot.py \
	tools/pack.py \

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
	env PYTHONPATH=.:tests mypy --python-version 3.6 --strict --no-error-summary $(PYTHON_OBJECTS) && touch $@

check-flake8: $(patsubst %.py,%.flake8,$(PYTHON_OBJECTS))

check-pylint: $(patsubst %.py,%.pylint,$(PYTHON_OBJECTS))

check-unit:
	env PYTHONPATH=.:tests coverage run --branch --module unittest $(PYTHON_TEST_OBJECTS)
	env PYTHONPATH=.:tests coverage report --show-missing --fail-under=100 $(PYTHON_SAFE_OBJECTS)

%.flake8: %.py Makefile
	flake8 $< && touch $@

%.pylint : %.py Makefile .pylintrc
	env PYTHONPATH=. pylint $< && touch $@

# If not macOS, assume Linux.
pack:
	rm -rf dist
ifeq ($(OS),Darwin)
	tools/pack.py
else
	make -C libreoffice VERSION=$(VERSION)
	mkdir -p dist
	cp libreoffice/*.oxt dist/
endif
