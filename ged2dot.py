#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import time
import os
import sys
import configparser
import codecs
from functools import cmp_to_key
from typing import Any
from typing import BinaryIO
from typing import Dict
from typing import List
from typing import Optional
from typing import TextIO
from typing import Tuple
from typing import cast


# Protocols

class Renderable:
    # pylint: disable=no-self-use
    def render(self, _out: TextIO) -> None:
        ...


# Exceptions

class NoSuchFamilyException(Exception):
    pass


class NoSuchIndividualException(Exception):
    pass


# Model

class Individual:
    placeholderDir = os.path.dirname(os.path.realpath(__file__))
    """An individual is our basic building block, can be part of multiple families (usually two)."""
    def __init__(self, model: 'Model') -> None:
        self.model = model
        self.id = ""
        self.sex = None  # type: Optional[str]
        self.forename = ""  # John
        self.surname = ""  # Smith
        self.famc = None  # type: Any  # str or Family
        self.fams = None  # type: Any  # str or Family
        self.birt = ""
        self.deat = ""
        # Horizontal order is ensured by order deps. Any order dep starting from this node?
        # Set to true on first addition, so that we can avoid redundant deps.

    def __str__(self) -> str:
        return "id: %s, sex: %s, forename: %s, surname: %s: famc: %s, fams: %s, birt: %s, deat: %s" % (self.id, self.sex, self.forename, self.surname, self.famc, self.fams, self.birt, self.deat)

    def resolve(self) -> None:
        """Replaces family reference strings with references to objects."""
        self.famc = self.model.get_family(self.famc)
        self.fams = self.model.get_family(self.fams)

    def getFullName(self) -> str:
        """Full name of the individual. Only used as comments in the output
        file to ease debugging."""
        return "%s %s" % (self.forename, self.surname)

    def getLabel(self) -> str:
        if self.forename:
            forename = self.forename
        else:
            forename = ""
        if self.surname:
            surname = self.surname
        else:
            surname = ""

        if self.model.config.imageFormatCase.lower() == 'lower':
            forename = forename.lower()
            surname = surname.lower()
        elif self.model.config.imageFormatCase.lower() == 'upper':
            forename = forename.upper()
            surname = surname.upper()

        path = self.model.config.imageFormat % {
            'forename': forename,
            'surname': surname,
            'gwIndex': self.model.getIndividualGeneWebIndex(self.id, self.forename, self.surname),
            'birt': self.birt
        }

        if self.model.config.imageFormatGeneweb:
            import unicodedata
            path = unicodedata.normalize('NFKD', path).encode('ascii', 'ignore').decode('ascii')
            path = path.translate(dict({ord("-"): "_"}))

        try:
            fullpath = os.path.join(self.model.basedir, path)
        except (UnicodeDecodeError) as ude:
            sys.stderr.write("Wrong encoding? %s\n" % str(ude))
            fullpath = ""
        if os.path.exists(fullpath) and not self.model.config.anonMode:
            picture = fullpath
        else:
            if self.sex:
                sex = self.sex.lower()
            else:
                sex = 'u'
            picture = os.path.join(Individual.placeholderDir, "placeholder-%s.png" % sex)

        try:
            from PIL import Image  # type: ignore  # No library stub file for module
            i = Image.open(picture)
            if i.size != (100, 100):
                picture = "%s.tumbnail.png" % picture
                if not os.path.exists(picture):
                    sys.stderr.write("// Scaling picture of %s as it didn't have 100x100 px\n" % self.getFullName())
                    i.thumbnail((100, 100), Image.ANTIALIAS)
                    i.save(picture, "PNG")
            i.close()
        except ImportError:
            pass

        format_string = ""
        if self.model.config.images:
            format_string = self.model.config.nodeLabelImage
        else:
            format_string = self.model.config.nodeLabelPlain
        if self.model.config.anonMode:
            birt = self.birt
            if len(birt) > 1:
                birt = "YYYY"
            deat = self.deat
            if len(deat) > 1:
                deat = "YYYY"
            return format_string % {
                'picture': picture,
                'surname': self.id[0],
                'forename': self.id[1:],
                'birt': birt,
                'deat': deat
            }
        return format_string % {
            'picture': picture,
            'surname': surname,
            'forename': forename,
            'birt': self.birt,
            'deat': self.deat
        }

    def getColor(self) -> str:
        if self.sex is None:
            sex = 'U'
        else:
            sex = self.sex.upper()
        return {'M': 'blue', 'F': 'pink', 'U': 'black'}[sex]

    def get_node(self) -> 'Node':
        return Node(self.id, '[ shape = box,\nlabel = %s,\ncolor = %s,\npenwidth=%s ]' % (self.getLabel(), self.getColor(), self.model.config.nodeBorderWidth))

    def setBirt(self, birt: str) -> None:
        if not birt:
            return
        self.birt = birt
        try:
            if time.localtime().tm_year - int(birt) > self.model.config.considerAgeDead:
                if not self.deat:
                    self.deat = "?"
        except ValueError:
            pass


