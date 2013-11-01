test.png: test.dot
	dot -Tpng -o test.png test.dot

test.dot: test.ged ged2dot.py Makefile
	python ged2dot.py > test.dot
