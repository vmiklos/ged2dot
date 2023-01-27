# Usage

You usually want to customize your input filename, output filenames, the root family and the depth
of the graph visitor. You can provide these either by using command-line arguments (see `ged2dot.py
--help`) or by using a configuration file (see `ged2dotrc.sample`). When using both, the
command-line arguments overwrite configuration values.

A typical flow looks like this with a provided test input:

```console
./ged2dot.py --input tests/happy.ged --output test.dot --rootfamily F1 --familydepth 3
dot -Tsvg -o test.svg test.dot
```

At this point you can open test.svg in your web browser and check the result. Mouse tooltips on the
marriage nodes give you family IDs. You can change the familydepth parameter to include less or more
nodes around the root family.

## Layout

The layout does a Breadth First Search (BFS) traversal on the graph, from the starting family.

This has several benefits over explicitly trying to guess which family belongs to which generation.
Some example more tricky cases, which are handled by `ged2dot`:

- root family → husband → sister → showing her kids

- root family → wife → cousin → showing her kid

- root family → husband → grand father → showing both wives with the matching kids

- marrying cousins

(ged2dot <= 7.0 allowed multiple layouts, none of them supported the above more tricky cases.)

GEDCOM files don't contain images, but you can put images next to the GEDCOM file, and in that case
ged2dot will try to pick them up when generating `dot` output. The expected location is
`images/Given Family 1234.jpg`, relative to the GEDCOM file. For example, there is a person called
Ray Smith in the above screenshot. The birth year string is `Y`, so the image location has to be
`images/Ray Smith Y.jpg`.

## Bugs

For `ged2dot`, in case a given input results in a runtime crash, it's
considered a bug. If you have a fix for it,
[pull requests](https://github.com/vmiklos/ged2dot/pull/new/master) on GitHub are
welcome. Make sure to run `make check` before submitting your changes.

For the LibreOffice extension, in case you get an error during opening:

- For Windows, the log file location is something like:

```
C:/Users/John/Application Data/LibreOffice/4/user/Scripts/python/log.txt
```

- For Linux, start LibreOffice from a terminal, the log is printed to the
  standard error.

- For Mac, start LibreOffice from Terminal:

```
cd /Applications/LibreOffice.app/Contents/program
./soffice --nologo /path/to/test.ged
```

then the log is printed to the standard error as well.

## Icons

Icons are from
[WPZOOM](http://www.wpzoom.com/wpzoom/new-freebie-wpzoom-developer-icon-set-154-free-icons/),
in case placeholders have to be used for missing images.

## Resources

- [GEDCOM specification](https://www.familysearch.org/developers/docs/guides/gedcom)
- [Translation of ged2dot to JavaScript](https://gist.github.com/fetsorn/1d5f6cbc47989b32cb461528c1e253b4)
