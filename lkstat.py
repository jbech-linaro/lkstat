#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser

import datetime
import git
import os
import re
import subprocess
import sys
import unicodedata
import yaml

###############################################################################
# Globals
###############################################################################
assignees = None
altemail = None


###############################################################################
# Class node
###############################################################################
class Node():
    def __init__(self, subsys, engineers, files, scaling):
        self.childrens = []
        self.color = None
        self.engineers = engineers
        self.files = files
        self.parent = None
        self.scaling = scaling
        self.stats = 0
        self.subsys = subsys
        self._indent = 0

    def add_subsys(self, subsys):
        print("Adding subsys: {}".format(subsys))

    def add_engineer(self, engineer):
        print("Adding engineer: {}".format(engineer))

    def add_file(self, f):
        print("Adding files: {}".format(f))

    def add_git_stats(self, stats):
        self.stats = stats

    def set_color(self, color):
        self.color = color

    def get_color(self):
        if self.color is not None:
            return self.color

        # Scale everything to a yearly factor
        scaled_stats = self.scaling * self.stats
        color = "#990000"  # Red
        if scaled_stats > 52:
            color = "#009900"  # Green
        elif scaled_stats > 12:
            color = "#ff6600"  # Orange
        return color

    def to_xml(self, f, author, indent=0):
        self._indent = indent
        # Main node
        fold = "false"
        color = self.get_color()
        if ", " in self.engineers and author:
            print("Warning, multiple maintainers, git statics will be ,"
                  "incorrect!")

        xml_info_start = "{}<node TEXT=\"{}\" POSITION=\"right\" folded=\"{}\" COLOR=\"{}\">\n".format(
            " " * (self._indent + 4), self.subsys, fold, color)
        f.write(xml_info_start)

        if author and ", " in self.engineers:
            xml_strikethrough = "<font STRIKETHROUGH=\"true\"/>"
            f.write(xml_strikethrough)

        xml_rich = "<richcontent TYPE=\"NOTE\"> <html> <head> </head> <body> <p> Maintainer: {}</p> <p> Stats: {}</p> </body> </html> </richcontent>\n".format(self.engineers, self.stats)
        f.write(xml_rich)

        xml_info_end = "{}{}\n".format(" " * (self._indent + 4), "</node>")
        f.write(xml_info_end)

    def __str__(self):
        return "{}\n{}\n{}\n{}\n{}\n".format(self.subsys,
                                             self.engineers,
                                             self.files,
                                             self.stats,
                                             self.scaling)


def open_file(filename):
    """
    This will open the user provided file and if there has not been any file
    provided it will create and open a temporary file instead.
    """
    print("filename: %s\n" % filename)
    if filename:
        return open(filename, "w")
    else:
        return tempfile.NamedTemporaryFile(delete=False)

###############################################################################
# Argument parser
###############################################################################


def get_parser():
    """ Takes care of script argument parsing. """
    parser = ArgumentParser(description="Script used to generate Freeplane "
                            + "mindmap files")

    # This is use when people in Linaro aren't using their email address.
    parser.add_argument('--disable-altname', required=False,
                        action="store_true", default=False,
                        help="Use alternative names (from cfg.yaml) to the tree")

    parser.add_argument('--assignee', required=False,
                        action="store_true", default=False,
                        help="Add assignees (from cfg.yaml) to the tree")

    parser.add_argument('-a', '--author', required=False,
                        action="store_true", default=False,
                        help="If set, git statistic only count the commit "
                        + "from the author")

    parser.add_argument('-p', '--path', required=False, action="store",
                        default="/home/jyx/devel/optee_projects/reference/linux",
                        help='Full path to the kernel tree')

    parser.add_argument('-s', '--since', required=False, action="store",
                        default=None,
                        help='Used with the git log --since command')

    parser.add_argument('-o', '--output', required=False, action="store",
                        default="linux-kernel.mm",
                        help='Output filename')

    parser.add_argument('-v', required=False, action="store_true",
                        default=False,
                        help='Output some verbose debugging info')

    return parser

###############################################################################
# General nodes
###############################################################################


def root_nodes_start(f, key):
    f.write("<map version=\"freeplane 1.7.0\">\n")
    f.write("<node TEXT=\"{}\" FOLDED=\"false\" COLOR=\"#000000\" LOCALIZED_STYLE_REF=\"AutomaticLayout.level.root\">\n".format(key))


def root_nodes_end(f):
    f.write("</node>\n</map>")


def orphan_node_start(f):
    f.write("<node TEXT=\"Orphans\" POSITION=\"left\" FOLDED=\"false\" COLOR=\"#000000\">\n")


def orphan_node_end(f):
    f.write("</node>\n")


###############################################################################
# Git stats
###############################################################################

