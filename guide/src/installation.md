# Installation

## Download

From [GitHub](https://github.com/vmiklos/ged2dot).

## Running the script in-place

You can build the code using:

```console
./ged2dot.py --help
```

You can run the tests using:

```console
make check
```

## Qt-based GUI

The `qged2dot.py` script is a Qt-based GUI for `ged2dot`, which can turn the `dot` output into PNG
files.

The installer bundles Graphviz for Windows.

The app icon is by [Appzgear](https://icon-icons.com/icon/family-tree/120659).

## LibreOffice Draw GEDCOM import filter

The `libreoffice/` subdirectory contains a LibreOffice extension, that
implements a GEDCOM import filter for Draw. Needless to say, it uses `ged2dot`
internally -- think of it as a GUI for `ged2dot`, with the additional benefit
that you can hand-edit the resulting layout in Draw, if you want.

Its dependencies:

- It uses Graphviz to process the `dot` format. In case you don't have Graphviz
  installed:

  - For Windows, [get it here](https://graphviz.gitlab.io/_pages/Download/Download_windows.html) (2.38 is tested).

  - For Linux, use your package manager to install the `graphviz` package (2.28 is tested).

- LibreOffice >= 7.2

Features:

- Filter detection: you can use File -> Open and select a GEDCOM file, and
  it'll be opened in Draw automatically.
- Import options: On import, a graphical dialog can be used to set a subset of
  the options available in a `ged2dotrc`.
- Internally reuses the excellent SVG import filter of LibreOffice, contributed
  by Fridrich Strba and Thorsten Behrens, so the result can be manually
  fine-tuned if necessary.
- Runs on Windows and Linux.

You can grap a release binary at [the releases page](https://github.com/vmiklos/ged2dot/releases) --
more on how to to install a LibreOffice extension
[here](https://wiki.documentfoundation.org/Documentation/HowTo/install_extension).

NOTE: Linux distributions install Python support separately, be sure to install the
`libreoffice-script-provider-python` (deb) or `libreoffice-pyuno` (rpm) packages before the OXT
file.

Once that's done, you'll see something like this if you open a GEDCOM file:

![screenshot](https://vmiklos.hu/ged2dot/libreoffice/screenshot.png)
