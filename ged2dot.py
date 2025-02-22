#!/usr/bin/env python3
#
# Copyright Miklos Vajna
#
# SPDX-License-Identifier: MPL-2.0
#

"""A version of ged2dot that uses breadth-first search to traverse the gedcom graph."""

from typing import BinaryIO
from typing import Dict
from typing import List
from typing import Optional
from typing import cast
import argparse
import configparser
import os
import sys


class Ged2DotException(Exception):
    """An exception that is intentionally raised by ged2dot."""


class Config:
    """Stores options from a config file or from cmdline args."""
    def __init__(self) -> None:
        self.input = "-"
        self.output = "-"
        self.rootfamily = "F1"
        # Could be 0, but defaulting to something that can easily explode on large input is not
        # helpful.
        self.familydepth = "3"
        self.imagedir = "images"
        self.nameorder = "little"
        self.direction = "both"
        self.birthformat = "{}-"
        self.relpath = "false"

    def read_config(self, config_file: str) -> None:
        """Reads config from a provided file."""
        if not config_file:
            return
        config_parser = configparser.ConfigParser()
        config_parser.read(config_file)
        for section in config_parser.sections():
            if section != "ged2dot":
                continue
            for option in config_parser.options(section):
                setattr(self, option, config_parser.get(section, option))

    def read_args(self, args: argparse.Namespace) -> None:
        """Reads config from cmdline args."""
        if args.input:
            self.input = args.input
        if args.output:
            self.output = args.output
        if args.rootfamily:
            self.rootfamily = args.rootfamily
        if args.familydepth:
            self.familydepth = args.familydepth
        if args.imagedir:
            self.imagedir = args.imagedir
        if args.nameorder:
            self.nameorder = args.nameorder
        if args.direction:
            self.direction = args.direction
        if args.birthformat:
            self.birthformat = args.birthformat
        if args.relpath:
            self.relpath = "true"

    def get_dict(self) -> Dict[str, str]:
        """Gets the config as a dict."""
        config = {
            "input": self.input,
            "output": self.output,
            "rootfamily": self.rootfamily,
            "familydepth": self.familydepth,
            "imagedir": self.imagedir,
            "nameorder": self.nameorder,
            "direction": self.direction,
            "birthformat": self.birthformat,
            "relpath": self.relpath,
        }
        return config


class Node:
    """Base class for an individual or family."""
    def get_identifier(self) -> str:  # pragma: no cover
        """Gets the ID of this node."""
        return str()

    def set_depth(self, depth: int) -> None:  # pragma: no cover
        """Set the depth of this node, during one graph traversal."""
        # pylint: disable=unused-argument

    def get_depth(self) -> int:  # pragma: no cover
        """Get the depth of this node, during one graph traversal."""
        return 0

    def get_neighbours(self, direction: str) -> List["Node"]:  # pragma: no cover
        """Get the neighbour nodes of this node."""
        return []

    def resolve(self, graph: List["Node"]) -> None:  # pragma: no cover
        """Resolve string IDs to node objects."""
        # pylint: disable=unused-argument


def graph_find(graph: List[Node], identifier: str) -> Optional[Node]:
    """Find identifier in graph."""
    if not identifier:
        return None

    results = [node for node in graph if node.get_identifier() == identifier]
    if not results:
        return None

    assert len(results) == 1
    return results[0]


def get_abspath(path: str) -> str:
    """Make a path absolute, taking the repo root as a base dir."""
    if os.path.isabs(path):
        return path

    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def get_data_abspath(gedcom: str, path: str) -> str:
    """Make a path absolute, taking the gedcom file's dir as a base dir."""
    if os.path.isabs(path):
        return path

    return os.path.join(os.path.dirname(os.path.realpath(gedcom)), path)


def to_bytes(string: str) -> bytes:
    """Encodes the string to UTF-8."""
    return string.encode("utf-8")


