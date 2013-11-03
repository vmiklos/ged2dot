#!/usr/bin/env python2
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
sys = reload(sys)
sys.setdefaultencoding("utf-8")
import time
import os
import ConfigParser


# Model

class Individual:
    """An individual is our basic building block, can be part of multiple families (usually two)."""
    def __init__(self, model):
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
        self.hasOrderDep = False

    def __str__(self):
        return "id: %s, sex: %s, forename: %s, surname: %s: famc: %s, fams: %s, birt: %s, deat: %s" % (self.id, self.sex, self.forename, self.surname, self.famc, self.fams, self.birt, self.deat)

    def getFullName(self):
        """Full name of the individual. Only used as comments in the output
        file to ease debugging."""
        return "%s %s" % (self.forename, self.surname)

    def getLabel(self):
        path = self.model.config.imageFormat % {
            'forename': self.forename,
            'surname': self.surname,
            'birt': self.birt
        }
        if os.path.exists(path) and not self.model.config.anonMode:
            picture = path
        else:
            if self.sex == "M":
                picture = "placeholder-m.png"
            else:
                picture = "placeholder-f.png"

        try:
            from PIL import Image
            i = Image.open(picture)
            if i.size != (100, 100):
                print "// warning, picture of %s has custom (not 100x100 px) size." % self.getFullName()
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
                'surname': self.surname,
                'forename': self.forename,
                'birt': self.birt,
                'deat': self.deat
            }

    def getColor(self):
        return {'M': 'blue', 'F': 'pink'}[self.sex]

    def getNode(self):
        return Node(self.id, '[ shape = box,\nlabel = %s,\ncolor = %s ]' % (self.getLabel(), self.getColor()))

    def setBirt(self, birt):
        if not len(birt):
            return
        self.birt = birt
        if time.localtime().tm_year - int(birt) > self.model.config.considerAgeDead:
            if not len(self.deat):
                self.deat = "?"


class Family:
    """Family has exactly one wife and husb, 0..* children."""
    def __init__(self, model):
        self.model = model
        self.id = None
        self.husb = None
        self.wife = None
        self.chil = []
        self.depth = 0

    def __str__(self):
        return "id: %s, husb: %s, wife: %s, chil: %s, depth: %s" % (self.id, self.husb, self.wife, self.chil, self.depth)

    def sortChildren(self, filteredFamilies):
        """Sort children, based on filtered families of the layout."""
        def compareChildren(x, y):
            # For now just try to produce a traditional "husb left, wife right"
            # order, ignore birth date.
            xObj = self.model.getIndividual(x)
            yObj = self.model.getIndividual(y)
            if xObj.sex == "M" and xObj.fams and self.model.getFamily(xObj.fams, filteredFamilies):
                return 1
            if yObj.sex == "M" and yObj.fams and self.model.getFamily(yObj.fams, filteredFamilies):
                return -1
            if xObj.sex == "F" and xObj.fams and self.model.getFamily(xObj.fams, filteredFamilies):
                return -1
            if yObj.sex == "F" and yObj.fams and self.model.getFamily(yObj.fams, filteredFamilies):
                return 1
            return 0
        self.chil.sort(compareChildren)


class Model:
    def __init__(self, config):
        self.config = config
        self.individuals = []  # List of all individuals.
        self.families = []  # List of all families.

    def getIndividual(self, id):
        for i in self.individuals:
            if i.id == id:
                return i

    def getFamily(self, id, familySet=None):
        if not familySet:
            familySet = self.families
        for i in familySet:
            if i.id == id:
                return i

    def load(self, name):
        inf = open(name)
        GedcomImport(inf, self).load()

    def save(self):
        """Save is done by calcularing and rendering the layout on the output."""
        layout = Layout(self)
        layout.calc()
        layout.render()


# Layout (view)

class Edge:
    """A graph edge."""
    def __init__(self, model, fro, to, invisible=False, comment=None):
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

    def render(self):
        print "%s -> %s %s" % (self.fro, self.to, self.rest)


class Node:
    """A graph node."""
    def __init__(self, id, rest="", point=False, visiblePoint=False, comment=None):
        self.id = id
        self.rest = rest
        if point:
            self.rest += "[ shape = point, width = 0 ]"
        elif visiblePoint:
            self.rest += "[ shape = point ]"
        if comment:
            self.rest += " // %s" % comment

    def render(self):
        print "%s %s" % (self.id, self.rest)


