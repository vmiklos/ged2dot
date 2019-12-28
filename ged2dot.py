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
        self.famc = self.model.getFamily(self.famc)
        self.fams = self.model.getFamily(self.fams)

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

    def getNode(self) -> 'Node':
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

    def sortChildren(self, filteredFamilies: List['Family']) -> None:
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

            if xObj.sex == "M" and xObj.fams and self.model.getFamily(xObj.fams.id, filteredFamilies):
                return 1
            if yObj.sex == "M" and yObj.fams and self.model.getFamily(yObj.fams.id, filteredFamilies):
                return -1
            if xObj.sex == "F" and xObj.fams and self.model.getFamily(xObj.fams.id, filteredFamilies):
                return -1
            if yObj.sex == "F" and yObj.fams and self.model.getFamily(yObj.fams.id, filteredFamilies):
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
        myList = []
        for i in self.individuals:
            if (i.forename == forename) and (i.surname == surname):
                myList.append(i.id)
        myList.sort()
        return myList.index(searchId)

    def getFamily(self, id_string: str, familySet: Optional[List[Family]] = None) -> Optional[Family]:
        if familySet:
            families = familySet
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
        layoutName = "Layout"
        if self.config.layout:
            layoutName = self.config.layout + layoutName
            layout = globals()[layoutName](self, out)
        else:
            layout = Layout(self, out)

        layout.calc()
        layout.render()

    @staticmethod
    def escape(s: str) -> str:
        return s.replace("-", "_")


# Layout (view)

class Edge(Renderable):
    """A graph edge."""
    def __init__(self, model: Model, fro: str, to: str, invisible: bool = False, comment: Optional[str] = None) -> None:
        self.fro = fro
        self.to = to
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
        out.write("%s -> %s %s\n" % (self.fro, self.to, self.rest))


class Node(Renderable):
    """A graph node."""
    def __init__(self, id_string: str, rest: str = "", point: bool = False, visiblePoint: bool = False, comment: str = "") -> None:
        self.id = id_string
        self.rest = rest
        if point:
            self.rest += "[ shape = point, width = 0 ]"
        elif visiblePoint:
            self.rest += "[ shape = point ]"
        if comment:
            self.rest += " // %s" % comment

    def render(self, out: TextIO) -> None:
        out.write("%s %s\n" % (self.id, self.rest))


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

    def findFamily(self, family: Family) -> Tuple[str, int]:
        """Find the wife or husb or a family in this subgraph.
        If any of them are found, return the individual's ID and pos."""
        count = 0
        for e in self.elements:
            if e.__class__ == Node:
                n = cast(Node, e)
                if family.wife and n.id == family.wife.id:
                    return (family.wife.id, count)
                if family.husb and n.id == family.husb.id:
                    return (family.husb.id, count)
            count += 1
        return ("", 0)

    def getPrevOf(self, individual: Individual) -> Optional[Individual]:
        """The passed individual follows the returned ID in this subgraph."""
        for e in self.elements:
            if e.__class__ == Edge:
                edge = cast(Edge, e)
                if hasattr(individual, 'id') and edge.to == individual.id:
                    return self.model.getIndividual(edge.fro)

        return None


class Marriage:
    """Kind of a fake node, produced from a family."""
    def __init__(self, family: Family) -> None:
        self.family = family

    def getName(self) -> str:
        return "%sAnd%s" % (self.family.getHusb().id, self.family.getWife().id)

    def getNode(self) -> Node:
        husb = self.family.getHusb().getFullName()
        wife = self.family.getWife().getFullName()
        return Node(self.getName(), visiblePoint=True, comment="%s, %s" % (husb, wife))


