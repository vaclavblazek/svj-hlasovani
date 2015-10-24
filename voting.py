#!/usr/bin/python

#
# @18:15
# Name = "Voting #1"
# Quorum = 50% (of all)
#
# + 1, 2, 3, 4, 5
# - 5, 6, 7
# ! 8, 9, 10
#

import sys
import os
from colorama import Fore, Style

def green(text):
    if os.isatty(sys.stdout.fileno()):
        return Fore.GREEN + Style.BRIGHT + str(text) + Style.RESET_ALL
    return text

def red(text):
    if os.isatty(sys.stdout.fileno()):
        return Fore.RED + Style.BRIGHT + str(text) + Style.RESET_ALL
    return text

def yellow(text):
    if os.isatty(sys.stdout.fileno()):
        return Fore.YELLOW + Style.NORMAL + str(text) + Style.RESET_ALL
    return text

def log(msg, *params):
    print >> sys.stderr, "voting:", msg.format(*params)

def fail(msg, *params):
    log("error: " + msg, *params)
    sys.exit(1)

class Votes:
    def __init__(self, array):
        self.set = set(array)

    def update(self, o):
        self.set.update(o.set)

    def empty(self):
        return not len(self.set)

    def __nonzero__(self):
        return len(self.set)

    def __iter__(self):
        return self.set.__iter__()

    def intersection(self, o):
        if isinstance(o, set):
            return self.set.intersection(o)
        return self.set.intersection(o.set)

    def difference(self, o):
        if isinstance(o, set):
            return self.set.difference(o)
        return self.set.difference(o.set)

    def checkForMissing(self, attending, type, name):
        wrong = self.difference(attending)
        if wrong:
            fail("[{}] in {} not present during voting {}"
             , ", ".join(map(lambda x: str(x), wrong)), type, name)

    def __repr__(self):
        return "Votes({})".format(self.set)

class VoteCollection:
    def __init__(self, yea, nay, present):
        self.yea = yea
        self.nay = nay
        self.present = present

    def mask(self):
        return "".join(("Y" if self.yea else "0"
                        , "N" if self.nay else "0"
                        , "P" if self.present else "0"))

    def checkForOverlap(self):
        if self.yea.intersection(self.nay):
            fail("yeas share some votes with nays in "
                 "voting '{}'", self.name)

        if self.yea.intersection(self.present):
            fail("yeas share some votes with presents in "
                 "voting '{}'", self.name)

        if self.nay.intersection(self.present):
            fail("nays share some votes with presents in "
                 "voting '{}'", self.name)

    def checkForMissing(self, name, attending):
        self.yea.checkForMissing(attending, "yeas", name)
        self.nay.checkForMissing(attending, "nay", name)
        self.present.checkForMissing(attending, "present", name)

    def area(self, apts):
        return VoteCollection(apts.area(self.yea)
                              , apts.area(self.nay)
                              , apts.area(self.present))

    def __repr__(self):
        return ("Votes([+] {}, [-] {}, [!] {})"
                .format(self.yea, self.nay, self.present))

    def __div__(self, divisor):
        return VoteCollection(float(self.yea) / float(divisor)
                              , float(self.nay) / float(divisor)
                              , float(self.present) / float(divisor))

    def __mul__(self, multiplier):
        return VoteCollection(float(self.yea) * float(multiplier)
                              , float(self.nay) * float(multiplier)
                              , float(self.present) * float(multiplier))


# ------------------------------------------------------------------------
# Grammar

from pyparsing import Word, nums, alphas, ZeroOrMore, OneOrMore
from pyparsing import Literal, Keyword, ParserElement, SkipTo, Combine
from pyparsing import stringEnd, delimitedList, restOfLine, Group, Optional
from pyparsing import ParseResults

from attendance import Attendance, Checkpoint, gCheckPoint
from attendance import integerList, integer

ParserElement.setDefaultWhitespaceChars("\t ")