class Subgraph:
    """A subgraph in the layout, contains edges and nodes.
    The special start node is not part of the elements list and it is at the
    begining.  The special end node is the separator between elements what are
    in the subgraph and what are outside of it."""

    class Start:
        """Special start node that acts like a node/edge."""
        def __init__(self, name):
            self.name = name

        def render(self):
            print "subgraph %s {" % self.name
            print "rank = same"

    class End:
        """Special end node that acts like a node/edge."""
        def render(self):
            print "}"

    def __init__(self, name):
        self.name = name
        self.elements = []
        self.start = Subgraph.Start(name)

    def prepend(self, element):
        self.elements.insert(0, element)

    def append(self, element):
        self.elements.append(element)

    def end(self):
        self.append(Subgraph.End())

    def render(self):
        self.start.render()
        for i in self.elements:
            i.render()
        print ""

    def findFamily(self, family):
        """Find the wife or husb or a family in this subgraph.
        If any of them are found, return the individual's ID and pos."""
        count = 0
        for e in self.elements:
            if e.__class__ == Node:
                if e.id == family.wife:
                    return (family.wife, count)
                elif e.id == family.husb:
                    return (family.husb, count)
            count += 1


class Marriage:
    """Kind of a fake node, produced from a family."""
    def __init__(self, family):
        self.family = family

    def getName(self):
        return "%sAnd%s" % (self.family.husb, self.family.wife)

    def getNode(self):
        model = self.family.model
        husb = model.getIndividual(self.family.husb).getFullName()
        wife = model.getIndividual(self.family.wife).getFullName()
        return Node(self.getName(), visiblePoint=True, comment="%s, %s" % (husb, wife))


