#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""A version of ged2dot that uses breadth-first search to traverse the gedcom graph."""

import os
from typing import cast
from typing import Dict
from typing import List
from typing import Optional


class Node:
    """Base class for an individual or family."""
    def get_identifier(self) -> str:
        """Gets the ID of this node."""
        # pylint: disable=no-self-use
        ...

    def set_depth(self, depth: int) -> None:
        """Set the depth of this node, during one graph traversal."""
        # pylint: disable=no-self-use
        # pylint: disable=unused-argument
        ...

    def get_depth(self) -> int:
        """Get the depth of this node, during one graph traversal."""
        # pylint: disable=no-self-use
        ...

    def get_neighbours(self) -> List["Node"]:
        """Get the neighbour nodes of this node."""
        # pylint: disable=no-self-use
        ...

    def resolve(self, graph: List["Node"]) -> None:
        """Resolve string IDs to node objects."""
        # pylint: disable=no-self-use
        # pylint: disable=unused-argument
        ...


def graph_find(graph: List[Node], identifier: str) -> Optional[Node]:
    """Find identifier in graph."""
    if not identifier:
        return None

    results = [node for node in graph if node.get_identifier() == identifier]
    assert len(results) == 1
    return results[0]


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
        self.__dict["birth"] = ""
        self.__dict["death"] = ""

    def resolve(self, graph: List[Node]) -> None:
        self.famc = cast(Optional["Family"], graph_find(graph, self.get_famc_id()))
        for fams_id in self.fams_ids:
            fams = graph_find(graph, fams_id)
            assert fams
            self.fams_list.append(cast("Family", fams))

    def get_neighbours(self) -> List[Node]:
        ret: List[Node] = []
        if self.famc:
            ret.append(self.famc)
        ret += self.fams_list
        return ret

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

    def set_birth(self, birth: str) -> None:
        """Sets the birth date."""
        self.__dict["birth"] = birth

    def get_birth(self) -> str:
        """Gets the birth date."""
        return self.__dict["birth"]

    def set_death(self, death: str) -> None:
        """Sets the death date."""
        self.__dict["death"] = death

    def get_death(self) -> str:
        """Gets the death date."""
        return self.__dict["death"]


class Family(Node):
    """Family has exactly one wife and husband, 0..* children."""
    def __init__(self) -> None:
        self.identifier = ""
        self.wife_id = ""
        self.wife: Optional["Individual"] = None
        self.husb_id = ""
        self.husb: Optional["Individual"] = None
        self.child_ids: List[str] = []
        self.child_list: List["Individual"] = []
        self.depth = 0

    def resolve(self, graph: List[Node]) -> None:
        self.wife = cast(Optional["Individual"], graph_find(graph, self.wife_id))
        self.husb = cast(Optional["Individual"], graph_find(graph, self.husb_id))
        for child_id in self.child_ids:
            child = graph_find(graph, child_id)
            assert child
            self.child_list.append(cast("Individual", child))

    def get_neighbours(self) -> List[Node]:
        ret: List[Node] = []
        if self.wife:
            ret.append(self.wife)
        if self.husb:
            ret.append(self.husb)
        ret += self.child_list
        return ret

    def get_identifier(self) -> str:
        return self.identifier

    def set_depth(self, depth: int) -> None:
        self.depth = depth

    def get_depth(self) -> int:
        return self.depth


