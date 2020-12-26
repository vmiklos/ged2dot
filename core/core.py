#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

"""A version of ged2dot that uses breadth-first search to traverse the gedcom graph."""

import os
from typing import cast
from typing import List
from typing import Optional


class Node:
    def get_identifier(self) -> str:
        ...

    def get_depth(self) -> int:
        ...


def graph_find(graph: List[Node], identifier: str) -> Optional[Node]:
    if not identifier:
        return None

    results = [node for node in graph if node.get_identifier() == identifier]
    assert len(results) == 1
    return results[0]


class Individual(Node):
    """An individual is always a child in a family, and is an adult in 0..* families."""
    def __init__(self) -> None:
        self.identifier = ""
        self.famc_id = ""
        self.famc: Optional[Family] = None
        self.fams_ids: List[str] = []
        self.fams_list: List["Family"] = []
        self.depth = 0
        self.forename = ""
        self.surname = ""
        self.sex = ""
        self.birth = ""
        self.death = ""

    def resolve(self, graph: List[Node]) -> None:
        self.famc = cast(Optional["Family"], graph_find(graph, self.famc_id))
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

    def get_identifier(self) -> str:
        return self.identifier

    def get_depth(self) -> int:
        return self.depth


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

    def get_depth(self) -> int:
        return self.depth


def import_gedcom() -> List[Node]:
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
                individual.identifier = rest[1:-6]
            elif rest.startswith("@") and rest.endswith("FAM"):
                family = Family()
                family.identifier = rest[1:-5]
        elif level == 1:
            if in_birt:
                in_birt = False
            elif in_deat:
                in_deat = False

            if rest.startswith("SEX") and individual:
                individual.sex = rest.split(' ')[1]
            elif rest.startswith("NAME") and individual:
                rest = rest[5:]
                tokens = rest.split('/')
                individual.forename = tokens[0].strip()
                if len(tokens) > 1:
                    individual.surname = tokens[1].strip()
            elif rest.startswith("FAMC") and individual:
                # At least <https://www.ancestry.com> sometimes writes multiple FAMC, which doesn't
                # make sense. Import only the first one.
                if not individual.famc_id:
                    individual.famc_id = rest[6:-1]
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
                    individual.birth = year
                elif in_deat:
                    individual.death = year
    return graph


def bfs(graph: List[Node], root: Node) -> List[Node]:
    visited = [root]
    queue = [root]
    ret: List[Node] = []

    while queue:
        node = queue.pop(0)
        if node.depth > 9:
            return ret
        ret.append(node)
        for neighbour in node.get_neighbours():
            if neighbour not in visited:
                neighbour.depth = node.depth + 1
                visited.append(neighbour)
                queue.append(neighbour)

    return ret


def export_dot(subgraph):
    with open("test.dot", "w") as stream:
        stream.write("digraph\n")
        stream.write("{\n")
        stream.write("splines = ortho;\n")
        stream.write("\n")

        for node in subgraph:
            if not node.identifier.startswith("P"):
                continue
            stream.write(node.identifier + " [shape=box, ")

            image_path = "images/" + node.forename + " " + node.surname + " " + node.birth + ".jpg"
            if not os.path.exists(image_path):
                if node.sex:
                    sex = node.sex.lower()
                else:
                    sex = 'u'
                image_path = os.path.join("..", "placeholder-%s.png" % sex)
            stream.write("label = <<table border=\"0\" cellborder=\"0\"><tr><td><img src=\"" + image_path + "\"/></td></tr><tr><td>" + node.surname + "<br/>" + node.forename + "<br/>" + node.birth + "-" + node.death + "</td></tr></table>>\n")

            if node.sex is None:
                sex = 'U'
            else:
                sex = node.sex.upper()
            color = {'M': 'blue', 'F': 'pink', 'U': 'black'}[sex]

            stream.write("color = " + color + "];\n")
        stream.write("\n")

        for node in subgraph:
            if not node.identifier.startswith("F"):
                continue
            stream.write(node.identifier + " [shape=point, width=0.1];\n")
        stream.write("\n")

        for node in subgraph:
            if not node.identifier.startswith("F"):
                continue
            if node.wife:
                stream.write(node.wife.identifier + " -> " + node.identifier + " [dir=none];\n")
            if node.husb:
                stream.write(node.husb.identifier + " -> " + node.identifier + " [dir=none];\n")
            for child in node.child_list:
                stream.write(node.identifier + " -> " + child.identifier + " [dir=none];\n")

        stream.write("}\n")


def main() -> None:
    """Commandline interface."""
    graph = import_gedcom()
    for node in graph:
        node.resolve(graph)
    subgraph = bfs(graph, graph_find(graph, "F24"))
    export_dot(subgraph)


if __name__ == '__main__':
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