class Family:
    """Family has exactly one wife and husb, 0..* children."""
    phCount = 0

    def __init__(self, model: 'Model') -> None:
        self.model = model
        self.id = None  # type: Optional[str]
        self.husb = None  # type: Any  # str or Individual
        self.wife = None  # type: Any  # str or Individual
        self.chil = []  # type: List[str]
        self.depth = 0

    def __str__(self) -> str:
        return "id: %s, husb: %s, wife: %s, chil: %s, depth: %s" % (self.id, self.husb, self.wife, self.chil, self.depth)

    def resolve(self) -> None:
        """Replaces individual reference strings with references to objects."""
        self.husb = self.model.getIndividual(self.husb)
        self.wife = self.model.getIndividual(self.wife)

    def sortChildren(self, filtered_families: List['Family']) -> None:
        """Sort children, based on filtered families of the layout."""
        def compareChildren(x: str, y: str) -> int:
            # For now just try to produce a traditional "husb left, wife right"
            # order, ignore birth date.
            xObj = self.model.getIndividual(x)
            if not xObj:
                raise NoSuchIndividualException("Can't find individual '%s' in the input file." % x)

            yObj = self.model.getIndividual(y)
            if not yObj:
                raise NoSuchIndividualException("Can't find individual '%s' in the input file." % y)

            if xObj.sex == "M" and xObj.fams and self.model.get_family(xObj.fams.id, filtered_families):
                return 1
            if yObj.sex == "M" and yObj.fams and self.model.get_family(yObj.fams.id, filtered_families):
                return -1
            if xObj.sex == "F" and xObj.fams and self.model.get_family(xObj.fams.id, filtered_families):
                return -1
            if yObj.sex == "F" and yObj.fams and self.model.get_family(yObj.fams.id, filtered_families):
                return 1
            return 0
        self.chil.sort(key=cmp_to_key(compareChildren))

    def getHusb(self) -> Individual:
        """Same as accessing 'husb' directly, except that in case that would be
        None, a placeholder individual is created."""
        if not self.husb:
            self.husb = Individual(self.model)
            self.husb.id = "PH%d" % Family.phCount
            Family.phCount += 1
            self.husb.sex = 'M'
            self.husb.forename = "?"
            self.husb.surname = ""
            self.model.individuals.append(self.husb)
        assert isinstance(self.husb, Individual)
        return self.husb

    def getWife(self) -> Individual:
        """Same as getHusb(), but for wifes."""
        if not self.wife:
            self.wife = Individual(self.model)
            self.wife.id = "PH%d" % Family.phCount
            Family.phCount += 1
            self.wife.sex = 'F'
            self.wife.forename = "?"
            self.wife.surname = ""
            self.model.individuals.append(self.wife)
        assert isinstance(self.wife, Individual)
        return self.wife


class Model:
    def __init__(self, config: 'Config') -> None:
        self.config = config
        # List of all individuals.
        self.individuals = []  # type: List[Individual]
        # List of all families.
        self.families = []  # type: List[Family]
        self.basedir = ""

    def getIndividual(self, id_string: str) -> Optional[Individual]:
        for i in self.individuals:
            if i.id == id_string:
                return i
        return None

    def getIndividualGeneWebIndex(self, searchId: str, forename: str, surname: str) -> int:
        my_list = []
        for i in self.individuals:
            if (i.forename == forename) and (i.surname == surname):
                my_list.append(i.id)
        my_list.sort()
        return my_list.index(searchId)

    def get_family(self, id_string: str, family_set: Optional[List[Family]] = None) -> Optional[Family]:
        if family_set:
            families = family_set
        else:
            families = self.families
        for i in families:
            if i.id == id_string:
                return i
        return None

    def load(self, name: str) -> None:
        self.basedir = os.path.dirname(name)
        inf = open(name, "rb")
        GedcomImport(inf, self).load()
        inf.close()
        for individual in self.individuals:
            individual.resolve()
        for family in self.families:
            family.resolve()

    def save(self, out: Optional[TextIO]) -> None:
        """Save is done by calcularing and rendering the layout on the output."""
        if not out:
            out = sys.stdout

        # Support multiple layouts.
        layout_name = "Layout"
        if self.config.layout:
            layout_name = self.config.layout + layout_name
            layout = globals()[layout_name](self, out)
        else:
            layout = Layout(self, out)

        layout.calc()
        layout.render()

    @staticmethod
    def escape(string: str) -> str:
        return string.replace("-", "_")


