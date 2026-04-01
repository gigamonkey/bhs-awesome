#!/usr/bin/env python

"""Extract a json key from a MCQs file"""

import re
import json
from argparse import ArgumentParser
from sys import stderr, stdout

from lxml import etree

def process_file(filename):

    answers = []

    tree = etree.parse(filename)
    qs = tree.xpath('/mcqs/mcq')

    for q in qs:
        correct = q.xpath('answers/item[@correct="true"]')

        if len(correct) == 0:
            answers.append({ "answer": "" })
        elif len(correct) == 1:
            answers.append({ "answer": text(correct[0]) })
        else:
            answers.append({ "answer": [text(c) for c in correct] })

    json.dump(answers, fp=stdout, indent=2)


def text(e):
    s = etree.tostring(e, method="text", encoding="unicode")
    return re.sub(r'\s+', ' ', s.strip())


if __name__ == "__main__":
    parser = ArgumentParser(prog="extract_key", description=__doc__)

    parser.add_argument("file", help="MCQ file")

    args = parser.parse_args()

    process_file(args.file)