class IndividualConfig:
    """Key-value pairs on an individual."""
    def __init__(self) -> None:
        self.__note = ""
        self.__birth = ""
        self.__death = ""

    def set_note(self, note: str) -> None:
        """Sets a note."""
        self.__note = note

    def get_note(self) -> str:
        """Gets a note."""
        return self.__note

    def set_birth(self, birth: str) -> None:
        """Sets the birth date."""
        self.__birth = birth

    def get_birth(self) -> str:
        """Gets the birth date."""
        return self.__birth

    def set_death(self, death: str) -> None:
        """Sets the death date."""
        self.__death = death

    def get_death(self) -> str:
        """Gets the death date."""
        return self.__death


class Individual(Node):
    """An individual is always a child in a family, and is an adult in 0..* families."""
    def __init__(self) -> None:
        self.__dict: Dict[str, str] = {}
        self.__dict["identifier"] = ""
        self.__dict["famc_id"] = ""
        self.famc: Optional[Family] = None
        self.fams_ids: List[str] = []
        self.fams_list: List["Family"] = []
        self.depth = 0
        self.__dict["forename"] = ""
        self.__dict["surname"] = ""
        self.__dict["sex"] = ""
        self.__config = IndividualConfig()

    def __str__(self) -> str:
        # Intentionally only print the famc/fams IDs, not the whole object to avoid not wanted
        # recursion.
        ret = "Individual(__dict=" + str(self.__dict)
        ret += ", fams_ids: " + str(self.fams_ids)
        ret += ", depth: " + str(self.depth) + ")"
        return ret

    def resolve(self, graph: List[Node]) -> None:
        self.famc = cast(Optional["Family"], graph_find(graph, self.get_famc_id()))
        for fams_id in self.fams_ids:
            fams = graph_find(graph, fams_id)
            assert fams
            self.fams_list.append(cast("Family", fams))

    def get_neighbours(self, direction: str) -> List[Node]:
        ret: List[Node] = []
        if self.famc and direction != "child":
            ret.append(self.famc)
        ret += self.fams_list
        return ret

    def get_config(self) -> IndividualConfig:
        """Returns key-value pairs of individual."""
        return self.__config

    def set_identifier(self, identifier: str) -> None:
        """Sets the ID of this individual."""
        self.__dict["identifier"] = identifier

    def get_identifier(self) -> str:
        return self.__dict["identifier"]

    def set_sex(self, sex: str) -> None:
        """Sets the sex of this individual."""
        self.__dict["sex"] = sex

    def get_sex(self) -> str:
        """Gets the sex of this individual."""
        return self.__dict["sex"]

    def set_forename(self, forename: str) -> None:
        """Sets the first name of this individual."""
        self.__dict["forename"] = forename

    def get_forename(self) -> str:
        """Gets the first name of this individual."""
        return self.__dict["forename"]

    def set_surname(self, surname: str) -> None:
        """Sets the family name of this individual."""
        self.__dict["surname"] = surname

    def get_surname(self) -> str:
        """Gets the family name of this individual."""
        return self.__dict["surname"]

    def set_depth(self, depth: int) -> None:
        self.depth = depth

    def get_depth(self) -> int:
        return self.depth

    def set_famc_id(self, famc_id: str) -> None:
        """Sets the child family ID."""
        self.__dict["famc_id"] = famc_id

    def get_famc_id(self) -> str:
        """Gets the child family ID."""
        return self.__dict["famc_id"]

    def get_label(self, image_dir: str, name_order: str, birth_format: str, basepath: str) -> str:
        """Gets the graphviz label."""
        image_path = os.path.join(image_dir, self.get_forename() + " " + self.get_surname())
        for suffix in [".jpg", ".jpeg", ".png", ".JPG", ".PNG"]:
            image_path += " " + self.get_config().get_birth() + suffix
            if not os.path.exists(to_bytes(image_path)):
                image_path = os.path.join(image_dir, self.get_forename() + " " + self.get_surname()) \
                    + ".jpg"
            if os.path.exists(to_bytes(image_path)):
                break
        if not os.path.exists(to_bytes(image_path)):
            if self.get_sex():
                sex = self.get_sex().lower()
            else:
                sex = 'u'
            image_path = get_abspath(f"placeholder-{sex}.svg")
        if basepath:
            image_path = os.path.relpath(image_path, basepath)
        label = "<table border=\"0\" cellborder=\"0\"><tr><td>"
        label += "<img scale=\"true\" src=\"" + image_path + "\"/>"
        # State the font face explicitly to help correct centering.
        label += "</td></tr><tr><td><font face=\"Times\">"
        if name_order == "big":
            # Big endian: family name first.
            label += self.get_surname() + "<br/>"
            label += self.get_forename() + "<br/>"
        else:
            # Little endian: given name first.
            label += self.get_forename() + "<br/>"
            label += self.get_surname() + "<br/>"
        if self.get_config().get_birth() and not self.get_config().get_death():
            label += birth_format.format(self.get_config().get_birth())
        elif not self.get_config().get_birth() and self.get_config().get_death():
            label += "† " + self.get_config().get_death()
        else:
            label += self.get_config().get_birth() + "-" + self.get_config().get_death()
        label += "</font></td></tr></table>"
        return label

    def get_color(self) -> str:
        """Gets the color around the node."""
        if not self.get_sex():
            sex = 'U'
        else:
            sex = self.get_sex().upper()
        color = {'M': 'blue', 'F': 'pink', 'U': 'black'}[sex]
        return color


