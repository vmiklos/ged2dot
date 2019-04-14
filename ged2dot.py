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


# Exceptions

class NoSuchFamilyException(Exception):
    pass


# Model

class Individual:
    placeholderDir = os.path.dirname(os.path.realpath(__file__))
    """An individual is our basic building block, can be part of multiple families (usually two)."""
    def __init__(self, model):  # type: ignore
        self.model = model
        self.id = None
        self.sex = None
        self.forename = None  # John
        self.surname = None  # Smith
        self.famc = None
        self.fams = None
        self.birt = ""
        self.deat = ""
        # Horizontal order is ensured by order deps. Any order dep starting from this node?
        # Set to true on first addition, so that we can avoid redundant deps.

    def __str__(self):  # type: ignore
        return "id: %s, sex: %s, forename: %s, surname: %s: famc: %s, fams: %s, birt: %s, deat: %s" % (self.id, self.sex, self.forename, self.surname, self.famc, self.fams, self.birt, self.deat)

    def resolve(self):  # type: ignore
        """Replaces family reference strings with references to objects."""
        self.famc = self.model.getFamily(self.famc)
        self.fams = self.model.getFamily(self.fams)

    def getFullName(self):  # type: ignore
        """Full name of the individual. Only used as comments in the output
        file to ease debugging."""
        return "%s %s" % (self.forename, self.surname)

    def getLabel(self):  # type: ignore
        if self.forename:
            forename = self.forename
        else:
            forename = ""
        if self.surname:
            surname = self.surname
        else:
            surname = ""

        if (self.model.config.imageFormatCase.lower() == 'lower'):
            forename = forename.lower()
            surname = surname.lower()
        elif (self.model.config.imageFormatCase.lower() == 'upper'):
            forename = forename.upper()
            surname = surname.upper()

        path = self.model.config.imageFormat % {
            'forename': forename,
            'surname': surname,
            'gwIndex': self.model.getIndividualGeneWebIndex(self.id, self.forename, self.surname),
            'birt': self.birt
        }

        if (self.model.config.imageFormatGeneweb):
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
            sex = 'u' if self.sex is None else self.sex.lower()
            picture = os.path.join(Individual.placeholderDir, "placeholder-%s.png" % sex)

        try:
            from PIL import Image  # type: ignore
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

        if self.model.config.images:
            format = self.model.config.nodeLabelImage
        else:
            format = self.model.config.nodeLabelPlain
        if self.model.config.anonMode:
            birt = self.birt
            if len(birt) > 1:
                birt = "YYYY"
            deat = self.deat
            if len(deat) > 1:
                deat = "YYYY"
            return format % {
                'picture': picture,
                'surname': self.id[0],
                'forename': self.id[1:],
                'birt': birt,
                'deat': deat
            }
        else:
            return format % {
                'picture': picture,
                'surname': surname,
                'forename': forename,
                'birt': self.birt,
                'deat': self.deat
            }

    def getColor(self):  # type: ignore
        sex = 'U' if self.sex is None else self.sex.upper()
        return {'M': 'blue', 'F': 'pink', 'U': 'black'}[sex]

    def getNode(self):  # type: ignore
        return Node(self.id, '[ shape = box,\nlabel = %s,\ncolor = %s ]' % (self.getLabel(), self.getColor()))  # type: ignore

    def setBirt(self, birt):  # type: ignore
        if not len(birt):
            return
        self.birt = birt
        try:
            if time.localtime().tm_year - int(birt) > self.model.config.considerAgeDead:
                if not len(self.deat):
                    self.deat = "?"
        except ValueError:
            pass


