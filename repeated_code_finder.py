from collections import defaultdict, namedtuple
from copy import copy
from itertools import combinations
import sys
from terminaltables import AsciiTable
from hashlib import sha1

# TODO:
    # sort-ability? (e.g. by len, # of occurrances, etc.?)

MatchingChunk = namedtuple("MatchingChunk", ["hashpattern", "lines1", "lines2"])
# where 'hashpattern' is a list of hashes (representing the sequence of lines), and 'lines1' and 'lines2' are lists of line #'s
    # e.g. line list [1,2,3,4] means that this hashpattern occurs at lines 1-4.
MIN_LENGTH = 3 # min. number of sequential identical lines that will be counted
MIN_OCCURRANCES = 2 # min. number of times a repeated chunk has to occur to be counted

# get filename from command line arguments
args = sys.argv[:]
script = args.pop(0)
filename = args.pop(0)

def make_dicts(f):
    """Makes dicts of the input file:
        1. hash_to_lines -- k = content hash (hash of line of content); v = list of line #s
            at which the content-line occurs
        2. lines_to_hash -- k = line #; v = hash of content occuring at that line.
        3. hash_to_content -- k = content hash; v = original content."""
    hash_to_lines = defaultdict(list)
    lines_to_hash = dict()
    hash_to_content = dict()
    with open(f) as infile:
        for i, line in enumerate(infile):
            # TODO: ignore comments, whitespace, etc.?
            line = line.strip()
            content_hash = sha1(line).hexdigest()
            hash_to_lines[content_hash].append(i+1)
            lines_to_hash[i+1] = content_hash
            hash_to_content[content_hash] = line
    return hash_to_lines, lines_to_hash, hash_to_content

def find_repeats(content_dict, line_dict):
    """Given a content-to-line and line-to-content dict., returns a dict. with k = list of
        sequential content-hashes and v = list of line ranges where that sequence of
        content-lines occurs.

    (A line range is a list of lines. E.g. [[1,2,3], [5,6,7]] indicates lines 1-3 and 5-7.)"""
    results = defaultdict(list)
    for line_list in [v for v in content_dict.itervalues() if len(v)>1]:
    # line_list = list of line #s at which a given content-line occurs.
    # (only returns a line_list for content-lines that occur more than once)
        for first, rest in first_rest(line_list):
            for line_no in rest:
                match = matching_streak(first, line_no, line_dict)
                if len(match.hashpattern) >= MIN_LENGTH:
                    add_match_to_results(match, results) # THIS IS NOT FUNCTIONAL PROGRAMMING GAAH
    return results

def add_match_to_results(match, res):
    """Expects a Match and a defaultdict(list). Adds that match to the given dict, with
        k = list of sequential content-hashes and v = list of line ranges where that
        sequence of content-lines occurs."""
    if tuple(match.hashpattern) not in res: # hash pattern not yet in results dict.
        res[tuple(match.hashpattern)].extend([match.lines1, match.lines2])
    else:
        if match.lines1 not in res[tuple(match.hashpattern)]:
            # if the first set of lines isn't in results, then NEITHER is... right?
            res[tuple(match.hashpattern)].extend([match.lines1, match.lines2])
        elif match.lines2 not in res[tuple(match.hashpattern)]: # first set of lines in results dict., but second set isn't.
            res[tuple(match.hashpattern)].append(match.lines2)

def remove_redundancies(repeats_dict):
    """Given a dict of repeated chunks and where they occur, remove redundancies
        (repeated-line chunks that only exist as subsets of other repeated-line chunks.)"""

    clean_dict = copy(repeats_dict)

    for pair in combinations(repeats_dict.keys(), 2): # check every pair of entries
        if is_redundant(repeats_dict[pair[0]], repeats_dict[pair[1]]):
            if len(repeats_dict[pair[0]][0]) > len(repeats_dict[pair[1]][0]): # if the first is the longer
                clean_dict.pop(pair[1], None) # delete the shorter
            else:
                clean_dict.pop(pair[0], None)

    return clean_dict

def format_table(d, content_dict):
    table_data = [["Content", "# Lines", "Line no.'s", "# Times"]]
    for hashlist, lineslist in d.iteritems():
        orig_content = "\n".join(content_dict[hash] for hash in hashlist)
        num_of_lines = str(len(hashlist))
        row_list = ", ".join(["%s-%s" % (lines[0], lines[-1]) for lines in lineslist])
        num_of_occurrances = str(len(lineslist))
        table_data.append([orig_content, num_of_lines, row_list, num_of_occurrances])
        table_data.append(["-----","-----","-----","-----"])

    table = AsciiTable(table_data)
    return table.table

def matching_streak(i, j, line_dict):
    """Given two starting indeces, step through content one line at a time from each until
        content no longer matches. Return the longest match (list of line-hashes and the
        two line-ranges at which it occurs.)"""
    matching = True
    match = MatchingChunk([],[],[])
    while matching:
        try:
            if line_dict[i] == line_dict[j]:
                match.hashpattern.append(line_dict[i])
                match.lines1.append(i)
                match.lines2.append(j)
                i += 1
                j += 1
            else:
                matching = False
        except KeyError: # catches case in which you fall off the end of the file (i.e. look in dict. for nonexistant line #)
            # DANGER, WILL ROBINSON -- might be other reasons you'd get a key error!
            matching = False
    return match

def is_redundant(line_list1, line_list2):
    """Given two lists of line ranges (lists of lists), finds if redundant.
        If all line ranges from one list fit inside all line ranges from the other,
        the two are redundant.
    E.g. [[1,2,3], [5,6,7], [10,11,12]] is redundant with [[1,2,3,4], [4,5,6,7], [9,10,11,12]]"""

    if len(line_list1) != len(line_list2): # if we have a different number of line ranges,
        # we know they are not perfectly redundant (i.e. not all instances of the smaller
        # occur within instances of the larger...)
        return False

    # otherwise, we compare the first elem. of each -- if one fits within the other, we know
        # the line range lists are redundant.
    line_list1.sort()
    line_list2.sort()
    compare1 = set(line_list1[0])
    compare2 = set(line_list2[0])

    return compare1.issubset(compare2) or compare2.issubset(compare1)

def first_rest(li):
    """Returns (first, rest) for all possible slices [n:] of given list li."""
    for i in xrange(len(li)-1):
        yield li[i], li[i+1:]

def apply_results_floor(d, floor):
    """Given a dictionary d, remove all entries with less than (floor) values."""
    output = copy(d)
    for k, v in d.iteritems():
        if len(v) < floor:
            del output[k]
    return output

if __name__ == '__main__':
    hash_to_lines, lines_to_hash, hash_to_content = make_dicts(filename)

    all_repeats = find_repeats(hash_to_lines, lines_to_hash)
    all_repeats = apply_results_floor(all_repeats, MIN_OCCURRANCES)
    clean_dict = remove_redundancies(all_repeats)

    print format_table(clean_dict, hash_to_content)