# Version descriptions

## master

- For people whose names have a suffix (like Richard III, or Sam Jr) extract that and keep it as part of the name (Gregory Dudek)

## 25.2

- Put spouses into a subgraph cluster, so they are closer to each other (Gregory Dudek)

## 24.8

- qget2dot is now ported to qt 6
- the macOS port is now deprecated, CI & release binary will be removed in the next release
- Support a few more image types or file suffixes, notably jpg as well as png (Gregory Dudek)

## 24.2

- Use ordering=out on family nodes to try to control the order of children nodes
- Fix crash on non-existing root family

## 7.6

- Fix crash on non-int line start
- Fix crash on invalid utf-8 lines

## 7.5

- new config option: direction (defaults to `both`, can be `child`)

## 7.4

- Fail nicer when the specified root family doesn't exist
- Document expected image location

## 7.3

- Resolves: gh#179 show date of marriage for a family

## 7.2

- Better support for GenoPro-generated GED files (Andreas Hrubak)
- Keep aspect ratio of images in the PDF output with long names (humaita)
- New --relpath option to use relative paths when referring to images
- Specify the font used for text explicitly to improve centering
- Better handling of death-only dates
- Add --birthformat option
- Switch to svg placeholders
- Add icon for marriage

## 7.1

- Rewritten ged2dot to use BFS for graph traversal (much more robust, though some incompatible old
  options are now ignored)
- Resolves: gh#19 fix infinite recursive stack in Individual.__str__ and Family.__str__
- Resolves: gh#13 marrying cousins is now handled
- Comes with a qged2dot GUI (packaged as DMG for macOS, MSI for Windows)

## 7.0

- tested with LibreOffice 7.0
- pylint fixes
- Use sys.stderr.write instead of print to print errors (Colin Chargy)
- add better error handling and error out on lack of rc file (Doug Hughes)

## 6.0

- fixed to work with 64-bit LibreOffice

## 0.8

- fixed to work with LibreOffice 6.1

## 0.7

- minor fixes, tested with LibreOffice 5.4

## 0.6

- two layout fixes, tested with LibreOffice 5.1

## 0.5

- pylint fixes, tested with LibreOffice 4.4

## 0.4

- New 'layout = Descendants' configuration key to show descendants, not ancestors of the root family.

- Next to "M" and "F", "U" is now accepted as a sex.

- Ancestors layout now handles if the root family has children.

- Mac instructions.

## 0.3

- Handle UTF-8 BOM at the beginning of .ged files
- Fixed layout crash on missing previous parent

## 0.2

- Initial LibreOffice extension

## 0.1

- Initial release