class Family:
    """Family has exactly one wife and husb, 0..* children."""
    phCount = 0

    def __init__(self, model):  # type: ignore
        self.model = model
        self.id = None
        self.husb = None
        self.wife = None
        self.chil = []  # type: ignore
        self.depth = 0

    def __str__(self):  # type: ignore
        return "id: %s, husb: %s, wife: %s, chil: %s, depth: %s" % (self.id, self.husb, self.wife, self.chil, self.depth)

    def resolve(self):  # type: ignore
        """Replaces individual reference strings with references to objects."""
        self.husb = self.model.getIndividual(self.husb)
        self.wife = self.model.getIndividual(self.wife)

    def sortChildren(self, filteredFamilies):  # type: ignore
        """Sort children, based on filtered families of the layout."""
        def compareChildren(x, y):  # type: ignore
            # For now just try to produce a traditional "husb left, wife right"
            # order, ignore birth date.
            xObj = self.model.getIndividual(x)
            yObj = self.model.getIndividual(y)
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

    def getHusb(self):  # type: ignore
        """Same as accessing 'husb' directly, except that in case that would be
        None, a placeholder individual is created."""
        if not self.husb:
            self.husb = Individual(self.model)  # type: ignore
            self.husb.id = "PH%d" % Family.phCount
            Family.phCount += 1
            self.husb.sex = 'M'
            self.husb.forename = "?"
            self.husb.surname = ""
            self.model.individuals.append(self.husb)
        return self.husb

    def getWife(self):  # type: ignore
        """Same as getHusb(), but for wifes."""
        if not self.wife:
            self.wife = Individual(self.model)  # type: ignore
            self.wife.id = "PH%d" % Family.phCount
            Family.phCount += 1
            self.wife.sex = 'F'
            self.wife.forename = "?"
            self.wife.surname = ""
            self.model.individuals.append(self.wife)
        return self.wife


class Model:
    def __init__(self, config):  # type: ignore
        self.config = config
        # List of all individuals.
        self.individuals = []  # type: ignore
        # List of all families.
        self.families = []  # type: ignore

    def getIndividual(self, id):  # type: ignore
        for i in self.individuals:
            if i.id == id:
                return i

    def getIndividualGeneWebIndex(self, searchId, forename, surname):  # type: ignore
        myList = []
        for i in self.individuals:
            if (i.forename == forename) and (i.surname == surname):
                myList.append(i.id)
        myList.sort
        return myList.index(searchId)

    def getFamily(self, id, familySet=None):  # type: ignore
        if not familySet:
            familySet = self.families
        for i in familySet:
            if i.id == id:
                return i

    def load(self, name):  # type: ignore
        self.basedir = os.path.dirname(name)
        inf = open(name, "rb")
        GedcomImport(inf, self).load()  # type: ignore
        inf.close()
        for i in self.individuals:
            i.resolve()
        for i in self.families:
            i.resolve()

    def save(self, out):  # type: ignore
        """Save is done by calcularing and rendering the layout on the output."""
        if not out:
            out = sys.stdout

        # Support multiple layouts.
        layoutName = "Layout"
        if len(self.config.layout):
            layoutName = self.config.layout + layoutName
            layout = globals()[layoutName](self, out)
        else:
            layout = Layout(self, out)  # type: ignore

        layout.calc()
        layout.render()

    def escape(self, s):  # type: ignore
        return s.replace("-", "_")


# Layout (view)

class Edge:
    """A graph edge."""
    def __init__(self, model, fro, to, invisible=False, comment=None):  # type: ignore
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

    def render(self, out):  # type: ignore
        out.write("%s -> %s %s\n" % (self.fro, self.to, self.rest))


class Node:
    """A graph node."""
    def __init__(self, id, rest="", point=False, visiblePoint=False, comment=None):  # type: ignore
        self.id = id
        self.rest = rest
        if point:
            self.rest += "[ shape = point, width = 0 ]"
        elif visiblePoint:
            self.rest += "[ shape = point ]"
        if comment:
            self.rest += " // %s" % comment

    def render(self, out):  # type: ignore
        out.write("%s %s\n" % (self.id, self.rest))


