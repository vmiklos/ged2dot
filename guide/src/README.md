# Introduction

ged2dot is a GEDCOM to Graphviz converter.

The latest version is v25.2, released on 2025-02-01.

## Description

`ged2dot` is a script that takes a [GEDCOM](http://en.wikipedia.org/wiki/GEDCOM) file and tries to
visualize it using [Graphviz](http://www.graphviz.org/)'s `dot` tool. The basic idea is that you can
map individuals and families to graph nodes and connections between them to graph edges, then `dot`
takes care of the rest. What's unique about `ged2dot` is that it allows more than showing ancestors
and descendants of a single individual (what you can easily do with other existing family editor
software).

It looks like this:

![screenshot](https://vmiklos.hu/ged2dot/tests/screenshot.png)

## Contributing

ged2dot is free and open source. You can find the source code on
[GitHub](https://github.com/vmiklos/ged2dot) and issues and feature requests can be posted on
the issue tracker. If you'd like to contribute, please consider opening a pull request.

## License

Use of this source code is governed by a MPL-style license that can be found in
the LICENSE file.
