#!/usr/bin/python

# # set time
# @18:00
#
# # in
# 1, 45, 12, 15, 140, 128
# 16, 17
#
# $18:30
# # out
# -128
#
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

from apttools import Apartments

class Checkpoint:
    def __init__(self, hh, mm):
        self.hh = hh
        self.mm = mm
        self.time = hh * 60 + mm

    def __repr__(self):
        return "{:02}:{:02}".format(self.hh, self.mm)

    def __le__(self, o):
        return self.time <= o.time

class Everyone:
    def __repr__(self):
        return "Everyone"

class InOut:
    def __init__(self, array):
        if (len(array) and array[0] == "all"):
            self.set = Everyone()
        else:
            self.set = set(array)
        self.ch = Checkpoint(0, 0)

    def expand(self, apts):
        if (isinstance(self.set, Everyone)):
            # everyone -> just place all apartments here
            self.set = set(apts.keys())

    def checkpoint(self, ch):
        self.ch = ch

class AttendanceIn(InOut):
    def __repr__(self):
        return "In({} @{})".format(self.set, self.ch)

    def __le__(self, o):
        if self.ch < o.ch:
            return True
        if self.ch > o.ch:
            return False
        return isinstance(o, AttendanceOut)

    def update(self, time, res):
        if self.ch <= time: res.update(self.set)

class AttendanceOut(InOut):
    def __repr__(self):
        return "Out({} @{})".format(self.set, self.ch)

    def __le__(self, o):
        if self.ch < o.ch:
            return True
        if self.ch > o.ch:
            return False
        return not isinstance(o, AttendanceIn)

    def update(self, time, res):
        if self.ch <= time: res.difference_update(self.set)

class AttendanceEvaluator:
    def __init__(self, attendance):
        if (not len(attendance)) or (not isinstance(attendance[0], Checkpoint)):
            raise ValueError("Invalid attendance "
                             "(empty or not starting with checkpoint)")

        self.attendance = []
        for p in attendance:
            if isinstance(p, Checkpoint):
                now = p
                continue
            p.checkpoint(now)
            self.attendance.append(p)

    def __repr__(self):
        return "AttendanceEvaluator({})".format(self.attendance)

    def expand(self, apts):
        for e in self.attendance:
            e.expand(apts)

    def get(self, time):
        res = set()
        for e in self.attendance:
            e.update(time, res)

        return res

from pyparsing import Word, nums, ZeroOrMore, OneOrMore
from pyparsing import Literal, ParserElement, SkipTo, Combine
from pyparsing import stringEnd, delimitedList, restOfLine

def debug(s, l, t):
    print "s:", s
    print "l:", l
    print "t:", t
    return t

ParserElement.setDefaultWhitespaceChars("\t ")

comment = (Literal("#") + restOfLine).suppress()

everyone = Literal("all")

integer = Word(nums).setParseAction(lambda s, l, t: [int(t[0])])

doubleInt = Word(nums, exact=2)

integerList = delimitedList(integer).setParseAction(lambda s, l, t: t)

gAttendanceIn = ((Literal("+").suppress() + (integerList | everyone))
               .setParseAction(lambda s, l, t: [AttendanceIn(t)]))
gAttendanceOut = ((Literal("-").suppress() + (integerList | everyone))
                .setParseAction(lambda s, l, t: [AttendanceOut(t)]))

gCheckPoint = ((doubleInt + Literal(":") + doubleInt)
               .leaveWhitespace()
               .setParseAction(lambda s, l, t: [Checkpoint(int(t[0]), int(t[2]))]))

gAttendance = (ZeroOrMore(comment
                        ^ (Literal("@").suppress() + gCheckPoint)
                        ^ gAttendanceIn
                        ^ gAttendanceOut
                        ^ Literal("\n").suppress())
             + stringEnd).setParseAction(lambda s, l, t: AttendanceEvaluator(t))

def checkpoint(value):
    return (gCheckPoint + stringEnd).parseString(value)[0]

class Attendance:
    def __init__(self, apartments, attendance):
        self.apts = Apartments(apartments, [13, 15, 17, 19, 21, 23, 25], 20)
        self.attendance = gAttendance.parseFile(attendance)[0]
        self.attendance.expand(self.apts)

    def __repr__(self):
        return "Attendance({}, {})".format(self.apts, self.attendance)

if __name__ == "__main__":
    import sys, argparse

    parser = (argparse.ArgumentParser
              (description="Attendance counter.", add_help=True))
    parser.add_argument("apartments", type=file)
    parser.add_argument("attendance", type=file)
    parser.add_argument("--time", type=checkpoint
                        , default=Checkpoint(24, 0))

    args = parser.parse_args()

    attendance = Attendance(args.apartments, args.attendance)

    attending = sorted(attendance.attendance.get(args.time))

    totalArea = attendance.apts.total
    totalCount = attendance.apts.count
    attendingArea = attendance.apts.area(attending)
    attendingCount = len(attending)
    missingArea = totalArea - attendingArea
    missingCount = totalCount - attendingCount

    print "{} {} {}".format(totalCount, attendingCount, missingCount)
    print ("attending: {}/{} {:%}"
           .format(attendingArea, totalArea, float(attendingArea) / totalArea))
    print ("missing: {}/{} {:%}"
           .format(missingArea, totalArea, float(missingArea) / totalArea))
    if float(attendingArea) / totalArea > 0.5:
        print green("QUORATE")
    else:
        print red("NOT QUORATE")
