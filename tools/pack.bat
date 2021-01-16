pyinstaller ^
    -y ^
    --clean ^
    --windowed ^
    --add-data="placeholder-f.png;." ^
    --add-data="placeholder-m.png;." ^
    --add-data="placeholder-u.png;." ^
    --add-binary="graphviz/bin/dot.exe;." ^
    qged2dot.py
copy /y graphviz\bin\*.* dist\qged2dot