class Layout:
    """Generates the graphviz digraph, contains subgraphs."""
    def __init__(self, model):
        self.model = model
        self.subgraphs = []
        self.filteredFamilies = []  # List of families, which are directly interesting for us.
        # TODO make this configurable
        self.maxSiblingFamilyDepth = 1  # Number of anchester generations, where also sibling families are shown.

    def append(self, subgraph):
        self.subgraphs.append(subgraph)

    def render(self):
        print "digraph {"
        print "splines = ortho"
        for i in self.subgraphs:
            i.render()
        print "}"

    def getSubgraph(self, id):
        for s in self.subgraphs:
            if s.name == id:
                return s

    def makeEdge(self, fro, to, invisible=False, comment=None):
        return Edge(self.model, fro, to, invisible=invisible, comment=comment)

    def __filterFamilies(self):
        """Iterate over all families, find out directly interesting and sibling
        families. Populates filteredFamilies, returns sibling ones."""
        familyRoot = "F8"  # TODO make this configurable

        self.filteredFamilies = [self.model.getFamily(familyRoot)]

        depth = 0
        pendings = [self.model.getFamily(familyRoot)]
        # List of families, which are interesting for us, as A is in the
        # family, B is in filteredFamilies, and A is a sibling of B.
        siblingFamilies = []
        while depth < self.model.config.layoutMaxDepth:
            nextPendings = []
            for pending in pendings:
                husbFamily = self.model.getFamily(self.model.getIndividual(pending.husb).famc)
                husbFamily.depth = depth + 1
                self.filteredFamilies.append(husbFamily)
                nextPendings.append(husbFamily)
                wifeFamily = self.model.getFamily(self.model.getIndividual(pending.wife).famc)
                wifeFamily.depth = depth + 1
                self.filteredFamilies.append(wifeFamily)
                nextPendings.append(wifeFamily)

                # Also collect children's family.
                if depth < self.model.config.layoutMaxSiblingDepth + 1:
                    # +1, because children are in the previous generation.
                    for chil in husbFamily.chil + wifeFamily.chil:
                        chilFamily = self.model.getFamily(self.model.getIndividual(chil).fams)
                        if not chilFamily or self.model.getFamily(chilFamily.id, self.filteredFamilies):
                            continue
                        chilFamily.depth = depth
                        siblingFamilies.append(chilFamily)
            pendings = nextPendings
            depth += 1

        for i in self.filteredFamilies:
            i.sortChildren(self.filteredFamilies)

        return siblingFamilies

    def __buildSubgraph(self, depth, pendingChildNodes):
        """Builds a subgraph, that contains the real nodes for a generation.
        This consists of:

        1) Wife / husb of a family that has the matching depth
        2) Pending children from the previous generation.

        Returns pending children for the next subgraph."""
        subgraph = Subgraph("Depth%s" % depth)
        for child in pendingChildNodes:
            subgraph.append(child)
        pendingChildNodes = []

        pendingChildrenDeps = []
        prevWife = None
        prevChil = None
        for family in filter(lambda f: f.depth == depth, self.filteredFamilies):
            husb = self.model.getIndividual(family.husb)
            subgraph.append(husb.getNode())
            if prevWife and not self.model.getIndividual(prevWife).hasOrderDep:
                subgraph.append(self.makeEdge(prevWife, family.husb, invisible=True))
            wife = self.model.getIndividual(family.wife)
            subgraph.append(wife.getNode())
            prevWife = family.wife
            marriage = Marriage(family)
            subgraph.append(marriage.getNode())
            subgraph.append(self.makeEdge(family.husb, marriage.getName(), comment=self.model.getIndividual(family.husb).getFullName()))
            subgraph.append(self.makeEdge(marriage.getName(), family.wife, comment=self.model.getIndividual(family.wife).getFullName()))
            for child in family.chil:
                pendingChildNodes.append(self.model.getIndividual(child).getNode())
                if prevChil:
                    pendingChildNodes.append(self.makeEdge(prevChil, child, invisible=True))
                    self.model.getIndividual(prevChil).hasOrderDep = True
                prevChil = child
                pendingChildrenDeps.append(self.makeEdge("%sConnect" % child, child, comment=self.model.getIndividual(child).getFullName()))
        subgraph.end()
        for i in pendingChildrenDeps:
            subgraph.append(i)
        self.append(subgraph)
        return pendingChildNodes

    def __buildConnectorSubgraph(self, depth):
        """Does the same as __buildSubgraph(), but deals with connector nodes."""
        subgraph = Subgraph("Depth%sConnects" % depth)
        pendingDeps = []
        prevChild = None
        for family in filter(lambda f: f.depth == depth, self.filteredFamilies):
            marriage = Marriage(family)
            children = family.chil[:]
            if not (len(children) % 2 == 1 or len(children) == 0):
                # If there is no middle child, then insert a fake node here, so
                # marriage can connect to that one.
                half = len(children) / 2
                children.insert(half, marriage.getName())
            for child in children:
                if self.model.getIndividual(child):
                    subgraph.append(Node("%sConnect" % child, point=True, comment=self.model.getIndividual(child).getFullName()))
                else:
                    subgraph.append(Node("%sConnect" % child, point=True))

            middle = (len(children) / 2)
            count = 0
            for child in children:
                if count < middle:
                    subgraph.append(self.makeEdge("%sConnect" % child, "%sConnect" % children[middle], comment=self.model.getIndividual(child).getFullName()))
                elif count == middle:
                    if self.model.getIndividual(child):
                        pendingDeps.append(self.makeEdge(marriage.getName(), "%sConnect" % child, comment=self.model.getIndividual(child).getFullName()))
                    else:
                        pendingDeps.append(self.makeEdge(marriage.getName(), "%sConnect" % child))
                elif count > middle:
                    subgraph.append(self.makeEdge("%sConnect" % children[middle], "%sConnect" % child, comment=self.model.getIndividual(child).getFullName()))
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

    def __addSiblingSpouses(self, family):
        """Add husb and wife from a family to the layout."""
        depth = family.depth
        subgraph = self.getSubgraph("Depth%s" % depth)
        existingIndi, existingPos = subgraph.findFamily(family)
        if existingIndi == family.wife:
            newIndi = family.husb
        else:
            newIndi = family.wife
        if not newIndi:
            # No spouse, probably has children. Ignore for now.
            return
        found = False
        for e in subgraph.elements:
            if existingIndi == family.wife and e.__class__ == Edge and e.to == existingIndi:
                e.to = newIndi
            elif existingIndi == family.husb and e.__class__ == Edge and e.fro == existingIndi:
                e.fro = newIndi
            found = True
        assert found
        subgraph.elements.insert(existingPos, self.model.getIndividual(newIndi).getNode())

        marriage = Marriage(family)
        subgraph.elements.insert(existingPos, marriage.getNode())

        subgraph.append(self.makeEdge(family.husb, marriage.getName(), comment=self.model.getIndividual(family.husb).getFullName()))
        subgraph.append(self.makeEdge(marriage.getName(), family.wife, comment=self.model.getIndividual(family.wife).getFullName()))

    def __addSiblingChildren(self, family):
        """Add children from a sibling family to the layout."""
        depth = family.depth

        if depth > self.maxSiblingFamilyDepth:
            return

        subgraph = self.getSubgraph("Depth%s" % depth)
        lastChild = None
        for e in subgraph.elements:
            # Let's assume for now that placing the children on the right side of the subgraph is a good idea.
            if e.__class__ == Edge and e.to == family.husb:
                prevParent = self.model.getIndividual(e.fro)
                lastChild = self.model.getFamily(prevParent.fams).chil[-1]
                break

        # First, add connect nodes and their deps.
        subgraphConnect = self.getSubgraph("Depth%sConnects" % depth)

        marriage = Marriage(family)
        subgraphConnect.prepend(Node("%sConnect" % marriage.getName(), point=True))
        subgraphConnect.append(self.makeEdge(marriage.getName(), "%sConnect" % marriage.getName()))

        children = family.chil[:]
        if not len(children) % 2 == 1:
            # If there is no middle child, then insert a fake node here, so
            # marriage can connect to that one.
            half = len(children) / 2
            children.insert(half, marriage.getName())

        prevChild = lastChild
        for c in children:
            if not prevChild in children:
                subgraphConnect.prepend(self.makeEdge("%sConnect" % prevChild, "%sConnect" % c, invisible=True))
            else:
                subgraphConnect.prepend(self.makeEdge("%sConnect" % prevChild, "%sConnect" % c))
            subgraphConnect.prepend(Node("%sConnect" % c, point=True))
            prevChild = c

        # Then, add the real nodes.
        subgraphChild = self.getSubgraph("Depth%s" % (depth - 1))
        prevChild = lastChild
        for c in family.chil:
            subgraphChild.prepend(self.makeEdge(prevChild, c, invisible=True))
            subgraphChild.prepend(self.model.getIndividual(c).getNode())
            subgraphChild.append(self.makeEdge("%sConnect" % c, c))
            prevChild = c

    def calc(self):
        """Tries the arrange nodes on a logical grid. Only logical order is
        defined, the exact positions and sizes are still determined by
        graphviz."""

        siblingFamilies = self.__filterFamilies()

        pendingChildNodes = []  # Children from generation N are nodes in the N+1th generation.
        for depth in reversed(range(self.model.config.layoutMaxDepth + 1)):
            # Draw two subgraphs for each generation. The first contains the real nodes.
            pendingChildNodes = self.__buildSubgraph(depth, pendingChildNodes)
            # The other contains the connector nodes.
            self.__buildConnectorSubgraph(depth)

        # Now add the side-families.
        for f in siblingFamilies:
            self.__addSiblingSpouses(f)

            # Any children to take care of?
            if len(f.chil):
                self.__addSiblingChildren(f)


