#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""The test_ged2dot module covers the ged2dot module."""

from typing import Dict
import os
import unittest
import unittest.mock

import ged2dot


class TestIndividual(unittest.TestCase):
    """Tests Individual."""
    def test_nosex(self) -> None:
        """Tests the no sex case."""
        config = {
            "familyDepth": "4",
            "input": "tests/nosex.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        individual = ged2dot.graph_find(graph, "P3")
        assert individual
        assert isinstance(individual, ged2dot.Individual)
        self.assertIn("placeholder-u", individual.get_label("tests/images"))
        self.assertEqual(individual.get_color(), "black")


class TestGedcomImport(unittest.TestCase):
    """Tests GedcomImport."""
    def test_no_surname(self) -> None:
        """Tests the no surname case."""
        config = {
            "familyDepth": "4",
            "input": "tests/no_surname.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        individual = ged2dot.graph_find(graph, "P1")
        assert individual
        assert isinstance(individual, ged2dot.Individual)
        self.assertEqual(individual.get_surname(), "")
        self.assertEqual(individual.get_forename(), "Alice")

    def test_level3(self) -> None:
        """Tests that we just ignore a 3rd level (only 0..2 is valid)."""
        config = {
            "familyDepth": "0",
            "input": "tests/level3.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        for node in graph:
            node.resolve(graph)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        subgraph = ged2dot.bfs(root_family, config)
        self.assertEqual(len(subgraph), 3)

    def test_unexpected_date(self) -> None:
        """Tests that we just ignore a date which is not birth/death."""
        config = {
            "familyDepth": "0",
            "input": "tests/unexpected_date.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        for node in graph:
            node.resolve(graph)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        subgraph = ged2dot.bfs(root_family, config)
        self.assertEqual(len(subgraph), 3)


class TestMain(unittest.TestCase):
    """Tests main()."""
    def test_happy(self) -> None:
        """Tests the happy path."""
        config = {
            "familyDepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/happy.dot",
            "rootFamily": "F1",
            "imageDir": "tests/images",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))
        with open(config["output"], "r") as stream:
            self.assertIn("images/", stream.read())

    def test_no_images(self) -> None:
        """Tests the happy path."""
        config = {
            "familyDepth": "4",
            "input": "tests/happy.ged",
            "output": "tests/happy.dot",
            "rootFamily": "F1",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))
        with open(config["output"], "r") as stream:
            self.assertNotIn("images/", stream.read())

    def test_bom(self) -> None:
        """Tests handling of an UTF-8 BOM."""
        config = {
            "familyDepth": "4",
            "input": "tests/bom.ged",
            "output": "tests/bom.dot",
            "rootFamily": "F1",
            "imageDir": "tests/images",
        }
        if os.path.exists(config["output"]):
            os.unlink(config["output"])
        self.assertFalse(os.path.exists(config["output"]))
        # Without the accompanying fix in place, this test would have failed with:
        # ValueError: invalid literal for int() with base 10: '\ufeff0'
        ged2dot.convert(config)
        self.assertTrue(os.path.exists(config["output"]))

    def test_family_depth(self) -> None:
        """Tests handling of the familyDepth parameter."""
        config = {
            "familyDepth": "0",
            "input": "tests/happy.ged",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        for node in graph:
            node.resolve(graph)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        subgraph = ged2dot.bfs(root_family, config)
        # Just 3 nodes: wife, husband and the family node.
        self.assertEqual(len(subgraph), 3)

    def test_no_wife(self) -> None:
        """Tests handling of no wife in a family."""
        config = {
            "familyDepth": "0",
            "input": "tests/no_wife.ged",
            "output": "tests/no_wife.dot",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        for node in graph:
            node.resolve(graph)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        neighbours = root_family.get_neighbours()
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
            "familyDepth": "0",
            "input": "tests/no_husband.ged",
            "output": "tests/no_husband.dot",
        }
        importer = ged2dot.GedcomImport()
        graph = importer.load(config)
        for node in graph:
            node.resolve(graph)
        root_family = ged2dot.graph_find(graph, "F1")
        assert root_family
        neighbours = root_family.get_neighbours()
        # Just 1 node: wife.
        self.assertEqual(len(neighbours), 1)
        self.assertEqual(neighbours[0].get_identifier(), "P1")

        # Test export of a no-husband model.
        subgraph = ged2dot.bfs(root_family, config)
        exporter = ged2dot.DotExport()
        exporter.store(subgraph, config)

    def test_default_options(self) -> None:
        """Tests which config options are set by default."""
        def mock_convert(config: Dict[str, str]) -> None:
            self.assertIn("familyDepth", config)
            self.assertIn("input", config)
            self.assertIn("output", config)
            self.assertIn("rootFamily", config)
            self.assertIn("imageDir", config)
        with unittest.mock.patch('ged2dot.convert', mock_convert):
            ged2dot.main()


if __name__ == '__main__':
    unittest.main()
