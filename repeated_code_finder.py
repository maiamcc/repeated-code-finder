from collections import defaultdict, namedtuple
from copy import copy
from itertools import combinations
import sys
from hashlib import sha1

# next:
    # display # of occurances
    # table view
    # include the duplicated text from the orig. file?
    # IGNORE REDUNDANCIES! E.g. ABCDEF is repeated, don't also record CDEF
        # (unless there are many more cdef's than abcdef??)

MatchingChunk = namedtuple("MatchingChunk", ["pattern", "lines1", "lines2"])
# where 'pattern' is a list of hashes (representing the sequence of lines), and 'lines1' and 'lines2' are lists of line no's
    # e.g. line list [1,2,3,4] means that this pattern occurs at lines 1-4.
MIN_LENGTH = 3 # minimum number of sequential identical lines that will be counted
args = sys.argv[:]
script = args.pop(0)
filename = args.pop(0)

def make_dicts(f):
    content_to_lines = defaultdict(list)
    lines_to_content = dict()
    with open(f) as infile:
        for i, line in enumerate(infile):
            # TODO: ignore comments, whitespace, etc.?
            line = line.strip()
            content_to_lines[sha1(line).hexdigest()].append(i+1)
            lines_to_content[i+1] = sha1(line).hexdigest()
    return content_to_lines, lines_to_content

def find_repeats(content_dict, line_dict):
    results = defaultdict(list)
    for line_list in [v for v in content_dict.itervalues() if len(v)>1]:
    # line_list = list of line no's at which a given content-line occurs
    # (only returns a line_list for content-lines that occur more than once)
        for first, rest in first_rest(line_list):
            for line_no in rest: # compare every line to every other line
                match = matching_streak(first, line_no, line_dict)
                if len(match.pattern) >= MIN_LENGTH:
                    results = add_match_to_results(match, results)
    return results

def matching_streak(i, j, line_dict):
    """Given two starting indeces, step through content one line at a time from each until content no longer matches.
        Return the longest match (list of line-hashes and the two line-ranges at which it occurs.)"""
    matching = True
    match = MatchingChunk([],[],[])
    while matching:
        try:
            if line_dict[i] == line_dict[j]:
                match.pattern.append(line_dict[i])
                match.lines1.append(i)
                match.lines2.append(j)
                i += 1
                j +=1
            else:
                matching = False
        except KeyError: # DANGER, WILL ROBINSON
            matching = False
    return match

def first_rest(li):
    """Returns (first, rest) for all possible slices [n:] of given list."""
    for i in xrange(len(li)-1):
        yield li[i], li[i+1:]

def add_match_to_results(m, res):
    """Expects a Match and a defaultdict(list)"""
    if tuple(m.pattern) not in res:
        res[tuple(m.pattern)].extend([m.lines1, m.lines2])
    else:
        if m.lines1 not in res[tuple(m.pattern)]:
            res[tuple(m.pattern)].extend([m.lines1, m.lines2])
        elif m.lines2 not in res[tuple(m.pattern)]:
            res[tuple(m.pattern)].append(m.lines2)
        else:
            pass
    return res # a little weird to return it, you're modifying it...

def readable_results(res):
    output = ["You have repeated chunks at:"]
    for val in res.values():
        output_str = "Lines"
        for lines in val:
            output_str = "%s %s-%s," % (output_str, lines[0], lines[-1])
        output_str = "%s (%d lines long)" % (output_str[:-1], int(val[0][-1])-int(val[0][0])+1)
        output.append(output_str)
    return "\n".join(output)

def remove_redundancies(repeats_dict):
    clean_dict = copy(repeats_dict)

    count = 0
    for pair in combinations(repeats_dict.keys(), 2):
        if is_redundant(repeats_dict[pair[0]], repeats_dict[pair[1]]):
            if len(repeats_dict[pair[0]][0]) > len(repeats_dict[pair[1]][0]): # if the first is the longer
                clean_dict.pop(pair[1], None) #delete the shorter
            else:
                clean_dict.pop(pair[0], None)
            count += 1

    return clean_dict

def is_redundant(line_list1, line_list2):
    # if all line ranges from lines1 fit inside all line ranges from lines2, return true
    # else, false
    # e.g. [[1,2,3], [5,6,7], [10,11,12]] is redundant with [[1,2,3,4], [4,5,6,7], [9,10,11,12]]
    if len(line_list1) != len(line_list2):
        return False

    line_list1.sort()
    line_list2.sort()
    compare1 = set(line_list1[0])
    compare2 = set(line_list2[0])

    return compare1.issubset(compare2) or compare2.issubset(compare1)

content_to_lines, lines_to_content = make_dicts(filename)

all_repeats = find_repeats(content_to_lines, lines_to_content)

clean_dict = remove_redundancies(all_repeats)

for k, v in all_repeats.iteritems():
    print k, v

print "here are all of your repeats:\n", readable_results(all_repeats)
print "here are only the non-redundant ones:\n", readable_results(clean_dict)

# check out pylint similarity checker
