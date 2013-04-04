#!/usr/bin/env python

# ----------------------------------------------------------------------------
#  "THE BEER-WARE LICENSE" (Revision 42):
#  Christian Brueffer <christian@brueffer.de> wrote this file. As long as you
#  retain this notice you can do whatever you want with this stuff. If we meet
#  some day, and you think this stuff is worth it, you can buy me a beer in
#  return.
# ----------------------------------------------------------------------------

# This script fixes the reads in a TopHat unmapped.bam to make them compatible
# with other tools, e.g. Picard and samtools.

import os
import pysam
import sys


def get_mapped_index(mapped_reads):
    """Builds a dict of all mapped reads with an unmapped mate, and their
    positions.""" 

    index = {}
    for i, read in enumerate(mapped_reads):
        if read.mate_is_unmapped:
            index[read.qname] = i

    return index


def get_mapped_read(index, mapped_reads, read):
    """Returns the position of a read in the index or None."""

    if read.qname in index:
        return mapped_reads[index[read.qname]]
    else:
        return None


def main(path, mapped_file="accepted_hits.bam", unmapped_file="unmapped.bam"):
    bam_mapped = pysam.Samfile(os.path.join(path, mapped_file))
    mapped_reads = list(bam_mapped.fetch())
    bam_unmapped = pysam.Samfile(os.path.join(path, unmapped_file))
    unmapped_reads = list(bam_unmapped.fetch(until_eof=True))

    index = get_mapped_index(mapped_reads)
    unmapped_dict = {}

    for i in range(len(unmapped_reads)):
        read = unmapped_reads[i]

        # remove /1 and /2 suffixes
        if read.qname.index("/") != -1:
            read.qname = read.qname[:-2]

        # work around "mate is unmapped" bug in Tophat before version 2.0.9
        if read.qname in unmapped_dict:
            unmapped_reads[unmapped_dict[read.qname]].mate_is_unmapped = True
            read.mate_is_unmapped = True
        else:
            unmapped_dict[read.qname] = i

        read.mapq = 0

        mate = get_mapped_read(index, mapped_reads, read)
        if mate:
            # map chromosome TIDs from mapped to unmapped file
            mate_rname = bam_mapped.getrname(mate.tid)
            read_new_tid = bam_unmapped.gettid(mate_rname)

            read.tid = read_new_tid
            read.rnext = read_new_tid
            read.pos = mate.pos
            read.pnext = 0

        unmapped_reads[i] = read

    bam_mapped.close()

    # for the output file, take the headers from the unmapped file
    base, ext = os.path.splitext(unmapped_file)
    out_filename = "".join([base, "_fixup", ext])
    bam_out = pysam.Samfile(os.path.join(path, out_filename), "wb",
                        template=bam_unmapped)

    bam_unmapped.close()

    for read in unmapped_reads:
        bam_out.write(read)

    bam_out.close()


def usage(scriptname):
    print "Usage:"
    print scriptname, "tophat_output_dir"
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        path = sys.argv[1]
        if os.path.exists(path) and os.path.isdir(path):
            main(sys.argv[1])
        else:
            usage(sys.argv[0])
    else:
        usage(sys.argv[0])