class Layout:
    """Generates the graphviz digraph, contains subgraphs.
    The stock layout shows ancestors of a root family."""
    def __init__(self, model: Model, out: TextIO) -> None:
        self.model = model
        self.out = out
        self.subgraphs = []  # type: List[Subgraph]
        # List of families, which are directly interesting for us.
        self.filteredFamilies = []  # type: List[Family]

    def append(self, subgraph: Subgraph) -> None:
        self.subgraphs.append(subgraph)

    def render(self) -> None:
        self.out.write("digraph tree {\n")
        self.out.write("splines = ortho\n")
        for i in self.subgraphs:
            i.render(self.out)
        self.out.write("}\n")

    def getSubgraph(self, id_string: str) -> Optional[Subgraph]:
        for s in self.subgraphs:
            if s.name == id_string:
                return s
        return None

    def makeEdge(self, fro: str, to: str, invisible: bool = False, comment: Optional[str] = None) -> Edge:
        return Edge(self.model, fro, to, invisible=invisible, comment=comment)

    def filterFamilies(self) -> List[Family]:
        """Iterate over all families, find out directly interesting and sibling
        families. Populates filteredFamilies, returns sibling ones."""

        family = self.model.getFamily(self.model.config.rootFamily)
        if not family:
            raise NoSuchFamilyException("Can't find family '%s' in the input file." % self.model.config.rootFamily)
        self.filteredFamilies = [family]

        depth = 0
        pendings = [family]
        # List of families, which are interesting for us, as A is in the
        # family, B is in filteredFamilies, and A is a sibling of B.
        siblingFamilies = []
        while depth < self.model.config.layoutMaxDepth:
            nextPendings = []
            for pending in pendings:
                children = []  # type: List[str]
                for indi in ('husb', 'wife'):
                    if getattr(pending, indi):
                        indiFamily = getattr(pending, indi).famc
                        if indiFamily:
                            indiFamily.depth = depth + 1
                            self.filteredFamilies.append(indiFamily)
                            nextPendings.append(indiFamily)
                            children += indiFamily.chil

                # Also collect children's family.
                if depth < self.model.config.layoutMaxSiblingDepth + 1:
                    # +1, because children are in the previous generation.
                    for chil in children:
                        individual = self.model.getIndividual(chil)
                        if not individual:
                            raise NoSuchIndividualException("Can't find individual '%s' in the input file." % chil)
                        chilFamily = individual.fams
                        if not chilFamily or self.model.getFamily(chilFamily.id, self.filteredFamilies):
                            continue
                        chilFamily.depth = depth
                        siblingFamilies.append(chilFamily)
            pendings = nextPendings
            depth += 1

        for i in self.filteredFamilies:
            i.sortChildren(self.filteredFamilies)

        return siblingFamilies

    def buildSubgraph(self, depth: int, pendingChildNodes: List[Renderable], descendants: bool = False) -> List[Renderable]:
        """Builds a subgraph, that contains the real nodes for a generation.
        This consists of:

        1) Wife / husb of a family that has the matching depth
        2) Pending children from the previous generation.

        Returns pending children for the next subgraph."""
        subgraph = Subgraph(self.model.escape("Depth%s" % depth), self.model)
        for child in pendingChildNodes:
            subgraph.append(child)
        pendingChildNodes = []

        pendingChildrenDeps = []
        prevWife = None
        prevChil = None
        for family in [f for f in self.filteredFamilies if f.depth == depth]:
            husb = family.getHusb()
            subgraph.append(husb.getNode())
            if prevWife:
                subgraph.append(self.makeEdge(prevWife.id, family.husb.id, invisible=True))
            wife = family.getWife()
            subgraph.append(wife.getNode())
            prevWife = family.wife
            marriage = Marriage(family)
            subgraph.append(marriage.getNode())
            subgraph.append(self.makeEdge(family.getHusb().id, marriage.getName(), comment=family.getHusb().getFullName()))
            subgraph.append(self.makeEdge(marriage.getName(), family.getWife().id, comment=family.getWife().getFullName()))
            for familyChild in family.chil:
                individual = self.model.getIndividual(familyChild)
                if not individual:
                    raise NoSuchIndividualException("Can't find individual '%s' in the input file." % familyChild)
                pendingChildNodes.append(individual.getNode())
                if prevChil:
                    # In case familyChild is female and has a husb, then link prevChild to husb, not to familyChild.
                    handled = False
                    familyChildIndi = self.model.getIndividual(familyChild)
                    if descendants and familyChildIndi.sex == 'F':
                        familyChildFamily = familyChildIndi.fams
                        if familyChildFamily and familyChildFamily.husb:
                            pendingChildNodes.append(self.makeEdge(prevChil, familyChildFamily.husb.id, invisible=True))
                            handled = True
                    if not handled:
                        pendingChildNodes.append(self.makeEdge(prevChil, familyChild, invisible=True))
                prevChil = familyChild
                pendingChildrenDeps.append(self.makeEdge("%sConnect" % familyChild, familyChild, comment=individual.getFullName()))
        subgraph.end()
        for i in pendingChildrenDeps:
            subgraph.append(i)
        self.append(subgraph)
        return pendingChildNodes

    def buildConnectorSubgraph(self, depth: int) -> None:
        """Does the same as buildSubgraph(), but deals with connector nodes."""
        subgraph = Subgraph(self.model.escape("Depth%sConnects" % depth), self.model)
        pendingDeps = []
        prevChild = None
        for family in [f for f in self.filteredFamilies if f.depth == depth]:
            marriage = Marriage(family)
            children = family.chil[:]
            if not (len(children) % 2 == 1 or not children):
                # If there is no middle child, then insert a fake node here, so
                # marriage can connect to that one.
                half = int(len(children) / 2)
                children.insert(half, marriage.getName())
            for child in children:
                individual = self.model.getIndividual(child)
                if individual:
                    subgraph.append(Node("%sConnect" % child, point=True, comment=individual.getFullName()))
                else:
                    subgraph.append(Node("%sConnect" % child, point=True))

            middle = int(len(children) / 2)
            count = 0
            for child in children:
                individual = self.model.getIndividual(child)
                if count < middle:
                    if not individual:
                        raise NoSuchIndividualException("Can't find individual '%s' in the input file." % child)
                    subgraph.append(self.makeEdge("%sConnect" % child, "%sConnect" % children[count + 1], comment=individual.getFullName()))
                elif count == middle:
                    if individual:
                        pendingDeps.append(self.makeEdge(marriage.getName(), "%sConnect" % child, comment=individual.getFullName()))
                    else:
                        pendingDeps.append(self.makeEdge(marriage.getName(), "%sConnect" % child))
                elif count > middle:
                    if not individual:
                        raise NoSuchIndividualException("Can't find individual '%s' in the input file." % child)
                    subgraph.append(self.makeEdge("%sConnect" % children[count - 1], "%sConnect" % child, comment=individual.getFullName()))
                if prevChild:
                    subgraph.append(self.makeEdge("%sConnect" % prevChild, "%sConnect" % child, invisible=True))
                    prevChild = None
                count += 1
            if children:
                prevChild = children[-1]
        subgraph.end()
        for dep in pendingDeps:
            subgraph.append(dep)
        self.append(subgraph)

    def __addSiblingSpouses(self, family: Family) -> None:
        """Add husb and wife from a family to the layout."""
        depth = family.depth
        subgraph = self.getSubgraph(self.model.escape("Depth%s" % depth))
        assert subgraph
        existingIndi, existingPos = subgraph.findFamily(family)
        newIndi = None
        if family.wife and existingIndi == family.wife.id:
            newIndi = family.husb
        else:
            newIndi = family.wife
        if not newIndi:
            # No spouse, probably has children. Ignore for now.
            return
        found = False
        for e in subgraph.elements:
            if existingIndi == family.wife.id and e.__class__ == Edge and cast(Edge, e).to == existingIndi:
                cast(Edge, e).to = newIndi.id
            elif existingIndi == family.husb.id and e.__class__ == Edge and cast(Edge, e).fro == existingIndi:
                cast(Edge, e).fro = newIndi.id
            found = True
        assert found
        subgraph.elements.insert(existingPos, newIndi.getNode())

        marriage = Marriage(family)
        subgraph.elements.insert(existingPos, marriage.getNode())

        subgraph.append(self.makeEdge(family.husb.id, marriage.getName(), comment=family.husb.getFullName()))
        subgraph.append(self.makeEdge(marriage.getName(), family.wife.id, comment=family.wife.getFullName()))

    def __addSiblingChildren(self, family: Family) -> None:
        """Add children from a sibling family to the layout."""
        depth = family.depth

        if depth > self.model.config.layoutMaxSiblingFamilyDepth:
            return

        subgraph = self.getSubgraph(self.model.escape("Depth%s" % depth))
        assert subgraph
        prevParent = subgraph.getPrevOf(family.husb)
        if not prevParent or not prevParent.fams or not prevParent.fams.chil:
            # TODO: handle cousins in this case
            # TODO: handle None prevParent.fams
            return
        if not prevParent.fams:
            return
        if not prevParent.fams.chil:
            sys.stderr.write("prevParent.fams.chil should not be empty?\n")
            return
        lastChild = prevParent.fams.chil[-1]

        # First, add connect nodes and their deps.
        subgraphConnect = self.getSubgraph(self.model.escape("Depth%sConnects" % depth))
        assert subgraphConnect

        marriage = Marriage(family)
        subgraphConnect.prepend(Node("%sConnect" % marriage.getName(), point=True))
        subgraphConnect.append(self.makeEdge(marriage.getName(), "%sConnect" % marriage.getName()))

        children = family.chil[:]
        if not len(children) % 2 == 1:
            # If there is no middle child, then insert a fake node here, so
            # marriage can connect to that one.
            half = int(len(children) / 2)
            children.insert(half, marriage.getName())

        prevChild = lastChild
        for c in children:
            if prevChild not in children:
                subgraphConnect.prepend(self.makeEdge("%sConnect" % prevChild, "%sConnect" % c, invisible=True))
            else:
                subgraphConnect.prepend(self.makeEdge("%sConnect" % prevChild, "%sConnect" % c))
            subgraphConnect.prepend(Node("%sConnect" % c, point=True))
            prevChild = c

        # Then, add the real nodes.
        subgraphChild = self.getSubgraph(self.model.escape("Depth%s" % (depth - 1)))
        assert subgraphChild
        prevChild = lastChild
        for c in family.chil:
            subgraphChild.prepend(self.makeEdge(prevChild, c, invisible=True))
            individual = self.model.getIndividual(c)
            if not individual:
                raise NoSuchIndividualException("Can't find individual '%s' in the input file." % individual)
            subgraphChild.prepend(individual.getNode())
            subgraphChild.append(self.makeEdge("%sConnect" % c, c))
            prevChild = c

    def calc(self) -> None:
        """Tries the arrange nodes on a logical grid. Only logical order is
        defined, the exact positions and sizes are still determined by
        graphviz."""

        siblingFamilies = self.filterFamilies()

        # Children from generation N are nodes in the N+1th generation.
        pendingChildNodes = []  # type: List[Renderable]
        for depth in reversed(list(range(-1, self.model.config.layoutMaxDepth + 1))):
            # Draw two subgraphs for each generation. The first contains the real nodes.
            pendingChildNodes = self.buildSubgraph(depth, pendingChildNodes)
            # The other contains the connector nodes.
            self.buildConnectorSubgraph(depth)

        # Now add the side-families.
        for f in siblingFamilies:
            self.__addSiblingSpouses(f)

            # Any children to take care of?
            if f.chil:
                self.__addSiblingChildren(f)