def import_gedcom() -> List[Node]:
    """Imports a gedcom file into a graph."""
    stream = open("test.ged", "rb")
    individual = None
    family = None
    graph: List[Node] = []
    in_birt = False
    in_deat = False
    for line_bytes in stream.readlines():
        line = line_bytes.strip().decode("UTF-8")
        tokens = line.split(" ")

        first_token = tokens[0]
        # Ignore UTF-8 BOM, if there is one at the begining of the line.
        if first_token.startswith("\ufeff"):
            first_token = first_token[1:]

        level = int(first_token)
        rest = " ".join(tokens[1:])
        if level == 0:
            if individual:
                graph.append(individual)
                individual = None
            if family:
                graph.append(family)
                family = None

            if rest.startswith("@") and rest.endswith("INDI"):
                individual = Individual()
                individual.set_identifier(rest[1:-6])
            elif rest.startswith("@") and rest.endswith("FAM"):
                family = Family()
                family.identifier = rest[1:-5]
        elif level == 1:
            if in_birt:
                in_birt = False
            elif in_deat:
                in_deat = False

            if rest.startswith("SEX") and individual:
                individual.set_sex(rest.split(' ')[1])
            elif rest.startswith("NAME") and individual:
                rest = rest[5:]
                tokens = rest.split('/')
                individual.set_forename(tokens[0].strip())
                if len(tokens) > 1:
                    individual.set_surname(tokens[1].strip())
            elif rest.startswith("FAMC") and individual:
                # At least <https://www.ancestry.com> sometimes writes multiple FAMC, which doesn't
                # make sense. Import only the first one.
                if not individual.get_famc_id():
                    individual.set_famc_id(rest[6:-1])
            elif rest.startswith("FAMS") and individual:
                individual.fams_ids.append(rest[6:-1])
            elif rest.startswith("BIRT"):
                in_birt = True
            elif rest.startswith("DEAT"):
                in_deat = True
            elif rest.startswith("HUSB") and family:
                family.husb_id = rest[6:-1]
            elif rest.startswith("WIFE") and family:
                family.wife_id = rest[6:-1]
            elif rest.startswith("CHIL") and family:
                family.child_ids.append(rest[6:-1])
        elif level == 2:
            if rest.startswith("DATE") and individual:
                year = rest.split(' ')[-1]
                if in_birt:
                    individual.set_birth(year)
                elif in_deat:
                    individual.set_death(year)
    return graph


def bfs(root: Node) -> List[Node]:
    """
    Does a breadth first search traversal of the graph, from root. Returns the traversed nodes.
    """
    visited = [root]
    queue = [root]
    ret: List[Node] = []

    while queue:
        node = queue.pop(0)
        if node.get_depth() > 9:
            return ret
        ret.append(node)
        for neighbour in node.get_neighbours():
            if neighbour not in visited:
                neighbour.set_depth(node.get_depth() + 1)
                visited.append(neighbour)
                queue.append(neighbour)

    return ret


def export_dot(subgraph: List[Node]) -> None:
    """Exports subgraph to graphviz."""
    with open("test.dot", "w") as stream:
        stream.write("// Generated by <https://github.com/vmiklos/ged2dot/tree/master/core>.\n")
        stream.write("digraph\n")
        stream.write("{\n")
        stream.write("splines = ortho;\n")
        stream.write("\n")

        for node in subgraph:
            if not node.get_identifier().startswith("P"):
                continue
            individual = cast(Individual, node)
            stream.write(node.get_identifier() + " [shape=box, ")

            image_path = "images/" + individual.get_forename() + " " + individual.get_surname()
            image_path += " " + individual.get_birth() + ".jpg"
            if not os.path.exists(image_path):
                if individual.get_sex():
                    sex = individual.get_sex().lower()
                else:
                    sex = 'u'
                image_path = os.path.join("..", "placeholder-%s.png" % sex)
            label = "<table border=\"0\" cellborder=\"0\"><tr><td>"
            label += "<img src=\"" + image_path + "\"/>"
            label += "</td></tr><tr><td>"
            label += individual.get_surname() + "<br/>"
            label += individual.get_forename() + "<br/>"
            label += individual.get_birth() + "-" + individual.get_death()
            label += "</td></tr></table>"
            stream.write("label = <" + label + ">\n")

            if not individual.get_sex():
                sex = 'U'
            else:
                sex = individual.get_sex().upper()
            color = {'M': 'blue', 'F': 'pink', 'U': 'black'}[sex]

            stream.write("color = " + color + "];\n")
        stream.write("\n")

        for node in subgraph:
            if not node.get_identifier().startswith("F"):
                continue
            stream.write(node.get_identifier() + " [shape=point, width=0.1];\n")
        stream.write("\n")

        for node in subgraph:
            if not node.get_identifier().startswith("F"):
                continue
            family = cast(Family, node)
            if family.wife:
                stream.write(family.wife.get_identifier() + " -> " + family.get_identifier() + " [dir=none];\n")
            if family.husb:
                stream.write(family.husb.get_identifier() + " -> " + family.get_identifier() + " [dir=none];\n")
            for child in family.child_list:
                stream.write(family.get_identifier() + " -> " + child.get_identifier() + " [dir=none];\n")

        stream.write("}\n")


def main() -> None:
    """Commandline interface."""
    graph = import_gedcom()
    for node in graph:
        node.resolve(graph)
    root_family = graph_find(graph, "F24")
    assert root_family
    subgraph = bfs(root_family)
    export_dot(subgraph)


if __name__ == '__main__':
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