# Import filter

class GedcomImport:
    """Builds the model from GEDCOM."""
    def __init__(self, inf, model):
        self.inf = inf
        self.model = model
        self.indi = None
        self.family = None
        self.inBirt = False
        self.inDeat = False

    def load(self):
        for i in self.inf.readlines():
            line = i.strip()
            tokens = line.split(' ')
            level = int(tokens[0])
            rest = " ".join(tokens[1:])
            if level == 0:
                if self.indi:
                    self.model.individuals.append(self.indi)
                    self.indi = None
                if self.family:
                    self.model.families.append(self.family)
                    self.family = None

                if rest.startswith("@") and rest.endswith("INDI"):
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
    def __init__(self):
        self.parser = ConfigParser.RawConfigParser()
        self.parser.read("ged2dotrc")  # TODO make this configurable
        self.input = self.get('input')
        self.considerAgeDead = int(self.get('considerAgeDead'))
        self.anonMode = self.get('anonMode') == "True"
        self.images = self.get('images') == "True"
        self.imageFormat = self.get('imageFormat')
        self.nodeLabelImage = self.get('nodeLabelImage')
        self.nodeLabelPlain = self.get('nodeLabelPlain')
        self.edgeInvisibleRed = self.get('edgeInvisibleRed') == "True"
        self.edgeVisibleDirected = self.get('edgeVisibleDirected') == "True"
        self.layoutMaxDepth = int(self.get('layoutMaxDepth'))
        self.layoutMaxSiblingDepth = int(self.get('layoutMaxSiblingDepth'))

    def get(self, what):
        return self.parser.get('ged2dot', what).split('#')[0]


def main():
    config = Config()
    model = Model(config)
    model.load(config.input)
    model.save()

if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