class Family(Node):
    """Family has exactly one wife and husband, 0..* children."""
    def __init__(self) -> None:
        self.__dict: Dict[str, str] = {}
        self.__dict["identifier"] = ""
        self.__dict["marr"] = ""
        self.__dict["wife_id"] = ""
        self.wife: Optional["Individual"] = None
        self.__dict["husb_id"] = ""
        self.husb: Optional["Individual"] = None
        self.child_ids: List[str] = []
        self.child_list: List["Individual"] = []
        self.depth = 0

    def __str__(self) -> str:
        # Intentionally only print the wife/husband/child IDs, not the whole object to avoid not
        # wanted recursion.
        ret = "Family(__dict=" + str(self.__dict)
        ret += ", child_ids: " + str(self.child_ids)
        ret += ", depth: " + str(self.depth) + ")"
        return ret

    def resolve(self, graph: List[Node]) -> None:
        self.wife = cast(Optional["Individual"], graph_find(graph, self.get_wife_id()))
        self.husb = cast(Optional["Individual"], graph_find(graph, self.get_husb_id()))
        for child_id in self.child_ids:
            child = graph_find(graph, child_id)
            assert child
            self.child_list.append(cast("Individual", child))

    def get_neighbours(self, direction: str) -> List[Node]:
        ret: List[Node] = []
        if self.wife:
            ret.append(self.wife)
        if self.husb:
            ret.append(self.husb)
        ret += self.child_list
        return ret

    def set_identifier(self, identifier: str) -> None:
        """Sets the ID of this family."""
        self.__dict["identifier"] = identifier

    def get_identifier(self) -> str:
        return self.__dict["identifier"]

    def set_marr(self, marr: str) -> None:
        """Sets the marriage date."""
        self.__dict["marr"] = marr

    def get_marr(self) -> str:
        """Gets the marriage date."""
        return self.__dict["marr"]

    def set_depth(self, depth: int) -> None:
        self.depth = depth

    def get_depth(self) -> int:
        return self.depth

    def set_wife_id(self, wife_id: str) -> None:
        """Sets the wife ID of this family."""
        self.__dict["wife_id"] = wife_id

    def get_wife_id(self) -> str:
        """Gets the wife ID of this family."""
        return self.__dict["wife_id"]

    def set_husb_id(self, husb_id: str) -> None:
        """Sets the husband ID of this family."""
        self.__dict["husb_id"] = husb_id

    def get_husb_id(self) -> str:
        """Gets the husband ID of this family."""
        return self.__dict["husb_id"]