class Subgraph:
    """A subgraph in the layout, contains edges and nodes.
    The special start node is not part of the elements list and it is at the
    begining.  The special end node is the separator between elements what are
    in the subgraph and what are outside of it."""

    class Start:
        """Special start node that acts like a node/edge."""
        def __init__(self, name):  # type: ignore
            self.name = name

        def render(self, out):  # type: ignore
            out.write("subgraph %s {\n" % self.name)
            out.write("rank = same\n")

    class End:
        """Special end node that acts like a node/edge."""
        def render(self, out):  # type: ignore
            out.write("}\n")

    def __init__(self, name, model):  # type: ignore
        self.name = name
        self.model = model
        self.elements = []  # type: ignore
        self.start = Subgraph.Start(name)  # type: ignore

    def prepend(self, element):  # type: ignore
        self.elements.insert(0, element)

    def append(self, element):  # type: ignore
        self.elements.append(element)

    def end(self):  # type: ignore
        self.append(Subgraph.End())

    def render(self, out):  # type: ignore
        self.start.render(out)
        for i in self.elements:
            i.render(out)
        out.write("\n")

    def findFamily(self, family):  # type: ignore
        """Find the wife or husb or a family in this subgraph.
        If any of them are found, return the individual's ID and pos."""
        count = 0
        for e in self.elements:
            if e.__class__ == Node:
                if family.wife and e.id == family.wife.id:
                    return (family.wife.id, count)
                elif family.husb and e.id == family.husb.id:
                    return (family.husb.id, count)
            count += 1

    def getPrevOf(self, individual):  # type: ignore
        """The passed individual follows the returned ID in this subgraph."""
        for e in self.elements:
            if e.__class__ == Edge and hasattr(individual, 'id') and e.to == individual.id:
                return self.model.getIndividual(e.fro)


class Marriage:
    """Kind of a fake node, produced from a family."""
    def __init__(self, family):  # type: ignore
        self.family = family

    def getName(self):  # type: ignore
        return "%sAnd%s" % (self.family.getHusb().id, self.family.getWife().id)

    def getNode(self):  # type: ignore
        husb = self.family.getHusb().getFullName()
        wife = self.family.getWife().getFullName()
        return Node(self.getName(), visiblePoint=True, comment="%s, %s" % (husb, wife))  # type: ignore