# Layout (view)

class Edge(Renderable):
    """A graph edge."""
    def __init__(self, model: Model, from_node: str, to_node: str, invisible: bool = False, comment: Optional[str] = None) -> None:
        self.from_node = from_node
        self.to_node = to_node
        self.rest = ""
        if invisible:
            if model.config.edgeInvisibleRed:
                self.rest += "[ color = red ]"
            else:
                self.rest += "[ style = invis ]"
        else:
            if not model.config.edgeVisibleDirected:
                self.rest += "[ arrowhead = none ]"
        if comment:
            self.rest += "// %s" % comment

    def render(self, out: TextIO) -> None:
        out.write("%s -> %s %s\n" % (self.from_node, self.to_node, self.rest))


class Node(Renderable):
    """A graph node."""
    def __init__(self, id_string: str, rest: str = "", point: bool = False, visiblePoint: bool = False, comment: str = "") -> None:
        self.node_id = id_string
        self.rest = rest
        if point:
            self.rest += "[ shape = point, width = 0 ]"
        elif visiblePoint:
            self.rest += "[ shape = point ]"
        if comment:
            self.rest += " // %s" % comment

    def render(self, out: TextIO) -> None:
        out.write("%s %s\n" % (self.node_id, self.rest))


class Subgraph:
    """A subgraph in the layout, contains edges and nodes.
    The special start node is not part of the elements list and it is at the
    begining.  The special end node is the separator between elements what are
    in the subgraph and what are outside of it."""

    class Start:
        """Special start node that acts like a node/edge."""
        def __init__(self, name: str) -> None:
            self.name = name

        def render(self, out: TextIO) -> None:
            out.write("subgraph %s {\n" % self.name)
            out.write("rank = same\n")

    class End(Renderable):
        """Special end node that acts like a node/edge."""
        def render(self, out: TextIO) -> None:
            out.write("}\n")

    def __init__(self, name: str, model: Model) -> None:
        self.name = name
        self.model = model
        self.elements = []  # type: List[Renderable]
        self.start = Subgraph.Start(name)

    def prepend(self, element: Renderable) -> None:
        self.elements.insert(0, element)

    def append(self, element: Renderable) -> None:
        self.elements.append(element)

    def end(self) -> None:
        self.append(Subgraph.End())

    def render(self, out: TextIO) -> None:
        self.start.render(out)
        for i in self.elements:
            i.render(out)
        out.write("\n")

    def find_family(self, family: Family) -> Tuple[str, int]:
        """Find the wife or husb or a family in this subgraph.
        If any of them are found, return the individual's ID and pos."""
        count = 0
        for element in self.elements:
            if element.__class__ == Node:
                node = cast(Node, element)
                if family.wife and node.node_id == family.wife.id:
                    return (family.wife.id, count)
                if family.husb and node.node_id == family.husb.id:
                    return (family.husb.id, count)
            count += 1
        return ("", 0)

    def get_prev_of(self, individual: Individual) -> Optional[Individual]:
        """The passed individual follows the returned ID in this subgraph."""
        for element in self.elements:
            if element.__class__ == Edge:
                edge = cast(Edge, element)
                if hasattr(individual, 'id') and edge.to_node == individual.id:
                    return self.model.getIndividual(edge.from_node)

        return None


class Marriage:
    """Kind of a fake node, produced from a family."""
    def __init__(self, family: Family) -> None:
        self.family = family

    def get_name(self) -> str:
        return "%sAnd%s" % (self.family.getHusb().id, self.family.getWife().id)

    def get_node(self) -> Node:
        husb = self.family.getHusb().getFullName()
        wife = self.family.getWife().getFullName()
        return Node(self.get_name(), visiblePoint=True, comment="%s, %s" % (husb, wife))


