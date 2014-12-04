from collections import defaultdict, namedtuple
import sys
from hashlib import sha1

# next:
    # display # of occurances
    # table view
    # include the duplicated text from the orig. file?
    # IGNORE REDUNDANCIES! E.g. ABCDEF is repeated, don't also record CDEF
        # (unless there are many more cdef's than abcdef??)

MatchingChunk = namedtuple("MatchingChunk", ["pattern", "lines1", "lines2"])
MIN_LENGTH = 5 # minimum number of sequential identical lines that will be counted
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
        for first, rest in first_rest(line_list):
            # print first, rest
            for line_no in rest:
                match = matching_streak(first, line_no, line_dict)
                if len(match.pattern) >= MIN_LENGTH:
                    results = add_match_to_results(match, results)
    return results

def matching_streak(i, j, line_dict):
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
    if tuple(m.pattern) not in res:
        res[tuple(m.pattern)].extend([m.lines1, m.lines2])
    else:
        if m.lines1 not in res[tuple(m.pattern)]:
            res[tuple(m.pattern)].extend([m.lines1, m.lines2])
        else:
            res[tuple(m.pattern)].append(m.lines2)
    return res

def readable_results(res):
    output = ["You have repeated chunks at:"]
    for val in res.values():
        output_str = "Lines"
        for lines in val:
            output_str = "%s %s-%s," % (output_str, lines[0], lines[-1])
        output_str = "%s (%d lines long)" % (output_str[:-1], int(val[0][-1])-int(val[0][0]))
        output.append(output_str)
    return "\n".join(output)

content_to_lines, lines_to_content = make_dicts(filename)

d = find_repeats(content_to_lines, lines_to_content)
print readable_results(d)

