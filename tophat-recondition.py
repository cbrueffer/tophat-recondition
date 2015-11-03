#!/usr/bin/env python
# -*- coding: utf-8 -*
#
# Copyright (c) 2013-2015 Christian Brueffer (ORCID: 0000-0002-3826-0989)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
"""
This script modifies the reads in a TopHat unmapped.bam file to make them
compatible with downstream tools (e.g., Picard, samtools or GATK).

Homepage: https://github.com/cbrueffer/tophat-recondition
"""

from __future__ import print_function

import errno
import logging
import os
import sys
try:
    import pysam
except ImportError:
    print('Cannot import the pysam package; please make sure it is installed.\n')
    sys.exit(1)

VERSION = "0.4"
DEFAULT_LOG_NAME = "tophat-recondition.log"
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMATTER = logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")


def init_logger():
    """Initializes a logger that emits into a string buffer."""
    from StringIO import StringIO

    logger = logging.getLogger("")
    logger.setLevel(DEFAULT_LOG_LEVEL)

    # Temporarily log to a buffer, until we know where to write the log to.
    logbuffer = StringIO()
    temp_handler = logging.StreamHandler(logbuffer)
    temp_handler.setFormatter(LOG_FORMATTER)
    logger.addHandler(temp_handler)
    return logger, temp_handler, logbuffer


def logger_add_console_handler(logger):
    """Adds a handler for logging to the console."""
    cons_handler = logging.StreamHandler()
    cons_handler.setFormatter(LOG_FORMATTER)
    logger.addHandler(cons_handler)
    return logger


def logger_add_file_handler(logger, temp_handler, logbuffer, logfile):
    """Writes the temporary log buffer to the log file, removes the
    temp handler and adds the correct log file handler."""
    import shutil

    logbuffer.seek(0)
    with open(logfile, 'w') as log:
        shutil.copyfileobj(logbuffer, log)
    logger.removeHandler(temp_handler)

    # Add the proper file handler.
    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(LOG_FORMATTER)
    logger.addHandler(file_handler)
    return logger


def get_index_pos(index, read):
    """Returns the position of a read in the index or None."""
    return index[read.qname] if read.qname in index else None


def unpair_read(read):
    """Makes read unpaired by resetting all mate-related flags."""
    read.is_paired = False
    read.is_proper_pair = False
    read.mate_is_reverse = False
    read.mate_is_unmapped = False
    read.is_read1 = False
    read.is_read2 = False
    return read


def mapped_to_unmapped_tid(mapped_file, unmapped_file, mapped_tid):
    """Map chromosome TIDs from mapped to unmapped file."""
    mapped_rname = mapped_file.getrname(mapped_tid)
    return unmapped_file.gettid(mapped_rname)


def unmapped_with_mapped_mate_standardize_fields(unmapped, mapped, bam_unmapped, bam_mapped):
    """For unmapped reads with mapped mate, give some fields
    values that downstream tools are more prone to accept."""
    unmapped_new_tid = mapped_to_unmapped_tid(bam_unmapped, bam_mapped, mapped.tid)
    unmapped.tid = unmapped_new_tid
    unmapped.rnext = unmapped_new_tid
    unmapped.pos = mapped.pos
    unmapped.pnext = 0
    return unmapped


def fix_unmapped_reads(path, outdir, mapped_file="accepted_hits.bam",
                       unmapped_file="unmapped.bam", cmdline="", logger=None):
    """Corrects various fields and flags of the unmapped reads to make them
    compatible with downstream processing tools."""
    unmapped_dict = {}
    unmapped_index = {}
    unmapped_with_mapped_mate = {}

    infile_unmapped = os.path.join(path, unmapped_file)
    logger.info("Opening unmapped BAM file: %s" % infile_unmapped)
    with pysam.Samfile(infile_unmapped) as bam_unmapped:
        logger.info("Loading unmapped BAM file into memory: %s" % infile_unmapped)
        unmapped_reads = list(bam_unmapped.fetch(until_eof=True))
        unmapped_header = bam_unmapped.header

        # Fix things that relate to all unmapped reads.
        for i in range(len(unmapped_reads)):
            read = unmapped_reads[i]

            # remove /1 and /2 suffixes
            if "/" in read.qname:
                read.qname = read.qname[:-2]

            unmapped_index[read.qname] = i

            # Work around "mate is unmapped" bug in TopHat (issue #3).
            # https://github.com/infphilo/tophat/issues/3
            if read.qname in unmapped_dict:
                logger.info("Setting missing 0x8 flag for unmapped read-pair: %s" % read.qname)
                unmapped_reads[unmapped_dict[read.qname]].mate_is_unmapped = True
                read.mate_is_unmapped = True
            else:
                unmapped_dict[read.qname] = i

            read.mapq = 0
            unmapped_reads[i] = read

        # Iterate through the unmapped reads again to record all unmapped reads
        # with mapped mate, so we can check for the mate's existence when we traverse
        # the mapped file.
        # This cannot be done in the same iteration as previously, or it would
        # collide with the fixes above and record false positives.
        for i, read in enumerate(unmapped_reads):
            if not read.mate_is_unmapped:
                unmapped_with_mapped_mate[read.qname] = i

        # Fix things that relate only to unmapped reads with a mapped mate.
        infile_mapped = os.path.join(path, mapped_file)
        logger.info("Opening mapped BAM file: %s" % infile_mapped)
        with pysam.Samfile(infile_mapped) as bam_mapped:
            for mapped in bam_mapped:
                if mapped.mate_is_unmapped:
                    i = get_index_pos(unmapped_index, mapped)
                    if i is not None:
                        unmapped = unmapped_reads[i]
                        logger.info("Standardizing flags of unmapped read: %s" % unmapped.qname)
                        unmapped_reads[i] = unmapped_with_mapped_mate_standardize_fields(unmapped,
                                                                                         mapped,
                                                                                         bam_unmapped,
                                                                                         bam_mapped)

                if mapped.qname in unmapped_with_mapped_mate:
                    unmapped_with_mapped_mate.pop(mapped.qname, None)

        # Reset unmapped reads with "mate is mapped" bit set, but where the
        # mapped mate is absent.  This works around TopHat issue #16
        # https://github.com/infphilo/tophat/issues/16
        for readname, readidx in unmapped_with_mapped_mate.iteritems():
            logger.info("Mapped mate not found, unpairing unmapped read: %s" % readname)
            unmapped_reads[readidx] = unpair_read(unmapped_reads[readidx])

        base, ext = os.path.splitext(unmapped_file)
        out_filename = "".join([base, "_fixup", ext])

    # For the output file, take the headers from the unmapped file.
    fixup_header = unmapped_header
    fixup_header['PG'].append({'ID': 'TopHat-Recondition',
                               'VN': VERSION,
                               'CL': cmdline})
    outfile = os.path.join(outdir, out_filename)
    logger.info("Writing corrected BAM file: %s" % outfile)
    with pysam.Samfile(outfile, "wb", header=fixup_header) as bam_out:
        for read in unmapped_reads:
            bam_out.write(read)