varValue = (restOfLine.copy()).setParseAction(lambda s, l, t: [t[0].strip()])

percent = (integer + '%')

nameParam = ((Keyword("Name") + '=' + varValue)
             .setParseAction(lambda s, l, t: t[2]))

def processQuorum(s, l, t):
    return t[2] if len(t) < 6 else -t[2]

quorumParam = ((Keyword("Quorum") + '=' + percent
                + Optional(Keyword("of") + Keyword("all")))
               .setParseAction(processQuorum))

comment = (Literal("#") + restOfLine).suppress()

gYea = ((Literal("+").suppress() + integerList)
        .setParseAction(lambda s, l, t: [Votes(t)]))
gNay = ((Literal("-").suppress() + integerList)
        .setParseAction(lambda s, l, t: [Votes(t)]))
gPresent = ((Literal("!").suppress() + integerList)
            .setParseAction(lambda s, l, t: [Votes(t)]))

checkpoint = (Literal("@").suppress() + gCheckPoint)
newline = Literal("\n").suppress()

attrs = (ZeroOrMore(nameParam.setResultsName("name")
                    ^ quorumParam.setResultsName("quorum")
                    ^ gYea.setResultsName("yea", True)
                    ^ gNay.setResultsName("nay", True)
                    ^ gPresent.setResultsName("present", True)
                    ^ comment
                    ^ newline))
# ------------------------------------------------------------------------


def join(record, key):
    sets = record.get(key, None)
    if sets is None:
        return Votes(set())

    out = sets[0][0]
    for s in sets[1:]:
        out.update(s[0])
    return out