class Layout:
    """Generates the graphviz digraph, contains subgraphs.
    The stock layout shows ancestors of a root family."""
    def __init__(self, model, out):  # type: ignore
        self.model = model
        self.out = out
        self.subgraphs = []  # type: ignore
        # List of families, which are directly interesting for us.
        self.filteredFamilies = []   # type: ignore

    def append(self, subgraph):  # type: ignore
        self.subgraphs.append(subgraph)

    def render(self):  # type: ignore
        self.out.write("digraph {\n")
        self.out.write("splines = ortho\n")
        for i in self.subgraphs:
            i.render(self.out)
        self.out.write("}\n")

    def getSubgraph(self, id):  # type: ignore
        for s in self.subgraphs:
            if s.name == id:
                return s

    def makeEdge(self, fro, to, invisible=False, comment=None):  # type: ignore
        return Edge(self.model, fro, to, invisible=invisible, comment=comment)  # type: ignore

    def filterFamilies(self):  # type: ignore
        """Iterate over all families, find out directly interesting and sibling
        families. Populates filteredFamilies, returns sibling ones."""

        self.filteredFamilies = [self.model.getFamily(self.model.config.rootFamily)]

        depth = 0
        if not self.model.getFamily(self.model.config.rootFamily):
            raise NoSuchFamilyException("Can't find family '%s' in the input file." % self.model.config.rootFamily)
        pendings = [self.model.getFamily(self.model.config.rootFamily)]
        # List of families, which are interesting for us, as A is in the
        # family, B is in filteredFamilies, and A is a sibling of B.
        siblingFamilies = []
        while depth < self.model.config.layoutMaxDepth:
            nextPendings = []
            for pending in pendings:
                children = []  # type: ignore
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
                        chilFamily = self.model.getIndividual(chil).fams
                        if not chilFamily or self.model.getFamily(chilFamily.id, self.filteredFamilies):
                            continue
                        chilFamily.depth = depth
                        siblingFamilies.append(chilFamily)
            pendings = nextPendings
            depth += 1

        for i in self.filteredFamilies:
            i.sortChildren(self.filteredFamilies)

        return siblingFamilies

    def buildSubgraph(self, depth, pendingChildNodes, descendants=False):  # type: ignore
        """Builds a subgraph, that contains the real nodes for a generation.
        This consists of:

        1) Wife / husb of a family that has the matching depth
        2) Pending children from the previous generation.

        Returns pending children for the next subgraph."""
        subgraph = Subgraph(self.model.escape("Depth%s" % depth), self.model)  # type: ignore
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
            marriage = Marriage(family)  # type: ignore
            subgraph.append(marriage.getNode())
            subgraph.append(self.makeEdge(family.getHusb().id, marriage.getName(), comment=family.getHusb().getFullName()))
            subgraph.append(self.makeEdge(marriage.getName(), family.getWife().id, comment=family.getWife().getFullName()))
            for child in family.chil:
                pendingChildNodes.append(self.model.getIndividual(child).getNode())
                if prevChil:
                    # In case child is female and has a husb, then link prevChild to husb, not to child.
                    handled = False
                    childIndi = self.model.getIndividual(child)
                    if descendants and childIndi.sex == 'F':
                        childFamily = childIndi.fams
                        if childFamily and childFamily.husb:
                            pendingChildNodes.append(self.makeEdge(prevChil, childFamily.husb.id, invisible=True))
                            handled = True
                    if not handled:
                        pendingChildNodes.append(self.makeEdge(prevChil, child, invisible=True))
                prevChil = child
                pendingChildrenDeps.append(self.makeEdge("%sConnect" % child, child, comment=self.model.getIndividual(child).getFullName()))
        subgraph.end()
        for i in pendingChildrenDeps:
            subgraph.append(i)
        self.append(subgraph)
        return pendingChildNodes

    def buildConnectorSubgraph(self, depth):  # type: ignore
        """Does the same as buildSubgraph(), but deals with connector nodes."""
        subgraph = Subgraph(self.model.escape("Depth%sConnects" % depth), self.model)  # type: ignore
        pendingDeps = []
        prevChild = None
        for family in [f for f in self.filteredFamilies if f.depth == depth]:
            marriage = Marriage(family)  # type: ignore
            children = family.chil[:]
            if not (len(children) % 2 == 1 or len(children) == 0):
                # If there is no middle child, then insert a fake node here, so
                # marriage can connect to that one.
                half = int(len(children) / 2)
                children.insert(half, marriage.getName())
            for child in children:
                if self.model.getIndividual(child):
                    subgraph.append(Node("%sConnect" % child, point=True, comment=self.model.getIndividual(child).getFullName()))  # type: ignore
                else:
                    subgraph.append(Node("%sConnect" % child, point=True))  # type: ignore

            middle = int(len(children) / 2)
            count = 0
            for child in children:
                if count < middle:
                    subgraph.append(self.makeEdge("%sConnect" % child, "%sConnect" % children[count + 1], comment=self.model.getIndividual(child).getFullName()))
                elif count == middle:
                    if self.model.getIndividual(child):
                        pendingDeps.append(self.makeEdge(marriage.getName(), "%sConnect" % child, comment=self.model.getIndividual(child).getFullName()))
                    else:
                        pendingDeps.append(self.makeEdge(marriage.getName(), "%sConnect" % child))
                elif count > middle:
                    subgraph.append(self.makeEdge("%sConnect" % children[count - 1], "%sConnect" % child, comment=self.model.getIndividual(child).getFullName()))
                if prevChild:
                    subgraph.append(self.makeEdge("%sConnect" % prevChild, "%sConnect" % child, invisible=True))
                    prevChild = None
                count += 1
            if len(children):
                prevChild = children[-1]
        subgraph.end()
        for dep in pendingDeps:
            subgraph.append(dep)
        self.append(subgraph)

    def __addSiblingSpouses(self, family):  # type: ignore
        """Add husb and wife from a family to the layout."""
        depth = family.depth
        subgraph = self.getSubgraph(self.model.escape("Depth%s" % depth))
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
            if existingIndi == family.wife.id and e.__class__ == Edge and e.to == existingIndi:
                e.to = newIndi.id
            elif existingIndi == family.husb.id and e.__class__ == Edge and e.fro == existingIndi:
                e.fro = newIndi.id
            found = True
        assert found
        subgraph.elements.insert(existingPos, newIndi.getNode())

        marriage = Marriage(family)  # type: ignore
        subgraph.elements.insert(existingPos, marriage.getNode())

        subgraph.append(self.makeEdge(family.husb.id, marriage.getName(), comment=family.husb.getFullName()))
        subgraph.append(self.makeEdge(marriage.getName(), family.wife.id, comment=family.wife.getFullName()))

    def __addSiblingChildren(self, family):  # type: ignore
        """Add children from a sibling family to the layout."""
        depth = family.depth

        if depth > self.model.config.layoutMaxSiblingFamilyDepth:
            return

        subgraph = self.getSubgraph(self.model.escape("Depth%s" % depth))
        prevParent = subgraph.getPrevOf(family.husb)
        if (not prevParent) or (not prevParent.fams) or (not len(prevParent.fams.chil)):
            # TODO: handle cousins in this case
            # TODO: handle None prevParent.fams
            return
        if not prevParent.fams:
            return
        if len(prevParent.fams.chil) == 0:
            sys.stderr.write("prevParent.fams.chil should not be empty?\n")
            return
        lastChild = prevParent.fams.chil[-1]

        # First, add connect nodes and their deps.
        subgraphConnect = self.getSubgraph(self.model.escape("Depth%sConnects" % depth))

        marriage = Marriage(family)  # type: ignore
        subgraphConnect.prepend(Node("%sConnect" % marriage.getName(), point=True))  # type: ignore
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
            subgraphConnect.prepend(Node("%sConnect" % c, point=True))  # type: ignore
            prevChild = c

        # Then, add the real nodes.
        subgraphChild = self.getSubgraph(self.model.escape("Depth%s" % (depth - 1)))
        prevChild = lastChild
        for c in family.chil:
            subgraphChild.prepend(self.makeEdge(prevChild, c, invisible=True))
            subgraphChild.prepend(self.model.getIndividual(c).getNode())
            subgraphChild.append(self.makeEdge("%sConnect" % c, c))
            prevChild = c

    def calc(self):  # type: ignore
        """Tries the arrange nodes on a logical grid. Only logical order is
        defined, the exact positions and sizes are still determined by
        graphviz."""

        siblingFamilies = self.filterFamilies()

        # Children from generation N are nodes in the N+1th generation.
        pendingChildNodes = []  # type: ignore
        for depth in reversed(list(range(-1, self.model.config.layoutMaxDepth + 1))):
            # Draw two subgraphs for each generation. The first contains the real nodes.
            pendingChildNodes = self.buildSubgraph(depth, pendingChildNodes)
            # The other contains the connector nodes.
            self.buildConnectorSubgraph(depth)

        # Now add the side-families.
        for f in siblingFamilies:
            self.__addSiblingSpouses(f)

            # Any children to take care of?
            if len(f.chil):
                self.__addSiblingChildren(f)


