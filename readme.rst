
########################
its_to_18s documentation
########################

.. contents::

________________________________________________________________________________

Overview
========

The ``its_to_18s`` script is a small set of tools for retrieving
sequences as indexed by taxonomy strings. The intended use case is for
indexing SILVA 18S small subunit rRNA sequences by NCBI taxonomy
strings as formatted by BROCC_. The ``its_to_18s`` tool accomplishes
this by using a LevelDB, disk-based key-value store to quickly and
memory-efficientlyturn taxonomy calls into FASTA-formatted files for
further analysis.

.. _BROCC: https://github.com/kylebittinger/brocc



Quick Start for the impatient
_____________________________

Should be just a few commands:

::

   # python 2.7 only!
   pip install -e 'git+https://bitbucket.org/biobakery/its_to_18s.git@master#egg=its_to_18s-0.0.1'   

   # add an index
   its_to_18s add silva119_SSU_NR99_eukonly.tgz

   # get some sequences
   its_to_18s lookup -d silva119_SSU_NR99_eukonly  > SSU.fasta 2> SSU.err



Installation
============

Installation is handled by the venerable python ``setuptools``
package. It should come pre-installed with your python
distribution. If it's not, please install it from setuptools_.  If you
have pip installed, you'll also have the setuptools packages
installed.

``its_to_18s`` depends on the python ``leveldb`` package. This package
will be installed automatically as part of the normal installation
process. Ensure that your system has a functioning C++ compiler before
installing ``its_to_18s``; without said compiler, the installation
will fail.


Getting the code
________________


There are a number of ways to install ``its_to_18s``. The recommended
way is by using virtualenv_. Below is an example of installation with
virtualenv:

::

   virtualenv -p /usr/bin/python2.7 my_env
   source my_env/bin/activate
   pip install -e 'git+https://bitbucket.org/biobakery/its_to_18s.git@master#egg=its_to_18s-0.0.1'

If you'd like to contribute or otherwise monkey with the code,
consider using the developer install:

::

   virtualenv -p /usr/bin/python2.7 my_dev_env
   source my_dev_env/bin/activate
   git clone https://bitbucket.org/biobakery/its_to_18s.git
   cd its_to_18s
   python setup.py develop
   
   
.. _setuptools: https://pypi.python.org/pypi/setuptools
.. _virtualenv: https://virtualenv.pypa.io/en/latest/


Downloading and installing indexes
__________________________________

``its_to_18s`` uses leveldb to index small subunit sequences. Some
indexes are pre-built and available for download (send user
rschwager-hsph a bitbucket message for access).

Use the ``list`` and ``add`` subcommands of the ``its_to_18s`` tool to
see what indexes are installed and add new indexes. Here's what a
typical usage scenario looks like:

::

   $ its_to_18s list
   Available databases for data directory `/my/install/path/../indexes':

   $ its_to_18s add silva119_SSU_NR99_eukonly.tgz

   $ its_to_18s list
   Available databases for data directory `/my/install/path/../indexes':
   silva119_SSU_NR99_eukonly       /my/install/path/indexes/silva119_SSU_NR99_eukonly

When adding a tarball index, the tool unpacks the tarball, copying it
into its default index location. Alternate index locations can be
specified with the ``-d`` flag. Tarballs already unpacked into
directories can also be added; the tool automatically detects the type
of index its adding and acts accordingly. To save disk space, use the
``-l`` flag on a directory to be imported directs ``its_to_18s`` to
symlink the tool to the index directory.
   

Running
=======

Retrieving sequences
____________________


The ``its_to_18s`` tool's ``lookup`` subcommand reads through a list
of taxonomy strings and retrieves the sequences that correspond to the
strings. A typical usage:

::

   its_to_18s lookup -d silva119_SSU_NR99_eukonly \
       mouseabx_120k_assignments.txt \
       > nr99_results2.fasta \
       2> nr99_results2.err

The input taxonomy list is expected to be a text file consisting of
tab-separated fields and unix newline-separated ('\n') lines. The last
field in each line is considered the taxonomy string; that string is
used as a query for the leveldb database.

No need to combine input files; the tool can handle that:

::

    its_to_18s lookup -d silva119_SSURef_NR99 \
        *_assignments.txt \
	> nr99_results2.fasta \
	2> nr99_results2.err



How it works
============

``its_to_18s`` is a simple tool. The tool builds indexes with a
one-to-many mapping of taxonomy strings to sequence IDs (usually NCBI
accession numbers) and a one-to-many mapping of sequence IDs to
sequences. The final one-to-many mapping is necessary because many
databases contain multiple sequences derived from the same NCBI
accession number. Lookups are accomplished by first finding all the
IDs associated with a taxonomy string, then looking up all the
sequences for each ID, roughly equivalent to two SQL outer joins.

Building indexes
________________

Building sequence indexes are done with the ``index`` subcommand.
The ``index`` subcommand expects a number of arguments: the output
index directory, the input sequenecs, and a list of taxonomic
mappings. The input sequences are expected to be a FASTA-formatted
text file. Taxonomic mapping files are expected to text files with
fields separated by tabs and lines separated by unix newlines ('\n');
two fields are expected: the first field should be the sequence ID and
the last field should be the taxonomy string for that
sequence ID. Fields between the first and last fields are ignored.

A typical usage of ``index`` is as follows:

::

   its_to_18s index  -ldebug \
       silva119_SSU_parc \        # output db directory 
       seqs.fasta \               # input sequences
       taxmaps/*.txt \            # list of taxonomy mapping files
       > parc_build.log \
       2>&1 &


© Copyright 2015, Randall Schwager and the Huttenhower Lab
