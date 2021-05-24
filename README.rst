######
lkstat
######

.. contents:: Table of Contents

``lkstat`` is simple tool to figure out where Linaro has maintainer in Linux
kernel and it will also give an indication of the activitiy in the different
subsystems. The tool will generate "mindmap" trees that can be imported by a
tool called Freeplane_. 

There are a couple of different parameters to tweak the query.


.. code-block:: bash

    usage: lkstat.py [-h] [--disable-altname] [--assignee] [-a] [-p PATH]
                     [-s SINCE] [-o OUTPUT] [-v]

    Script used to generate Freeplane mindmap files

    optional arguments:
      -h, --help            show this help message and exit
      --disable-altname     Use alternative names (from cfg.yaml) to the tree
      --assignee            Add assignees (from cfg.yaml) to the tree
      -a, --author          If set, git statistic only count the commit from the
                            author
      -p PATH, --path PATH  Full path to the kernel tree
      -s SINCE, --since SINCE
                            Used with the git log --since command
      -o OUTPUT, --output OUTPUT
                            Output filename
      -v                    Output some verbose debugging info


Default
*******
The script by default look at the script authors kernel tree (hardcoded), hence
other users of ``lkstat`` must at least use the ``-p`` parameter to give the
**absolute** path to a kernel tree that is up-to-date. Then by calling just the
script, it will:

- find all Linaro maintainers and also the ones who aren't using their
  Linaro email address (see ``cfg.yaml``).

- **not** include assignees (again see ``cfg.yaml``).

- look a year back from todays date.

- show activity based on **all** patches in that subsystem. I.e., not only
  the ones from the maintainer itself (see ``Maintainer activity`` below for
  more information regarding that).


Include assignees
*****************
First ensure that the cfg ``cfg.yaml`` contains the correct information. Then
after that run the script as usual, but also append the ``--assignee``
parameter. Now, the mindmap tree will contain the assignees as well.


Maintainer activity
*******************
If you want to generate a graph to get an idea of the contributions from the
maintainer itself in the subsystem, then you should append ``-a`` as a parameter
when running the script.

**Note!** The script is currently unable to gather correct statics is there are
more than a single Linaro maintainer for a subsystem. To avoid confusion,
subsystems is colored in blue and overstike when there are more than one Linaro
maintainer (i.e., result isn't usable).


Change timeframe
****************
By default ``lkstat`` looks a year back. If you want to check another period,
then you can do that by providing a ``-s yyyy-nn-dd`` parameter.


Alternate output filename
*************************
With the ``-o another-name.mm`` parameter you tell ``lkstat`` to create a
mindmap tree with another filename than the default ``linux-kernel.mm``.


Color legend
************
The nodes in the mindmap tree have different colors.

- Green: indicates more than a patch per week.

- Orange: indicates more than a patch per month.

- Red: Less than a patch per month.

- Blue: More than a single Maintainer, node statistic information isn't usable.

- Grey: File in MAINTAINERS doesn't actually exist (patch should be sent to
  LKML to fix it).


.. _Freeplane: https://www.freeplane.org/wiki/index.php/Home