class Layout:
    """Generates the graphviz digraph, contains subgraphs.
    The stock layout shows ancestors of a root family."""
    def __init__(self, model: Model, out: TextIO) -> None:
        self.model = model
        self.out = out
        self.subgraphs = []  # type: List[Subgraph]
        # List of families, which are directly interesting for us.
        self.filtered_families = []  # type: List[Family]

    def append(self, subgraph: Subgraph) -> None:
        self.subgraphs.append(subgraph)

    def render(self) -> None:
        self.out.write("digraph tree {\n")
        self.out.write("splines = ortho\n")
        for i in self.subgraphs:
            i.render(self.out)
        self.out.write("}\n")

    def get_subgraph(self, id_string: str) -> Optional[Subgraph]:
        for subgraph in self.subgraphs:
            if subgraph.name == id_string:
                return subgraph
        return None

    def make_edge(self, from_id: str, to_id: str, invisible: bool = False, comment: Optional[str] = None) -> Edge:
        return Edge(self.model, from_id, to_id, invisible=invisible, comment=comment)

    def filter_families(self) -> List[Family]:
        """Iterate over all families, find out directly interesting and sibling
        families. Populates filtered_families, returns sibling ones."""

        family = self.model.get_family(self.model.config.rootFamily)
        if not family:
            raise NoSuchFamilyException("Can't find family '%s' in the input file." % self.model.config.rootFamily)
        self.filtered_families = [family]

        depth = 0
        pendings = [family]
        # List of families, which are interesting for us, as A is in the
        # family, B is in filtered_families, and A is a sibling of B.
        sibling_families = []
        while depth < self.model.config.layoutMaxDepth:
            next_pendings = []
            for pending in pendings:
                children = []  # type: List[str]
                for indi in ('husb', 'wife'):
                    if getattr(pending, indi):
                        indi_family = getattr(pending, indi).famc
                        if indi_family:
                            indi_family.depth = depth + 1
                            self.filtered_families.append(indi_family)
                            next_pendings.append(indi_family)
                            children += indi_family.chil

                # Also collect children's family.
                if depth < self.model.config.layoutMaxSiblingSpouseDepth + 1:
                    # +1, because children are in the previous generation.
                    for chil in children:
                        individual = self.model.getIndividual(chil)
                        if not individual:
                            raise NoSuchIndividualException("Can't find individual '%s' in the input file." % chil)
                        chil_family = individual.fams
                        if not chil_family or self.model.get_family(chil_family.id, self.filtered_families):
                            continue
                        chil_family.depth = depth
                        sibling_families.append(chil_family)
            pendings = next_pendings
            depth += 1

        for i in self.filtered_families:
            i.sortChildren(self.filtered_families)

        return sibling_families

    def build_subgraph(self, depth: int, pending_child_nodes: List[Renderable], descendants: bool = False) -> List[Renderable]:
        """Builds a subgraph, that contains the real nodes for a generation.
        This consists of:

        1) Wife / husb of a family that has the matching depth
        2) Pending children from the previous generation.

        Returns pending children for the next subgraph."""
        subgraph = Subgraph(self.model.escape("Depth%s" % depth), self.model)
        for child in pending_child_nodes:
            subgraph.append(child)
        pending_child_nodes = []

        pending_children_deps = []
        prev_wife = None
        prev_chil = None
        for family in [f for f in self.filtered_families if f.depth == depth]:
            husb = family.getHusb()
            subgraph.append(husb.get_node())
            if prev_wife:
                subgraph.append(self.make_edge(prev_wife.id, family.husb.id, invisible=True))
            wife = family.getWife()
            subgraph.append(wife.get_node())
            prev_wife = family.wife
            marriage = Marriage(family)
            subgraph.append(marriage.get_node())
            subgraph.append(self.make_edge(family.getHusb().id, marriage.get_name(), comment=family.getHusb().getFullName()))
            subgraph.append(self.make_edge(marriage.get_name(), family.getWife().id, comment=family.getWife().getFullName()))
            for family_child in family.chil:
                individual = self.model.getIndividual(family_child)
                if individual and family.depth > self.model.config.layoutMaxSiblingDepth and individual.fams not in self.filtered_families:
                    continue
                if not individual:
                    raise NoSuchIndividualException("Can't find individual '%s' in the input file." % family_child)
                pending_child_nodes.append(individual.get_node())
                if prev_chil:
                    # In case family_child is female and has a husb, then link prev_child to husb,
                    # not to family_child.
                    handled = False
                    family_child_indi = self.model.getIndividual(family_child)
                    if descendants and family_child_indi.sex == 'F':
                        family_child_family = family_child_indi.fams
                        if family_child_family and family_child_family.husb:
                            pending_child_nodes.append(self.make_edge(prev_chil, family_child_family.husb.id, invisible=True))
                            handled = True
                    if not handled:
                        pending_child_nodes.append(self.make_edge(prev_chil, family_child, invisible=True))
                prev_chil = family_child
                pending_children_deps.append(self.make_edge("%sConnect" % family_child, family_child, comment=individual.getFullName()))
        subgraph.end()
        for i in pending_children_deps:
            subgraph.append(i)
        self.append(subgraph)
        return pending_child_nodes

    def build_connector_subgraph(self, depth: int) -> None:
        """Does the same as build_subgraph(), but deals with connector nodes."""
        subgraph = Subgraph(self.model.escape("Depth%sConnects" % depth), self.model)
        pending_deps = []
        prev_child = None
        for family in [f for f in self.filtered_families if f.depth == depth]:
            marriage = Marriage(family)
            children = family.chil[:]
            if not (len(children) % 2 == 1 or not children):
                # If there is no middle child, then insert a fake node here, so
                # marriage can connect to that one.
                half = int(len(children) / 2)
                children.insert(half, marriage.get_name())
            for child in children:
                individual = self.model.getIndividual(child)
                if individual:
                    if family.depth > self.model.config.layoutMaxSiblingDepth and individual.fams not in self.filtered_families:
                        continue
                    subgraph.append(Node("%sConnect" % child, point=True, comment=individual.getFullName()))
                else:
                    subgraph.append(Node("%sConnect" % child, point=True))

            middle = int(len(children) / 2)
            count = 0
            for child in children:
                individual = self.model.getIndividual(child)
                if individual and family.depth > self.model.config.layoutMaxSiblingDepth and individual.fams not in self.filtered_families:
                    continue
                if count < middle:
                    if not individual:
                        raise NoSuchIndividualException("Can't find individual '%s' in the input file." % child)
                    subgraph.append(self.make_edge("%sConnect" % child, "%sConnect" % children[count + 1], comment=individual.getFullName()))
                elif count == middle:
                    if individual:
                        pending_deps.append(self.make_edge(marriage.get_name(), "%sConnect" % child, comment=individual.getFullName()))
                    else:
                        pending_deps.append(self.make_edge(marriage.get_name(), "%sConnect" % child))
                elif count > middle:
                    if not individual:
                        raise NoSuchIndividualException("Can't find individual '%s' in the input file." % child)
                    subgraph.append(self.make_edge("%sConnect" % children[count - 1], "%sConnect" % child, comment=individual.getFullName()))
                if prev_child:
                    subgraph.append(self.make_edge("%sConnect" % prev_child, "%sConnect" % child, invisible=True))
                    prev_child = None
                count += 1
            if children:
                prev_child = children[-1]
        subgraph.end()
        for dep in pending_deps:
            subgraph.append(dep)
        self.append(subgraph)

    def __add_sibling_spouses(self, family: Family) -> None:
        """Add husb and wife from a family to the layout."""
        depth = family.depth
        subgraph = self.get_subgraph(self.model.escape("Depth%s" % depth))
        assert subgraph
        existing_indi, existing_pos = subgraph.find_family(family)
        new_indi = None
        if family.wife and existing_indi == family.wife.id:
            new_indi = family.husb
        else:
            new_indi = family.wife
        if not new_indi:
            # No spouse, probably has children. Ignore for now.
            return
        found = False
        for element in subgraph.elements:
            if existing_indi == family.wife.id and element.__class__ == Edge and cast(Edge, element).to_node == existing_indi:
                cast(Edge, element).to_node = new_indi.id
            elif existing_indi == family.husb.id and element.__class__ == Edge and cast(Edge, element).from_node == existing_indi:
                cast(Edge, element).from_node = new_indi.id
            found = True
        assert found
        subgraph.elements.insert(existing_pos, new_indi.get_node())

        marriage = Marriage(family)
        subgraph.elements.insert(existing_pos, marriage.get_node())

        subgraph.append(self.make_edge(family.husb.id, marriage.get_name(), comment=family.husb.getFullName()))
        subgraph.append(self.make_edge(marriage.get_name(), family.wife.id, comment=family.wife.getFullName()))

    def __add_sibling_children(self, family: Family) -> None:
        """Add children from a sibling family to the layout."""
        depth = family.depth

        if depth > self.model.config.layoutMaxSiblingFamilyDepth:
            return

        subgraph = self.get_subgraph(self.model.escape("Depth%s" % depth))
        assert subgraph
        prev_parent = subgraph.get_prev_of(family.husb)
        if not prev_parent or not prev_parent.fams or not prev_parent.fams.chil:
            # TODO: handle cousins in this case; handle None prev_parent.fams
            return
        if not prev_parent.fams:
            return
        if not prev_parent.fams.chil:
            sys.stderr.write("prev_parent.fams.chil should not be empty?\n")
            return
        last_child = prev_parent.fams.chil[-1]

        # First, add connect nodes and their deps.
        subgraph_connect = self.get_subgraph(self.model.escape("Depth%sConnects" % depth))
        assert subgraph_connect

        marriage = Marriage(family)
        subgraph_connect.prepend(Node("%sConnect" % marriage.get_name(), point=True))
        subgraph_connect.append(self.make_edge(marriage.get_name(), "%sConnect" % marriage.get_name()))

        children = family.chil[:]
        if not len(children) % 2 == 1:
            # If there is no middle child, then insert a fake node here, so
            # marriage can connect to that one.
            half = int(len(children) / 2)
            children.insert(half, marriage.get_name())

        prev_child = last_child
        for chil in children:
            if prev_child not in children:
                subgraph_connect.prepend(self.make_edge("%sConnect" % prev_child, "%sConnect" % chil, invisible=True))
            else:
                subgraph_connect.prepend(self.make_edge("%sConnect" % prev_child, "%sConnect" % chil))
            subgraph_connect.prepend(Node("%sConnect" % chil, point=True))
            prev_child = chil

        # Then, add the real nodes.
        subgraph_child = self.get_subgraph(self.model.escape("Depth%s" % (depth - 1)))
        assert subgraph_child
        prev_child = last_child
        for chil in family.chil:
            subgraph_child.prepend(self.make_edge(prev_child, chil, invisible=True))
            individual = self.model.getIndividual(chil)
            if not individual:
                raise NoSuchIndividualException("Can't find individual '%s' in the input file." % individual)
            subgraph_child.prepend(individual.get_node())
            subgraph_child.append(self.make_edge("%sConnect" % chil, chil))
            prev_child = chil

    def calc(self) -> None:
        """Tries the arrange nodes on a logical grid. Only logical order is
        defined, the exact positions and sizes are still determined by
        graphviz."""

        sibling_families = self.filter_families()

        # Children from generation N are nodes in the N+1th generation.
        pending_child_nodes = []  # type: List[Renderable]
        for depth in reversed(list(range(-1, self.model.config.layoutMaxDepth + 1))):
            # Draw two subgraphs for each generation. The first contains the real nodes.
            pending_child_nodes = self.build_subgraph(depth, pending_child_nodes)
            # The other contains the connector nodes.
            self.build_connector_subgraph(depth)

        # Now add the side-families.
        for family in sibling_families:
            self.__add_sibling_spouses(family)

            # Any children to take care of?
            if family.chil:
                self.__add_sibling_children(family)


