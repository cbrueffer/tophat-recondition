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
import os
import sys
try:
    import pysam
except ImportError:
    print('Cannot import the pysam package; please make sure it is installed.\n')
    sys.exit(1)

VERSION = "0.3"


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


def unmapped_with_mapped_mate_standardize_flags(unmapped, bam_mapped, mapped_tid):
    """For unmapped reads with mapped mate, give some field more
    values downstream are more prone to accept."""
    unmapped_new_tid = translate_tid(mapped_tid)
    unmapped.tid = unmapped_new_tid
    unmapped.rnext = unmapped_new_tid
    unmapped.pos = mapped.pos
    unmapped.pnext = 0
    return read


def fix_unmapped_reads(path, outdir, mapped_file="accepted_hits.bam",
                       unmapped_file="unmapped.bam", cmdline=""):
    unmapped_dict = {}
    unmapped_index = {}
    unmapped_with_mapped_mate = {}

    with pysam.Samfile(os.path.join(path, unmapped_file)) as bam_unmapped:
        unmapped_reads = list(bam_unmapped.fetch(until_eof=True))
        unmapped_header = bam_unmapped.header

        # Fix things that relate to all unmapped reads.
        for i in range(len(unmapped_reads)):
            read = unmapped_reads[i]

            # remove /1 and /2 suffixes
            if read.qname.find("/") != -1:
                read.qname = read.qname[:-2]

            unmapped_index[read.qname] = i

            # Work around "mate is unmapped" bug in TopHat (issue #3).
            # https://github.com/infphilo/tophat/issues/3
            if read.qname in unmapped_dict:
                unmapped_reads[unmapped_dict[read.qname]].mate_is_unmapped = True
                read.mate_is_unmapped = True
            else:
                unmapped_dict[read.qname] = i

            read.mapq = 0
            unmapped_reads[i] = read

        # Iterate through the unmapped reads again to record all unmapped reads
        # with mapped mate, so we can check for the mate's existence when we traverse
        # the mapped file.
        # This cannot be done in the same iteration as prviously, or it would
        # collide with the fixes above and record false positives.
        for i, read in enumerate(unmapped_reads):
            if not read.mate_is_unmapped:
                unmapped_with_mapped_mate[read.qname] = i

        # Fix things that relate only to unmapped reads with a mapped mate.
        with pysam.Samfile(os.path.join(path, mapped_file)) as bam_mapped:
            for mapped in bam_mapped:
                if mapped.mate_is_unmapped:
                    i = get_index_pos(unmapped_index, mapped)
                    if i is not None:
                        unmapped_reads[i] = unmapped_with_mapped_mate_standardize_flags(unmapped_reads[i],
                                                                                        bam_mapped,
                                                                                        mapped.tid)

                if mapped.qname in unmapped_with_mapped_mate:
                    unmapped_with_mapped_mate.pop(mapped.qname, None)

        # Reset unmapped reads with "mate is mapped" bit set, but where the
        # mapped mate is absent.  This works around TopHat issue #16
        # https://github.com/infphilo/tophat/issues/16
        for readidx in unmapped_with_mapped_mate.values():
            unmapped_reads[readidx] = unpair_read(unmapped_reads[readidx])

        base, ext = os.path.splitext(unmapped_file)
        out_filename = "".join([base, "_fixup", ext])

    # For the output file, take the headers from the unmapped file.
    fixup_header = unmapped_header
    fixup_header['PG'].append({'ID': 'TopHat-Recondition',
                               'VN': VERSION,
                               'CL': cmdline})
    with pysam.Samfile(os.path.join(outdir, out_filename), "wb",
                       header=fixup_header) as bam_out:
        for read in unmapped_reads:
            bam_out.write(read)


def usage(scriptname, errcode=errno.EINVAL):
    print("Usage:\n")
    print(scriptname, "[-hv] tophat_output_dir [result_dir]\n")
    print("-h                 print this usage text and exit")
    print("-v                 print the script name and version, and exit")
    print("tophat_output_dir: directory containing accepted_hits.bam and unmapped.bam")
    print("result_dir:        directory to write unmapped_fixup.bam to (default: tophat_output_dir)")
    sys.exit(errcode)


if __name__ == "__main__":
    import getopt

    scriptname = os.path.basename(sys.argv[0])
    cmdline = " ".join(sys.argv)

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "dhv")
    except getopt.GetoptError as err:
        # print help information and exit
        print(str(err), file=sys.stderr)
        usage(scriptname, errcode=errno.EINVAL)

    debug = False
    for o, a in opts:
        if o in "-d":
            debug = True
        elif o in "-h":
            usage(scriptname, errcode=0)
        elif o in "-v":
            print(scriptname, VERSION)
            sys.exit(0)
        else:
            assert False, "unhandled option"
            sys.exit(errno.EINVAL)

    if len(args) == 0 or len(args) > 2:
        usage(scriptname, errcode=errno.EINVAL)

    bamdir = args.pop(0)
    if not os.path.isdir(bamdir):
        print("Specified tophat_output_dir does not exist or is not a directory: %s" % bamdir, file=sys.stderr)
        sys.exit(errno.EINVAL)

    if len(args) > 0:
        resultdir = args.pop(0)
        if not os.path.isdir(resultdir):
            print("Specified result_dir does not exist or is not a directory: %s" % resultdir, file=sys.stderr)
            sys.exit(errno.EINVAL)
    else:
        resultdir = bamdir

    try:
        fix_unmapped_reads(bamdir, resultdir, cmdline=cmdline)
    except KeyboardInterrupt:
        print("Program interrupted by user, exiting.")
        sys.exit(errno.EINTR)
    except Exception as e:
        if debug:
            import traceback
            print(traceback.format_exc(), file=sys.stderr)

        print("Error: %s" % str(e), file=sys.stderr)
        if hasattr(e, "errno"):
            sys.exit(e.errno)
        else:
            sys.exit(1)