def usage(scriptname, errcode=errno.EINVAL):
    """Prints the usage text and exits with the specified error code."""
    print("Usage:\n")
    print(scriptname, "[-hqv] [-l logfile] tophat_output_dir [result_dir]\n")
    print("-h                 print this usage text and exit (optional)")
    print("-l                 log file (optional, default: result_dir/tophat-recondition.log)")
    print("-q                 quiet mode, no console output (optional)")
    print("-v                 print the script name and version, and exit (optional)")
    print("tophat_output_dir: directory containing accepted_hits.bam and unmapped.bam")
    print("result_dir:        directory to write unmapped_fixup.bam to (optional, default: tophat_output_dir)")
    sys.exit(errcode)


if __name__ == "__main__":
    import getopt

    scriptname = os.path.basename(sys.argv[0])
    cmdline = " ".join(sys.argv)
    logger, temp_handler, logbuffer = init_logger()

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "dhl:qv")
    except getopt.GetoptError as err:
        # print help information and exit
        print(str(err), file=sys.stderr)
        usage(scriptname, errcode=errno.EINVAL)

    debug = False
    logfile = None
    quiet = False
    for o, a in opts:
        if o in "-d":
            debug = True
        elif o in "-h":
            usage(scriptname, errcode=0)
        elif o in "-l":
            logfile = a
        elif o in "-q":
            quiet = True
        elif o in "-v":
            print(scriptname, VERSION)
            sys.exit(0)
        else:
            assert False, "unhandled option"
            sys.exit(errno.EINVAL)

    if not quiet:
          logger_add_console_handler(logger)

    logger.info("Starting run of tophat-recondition %s" % VERSION)
    logger.info("Command: %s" % cmdline)
    logger.info("Current working directory: %s" % os.getcwd())

    if len(args) == 0 or len(args) > 2:
        usage(scriptname, errcode=errno.EINVAL)

    bamdir = args.pop(0)
    if not os.path.isdir(bamdir):
        logger.error("Specified tophat_output_dir does not exist or is not a directory: %s" % bamdir)
        sys.exit(errno.EINVAL)

    if len(args) > 0:
        resultdir = args.pop(0)
        if not os.path.isdir(resultdir):
            logger.error("Specified result_dir does not exist or is not a directory: %s" % resultdir)
            sys.exit(errno.EINVAL)
    else:
        resultdir = bamdir

    if logfile is None:
        logfile = os.path.join(resultdir, DEFAULT_LOG_NAME)
    try:
        logger = logger_add_file_handler(logger, temp_handler, logbuffer, logfile)
    except Exception as e:
        logger.error("Cannot open log file %s: %s" % (logfile, str(e)))
        sys.exit(1)

    logger.info("Writing logfile: %s" % logfile)
    try:
        fix_unmapped_reads(bamdir, resultdir, cmdline=cmdline, logger=logger)
        logger.info("Program finished successfully.")
    except KeyboardInterrupt:
        logger.info("Program interrupted by user, exiting.")
        print("Program interrupted by user, exiting.")
        sys.exit(errno.EINTR)
    except Exception as e:
        if debug:
            import traceback
            logger.error(traceback.format_exc())

        logger.error("Error: %s" % str(e))
        if hasattr(e, "errno"):
            sys.exit(e.errno)
        else:
            sys.exit(1)