class DescendantsLayout(Layout):
    """A layout that shows all descendants of a root family."""
    def filterFamilies(self) -> List[Family]:
        family = self.model.getFamily(self.model.config.rootFamily)
        assert family
        self.filteredFamilies = [family]

        depth = 0
        pendings = [family]
        while depth < self.model.config.layoutMaxDepth:
            nextPendings = []
            for pending in pendings:
                for indi in pending.chil:
                    individual = self.model.getIndividual(indi)
                    assert individual
                    indiFamily = individual.fams
                    if indiFamily:
                        indiFamily.depth = depth + 1
                        self.filteredFamilies.append(indiFamily)
                        nextPendings.append(indiFamily)
            pendings = nextPendings
            depth += 1

        return []

    def calc(self) -> None:
        self.filterFamilies()

        pendingChildNodes = []  # type: List[Renderable]
        for depth in range(self.model.config.layoutMaxDepth + 1):
            pendingChildNodes = self.buildSubgraph(depth, pendingChildNodes, descendants=True)
            self.buildConnectorSubgraph(depth)


# Import filter

class GedcomImport:
    """Builds the model from GEDCOM."""
    def __init__(self, inf: BinaryIO, model: Model) -> None:
        self.inf = inf
        self.model = model
        self.indi = None  # type: Optional[Individual]
        self.family = None  # type: Optional[Family]
        self.inBirt = False
        self.inDeat = False

    def load(self) -> None:
        linecount = 0

        for i in self.inf.readlines():
            line = i.strip().decode(self.model.config.inputEncoding)
            linecount += 1
            tokens = line.split(' ')

            firstToken = tokens[0]
            # Ignore UTF-8 BOM, if there is one at the begining of the line.
            if firstToken.startswith("\ufeff"):
                firstToken = firstToken[1:]

            level = int(firstToken)
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
                    if self.inBirt:
                        self.inBirt = False
                    elif self.inDeat:
                        self.inDeat = False

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
                        self.inBirt = True
                    elif rest.startswith("DEAT"):
                        self.inDeat = True
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
                        if self.inBirt:
                            self.indi.setBirt(year)
                        elif self.inDeat:
                            self.indi.deat = year

            # pylint: disable=broad-except
            except Exception as e:
                print("Encountered parsing error in .ged: " + str(e))
                print("line (%d): %s" % (linecount, line))
                sys.exit(1)

