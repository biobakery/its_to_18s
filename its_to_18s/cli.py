import sys
import logging

from . import (
    index, taxlookup, download, db
)


    

BANNER = "its_to_18s uses leveldb to quickly lookup 18s sequences from taxonomy calls"

def print_help(*args):
    print >> sys.stderr, BANNER
    print >> sys.stderr, "Available Subcommands:"
    for key in subcommand_map.keys():
        if key.startswith('-'):
            continue
        print >> sys.stderr, "\t "+key

subcommand_map = {
    "--help": print_help,
    "-h": print_help,
    "help": print_help,
    "index": index.main,
    "lookup": taxlookup.main,
    "add": db.add_cmd,
    "list": db.list_cmd,
    "remove": db.remove_cmd
}


def main():
    if len(sys.argv) < 2:
        print_help()
        return 1

    subcommand = sys.argv[1]
    if subcommand not in subcommand_map:
        print "`%s' is not a recognized command. Try `help'"%(subcommand)
        return 1
    else:
        logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s")
        return subcommand_map[subcommand](sys.argv[2:])


if __name__ == "__main__":
    ret = main()
    sys.exit(ret)
