import logging
import os
import platform
from pathlib import Path

from .utils import call_shell


class Git(object):
    def parse_version(self, vstring=None):
        if vstring and vstring not in ("release", "current"):
            return vstring

        logging.info("Getting Git version info...")

        cmd = "git describe HEAD --tags"
        if vstring is None or vstring == "release":
            cmd += " --abbrev=0"

        version = call_shell(cmd, error_exit=False)

        if version is False:
            # Perhaps no tag has been set yet. Try to grab commit ID before
            # giving up and exiting
            version = call_shell("git rev-parse --short HEAD")

        return version

    def archive(self, version, outdir):
        logging.info("Exporting Git archive...")
        if not outdir or not version:
            return False

        # Convert Path object to string and normalize slashes
        outdir = str(outdir).replace('\\', '/')

        if version == "dev":
            # https://stackoverflow.com/a/12010656
            cmd = (
                "stash=`git stash create`; git archive --format tar $stash |"
                " tar -x -C \"{outdir}\"".format(outdir=outdir)
            )
        else:
            cmd = "git archive --format tar {vers} | tar -x -C \"{outdir}\"".format(
                vers=version, outdir=outdir
            )
        return call_shell(cmd)

    def modtime(self, version):
        if version == "dev":
            # Get timestamps of uncommitted changes and return the most recent.
            # https://stackoverflow.com/a/14142413
            cmd = (
                "git status -s | while read mode file;"
                " do echo $(stat -c %Y $file); done"
            )
            modtimes = call_shell(cmd).splitlines()
            # https://stackoverflow.com/a/12010656
            modtimes = [int(modtime) for modtime in modtimes]
            return max(modtimes)
        else:
            return int(call_shell("git log -1 -s --format=%ct {}".format(version)))