# Configuration handling


class Config:
    layoutMaxDepthDefault = '5'
    rootFamilyDefault = 'F1'
    nodeBorderWidthDefault = '1.0'
    nodeLabelImageDefault = '<<table border="0" cellborder="0"><tr><td><img src="%(picture)s"/></td></tr><tr><td>%(forename)s<br/>%(surname)s<br/>%(birt)s-%(deat)s</td></tr></table>>'
    nodeLabelImageSwappedDefault = '<<table border="0" cellborder="0"><tr><td><img src="%(picture)s"/></td></tr><tr><td>%(surname)s<br/>%(forename)s<br/>%(birt)s-%(deat)s</td></tr></table>>'

    def __init__(self, configDict: Any) -> None:
        self.configDict = configDict
        self.parse()

    def parse(self) -> None:
        path = None

        if isinstance(self.configDict, list):
            args = cast(List[str], self.configDict)
            if args:
                path = args[0]
            else:
                path = "ged2dotrc"
        else:
            args = []

        self.parser = configparser.RawConfigParser()
        if not path:
            self.parser.read_dict(self.configDict)
        else:
            self.parser.read(path)
        self.option = {}  # type: Dict[str, Any]
        for entry in configOptions:
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
        for entry in configOptions:
            for l in entry[3].split('\n'):
                sys.stdout.write("#%s\n" % l)
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
configOptions = (
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

    ('layoutMaxSiblingDepth', 'int', Config.layoutMaxDepthDefault, "Number of ancestor generations, where also sibling spouses are shown."),
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
    except (BaseException) as be:
        print("Configuration invalid? %s" % (str(be)))
        sys.exit(1)

    if len(sys.argv) > 1 and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        config.usage()
        sys.exit(0)

    model = Model(config)
    try:
        model.load(config.input)
    except (BaseException) as be:
        sys.stderr.write("error in tree file:\n")
        raise be
    if sys.version_info[0] < 3:
        sys.stdout = codecs.getwriter(config.outputEncoding)(sys.stdout)
    model.save(sys.stdout)


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