class DescendantsLayout(Layout):
    """A layout that shows all descendants of a root family."""
    def filter_families(self) -> List[Family]:
        family = self.model.get_family(self.model.config.rootFamily)
        assert family
        self.filtered_families = [family]

        depth = 0
        pendings = [family]
        while depth < self.model.config.layoutMaxDepth:
            next_pendings = []
            for pending in pendings:
                for indi in pending.chil:
                    individual = self.model.getIndividual(indi)
                    assert individual
                    indi_family = individual.fams
                    if indi_family:
                        indi_family.depth = depth + 1
                        self.filtered_families.append(indi_family)
                        next_pendings.append(indi_family)
            pendings = next_pendings
            depth += 1

        return []

    def calc(self) -> None:
        self.filter_families()

        pending_child_nodes = []  # type: List[Renderable]
        for depth in range(self.model.config.layoutMaxDepth + 1):
            pending_child_nodes = self.build_subgraph(depth, pending_child_nodes, descendants=True)
            self.build_connector_subgraph(depth)


# Import filter

class GedcomImport:
    """Builds the model from GEDCOM."""
    def __init__(self, inf: BinaryIO, model: Model) -> None:
        self.inf = inf
        self.model = model
        self.indi = None  # type: Optional[Individual]
        self.family = None  # type: Optional[Family]
        self.in_birt = False
        self.in_deat = False

    def load(self) -> None:
        linecount = 0

        for i in self.inf.readlines():
            line = i.strip().decode(self.model.config.inputEncoding)
            linecount += 1
            tokens = line.split(' ')

            first_token = tokens[0]
            # Ignore UTF-8 BOM, if there is one at the begining of the line.
            if first_token.startswith("\ufeff"):
                first_token = first_token[1:]

            level = int(first_token)
            rest = " ".join(tokens[1:])
            # try to identify lines with errors
            try:
                if level == 0:
                    if self.indi:
                        self.model.individuals.append(self.indi)
                        self.indi = None
                    if self.family:
                        self.model.families.append(self.family)
                        self.family = None

                    if rest.startswith("@") and rest.endswith("INDI"):
                        id_string = rest[1:-6]
                        if id_string not in self.model.config.indiBlacklist:
                            self.indi = Individual(self.model)
                            self.indi.id = rest[1:-6]
                    elif rest.startswith("@") and rest.endswith("FAM"):
                        self.family = Family(self.model)
                        self.family.id = rest[1:-5]

                elif level == 1:
                    if self.in_birt:
                        self.in_birt = False
                    elif self.in_deat:
                        self.in_deat = False

                    if rest.startswith("SEX") and self.indi:
                        self.indi.sex = rest.split(' ')[1]
                    elif rest.startswith("NAME") and self.indi:
                        rest = rest[5:]
                        tokens = rest.split('/')
                        self.indi.forename = tokens[0].strip()
                        if len(tokens) > 1:
                            self.indi.surname = tokens[1].strip()
                    elif rest.startswith("FAMC") and self.indi:
                        # Child in multiple families? That's crazy...
                        if not self.indi.famc:
                            self.indi.famc = rest[6:-1]
                    elif rest.startswith("FAMS") and self.indi:
                        self.indi.fams = rest[6:-1]
                    elif rest.startswith("BIRT"):
                        self.in_birt = True
                    elif rest.startswith("DEAT"):
                        self.in_deat = True
                    elif rest.startswith("HUSB") and self.family:
                        self.family.husb = rest[6:-1]
                    elif rest.startswith("WIFE") and self.family:
                        self.family.wife = rest[6:-1]
                    elif rest.startswith("CHIL") and self.family:
                        id_string = rest[6:-1]
                        if id_string not in self.model.config.indiBlacklist:
                            self.family.chil.append(rest[6:-1])

                elif level == 2:
                    if rest.startswith("DATE") and self.indi:
                        year = rest.split(' ')[-1]
                        if self.in_birt:
                            self.indi.setBirt(year)
                        elif self.in_deat:
                            self.indi.deat = year

            # pylint: disable=broad-except
            except Exception as exc:
                print("Encountered parsing error in .ged: " + str(exc))
                print("line (%d): %s" % (linecount, line))
                sys.exit(1)

