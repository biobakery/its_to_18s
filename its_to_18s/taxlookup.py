import sys
import base64
import bz2
import optparse
import contextlib
import cPickle as pickle
from itertools import chain

from . import db


def taxonomies(brocc_table_f):
    for line in brocc_table_f:
        yield line.strip().split('\t')[-1]


def deserialize_seq(seq_pickle):
 return [
     bz2.decompress(base64.b64decode(seq_binary))
     for seq_binary in pickle.loads(seq_pickle)
 ]


def deserialize_accessions(acc_pickle):
    return pickle.loads(acc_pickle)


def lookup_seq_init(ldb):
    def lookup_seq(accession_str):
        try:
            val = ldb.Get(accession_str)
        except KeyError:
            raise KeyError("Accession string `{}' "
                           "missing from index".format(accession_str))
        else:
            return deserialize_seq(val)

    return lookup_seq


def lookup_init(ldb, accessions=False):
    lookup_seq = lookup_seq_init(ldb)

    def lookup_acc(accession_str):
        for seq in lookup_seq(accession_str):
            yield (accession_str, seq)
    
    def lookup_tax(taxonomy):
        try:
            accession_collection = deserialize_accessions(ldb.Get(taxonomy))
        except KeyError:
            raise KeyError("Taxonomy %s is not indexed")
        for accession in accession_collection:
            try:
                ss = lookup_seq(accession)
            except KeyError:
                raise IndexError(
                    "Accession {} missing from index".format(accession))
            for seq in ss:
                yield accession, seq


    if accessions:
        return lookup_acc
    else:
        return lookup_tax


def fasta_output(taxonomy, seq_iter):
    record = ">{} {}\n{}\n"
    for accession, seq in seq_iter:
        sys.stdout.write(record.format(accession, taxonomy, seq))


def lookup(index_dir, brocc_tables,
           database_directory=db.default_index_dir,
           accessions=False):
    ldb = db.get(index_dir, datadir=database_directory)
    lookup = lookup_init(ldb, accessions)

    brocc_fs = map(open, brocc_tables)
    with contextlib.nested(*brocc_fs):
        ts = chain.from_iterable(map(taxonomies, brocc_fs))
        for taxonomy in ts:
            try:
                seq_iter = lookup(taxonomy)
                fasta_output(taxonomy, seq_iter)
            except KeyError:
                print >> sys.stderr, "Taxonomy not indexed: "+taxonomy
                continue
            except IndexError as e:
                print >> sys.stderr, str(e)
                continue
            


HELP="""%prog [options] <taxonomy_calls> [<taxonomy_calls> [...]] 

%prog - Retrieve Small subunit sequences as indexed by 
        lineage strings (taxonomy calls)

<taxonomy_calls> - Tab-separated text files with the last column or 
                   field being the taxonomy or lineage string """


options = [
    optparse.make_option(
        '-D', '--data-dir',
        dest="datadir", default=db.default_index_dir,
        action="store", type="string",
        help=("Specify alternate database directory,"
              " default `{}'".format(db.default_index_dir))),
    optparse.make_option(
        '-d', '--db',
        dest="db_name", default=None,
        action="store", type="string",
        help=("Specify which database to use for lookup")),
    optparse.make_option(
        '-a', '--accessions',
        default=False,
        action="store_true", 
        help=("Treat input as accession numbers instead of lineage strings"))
]

def main(argv):
    opts, args = optparse.OptionParser(
        option_list=options, usage=HELP
    ).parse_args(args=argv)
    
    return lookup(opts.db_name, args,
                  database_directory=opts.datadir,
                  accessions=opts.accessions)
            

if __name__ == "__main__":
    ret = main(*sys.argv[1:])
    sys.exit(ret)
