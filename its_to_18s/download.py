import re
import sys
import string

from toolz import pluck

from brocclib.get_xml import get_lineage
from brocclib.taxonomy import Lineage

fields = lambda f: iter(map(string.strip, l.split('\t')) for l in f)
isnumeric = re.compile(r'\d+').match

standard = lambda d: ";".join( Lineage(d).get_standard_taxa("species") )
full = lambda d: ";".join( Lineage(d).get_all_taxa("species") )

def get_lin(line):
    if all(( type(line) in (tuple, list),
             len(line) >=5,
             isnumeric(line[-1]) )):
        return get_lineage(line[-1])
           

def main(out_standard, out_full, cont_=None):
    with open(out_standard, 'w') as out_s, open(out_full, 'w') as out_f:
        fs = fields(sys.stdin)
        for line in fs:
            if cont_ is not None and line[-1] != cont_:
                continue
            elif cont_ is not None and line[-1] == cont_:
                cont_ = None

            try:
                lineage = get_lin(line)
                print >> out_s, "\t".join(line + [standard(lineage)])
                print >> out_f, "\t".join(line + [full(lineage)])
            except Exception as e:
                print >> sys.stderr, "Couldn't get %s: %s"%(line[0], str(e))
                continue
            print >> sys.stderr, "finished %s"%(line[0])

if __name__ == "__main__":
    ret = main(*sys.argv[1:])
    sys.exit(ret)
