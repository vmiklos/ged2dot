pyinstaller ^
    -y ^
    --clean ^
    --windowed ^
    --add-data="placeholder-f.png;." ^
    --add-data="placeholder-m.png;." ^
    --add-data="placeholder-u.png;." ^
    --add-binary="graphviz/bin/cdt.dll;." ^
    --add-binary="graphviz/bin/cgraph.dll;." ^
    --add-binary="graphviz/bin/dot.exe;." ^
    --add-binary="graphviz/bin/expat.dll;." ^
    --add-binary="graphviz/bin/gvc.dll;." ^
    --add-binary="graphviz/bin/pathplan.dll;." ^
    --add-binary="graphviz/bin/xdot.dll;." ^
    qged2dot.py