# Configuration handling


class Config:
    layoutMaxDepthDefault = '5'
    rootFamilyDefault = 'F1'
    nodeBorderWidthDefault = '1.0'
    nodeLabelImageDefault = '<<table border="0" cellborder="0"><tr><td><img src="%(picture)s"/></td></tr><tr><td>%(forename)s<br/>%(surname)s<br/>%(birt)s-%(deat)s</td></tr></table>>'
    nodeLabelImageSwappedDefault = '<<table border="0" cellborder="0"><tr><td><img src="%(picture)s"/></td></tr><tr><td>%(surname)s<br/>%(forename)s<br/>%(birt)s-%(deat)s</td></tr></table>>'

    def __init__(self, config_dict: Any) -> None:
        self.config_dict = config_dict
        self.parse()

    def parse(self) -> None:
        path = None

        if isinstance(self.config_dict, list):
            args = cast(List[str], self.config_dict)
            if args:
                path = args[0]
            else:
                path = "ged2dotrc"
        else:
            args = []

        self.parser = configparser.RawConfigParser()
        if not path:
            self.parser.read_dict(self.config_dict)
        else:
            self.parser.read(path)
        self.option = {}  # type: Dict[str, Any]
        for entry in CONFIG_OPTIONS:
            if entry[1] == 'str':
                self.option[entry[0]] = self.get(entry[0], entry[2])
            elif entry[1] == 'int':
                self.option[entry[0]] = int(self.get(entry[0], entry[2]))
            elif entry[1] == 'bool':
                self.option[entry[0]] = (self.get(entry[0], entry[2]).lower() == "true")

    @staticmethod
    def usage() -> None:
        sys.stdout.write("\n -- Sample config file below --\n")
        sys.stdout.write("    Un-comment all options where the given default does not fit your needs\n")
        sys.stdout.write("    and either save as \"ged2dotrc\" or provide the filename as first argument\n")

        sys.stdout.write("\n--------\n")
        sys.stdout.write("[ged2dot]\n")
        for entry in CONFIG_OPTIONS:
            for i in entry[3].split('\n'):
                sys.stdout.write("#%s\n" % i)
            sys.stdout.write("#type: %s\n" % entry[1])
            sys.stdout.write("#%s = %s\n\n" % (entry[0], entry[2]))
        sys.stdout.write("--------\n")

    def __getattr__(self, attr: str) -> Any:
        if attr in self.__dict__:
            return self.__dict__[attr]
        if attr in self.__dict__["option"]:
            return self.__dict__["option"][attr]
        return None

    def get(self, what: str, fallback: str = configparser._UNSET) -> str:  # type: ignore  # This is incompatible with MutableMapping, says configparser.pyi
        return self.parser.get('ged2dot', what, fallback=fallback).split('#')[0]


