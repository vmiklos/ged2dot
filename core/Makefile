PYTHON_SAFE_OBJECTS = \
	core.py \

PYTHON_TEST_OBJECTS = \
	tests/test_core.py \

PYTHON_OBJECTS = \
	$(PYTHON_SAFE_OBJECTS) \
	$(PYTHON_TEST_OBJECTS) \

test.svg: test.dot
	dot -Tsvg -o test.svg test.dot

test.dot: core.py test.ged
	./core.py

check: check-mypy check-flake8 check-pylint #check-unit

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