class DescendantsLayout(Layout):
    """A layout that shows all descendants of a root family."""
    def filterFamilies(self):  # type: ignore
        self.filteredFamilies = [self.model.getFamily(self.model.config.rootFamily)]

        depth = 0
        pendings = [self.model.getFamily(self.model.config.rootFamily)]
        while depth < self.model.config.layoutMaxDepth:
            nextPendings = []
            for pending in pendings:
                for indi in pending.chil:
                    indiFamily = self.model.getIndividual(indi).fams
                    if indiFamily:
                        indiFamily.depth = depth + 1
                        self.filteredFamilies.append(indiFamily)
                        nextPendings.append(indiFamily)
            pendings = nextPendings
            depth += 1

    def calc(self):  # type: ignore
        self.filterFamilies()

        pendingChildNodes = []  # type: ignore
        for depth in range(self.model.config.layoutMaxDepth + 1):
            pendingChildNodes = self.buildSubgraph(depth, pendingChildNodes, descendants=True)
            self.buildConnectorSubgraph(depth)


# Import filter

class GedcomImport:
    """Builds the model from GEDCOM."""
    def __init__(self, inf, model):  # type: ignore
        self.inf = inf
        self.model = model
        self.indi = None
        self.family = None
        self.inBirt = False
        self.inDeat = False

    def load(self):  # type: ignore
        for i in self.inf.readlines():
            line = i.strip().decode(self.model.config.inputEncoding)
            tokens = line.split(' ')

            firstToken = tokens[0]
            # Ignore UTF-8 BOM, if there is one at the begining of the line.
            if firstToken.startswith("\ufeff"):
                firstToken = firstToken[1:]

            level = int(firstToken)
            rest = " ".join(tokens[1:])
            if level == 0:
                if self.indi:
                    self.model.individuals.append(self.indi)
                    self.indi = None
                if self.family:
                    self.model.families.append(self.family)
                    self.family = None

                if rest.startswith("@") and rest.endswith("INDI"):
                    id = rest[1:-6]
                    if id not in self.model.config.indiBlacklist:
                        self.indi = Individual(self.model)  # type: ignore
                        self.indi.id = rest[1:-6]
                elif rest.startswith("@") and rest.endswith("FAM"):
                    self.family = Family(self.model)  # type: ignore
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
                    id = rest[6:-1]
                    if id not in self.model.config.indiBlacklist:
                        self.family.chil.append(rest[6:-1])

            elif level == 2:
                if rest.startswith("DATE") and self.indi:
                    year = rest.split(' ')[-1]
                    if self.inBirt:
                        self.indi.setBirt(year)
                    elif self.inDeat:
                        self.indi.deat = year