class GedcomImport:
    """Builds the graph from GEDCOM."""
    def __init__(self) -> None:
        self.individual: Optional[Individual] = None
        self.family: Optional[Family] = None
        self.graph: List[Node] = []
        self.in_birt = False
        self.in_deat = False
        self.in_marr = False

    def __reset_flags(self) -> None:
        if self.in_birt:
            self.in_birt = False
        elif self.in_deat:
            self.in_deat = False
        elif self.in_marr:
            self.in_marr = False

    def __handle_level0(self, line: str) -> None:
        if self.individual:
            self.graph.append(self.individual)
            self.individual = None
        if self.family:
            self.graph.append(self.family)
            self.family = None

        if line.startswith("@") and line.endswith("INDI"):
            self.individual = Individual()
            self.individual.set_identifier(line[1:-6])
        elif line.startswith("@") and line.endswith("FAM"):
            self.family = Family()
            self.family.set_identifier(line[1:-5])

    def __handle_indi_name(self, line: str) -> None:
        # Expected style: 'first /last/ suffix', suffix is optional.
        tokens = line.split('/')
        assert self.individual
        self.individual.set_forename(tokens[0].strip())
        if len(tokens) > 1:
            self.individual.set_surname(tokens[1].strip())
        if len(tokens) > 2 and tokens[2]:
            # We have suffix, append that to the surname.
            surname = self.individual.get_surname()
            suffix = tokens[2].strip()
            self.individual.set_surname(f"{surname} {suffix}")

    def __handle_level1(self, line: str) -> None:
        self.__reset_flags()

        line_lead_token = line.split(' ')[0]

        if line_lead_token == "SEX" and self.individual:
            tokens = line.split(' ')
            if len(tokens) > 1:
                self.individual.set_sex(tokens[1])
        elif line_lead_token == "NAME" and self.individual:
            line = line[5:]
            self.__handle_indi_name(line)
        elif line_lead_token == "FAMC" and self.individual:
            # At least <https://www.ancestry.com> sometimes writes multiple FAMC, which doesn't
            # make sense. Import only the first one.
            if not self.individual.get_famc_id():
                self.individual.set_famc_id(line[6:-1])
        elif line_lead_token == "FAMS" and self.individual:
            self.individual.fams_ids.append(line[6:-1])
        elif line_lead_token == "HUSB" and self.family:
            self.family.set_husb_id(line[6:-1])
        elif line_lead_token == "WIFE" and self.family:
            self.family.set_wife_id(line[6:-1])
        elif line_lead_token == "CHIL" and self.family:
            self.family.child_ids.append(line[6:-1])
        elif line_lead_token == "MARR" and self.family:
            self.in_marr = True
        else:
            self.__handle_individual_config(line)

    def __handle_individual_config(self, line: str) -> None:
        """Handles fields stored in individual.get_config()."""
        line_lead_token = line.split(' ')[0]

        if line_lead_token == "BIRT":
            self.in_birt = True
        elif line_lead_token == "DEAT":
            self.in_deat = True
        elif line_lead_token == "NOTE" and self.individual:
            self.individual.get_config().set_note(line[5:])

    def load(self, config: Dict[str, str]) -> List[Node]:
        """Tokenizes and resolves a gedcom file into a graph."""
        graph = self.tokenize(config)
        for node in graph:
            node.resolve(graph)
        return graph

    def tokenize(self, config: Dict[str, str]) -> List[Node]:
        """Tokenizes a gedcom file into a graph."""
        if config["input"] == "-":
            return self.tokenize_from_stream(sys.stdin.buffer)
        with open(config["input"], "rb") as stream:
            return self.tokenize_from_stream(stream)

    def tokenize_from_stream(self, stream: BinaryIO) -> List[Node]:
        """Tokenizes a gedcom stream into a graph."""
        stream_buf = stream.read()
        lines = stream_buf.split(b"\r\n")
        if b"\r" not in stream_buf:
            lines = stream_buf.split(b"\n")
        for line_bytes in lines:
            line = safe_utf8_decode(line_bytes.strip())
            if not line:
                continue
            tokens = line.split(" ")

            first_token = tokens[0]
            # Ignore UTF-8 BOM, if there is one at the beginning of the line.
            if first_token.startswith("\ufeff"):
                first_token = first_token[1:]

            level = safe_atoi(first_token)
            rest = " ".join(tokens[1:])
            if level == 0:
                self.__handle_level0(rest)
            elif level == 1:
                self.__handle_level1(rest)
            elif level == 2:
                if rest.startswith("DATE"):
                    year = rest.rsplit(' ', maxsplit=1)[-1]
                    if self.individual:
                        if self.in_birt:
                            self.individual.get_config().set_birth(year)
                        elif self.in_deat:
                            self.individual.get_config().set_death(year)
                    elif self.family and self.in_marr:
                        self.family.set_marr(year)
        return self.graph


def bfs(root: Node, config: Dict[str, str]) -> List[Node]:
    """
    Does a breadth first search traversal of the graph, from root. Returns the traversed nodes.
    """
    visited = [root]
    queue = [root]
    ret: List[Node] = []

    direction = config.get("direction", "both")
    while queue:
        node = queue.pop(0)
        # Every 2nd node is a family + the root is always a family.
        family_depth = int(config["familydepth"])
        if node.get_depth() > family_depth * 2 + 1:
            return ret
        ret.append(node)
        for neighbour in node.get_neighbours(direction):
            if neighbour not in visited:
                neighbour.set_depth(node.get_depth() + 1)
                visited.append(neighbour)
                queue.append(neighbour)

    return ret


def safe_atoi(string: str) -> int:
    """Converts str to an int, raising an own exception on error."""
    try:
        return int(string)
    except ValueError as exc:
        raise Ged2DotException() from exc


def safe_utf8_decode(source: bytes) -> str:
    """Decodes bytes to a string, raising an own exception on error."""
    try:
        return source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Ged2DotException() from exc


class DotExport:
    """Serializes the graph to Graphviz / dot."""
    def __init__(self) -> None:
        self.subgraph: List[Node] = []
        self.config: Dict[str, str] = {}

    def __store_individual_nodes(self, stream: BinaryIO) -> None:
        for node in self.subgraph:
            if not isinstance(node, Individual):
                continue
            individual = node
            stream.write(to_bytes(node.get_identifier() + " [shape=box, "))
            image_dir = self.config.get("imagedir", "")
            image_dir_abs = get_data_abspath(self.config.get("input", ""), image_dir)
            name_order = self.config.get("nameorder", "little")
            birth_format = self.config.get("birthformat", "{}-")
            basepath = ""
            if self.config.get("relpath", "false") == "true" and self.config["output"] != "-":
                basepath = os.path.dirname(os.path.abspath(self.config["output"]))
            label = individual.get_label(image_dir_abs, name_order, birth_format, basepath)
            stream.write(to_bytes("label = <" + label + ">\n"))
            stream.write(to_bytes("color = " + individual.get_color() + "];\n"))

    def __store_family_nodes(self, stream: BinaryIO) -> None:
        stream.write(to_bytes("\n"))
        for node in self.subgraph:
            if not isinstance(node, Family):
                continue
            image_path = get_abspath("marriage.svg")
            if self.config.get("relpath", "false") == "true" and self.config["output"] != "-":
                basepath = os.path.dirname(os.path.abspath(self.config["output"]))
                image_path = os.path.relpath(image_path, basepath)

            # Emit explicit size from marriage.svg, otherwise it won't be centered in the PNG
            # output.
            table_start = "<table border=\"0\" cellborder=\"0\" width=\"32px\" height=\"23px\">"

            label = table_start + "<tr><td><img src=\"" + image_path + "\"/></td></tr></table>"
            if node.get_marr():
                label = node.get_marr()
            # Make sure family -> children edges appear left-to-right in the same order in which
            # they are defined in the input.
            attrs = "shape=circle, margin=\"0,0\", label=<" + label + ">, ordering=out"
            stream.write(to_bytes(node.get_identifier() + " [" + attrs + "];\n"))
        stream.write(to_bytes("\n"))

    def __store_edges(self, stream: BinaryIO) -> None:
        for node in self.subgraph:
            if not isinstance(node, Family):
                continue
            family = node

            # Open subgraph of the family.
            cname = "cluster_" + family.get_identifier()
            stream.write(to_bytes("subgraph " + cname + " { style=invis; \n"))

            if family.wife:
                from_wife = family.wife.get_identifier() + " -> " + family.get_identifier() + " [dir=none];\n"
                stream.write(to_bytes(from_wife))
            if family.husb:
                from_husb = family.husb.get_identifier() + " -> " + family.get_identifier() + " [dir=none];\n"
                stream.write(to_bytes(from_husb))

            # Close subgraph of the family.
            stream.write(to_bytes("}\n"))

            for child in family.child_list:
                stream.write(to_bytes(family.get_identifier() + " -> " + child.get_identifier() + " [dir=none];\n"))

    def store(self, subgraph: List[Node], config: Dict[str, str]) -> None:
        """Exports subgraph to a graphviz path."""
        if config["output"] == "-":
            self.store_to_stream(subgraph, sys.stdout.buffer, config)
            return
        with open(config["output"], "wb") as stream:
            self.store_to_stream(subgraph, stream, config)

    def store_to_stream(self, subgraph: List[Node], stream: BinaryIO, config: Dict[str, str]) -> None:
        """Exports subgraph to a graphviz stream."""
        stream.write(to_bytes("// Generated by <https://github.com/vmiklos/ged2dot>.\n"))
        stream.write(to_bytes("digraph\n"))
        stream.write(to_bytes("{\n"))
        stream.write(to_bytes("splines = ortho;\n"))
        stream.write(to_bytes("\n"))

        self.subgraph = subgraph
        self.config = config
        self.__store_individual_nodes(stream)
        self.__store_family_nodes(stream)
        self.__store_edges(stream)

        stream.write(to_bytes("}\n"))


