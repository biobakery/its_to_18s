import os
import shutil
import tarfile
import optparse
from collections import OrderedDict

import leveldb

from .exceptions import UserError

here = os.path.abspath(os.path.dirname(__file__))
default_index_dir = os.path.join(here, "..", "indexes")
if not os.path.exists(default_index_dir):
    try:
        os.mkdir(default_index_dir)
    except OSError as e:
        msg = ("Unable to create default index "
               "directory `{}'. Specify your"
               " own directory.")
        print >> sys.stderr, str(e)
        print >> sys.stderr, msg.format(default_index_dir)


_available_dbs = OrderedDict()

def available_dbs(datadir=default_index_dir):
    global _available_dbs
    if datadir not in _available_dbs:
        fulldirs = [ os.path.join(datadir, d) for d in os.listdir(datadir) ]
        paths = filter(os.path.isdir, fulldirs)
        _available_dbs[datadir] = OrderedDict([
            (os.path.basename(bigpath), os.path.abspath(bigpath))
            for bigpath in paths
        ])
    return _available_dbs[datadir]


def get(db_str=None, datadir=default_index_dir, **kwargs):
    if not db_str:
        default_str = next(available_dbs(default_index_dir).itervalues())
        return leveldb.LevelDB(default_str, **kwargs)
    if os.path.isdir(db_str):
        return leveldb.LevelDB(db_str, **kwargs)
    elif db_str in available_dbs(datadir=datadir):
        return leveldb.LevelDB(_available_dbs[datadir][db_str], **kwargs)
    elif db_str in available_dbs():
        return leveldb.LevelDB(
            _available_dbs[default_index_dir][db_str],
            **kwargs
        )
    else:
        raise ValueError("Unable to find database `%s'"%(db_str))
    

def format_tree_2deep(tree_dict):
    msg = ""
    for name, path in tree_dict.iteritems():
        msg += "{:<30}\t{}\n".format(name, path)
    return msg


def list_cmd(argv):
    HELP = "List available databases"

    options = [
        optparse.make_option('-d', '--data-dir',
                             dest="datadir", default=default_index_dir,
                             action="store", type="string",
                             help=("Specify alternate database directory,"
                                   " default `{}'".format(default_index_dir)))
    ]
    (opts, args) = optparse.OptionParser(
        option_list=options, usage=HELP
    ).parse_args(args=argv)

    dbs = available_dbs(datadir=opts.datadir)
    print "Available databases for data directory `{}':".format(opts.datadir)
    print format_tree_2deep(dbs)


def guess_type(fname):
    if os.path.isdir(fname):
        return "directory"
    else:
        return "tarball"


def add_tarball(fname, datadir=default_index_dir):
    with tarfile.open(fname, 'r:*') as tfile:
        tfile.extractall(datadir)


def add_directory(fname, link=False, datadir=default_index_dir):
    fname = fname.rstrip('/')
    if link:
        destdir = os.path.join(datadir, os.path.basename(fname))
        os.symlink(os.path.abspath(fname), destdir)
    else:
        shutil.copytree(fname, os.path.join(datadir, os.path.basename(fname)))


importer_map = {
    "tarball": add_tarball,
    "directory": add_directory,
}


def add(fname, type=None, link=False, datadir=default_index_dir):
    if not type:
        type = guess_type(fname)

    if type == "tarball" and link is True:
        raise UserError("Cannot link a tarball; Unpack first "
                            "and add the directory")

    if type not in importer_map:
        raise UserError("Unrecognized database type: `{}'".format(type))

    if link is True:
        return importer_map[type](fname, link, datadir=datadir)
    else:
        return importer_map[type](fname, datadir=datadir)


def add_cmd(argv):
    HELP = "Add database directory or tarball to available databases"

    options = [
        optparse.make_option(
            '-d', '--data-dir',
            dest="datadir", default=default_index_dir,
            action="store", type="string",
            help=("Specify alternate database directory,"
                  " default `{}'".format(default_index_dir))),
        optparse.make_option(
            '-t', '--type',
            default=None,
            action="store", type="string",
            help=("Specify database type. "
                  "Available choices are `directory' and `tarball'. "
                  "Default guesses the type")),
        optparse.make_option(
            '-l', '--link',
            default=False,
            action="store_true", 
            help=("Link the database directory to the data directory "
                  "with a symbolic link instead of copying."))
    ]
    
    (opts, args) = optparse.OptionParser(
        option_list=options, usage=HELP
    ).parse_args(args=argv)

    for fname in args:
        try:
            add(fname, opts.type, opts.link, opts.datadir)
        except UserError as e:
            print >> sys.stderr, e.format_for_user()


def remove(db_name, datadir=default_index_dir):
    to_del = os.path.join(datadir, db_name)
    if os.path.islink(to_del):
        os.remove(to_del)
    else:
        shutil.rmtree(to_del)


def remove_cmd(argv):
    HELP = "Remove database from list of available databases"

    options = [
        optparse.make_option(
            '-d', '--data-dir',
            dest="datadir", default=default_index_dir,
            action="store", type="string",
            help=("Specify alternate database directory,"
                  " default `{}'".format(default_index_dir))),
    ]
    
    (opts, args) = optparse.OptionParser(
        option_list=options, usage=HELP
    ).parse_args(args=argv)

    for db_name in args:
        remove(db_name, opts.datadir)

def new(db_str, clobber=False):
    if os.path.exists(db_str):
        if clobber:
            shutil.rmtree(db_str, ignore_errors=True)
        else:
            raise ValueError("path already exists: `%s'"%(db_str))
    return leveldb.LevelDB(db_str, error_if_exists=True)

