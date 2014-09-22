#!/usr/bin/env python
# -*- coding: utf-8 -*
#
# Copyright (c) 2013-2014 Christian Brueffer (ORCID: 0000-0002-3826-0989)
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
# This script fixes the reads in a TopHat unmapped.bam to make them compatible
# with downstream tools (i.e., Picard and samtools).

import os
import pysam
import sys


def get_index_pos(index, unmapped_reads, read):
    """Returns the position of a read in the index or None."""

    if read.qname in index:
        return index[read.qname]
    else:
        return None


def main(path, outdir, mapped_file="accepted_hits.bam", unmapped_file="unmapped.bam"):
    # Fix things that relate to all unmapped reads.
    unmapped_dict = {}
    unmapped_index = {}
    with pysam.Samfile(os.path.join(path, unmapped_file)) as bam_unmapped:  
        unmapped_reads = list(bam_unmapped.fetch(until_eof=True))
        for i in range(len(unmapped_reads)):
            read = unmapped_reads[i]

            # remove /1 and /2 suffixes
            if read.qname.find("/") != -1:
                read.qname = read.qname[:-2]

            unmapped_index[read.qname] = i

            # work around "mate is unmapped" bug in TopHat
            if read.qname in unmapped_dict:
                unmapped_reads[unmapped_dict[read.qname]].mate_is_unmapped = True
                read.mate_is_unmapped = True
            else:
                unmapped_dict[read.qname] = i

            read.mapq = 0

            unmapped_reads[i] = read

        # Fix things that relate only to unmapped reads with a mapped mate.
        with pysam.Samfile(os.path.join(path, mapped_file)) as bam_mapped:
            for mapped in bam_mapped:
                if mapped.mate_is_unmapped:
                    i = get_index_pos(unmapped_index, unmapped_reads, mapped)
                    if i is not None:
                        unmapped = unmapped_reads[i]

                        # map chromosome TIDs from mapped to unmapped file
                        mapped_rname = bam_mapped.getrname(mapped.tid)
                        unmapped_new_tid = bam_unmapped.gettid(mapped_rname)

                        unmapped.tid = unmapped_new_tid
                        unmapped.rnext = unmapped_new_tid
                        unmapped.pos = mapped.pos
                        unmapped.pnext = 0

                        unmapped_reads[i] = unmapped

        # for the output file, take the headers from the unmapped file
        base, ext = os.path.splitext(unmapped_file)
        out_filename = "".join([base, "_fixup", ext])

        with pysam.Samfile(os.path.join(outdir, out_filename), "wb",
                           template=bam_unmapped) as bam_out:
            for read in unmapped_reads:
                bam_out.write(read)


def usage(scriptname):
    print "Usage:"
    print scriptname, "tophat_output_dir"
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        path = sys.argv[1]
        if os.path.exists(path) and os.path.isdir(path):
            # no tmpdir specified, use the bam dir
            main(path, path)
        else:
            usage(sys.argv[0])
    elif len(sys.argv) == 3:
        path = sys.argv[1]
        outdir = sys.argv[2]
        if os.path.exists(path) and os.path.isdir(path) and os.path.exists(outdir) and os.path.isdir(outdir):
            main(path, outdir)
        else:
            usage(sys.argv[0])
    else:
        usage(sys.argv[0])
