#!/usr/bin/env python
# coding: utf-8
"""
strip_statedept_headers.py -

 Input: Text files output by extract_text_from_pdfs.sh

 Output: Text files w/ State Department classification header/footers removed

"""
import os
import argparse
from glob import glob
import re

# Post-classified header lines to check for directly
# Could do this more efficiently w/ a regex, but electricity is cheap
#HEADER_SKIP_LINES = ['RELEASE IN', 'FULL', 'PART B6', 'B6', 'RELEASE IN PART', 'RELEASE IN PART B6', 'RELEASE IN FULL']
HEADER_SKIP_LINES = []

def clean_and_enumerate(txt):
    """
    Generator to perform some basic REGEX cleaning on each line of text
    Strip trailing classification marks
    :param txt:
    :return:
    """
    for i, line in enumerate(txt):
        # Stagger these so they "cut down" to the next case
        # RELEASE IN PART B4,B5,B6 > RELEASE IN PART > RELEASE IN
        # Ending in B5 or B6 or B5,B6, or B6,B7(C),B7(E),B7(F),B6 etc
        line = re.sub(r'(\s*B\d(\([A-F]\))?,)*\s*B\d(\([A-F]\))?$', '', line)
        # Ending in FULL or PART
        line = re.sub(r'\s*(FULL|PART)$', '', line)
        line = re.sub(r'\s*(RELEASE IN)$', '', line)
        yield i, line



def remove_headers(in_txt):
    """
    Remove the FOIA header/footer lines
    :param in_txt: OCR text extracted from PDFs. Assumed -layout option was used.
    :return: text with FOIA headers and footers removed
    """

    # Sanity check document starts as expected
    if not re.match('UNCLASSIFIED', in_txt[0]):
        print "NOOOOOO"
        print in_txt[0]
        return []


    #line_iterator = enumerate(in_txt)
    line_iterator = clean_and_enumerate(in_txt)
    otxt = []

    for idx, line in line_iterator:
        # Actually want this to run an additional time AFTER passing through regexes
        # Because of how wonky our iterators are, it ends up living here
        # Also check exceptions to make sure we didn't go outside the file
        try:
            # Note: removed empty linebreak from list to maintain readability
            while line in HEADER_SKIP_LINES:
                idx, line = next(line_iterator)
        except StopIteration:
            continue

        # Check if it's the newer single-line header
        m = re.match('UNCLASSIFIED U.S. Department of State Case No. (F-\d\d\d\d-\d*) Doc No. (C\d*) Date: (\d\d/\d\d/\d\d\d\d)', line)
        if m is not None:
            #caseno = m.group(1)
            #docno = m.group(2)
            #date = m.group(3)
            continue
        # Check for start of Benghazi format
        # Footer, subsequent headers are a plain "UNCLASSIFIED"
        m = re.match('UNCLASSIFIED\s*STATE DEPT. - PRODUCED TO HOUSE SELECT BENGHAZI COMM.', line)
        if m is not None or line == "UNCLASSIFIED":
            for regex in ['U.S. Department of State', 'Case No.', 'Doc No.', 'Date']:
                #print "REGEX TEST: %s" % regex
                idx, line = next(line_iterator)
                # Cycle through any incorrect line breaks introduced into header during OCR
                while line in [''] + HEADER_SKIP_LINES:
                    #print "empty line in header section"
                    idx, line = next(line_iterator)
                m = re.match(regex, line)
                if m is None:
                    # Something is screwed up, we didn't match the expected following header lines
                    print "HEADER PROBLEM Line %s: %s" % (idx, line)
                    return []
            continue  # don't store the Date:!

        # Otherwise, assume it's a normal line and return it
        otxt.append(line)

    return otxt



def main():

    args = parse_options()
    #ifile = args.json_results
    out_dir = args.out_dir
    input_glob = args.input_glob

    # Track some things
    header_problem_files = []

    for fname in glob(input_glob):
    #for fname in glob(input_glob)[:200]:
    #for fname in glob(input_glob)[-2000:]:

        basename = os.path.splitext(os.path.basename(fname))[0]
        oname = os.path.join(out_dir, basename+".txt")

        # Read in the file and strip leading, trailing whitespace
        txt = [line.strip() for line in open(fname)]

        print "{} {} {}".format(fname, oname, len(txt))

        raw_txt = remove_headers(txt)

        if len(raw_txt) == 0:
            header_problem_files.append(fname)
            continue

        #Output the file
        with open(oname, 'w') as fout:
            fout.write("\n".join(raw_txt))

    # Report what we collected
    print "Files with header issues (%s)" % len(header_problem_files)
    for fname in header_problem_files:
        print fname




def parse_options():
     parser = argparse.ArgumentParser(description='Clean Header/Footers of text emails')
     parser.add_argument('-o', '--out_dir', dest='out_dir', action="store", metavar="DIR", required=True)
     parser.add_argument('-f', '--files', dest='input_glob', action="store", metavar="GLOB", required=True)

     return parser.parse_args()

if __name__ == '__main__':
    main()


