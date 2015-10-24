#!/usr/bin/python

import sys

def log(msg, *params):
    print >> sys.stderr, "voting:", msg.format(*params)

def fail(msg, *params):
    log("error: " + msg, *params)
    sys.exit(1)

class Apartment:
    def __init__(self, building, id, localBuilding, localId, area, name):
        self.building = building
        self.localBuilding = localBuilding
        self.id = id
        self.localId = localId
        self.area = area
        self.name = [name]

    def __cmp__(self, o):
        if isinstance(o, Apartment):
            return self.id.__cmp__(o.id)
        return self.id.__cmp__(o)

    def __repr__(self):
        return ("Apartment({}({}), {}({}), {}, ({}))"
                .format(self.building, self.localBuilding, self.id
                        , self.localId, self.area
                        , ", ".join(self.name)))

    def __hash__(self):
        return self.id

class Apartments:
    def __init__(self, file, localNumbers = (), aptPerBuilding=0):
        self.apts = {}
        self.total = 0
        for line in file.xreadlines():
            building, id, area, name = line.strip().split('\t')[:4]
            building = int(building)
            id = int(id)
            area = int(area)

            localId = ((id - 1) % aptPerBuilding) + 1 \
                      if aptPerBuilding \
                      else id
            localBuilding = localNumbers[int((id - 1) / aptPerBuilding)] \
                            if aptPerBuilding and localNumbers \
                            else building

            apt = Apartment(building, id, localBuilding, localId, area, name)
            existing = self.apts.get(apt.id, None)
            if existing is None:
                self.apts[apt.id] = apt
                self.total += apt.area
            else:
                existing.name.extend(apt.name)

        self.count = len(self.apts)

    def area(self, dataset):
        nonexistent = set(dataset).difference(set(self.apts))
        if nonexistent:
            fail("Non-existent apartment attends: {}.", nonexistent)

        a = 0
        for id in dataset: a += self.apts[id].area
        return a

    def values(self):
        return self.apts.values()

    def keys(self):
        return self.apts.keys()

    def items(self):
        return self.apts.items()

    def __getitem__(self, index):
        return self.apts[index]

    def __iter__(self):
        return self.apts.__iter__()

    def __str__(self):
        return "{} apts, total area: {}".format(len(self.apts), self.total)