# Configuration handling

class Config:
    layoutMaxDepthDefault = '5'
    rootFamilyDefault = 'F1'
    nodeLabelImageDefault = '<<table border="0" cellborder="0"><tr><td><img src="%(picture)s"/></td></tr><tr><td>%(forename)s<br/>%(surname)s<br/>%(birt)s-%(deat)s</td></tr></table>>'
    nodeLabelImageSwappedDefault = '<<table border="0" cellborder="0"><tr><td><img src="%(picture)s"/></td></tr><tr><td>%(surname)s<br/>%(forename)s<br/>%(birt)s-%(deat)s</td></tr></table>>'

    def __init__(self, configDict):  # type: ignore
        self.configDict = configDict
        self.configOptions = ()
        # (name, type, default, description)
        self.configOptions += (('input', 'str', "test.ged", "Input filename (GEDCOM file)"),)
        self.configOptions += (('rootFamily', 'str', Config.rootFamilyDefault, "Starting from family with this identifier"),)

        self.configOptions += (('considerAgeDead', 'int', "120", "Consider someone dead at this age: put a question mark if death date is missing."),)
        self.configOptions += (('anonMode', 'bool', 'False', "Anonymous mode: avoid any kind of sensitive data in the output."),)
        self.configOptions += (('images', 'bool', 'True', "Should the output contain images?"),)
        self.configOptions += (('imageFormat', 'str', 'images/%(forename)s %(surname)s %(birt)s.jpg', """If images is True: format of the image paths.
Use a path relative to \"input\" document here!
Possible variables: %(forename)s, %(surname)s, %(birt)s and %(gwIndex)s.
where gwIndex is 0 unless there are more individuals with the same forename and surname"""),)
        self.configOptions += (('imageFormatCase', 'str', '', """Should the filenames (from \"imageFormat\") be converted?
Possible values: \"\" - don't convert
                 \"upper\" - convert all characters to upper case
                 \"lower\" - convert all characters to lower case (use this for geneweb export)
"""),)
        self.configOptions += (('imageFormatGeneweb', 'bool', 'False', """Convert some special characters in the imagefilename
to find pictures of geneweb (also set imageFormatCase to lower for geneweb images)
"""),)

        self.configOptions += (('nodeLabelImage', 'str', Config.nodeLabelImageDefault, """If images is True: label text of nodes.
Possible values: %(picture)s, %(surname)s, %(forename)s, %(birt)s and %(deat)s."""),)

        self.configOptions += (('nodeLabelPlain', 'str', '"%(forename)s\\n%(surname)s\\n%(birt)s-%(deat)s"', """If images is False: label text of nodes.
Possible values: %(picture)s, %(surname)s, %(forename)s, %(birt)s and %(deat)s."""),)

        self.configOptions += (('edgeInvisibleRed', 'bool', 'False', "Invisible edges: red for debugging or really invisible?"),)
        self.configOptions += (('edgeVisibleDirected', 'bool', 'False', "Visible edges: show direction for debugging?"),)
        self.configOptions += (('layoutMaxDepth', 'int', Config.layoutMaxDepthDefault, "Number of ancestor generations to show."),)

        # TODO: implement 'parameter-copy' Default: same as layoutMaxDepth
        self.configOptions += (('layoutMaxSiblingDepth', 'int', Config.layoutMaxDepthDefault, "Number of ancestor generations, where also sibling spouses are shown."),)
        self.configOptions += (('layoutMaxSiblingFamilyDepth', 'int', '1', """Number of anchester generations, where also sibling families are shown.
It's 1 by default, as values >= 2 causes edges to overlap each other in general."""),)

        self.configOptions += (('indiBlacklist', 'str', '', """Comma-sepated list of individual ID's to hide from the output for debugging.
Example: \"P526, P525\""""),)

        self.configOptions += (('layout', 'str', '', "Currently supported: \"\" or Descendants"),)

        self.configOptions += (('inputEncoding', 'str', 'UTF-8', """encoding of the gedcom
example \"UTF-8\" or \"ISO 8859-15\""""),)

        self.configOptions += (('outputEncoding', 'str', 'UTF-8', """encoding of the output file
should be UTF-8 for dot-files"""),)
        self.parse()

    def parse(self):  # type: ignore
        path = None

        if type(self.configDict) == list:
            args = self.configDict
            if len(args):
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
        self.option = {}  # type: ignore
        for entry in self.configOptions:
            if (entry[1] == 'str'):
                self.option[entry[0]] = self.get(entry[0], entry[2])
            elif (entry[1] == 'int'):
                self.option[entry[0]] = int(self.get(entry[0], entry[2]))
            elif (entry[1] == 'bool'):
                self.option[entry[0]] = (self.get(entry[0], entry[2]).lower() == "true")

    def usage(self):  # type: ignore
        sys.stderr.write("\n -- Sample config file below --\n")
        sys.stderr.write("    Un-comment all options where the given default does not fit your needs\n")
        sys.stderr.write("    and either save as \"ged2dotrc\" or provide the filename as first argument\n")

        sys.stderr.write("\n--------\n")
        sys.stderr.write("[ged2dot]\n")
        for entry in self.configOptions:
            for l in entry[3].split('\n'):
                sys.stderr.write("#%s\n" % l)
            sys.stderr.write("#type: %s\n" % entry[1])
            sys.stderr.write("#%s = %s\n\n" % (entry[0], entry[2]))
        sys.stderr.write("--------\n")

    def __getattr__(self, attr):  # type: ignore
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            if attr in self.__dict__["option"]:
                return self.__dict__["option"][attr]
            else:
                return None

    def get(self, what, fallback=configparser._UNSET):  # type: ignore
        return self.parser.get('ged2dot', what, fallback=fallback).split('#')[0]


def main():  # type: ignore
    try:
        config = Config(sys.argv[1:])  # type: ignore
    except (BaseException) as be:
        print("Configuration invalid? %s" % (str(be)))
        config.usage()
        sys.exit(1)
    model = Model(config)  # type: ignore
    try:
        model.load(config.input)
    except (BaseException) as be:
        config.usage()
        raise be
    if (sys.version_info[0] < 3):
        sys.stdout = codecs.getwriter(config.outputEncoding)(sys.stdout)
    model.save(sys.stdout)


if __name__ == "__main__":
    main()  # type: ignore

# vim:set shiftwidth=4 softtabstop=4 expandtab:
