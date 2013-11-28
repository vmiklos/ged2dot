test.png: test.dot
	dot -Tpng -o test.png test.dot

test.dot: test.ged ged2dot.py ged2dotrc Makefile
	./ged2dot.py > test.dot

check:
	cd test && ./test.py
	pep8 --ignore=E501 ged2dot.py test/test.py
