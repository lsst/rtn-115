.. image:: https://img.shields.io/badge/rtn--115-lsst.io-brightgreen.svg
   :target: https://rtn-115.lsst.io
.. image:: https://github.com/lsst/rtn-115/workflows/CI/badge.svg
   :target: https://github.com/lsst/rtn-115/actions/

############################################
The Vera C. Rubin Observatory Data Preview 2
############################################

RTN-115
=======

We present Rubin Data Preview 2 (DP2), the second data preview from the NSF-DOE Vera C. Rubin Observatory,

Links
=====

- Live drafts: https://rtn-115.lsst.io
- GitHub: https://github.com/lsst/rtn-115

Build
=====

This repository includes lsst-texmf_ as a Git submodule.
Clone this repository::

    git clone --recurse-submodules https://github.com/lsst/rtn-115

Compile the PDF::

    make deps; make

Clean built files::

    make clean

AAS ::

    make flat
This will populate forAAS directory with a ingle tex file and all images.

Updating acronyms
-----------------

A table of the technote's acronyms and their definitions are maintained in the `acronyms.tex` file, which is committed as part of this repository.
To update the acronyms table in ``acronyms.tex``::

    make acronyms.tex

*Note: this command requires that this repository was cloned as a submodule.*

The acronyms discovery code scans the LaTeX source for probable acronyms.
You can ensure that certain strings aren't treated as acronyms by adding them to the `skipacronyms.txt <./skipacronyms.txt>`_ file.

The lsst-texmf_ repository centrally maintains definitions for LSST acronyms.
You can also add new acronym definitions, or override the definitions of acronyms, by editing the `myacronyms.txt <./myacronyms.txt>`_ file.

Updating lsst-texmf
-------------------

`lsst-texmf`_ includes BibTeX files, the ``lsstdoc`` class file, and acronym definitions, among other essential tooling for LSST's LaTeX documentation projects.
To update to a newer version of `lsst-texmf`_, you can update the submodule in this repository::

   git submodule update --init --recursive

Commit, then push, the updated submodule.

.. _lsst-texmf: https://github.com/lsst/lsst-texmf

Producing the parameters file
-----------------------------

All parameters in the DP2 paper are auto generated.
They can be broadly grouped into  two categories, static or hard-coded paramteres, and those extracted or computed from the DP2 dataset or metadata.
The static parameters are all in the ``data/static_parameters.tex`` file and  include for example, the LSST start date,
whereas parameters such as the number of visits in a release are extracted from the dataset itself and require a connection to the dataset.

To generate the parameters.tex file with the static parameters only. Sections is the defaut directory

.. uv run python bin/dp2_parameters.py --static-only

.. uv run python bin/dp2_parameters.py --static-only --output-dir adir

Running the copyedit check script
---------------------------------

Copy editing is a very tedious and time-consuming task of producing a paper.
To ease this burden and to harmonise style across a paper which contains contributions from many people, journal copy edit rules have been codified.
They are defined in .copyedit-rules.yaml
They can be applied by running the script  bin/copyedit.py

Fix violations in place (modifies input file)
..  uv run python bin/copyedit.py sections/introduction.tex

Report violations without modifying any files
.. uv run python bin/copyedit.py --check sections/introduction.tex

Report violations for rule that ate marked as "audit" only. These are rules that are never auto-applied because they have high false-positive rates and require
human intervention
.. uv run python bin/copyedit.py --check --audit $(git ls-files '*.tex')

Running the precommit checks
----------------------------

The DP2 repository now contains a number of pre-commit hooks to reduce the burden of a number of tasks, the main one being appliction of copy-edit rules.

Run only the copyedit precommit check on all files
.. pre-commit run copyedit

Run only the copyedit precommit check on the introduction file only
..  pre-commit run copyedit --files sections/introduction.tex

Run all precommit checks on all files
.. pre-commit run --all-files
