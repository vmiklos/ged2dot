pyinstaller ^
    -y ^
    --clean ^
    --windowed ^
    --add-data="placeholder-f.png;." ^
    --add-data="placeholder-m.png;." ^
    --add-data="placeholder-u.png;." ^
    qged2dot.py