# (name, type, default, description)
CONFIG_OPTIONS = (
    ('input', 'str', "test.ged", "Input filename (GEDCOM file)"),
    ('rootFamily', 'str', Config.rootFamilyDefault, "Starting from family with this identifier"),

    ('considerAgeDead', 'int', "120", "Consider someone dead at this age: put a question mark if death date is missing."),
    ('anonMode', 'bool', 'False', "Anonymous mode: avoid any kind of sensitive data in the output."),
    ('images', 'bool', 'True', "Should the output contain images?"),
    ('imageFormat', 'str', 'images/%(forename)s %(surname)s %(birt)s.jpg', """If images is True: format of the image paths.
Use a path relative to \"input\" document here!
Possible variables: %(forename)s, %(surname)s, %(birt)s and %(gwIndex)s.
where gwIndex is 0 unless there are more individuals with the same forename and surname"""),
    ('imageFormatCase', 'str', '', """Should the filenames (from \"imageFormat\") be converted?
Possible values: \"\" - don't convert
                 \"upper\" - convert all characters to upper case
                 \"lower\" - convert all characters to lower case (use this for geneweb export)
"""),
    ('imageFormatGeneweb', 'bool', 'False', """Convert some special characters in the imagefilename
to find pictures of geneweb (also set imageFormatCase to lower for geneweb images)
"""),

    ('nodeLabelImage', 'str', Config.nodeLabelImageDefault, """If images is True: label text of nodes.
Possible values: %(picture)s, %(surname)s, %(forename)s, %(birt)s and %(deat)s."""),

    ('nodeLabelPlain', 'str', '"%(forename)s\\n%(surname)s\\n%(birt)s-%(deat)s"', """If images is False: label text of nodes.
Possible values: %(picture)s, %(surname)s, %(forename)s, %(birt)s and %(deat)s."""),
    ('nodeBorderWidth', 'str', Config.nodeBorderWidthDefault, """The box pencil thickness on individual person boxes. It should resemble a floating point number. Default=1.0"""),

    ('edgeInvisibleRed', 'bool', 'False', "Invisible edges: red for debugging or really invisible?"),
    ('edgeVisibleDirected', 'bool', 'False', "Visible edges: show direction for debugging?"),
    ('layoutMaxDepth', 'int', Config.layoutMaxDepthDefault, "Number of ancestor generations to show."),

    ('layoutMaxSiblingDepth', 'int', Config.layoutMaxDepthDefault, "Number of ancestor generations, where also siblings are shown."),
    ('layoutMaxSiblingSpouseDepth', 'int', Config.layoutMaxDepthDefault, "Number of ancestor generations, where also sibling spouses are shown."),
    ('layoutMaxSiblingFamilyDepth', 'int', '1', """Number of anchester generations, where also sibling families are shown.
It's 1 by default, as values >= 2 causes edges to overlap each other in general."""),

    ('indiBlacklist', 'str', '', """Comma-sepated list of individual ID's to hide from the output for debugging.
Example: \"P526, P525\"."""),

    ('layout', 'str', '', "Currently supported: \"\" or Descendants"),

    ('inputEncoding', 'str', 'UTF-8', """encoding of the gedcom
example \"UTF-8\" or \"ISO 8859-15\"."""),

    ('outputEncoding', 'str', 'UTF-8', """encoding of the output file
should be UTF-8 for dot-files"""),
)


def main() -> None:
    if not os.path.exists("ged2dotrc"):
        sys.stderr.write("Fatal: ged2dotrc configuration file doesn't exist.\nCreate a config file similar to test/screenshotrc, name it ged2dotrc and continue.\n")
        sys.exit(1)
    try:
        config = Config(sys.argv[1:])
    # pylint: disable=broad-except
    except (BaseException) as base_exception:
        print("Configuration invalid? %s" % (str(base_exception)))
        sys.exit(1)

    if len(sys.argv) > 1 and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        config.usage()
        sys.exit(0)

    model = Model(config)
    try:
        model.load(config.input)
    except (BaseException) as base_exception:
        sys.stderr.write("error in tree file:\n")
        raise base_exception
    if sys.version_info[0] < 3:
        sys.stdout = codecs.getwriter(config.outputEncoding)(sys.stdout)
    model.save(sys.stdout)


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