def get_git_stats(kernel_path, node, since, author):
    os.chdir(kernel_path)

    cmd = []
    if author:
        cmd.append('--author={}'.format(node.engineers))
        # Currently it doesn't support multiple authors, hence mark it in blue
        if ", " in node.engineers:
            node.set_color("#3333FF")
    cmd.append("--since='{}'".format(since))
    cmd.append("--oneline")
    for f in node.files.split(' '):
        cmd.append(f)

    g = git.Git(kernel_path)
    log = ""

    # Needed to catch then files are listen in the MAINTAINERS file, but
    # doesn't actually exist in the tree.
    try:
        log = g.log(cmd)

    except git.exc.GitCommandError as e:
        print("Error: {}".format(e))
        node.set_color("#C0C0C0")
        return -1

    return len(log.split("\n"))


def get_assignees():
    global assignees

    # Only load if form the yaml-file once.
    if assignees is None:
        with open('cfg.yaml') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            assignees = data['assignees']

    return assignees


def get_non_linaro_email():
    global altemail

    # Only load if form the yaml-file once.
    if altemail is None:
        with open('cfg.yaml') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            altemail = data['non_linaro_email']

    return altemail


def is_assignee(l):
    for a in get_assignees():
        if a in l.strip():
            # print("l: {}, assignee: {}".format(l.strip(), a))
            return True

    return False


def is_altname(l):
    for a in get_non_linaro_email():
        if a in l.strip():
            alt_eng_line = re.match(r'^M:\t(' + a + ') <.*@.*', l, re.I)
            # print("l: {}, altname: {}".format(l.strip(), a))
            if alt_eng_line is not None:
                return a
    return None


def start_parsing(f, kernel_path, add_assignee, use_altname, since=None,
                  scaling=1):
    maintainer_file = "{}/MAINTAINERS".format(kernel_path)
    parse_started = False
    read_subsystem = False
    subsystem = None
    engineers = ""
    files = ""
    nodes = []

    altnames = get_non_linaro_email()

    with open(maintainer_file, 'r') as mf:
        for l in mf:
            maintainer_line = re.match(r'^(Maintainers List)', l)

            # Ignore all lines until we fine the "Maintainers List" line
            if maintainer_line is not None:
                print(maintainer_line)
                parse_started = True

            if not parse_started:
                continue

            # Read and save the subsystem
            if read_subsystem:
                subsystem = l.strip()
                read_subsystem = False
                continue

            alt_eng_line = is_altname(l) if use_altname else None

            # Read and save Linaro maintainers
            eng_line = re.match(r'^M:\t(.*) <.*@linaro.org.*', l, re.I)
            if eng_line is not None or alt_eng_line is not None:
                if eng_line:
                    engineer = eng_line.groups(0)[0]
                elif alt_eng_line:
                    engineer = alt_eng_line
                else:
                    print("ERROR: shouldn't happen!")
                    exit(1)

                if is_assignee(engineer):
                    if not add_assignee:
                        continue

                if len(engineers) + len(engineer) > len(engineer):
                    engineers += ", "
                engineers += engineer
                continue

            # Read and save files
            file_line = re.match(r'^F:\t(.*)', l, re.I)
            if file_line is not None and subsystem is not None and len(engineers) > 0:
                fl = file_line.groups(0)[0]
                if len(files) + len(fl) > len(fl):
                    files += " "
                files += fl
                continue

            empty_line = re.match(r'^\n$', l)
            if empty_line is not None:
                # Before cleaning up, create a node if we've found Linaro
                # maintainers
                if len(engineers) > 0 and len(files) > 0:
                    nodes.append(Node(subsystem, engineers, files, scaling))

                # Reset variables
                read_subsystem = True
                subsystem = None
                engineers = ""
                files = ""

    return nodes


def get_default_since():
    d = datetime.datetime.now() - datetime.timedelta(days=1*365)
    return "{}-{:02d}-{:02d}".format(d.year, d.month, d.day)


def get_scaling(d):
    d = datetime.datetime.now() - d
    return 365.0 / d.days


###############################################################################
# Main function
###############################################################################
def main(argv):
    parser = get_parser()

    # The parser arguments (cfg.args) are accessible everywhere after this
    # call.
    args = parser.parse_args()

    # Open and initialize the file
    f = open_file(args.output)
    root_nodes_start(f, "Linux kernel")

    since = get_default_since()
    if args.since is not None:
        since = args.since

    # Convert it back to a date object so we can calculate a scaling
    # factor.
    date_time_obj = datetime.datetime.strptime(since, "%Y-%m-%d")
    print("{}".format(date_time_obj))

    scaling = get_scaling(date_time_obj)
    print("since: {}, scaling: {}".format(since, scaling))

    use_altname = False if args.disable_altname else True
    print("Use altname: {}".format(use_altname))

    nodes = start_parsing(f, args.path, args.assignee, use_altname, since,
                          scaling)

    for n in nodes:
        n.add_git_stats(get_git_stats(args.path, n, since, args.author))
        n.to_xml(f, args.author)
        print(n)

    root_nodes_end(f)
    f.close()


if __name__ == "__main__":
    main(sys.argv)