class Voting:
    def __init__(self, record):
        self.checkpoint = record["checkpoint"][0]
        self.name = record["name"]
        self.quorum = record["quorum"]
        if self.quorum < 0:
            self.quorum = -self.quorum
            self.all = True
        else:
            self.all = False

        self.votes = VoteCollection(join(record, "yea")
                                    , join(record, "nay")
                                    , join(record, "present"))

        mask = self.votes.mask()

        if mask == "YNP":
            fail("You have to specify up to 2 vote types in "
                 "voting '{}'", self.name)

        self.votes.checkForOverlap()

        self.processImpl = getattr(self, "process" + mask)


    def __repr__(self):
        return ("Voting(@{}, '{}', {}% of {}, {})"
                .format(self.checkpoint, self.name, self.quorum
                        , "all" if self.all else "present"
                        , self.votes))

    def process(self, apts, attendance):
        attending = attendance.get(self.checkpoint)

        self.votes.checkForMissing(self.name, attending)

        totalArea = apts.total
        attendingArea = apts.area(attending)
        missingArea = totalArea - attendingArea
        missingAreaPercentage = float(100 * missingArea) / float(totalArea)

        print >> sys.stderr, attending
        print >> sys.stderr, "input:", self.votes
        votes = self.processImpl(attending)
        print >> sys.stderr, "deduced:", votes
        area = votes.area(apts)

        base = totalArea if self.all else attendingArea
        percentage = (area * 100) / base

        print >> sys.stderr
        print yellow(self.checkpoint), self.name
        print

        quorate = (float(attendingArea) / totalArea) > 0.5

        print ("Quorum : {}% {}"
               .format(self.quorum, "of all" if self.all else ""))
        print "Quorate: {}".format(green("Yes") if quorate else red("NO!"))
        print "Yea    : {}\t {:5.2f}%".format(area.yea, percentage.yea)
        print "Nay    : {}\t {:5.2f}%".format(area.nay, percentage.nay)
        print "Present: {}\t {:5.2f}%".format(area.present, percentage.present)

        if self.all:
            print ("Missing: {}\t {:5.2f}%"
                   .format(missingArea, missingAreaPercentage))

        if not quorate:
            print "Result : {}".format(red("NOT QUORATE"))
        elif (percentage.yea > self.quorum):
            print "Result : {}".format(green("PASSED"))
        else:
            print "Result : {}".format(red("NOT PASSED"))

    def generate(self, apts, attendance):
        class Record:
            def __init__(self, **kwds):
                for name, value in kwds.items():
                    setattr(self, name, value)

            def isAttending(self, apt):
                return apt in self.attending

            def vote(self, apt):
                if apt in self.votes.yea:
                    return "YEA"
                elif apt in self.votes.nay:
                    return "NAY"
                elif apt in self.votes.present:
                    return "PRESENT"
                else:
                    return "MISSING"

            def passed(self):
                return (percentage.yea > self.quorum)

        attending = attendance.get(self.checkpoint)

        self.votes.checkForMissing(self.name, attending)

        totalArea = apts.total
        attendingArea = apts.area(attending)
        missingArea = totalArea - attendingArea
        missingAreaPercentage = float(100 * missingArea) / float(totalArea)

        votes = self.processImpl(attending)
        area = votes.area(apts)

        base = totalArea if self.all else attendingArea
        percentage = (area * 100) / base
        quorate = (float(attendingArea) / totalArea) > 0.5

        return Record(attending=attending
                      , totalArea=totalArea
                      , missingArea=missingArea
                      , missingAreaPercentage=missingAreaPercentage
                      , votes=votes
                      , area=area
                      , base=base
                      , percentage=percentage
                      , quorate=quorate
                      , quorum=self.quorum
                      , all=self.all)

    def processYN0(self, attending):
        # yea = given
        # nay = given
        # present = attending - yea - nay
        return VoteCollection(self.votes.yea
                              , self.votes.nay
                              , (attending.difference(self.votes.yea)
                                 .difference(self.votes.nay)))

    def processY00(self, attending):
        # yea = given
        # nay = attending - yea
        # present = empty
        return VoteCollection(self.votes.yea
                              , attending.difference(self.votes.yea)
                              , set())

    def process0N0(self, attending):
        # yea = attending - nay
        # nay = given
        # present = empty
        return VoteCollection(attending.difference(self.votes.nay)
                              , self.votes.nay
                              , set())

    def process0NP(self, attending):
        # yea = attending - nay - present
        # nay = given
        # present = given
        return VoteCollection((attending.difference(self.votes.nay)
                               .difference(self.votes.present))
                              , self.votes.nay
                              , self.votes.present)

    def processY0P(self, attending):
        # yea = given
        # nay = attending - yea - present
        # present = given
        return VoteCollection(self.votes.yea
                              , (attending.difference(self.votes.yea)
                                 .difference(self.votes.present))
                              , self.votes.present)

    def process00P(self, attending):
        # yea = attending - present
        # nay = empty
        # present = given
        return VoteCollection(attending.difference(self.votes.present)
                              , set()
                              , self.votes.present)

    def process000(self, attending):
        # yea = attending
        # nay = empty
        # present = empty
        return VoteCollection(attending, set(), set())

gVoting = ((checkpoint.setResultsName("checkpoint") + attrs)
           .setParseAction(lambda s, l, t: [Voting(t)]))

gVotings = ZeroOrMore(gVoting)

def parseVotings(file):
    return (gVotings + stringEnd).parseFile(file)

if __name__ == "__main__":
    import argparse

    parser = (argparse.ArgumentParser
              (description="Voting evaluator.", add_help=True))
    parser.add_argument("apartments", type=file)
    parser.add_argument("attendance", type=file)
    parser.add_argument("votes", type=file)
    parser.add_argument("--last", action="store_true")

    args = parser.parse_args()

    attendance = Attendance(args.apartments, args.attendance)

    #gVotings.setDebug()
    votings = (gVotings + stringEnd).parseFile(args.votes)

    if args.last and len(votings):
        votings = votings[-1:]

    for voting in votings:
        print
        print ("===================================="
               "====================================")
        voting.process(attendance.apts, attendance.attendance)
        print ("===================================="
               "====================================")
