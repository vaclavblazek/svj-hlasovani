#!/usr/bin/python
# -*- coding: utf-8 -*-
from voting import Attendance, parseVotings

if __name__ == "__main__":
    import argparse

    parser = (argparse.ArgumentParser
              (description="Voting evaluator.", add_help=True))
    parser.add_argument("apartments", type=file)
    parser.add_argument("attendance", type=file)
    parser.add_argument("votes", type=file)

    args = parser.parse_args()

    attendance = Attendance(args.apartments, args.attendance)

    votings = parseVotings(args.votes)

    results = map(lambda v: v.generate(attendance.apts, attendance.attendance)
                  , votings)

    names = {"YEA":       "pro"
             , "NAY":     "proti"
             , "PRESENT": "zdržel se"
             , "MISSING": "" } #nepřítomen"}

    rows = []

    def generateHeader():
        row = ["jednotka", "hlas"]
        for index in xrange(1, len(results) + 1):
            row.append("{}.".format(index))
            row.append("")
        return row

    rows.append(generateHeader())

    for apt in attendance.apts.keys():
        row = [str(apt), str(attendance.apts[apt].area)]
        for result in results:
            row.append("přítomen" if (apt in result.attending)
                       else "nepřítomen")
            row.append(names[result.vote(apt)])

        rows.append(row)

    def voteRow(prefix, getters):
        row = list(prefix)
        for result in results:
            for getter in getters:
                if getter is None:
                    row.append("")
                    continue

                value = getter(result)
                if value is None:
                    row.append("")
                elif isinstance(value, str):
                    row.append(value)
                elif isinstance(value, float):
                    row.append("{:.2f} %".format(value))
                else:
                    row.append("{}".format(value))
        return row

    rows.append([])

    rows.append(voteRow(("pro:", ""), [lambda x: x.area.yea
                                       , lambda x: x.percentage.yea]))
    rows.append(voteRow(("proti:", ""), [lambda x: x.area.nay
                                         , lambda x: x.percentage.nay]))
    rows.append(voteRow(("zdržel se:", ""), [lambda x: x.area.present
                                             ,lambda x: x.percentage.present]))
    rows.append(voteRow(("nepřítomen:", "")
                        , [lambda x: x.missingAreaPercentage if x.all else None
                           , lambda x: x.missingArea if x.all else None]))
    rows.append(voteRow(("kvórum:", ""), [lambda x: float(x.quorum), None]))
    rows.append(voteRow(("základ:", ""),
                        [lambda x: "všichni" if x.all else "přítomní"
                         , None]))
    rows.append(voteRow(("schváleno:", "")
                        , [lambda x: "ano" if x.passed() else "ne"
                           , None]))

    for row in rows:
        print "\t".join(row)
