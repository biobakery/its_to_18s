import os
import sys
import bz2
import base64
import logging
import optparse
import contextlib
import cPickle as pickle
from operator import truth
from collections import defaultdict
from itertools import chain, izip_longest, takewhile

from . import db

logger = logging.getLogger(__name__)

class AccessionCache(object):
    def __init__(self, maxsize):
        self._cache = defaultdict(list)
        self.maxsize = maxsize


    def add(self, taxonomy_str, accession_str):
        self._cache[taxonomy_str].append(accession_str)

    def get_smallest_keys(self, n):
        return [
            key for (key, value) in
            sorted(self._cache.iteritems(), key = lambda kv: len(kv[0]))[:n]
        ]

    def flush(self, ldb, n=None):
        if not n:
            n = int(self.maxsize*.9)
        to_flush = self.get_smallest_keys(n)
        self._flush_keys(ldb, to_flush)
        
    def flushall(self, ldb):
        self._flush_keys(ldb, self._cache.iterkeys())

    def _flush_keys(self, ldb, keys):
        for key in keys:
            val = self._cache.pop(key)
            try:
                existing = ldb.Get(key)
            except KeyError:
                ldb.Put(key, pickle.dumps(val))
            else:
                existing_collection = pickle.loads(existing)
                ldb.Put(key, pickle.dumps(existing_collection+val))



def fasta_sequences(seqs_f):
    id = None
    lines = iter(seqs_f)
    line = next(lines).strip()
    while True:
        if line.startswith(">"):
            id, rest = line.split(None, 1)
            id = id.replace(">", "")
            line = next(lines).strip()
        else:
            seq = str()
            while not line.startswith(">"):
                seq += line
                line = next(lines).strip()
            yield (id, seq)
            id, seq = str(), str()



def partition(iterable, binsize):
    iters = [iter(iterable)]*binsize
    return izip_longest(fillvalue=None, *iters)


def stop_at_false(iterable):
    return takewhile(truth, iterable)


def compress(seq):
    return base64.b64encode(bz2.compress(seq))


def read_and_compress(seqs_f):
    for id, seq in fasta_sequences(seqs_f):
        id = id.split(".", 1)[0]
        yield id, compress(seq)


def accession_fields(mapping_f):
    for line in mapping_f:
        fields = line.strip().split("\t")
        yield fields[0], fields[-1]


def add_seq_to_db(ldb, key, seq):
    seq_collection = [seq]
    ldb.Put(key, pickle.dumps(seq_collection))


def update_seq_db(ldb, key, seq, pickled):
    seq_collection = pickle.loads(pickled)
    seq_collection.append(seq)
    ldb.Put(key, pickle.dumps(seq_collection))


def build_index(db_fname, sequences_fname, *mapping_files):
    is_logging_debug = logger.isEnabledFor(logging.DEBUG)

    binsize = 10000
    ldb = db.new(db_fname)

    logger.info("Step 1: index taxonomy -> accession")
    open_mapping_files = map(open, mapping_files)
    with contextlib.nested(*open_mapping_files):
        mappings = chain.from_iterable(
            map(accession_fields, open_mapping_files))
        chunks = partition(mappings, binsize)
        cache = AccessionCache(binsize+1)
        for i, chunk in enumerate(chunks):
            batch = db.leveldb.WriteBatch()
            for accession, tax in stop_at_false(chunk):
                cache.add(tax, accession)
            cache.flush(ldb)
            ldb.Write(batch, sync=True)
            
            if is_logging_debug and i % 10 == 0:
                logger.debug("Indexed %i taxonomies"%(i*binsize))
        cache.flushall(ldb)

    logger.info("Step 2: index accession -> SSU Sequence")
    with open(sequences_fname) as seqs_f:
        for i, (accession, seq) in enumerate(read_and_compress(seqs_f)):
            try:
                val = ldb.Get(accession)
            except KeyError:
                add_seq_to_db(ldb, accession, seq)
            else:
                update_seq_db(ldb, accession, seq, val)
            if is_logging_debug and i % 10000 == 0:
                logger.debug("Indexed %i sequences"%(i))
            
    logger.info("Complete.")


HELP = """%prog <output_db> <sequences.fasta> <taxonomy_map> [<taxonomy_map> [...]]

%prog - Build sequence database linking taxonomies -> accession numbers -> sequences
"""

options = [
    optparse.make_option('-l', '--logging', action="store", type="string",
                         dest="logging", default="INFO",
                         help="Logging verbosity, options are debug, info,"
                         " warning, and critical"),
]


def main(argv):
    opts, args = optparse.OptionParser(
        option_list=options, usage=HELP
    ).parse_args(args=argv)
    
    logger.setLevel(getattr(logging, opts.logging.upper()))

    return build_index(args[0], args[1], *args[2:])



if __name__ == "__main__":
    ret = main(sys.argv[1:])
    sys.exit(ret)