def convert(config: Dict[str, str]) -> None:
    """API interface."""
    importer = GedcomImport()
    graph = importer.load(config)
    root_family = graph_find(graph, config["rootfamily"])
    if not root_family:
        family_id = ""
        for node in graph:
            if not isinstance(node, Family):
                continue
            family_id = node.get_identifier()
            break
        reason = f"Root family '{config['rootfamily']}' is not found."
        if family_id:
            reason += f" First valid family would be '{family_id}'."
        raise Ged2DotException(reason)
    subgraph = bfs(root_family, config)
    exporter = DotExport()
    exporter.store(subgraph, config)


def main() -> None:
    """Commandline interface."""

    # Parse config from file and cmdline args.
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str,
                        help="configuration file")
    parser.add_argument("--input", type=str,
                        help="input GEDCOM file")
    parser.add_argument("--output", type=str,
                        help="output DOT file")
    parser.add_argument("--rootfamily", type=str,
                        help="root family")
    parser.add_argument("--familydepth", type=str,
                        help="family depth")
    parser.add_argument("--imagedir", type=str,
                        help="image directory")
    parser.add_argument("--nameorder", choices=["little", "big"],
                        help="name order")
    parser.add_argument("--direction", choices=["both", "child"],
                        help="name order")
    parser.add_argument("--birthformat", type=str,
                        help="birth format when death is missing (default: '{}-', e.g. '1942-')")
    parser.add_argument("--relpath", dest="relpath", action="store_true",
                        help="try to use relative paths (default: false)")
    args = parser.parse_args()
    config = Config()
    config.read_config(args.config)
    config.read_args(args)
    convert(config.get_dict())


if __name__ == '__main__':
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
