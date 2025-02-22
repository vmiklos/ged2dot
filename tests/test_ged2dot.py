#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0

"""The test_ged2dot module covers the ged2dot module."""

from typing import Dict
import io
import os
import unittest
import unittest.mock
import xml.etree.ElementTree as ET

import pygraphviz  # type: ignore

import ged2dot


class TestIndividual(unittest.TestCase):
    """Tests Individual."""
    def test_nosex(self) -> None:
        """Tests the no sex case."""
        config = {
            "familydepth": "4",
            "input": "tests/nosex.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.tokenize(config)
        individual = ged2dot.graph_find(graph, "42")
        assert individual is None
        individual = ged2dot.graph_find(graph, "P3")
        assert individual
        assert isinstance(individual, ged2dot.Individual)
        self.assertIn("placeholder-u", individual.get_label("tests/images", "little", "{}-", basepath=""))
        self.assertEqual(individual.get_color(), "black")

    def test_big_endian_name(self) -> None:
        """Tests the case when the name starts with the family name."""
        config = {
            "input": "tests/hello.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.tokenize(config)
        individual = ged2dot.graph_find(graph, "P1")
        assert individual
        assert isinstance(individual, ged2dot.Individual)
        label = individual.get_label(image_dir="", name_order="big", birth_format="{}-", basepath="")
        self.assertIn("A<br/>Alice", label)

    def test_name_suffix(self) -> None:
        """Tests the case when the name has a suffix."""
        config = {
            "input": "tests/suffix.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.tokenize(config)
        individual = ged2dot.graph_find(graph, "P1")
        assert individual
        assert isinstance(individual, ged2dot.Individual)
        label = individual.get_label(image_dir="", name_order="little", birth_format="{}-", basepath="")
        self.assertIn("Alice<br/>A Suffix", label)

    def test_str(self) -> None:
        """Tests __str()__."""
        config = {
            "input": "tests/hello.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.tokenize(config)
        individual = ged2dot.graph_find(graph, "P1")
        # Make sure that this doesn't loop.
        self.assertNotEqual(str(individual), "")


class TestFamily(unittest.TestCase):
    """Tests Family."""
    def test_str(self) -> None:
        """Tests __str()__."""
        config = {
            "input": "tests/hello.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.tokenize(config)
        family = ged2dot.graph_find(graph, "F1")
        # Make sure that this doesn't loop.
        self.assertNotEqual(str(family), "")


class TestGedcomImport(unittest.TestCase):
    """Tests GedcomImport."""
    def test_no_surname(self) -> None:
        """Tests the no surname case."""
        config = {
            "familydepth": "4",
            "input": "tests/no_surname.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.tokenize(config)
        individual = ged2dot.graph_find(graph, "P1")
        assert individual
        assert isinstance(individual, ged2dot.Individual)
        self.assertEqual(individual.get_surname(), "")
        self.assertEqual(individual.get_forename(), "Alice")

    def test_level3(self) -> None:
        """Tests that we just ignore a 3rd level (only 0..2 is valid)."""
        config = {
            "familydepth": "0",
            "input": "tests/level3.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        subgraph = ged2dot.bfs(root_family, config)
        self.assertEqual(len(subgraph), 3)

    def test_unexpected_date(self) -> None:
        """Tests that we just ignore a date which is not birth/death."""
        config = {
            "familydepth": "0",
            "input": "tests/unexpected_date.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        subgraph = ged2dot.bfs(root_family, config)
        self.assertEqual(len(subgraph), 3)


class BufferHolder:
    """Mock for sys.stdin."""
    def __init__(self) -> None:
        self.buffer = io.BytesIO()


class TestMain(unittest.TestCase):
    """Tests main(), first test set."""
    def test_happy(self) -> None:
        """Tests the happy path."""
        config = {
            "familydepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/happy.dot",
            "rootfamily": "F1",
            "imagedir": "images",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))
        with open(config["output"], "r", encoding="utf-8") as dot_stream:
            graph = pygraphviz.AGraph(string=dot_stream.read())
        person = graph.get_node("P48")
        stream = io.StringIO(person.attr.get("label"))
        tree = ET.parse(stream)
        root = tree.getroot()
        row = root.find("tr")
        assert row
        cell = row.find("td")
        assert cell
        img = cell.find("img")
        assert img is not None
        actual_src = img.attrib.get("src")
        expected_src = os.path.join(os.getcwd(), "tests", "images", "Richard Smith Y.jpg")
        self.assertEqual(actual_src, expected_src)

    def test_image_abspath(self) -> None:
        """Tests the case when imagedir is an abs path already."""
        config = {
            "familydepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/image-abspath.dot",
            "rootfamily": "F1",
            "imagedir": os.path.join(os.getcwd(), "tests/images"),
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))
        with open(config["output"], "r", encoding="utf-8") as stream:
            self.assertIn(config["imagedir"], stream.read())

    def test_config(self) -> None:
        """Tests the case when there is a ged2dotrc in the current dir."""
        pwd = os.getcwd()
        os.chdir("tests/config")
        try:
            if os.path.exists("hello.dot"):
                os.unlink("hello.dot")
            self.assertFalse(os.path.exists("hello.dot"))
            argv = ["", "--config", "ged2dotrc"]
            with unittest.mock.patch('sys.argv', argv):
                ged2dot.main()
            self.assertTrue(os.path.exists("hello.dot"))
        finally:
            os.chdir(pwd)

    def test_no_images(self) -> None:
        """Tests the happy path."""
        config = {
            "familydepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/happy.dot",
            "rootfamily": "F1",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))
        with open(config["output"], "r", encoding="utf-8") as stream:
            self.assertNotIn("images/", stream.read())

    def test_bom(self) -> None:
        """Tests handling of an UTF-8 BOM."""
        config = {
            "familydepth": "4",
            "input": "tests/bom.ged",
            "output": "tests/bom.dot",
            "rootfamily": "F1",
            "imagedir": "tests/images",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        # Without the accompanying fix in place, this test would have failed with:
        # ValueError: invalid literal for int() with base 10: '\ufeff0'
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))

    def test_family_depth(self) -> None:
        """Tests handling of the familydepth parameter."""
        config = {
            "familydepth": "0",
            "input": "tests/happy.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        subgraph = ged2dot.bfs(root_family, config)
        # Just 3 nodes: wife, husband and the family node.
        self.assertEqual(len(subgraph), 3)

    def test_no_wife(self) -> None:
        """Tests handling of no wife in a family."""
        config = {
            "familydepth": "0",
            "input": "tests/no_wife.ged",
            "output": "tests/no_wife.dot",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        neighbours = root_family.get_neighbours("both")
        # Just 1 node: husband.
        self.assertEqual(len(neighbours), 1)
        self.assertEqual(neighbours[0].get_identifier(), "P2")

        # Test export of a no-wife model.
        subgraph = ged2dot.bfs(root_family, config)
        exporter = ged2dot.DotExport()
        exporter.store(subgraph, config)

    def test_no_husband(self) -> None:
        """Tests handling of no husband in a family."""
        config = {
            "familydepth": "0",
            "input": "tests/no_husband.ged",
            "output": "tests/no_husband.dot",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        neighbours = root_family.get_neighbours("both")
        # Just 1 node: wife.
        self.assertEqual(len(neighbours), 1)
        self.assertEqual(neighbours[0].get_identifier(), "P1")

        # Test export of a no-husband model.
        subgraph = ged2dot.bfs(root_family, config)
        exporter = ged2dot.DotExport()
        exporter.store(subgraph, config)

    def test_config_input_default(self) -> None:
        """Tests config: input: default."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["input"], "-")
        argv = [""]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

        # Now test reading from stdin.
        argv = ["", "--output", "tests/output.dot"]
        stdin = BufferHolder()
        with open("tests/happy.ged", "rb") as stream:
            stdin.buffer.write(stream.read())
            stdin.buffer.seek(0)
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('sys.stdin', stdin):
                ged2dot.main()

    def test_config_input_custom(self) -> None:
        """Tests config: input: custom."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["input"], "test.ged")
        argv = ["", "--input", "test.ged"]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_config_output_default(self) -> None:
        """Tests config: output: default."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["output"], "-")
        argv = [""]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

        # Now test writing to stdout.
        argv = ["", "--input", "tests/happy.ged"]
        stdout = BufferHolder()
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('sys.stdout', stdout):
                ged2dot.main()
        stdout.buffer.seek(0)
        actual = stdout.buffer.read()
        self.assertTrue(actual.startswith(b"// Generated by "))

    def test_config_output_custom(self) -> None:
        """Tests config: output: custom."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["output"], "test.ged")
        argv = ["", "--output", "test.ged"]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_config_rootfamily_default(self) -> None:
        """Tests config: rootfamily: default."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["rootfamily"], "F1")
        argv = [""]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_config_rootfamily_custom(self) -> None:
        """Tests config: rootfamily: custom."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["rootfamily"], "F42")
        argv = ["", "--rootfamily", "F42"]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_config_familydepth_default(self) -> None:
        """Tests config: familydepth: default."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["familydepth"], "3")
        argv = [""]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_config_familydepth_custom(self) -> None:
        """Tests config: familydepth: custom."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["familydepth"], "0")
        argv = ["", "--familydepth", "0"]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_config_imagedir_default(self) -> None:
        """Tests config: imagedir: default."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["imagedir"], "images")
        argv = [""]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_config_imagedir_custom(self) -> None:
        """Tests config: imagedir: custom."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["imagedir"], "myimagedir")
        argv = ["", "--imagedir", "myimagedir"]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_config_nameorder_default(self) -> None:
        """Tests config: nameorder: default."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["nameorder"], "little")
        argv = [""]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_config_birthformat_custom(self) -> None:
        """Tests config: birthformat: custom."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["birthformat"], "* {}")
        argv = ["", "--birthformat", "* {}"]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()


class TestMain2(unittest.TestCase):
    """Tests main(), second test set."""
    def test_cousins_marrying(self) -> None:
        """Tests cousins marrying."""
        config = {
            "familydepth": "4",
            "input": "tests/cousins-marrying.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        subgraph = ged2dot.bfs(root_family, config)
        # 8 nodes:
        # 1) A
        # 2) B
        # 3) family in which A and B are kids
        # 4) A's family
        # 5) B's family
        # 6) A's kid: C
        # 7) B's kid: D
        # 8) C and D's family
        self.assertEqual(len(subgraph), 8)

    def test_multiline_note(self) -> None:
        """Tests multiline notes."""
        config = {
            "familydepth": "4",
            "input": "tests/multiline-note.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        person = ged2dot.graph_find(graph, "P2")
        assert person
        assert isinstance(person, ged2dot.Individual)
        self.assertEqual(person.get_config().get_note(), "This is a note with\n3\nlines")

    def test_no_cr(self) -> None:
        """Tests the case when the file contains no \r."""
        config = {
            "familydepth": "4",
            "input": "tests/no-cr.ged",
            "output": "tests/no-cr.dot",
            "rootfamily": "F1",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))

    def test_relpath(self) -> None:
        """Tests the happy path."""
        config = {
            "familydepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/happy.dot",
            "rootfamily": "F1",
            "imagedir": os.path.join(os.getcwd(), "tests/images"),
            "relpath": "true",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))
        with open(config["output"], "r", encoding="utf-8") as stream:
            self.assertNotIn('src="/', stream.read())

    def test_config_relpath_custom(self) -> None:
        """Tests config: relpath: custom."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["relpath"], "true")
        argv = ["", "--relpath"]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_death_date(self) -> None:
        """Tests the case when no birth date is provided."""
        config = {
            "familydepth": "4",
            "input": "tests/death_date.ged",
            "output": "tests/death_date.dot",
            "rootfamily": "F1",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))
        with open(config["output"], "r", encoding="utf-8") as stream:
            self.assertIn("† Y", stream.read())

    def test_config_nameorder_custom(self) -> None:
        """Tests config: nameorder: custom."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["nameorder"], "big")
        argv = ["", "--nameorder", "big"]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_fam_marr(self) -> None:
        """Tests handling of marriage date in a family."""
        config = {
            "familydepth": "0",
            "input": "tests/fam_marr.ged",
            "output": "tests/fam_marr.dot",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        assert isinstance(root_family, ged2dot.Family)
        # Check the found date, both the husb and the wife has a bogus date, which should be
        # ignored.
        self.assertEqual(root_family.get_marr(), "1970")

        # Test export of a fam-marr model.
        subgraph = ged2dot.bfs(root_family, config)
        exporter = ged2dot.DotExport()
        exporter.store(subgraph, config)

    def test_fam_no_marr(self) -> None:
        """Tests handling of marriage node when it has no date."""
        # Given a family with no marriage date:
        config = {
            "familydepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/happy.dot",
            "rootfamily": "F1",
            "imagedir": os.path.join(os.getcwd(), "tests/images"),
            "relpath": "true",
        }

        # When converting from ged to dot:
        ged2dot.convert(config)

        # Then make sure that explicit width and height is specified for the table around the image,
        # required by the PNG output:
        with open(config["output"], "r", encoding="utf-8") as dot_stream:
            graph = pygraphviz.AGraph(string=dot_stream.read())
        family = graph.get_node("F1")
        stream = io.StringIO(family.attr.get("label"))
        tree = ET.parse(stream)
        root = tree.getroot()
        self.assertIn("width", root.attrib)
        self.assertIn("height", root.attrib)

    def test_bad_rootfamily(self) -> None:
        """Tests the happy path."""
        config = {
            "familydepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/happy.dot",
            "rootfamily": "42",
            "imagedir": "images",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        with self.assertRaises(Exception):
            ged2dot.convert(config)

    def test_bad_rootfamily_empty_graph(self) -> None:
        """Tests the happy path."""
        config = {
            "familydepth": "4",
            "input": "tests/empty.ged",
            "output": "tests/empty.dot",
            "rootfamily": "42",
            "imagedir": "images",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        with self.assertRaises(Exception):
            ged2dot.convert(config)

    def test_config_direction_custom(self) -> None:
        """Tests config: direction: custom."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertEqual(config["direction"], "child")
        argv = ["", "--direction", "child"]
        with unittest.mock.patch('sys.argv', argv):
            with unittest.mock.patch('ged2dot.convert', mock_convert):
                ged2dot.main()

    def test_direction_child(self) -> None:
        """Tests the direction=child case."""
        config = {
            "familydepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/happy.dot",
            "direction": "child",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        indi = ged2dot.graph_find(graph, "P157")
        assert indi
        neighbours = indi.get_neighbours("both")
        # parent: F152 + child: F25
        self.assertEqual(len(neighbours), 2)
        neighbours = indi.get_neighbours("child")
        # child: F25
        self.assertEqual(len(neighbours), 1)


class TestGetAbspath(unittest.TestCase):
    """Tests get_abspath()."""
    def test_happy(self) -> None:
        """Tests the happy path."""
        self.assertEqual(ged2dot.get_abspath("foo"), os.path.join(os.getcwd(), "foo"))

    def test_abs(self) -> None:
        """Tests the case when the input is abs already."""
        abspath = os.path.join(os.getcwd(), "foo")
        self.assertEqual(ged2dot.get_abspath(abspath), abspath)


class TestFuzz(unittest.TestCase):
    """Tests fixed fuzz-generated input."""
    def test_dir(self) -> None:
        """Tests all files in the input directory."""
        root = "tests/fuzz"
        for file in os.listdir(root):
            importer = ged2dot.GedcomImport()
            path = os.path.join(root, file)
            config = {
                "input": path
            }
            try:
                importer.load(config)
            except ged2dot.Ged2DotException:
                pass


if __name__ == '__main__':
    unittest.main()
