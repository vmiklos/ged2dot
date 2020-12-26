PYTHON_OBJECTS = \
	core.py \

test.svg: test.dot
	dot -Tsvg -o test.svg test.dot

test.dot: core.py test.ged
	./core.py

check: check-mypy

check-mypy: $(patsubst %.py,%.mypy,$(PYTHON_OBJECTS))

%.mypy: %.py Makefile
	mypy --python-version 3.6 --strict --no-error-summary $< && touch $@
