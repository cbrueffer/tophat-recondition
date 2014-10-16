misc_bioinf
===========

Repository for miscellaneous bioinformatics scripts that may be useful to others.

fix_tophat_unmapped_reads.py
----------------------------

Fixes unmapped TopHat reads (contained in unmapped.bam) to make them compatible with downstream tools
(i.e., the Picard suite and samtools).  It also works around a bug in TopHat where
the "mate is unmapped" SAM flag is not set on any reads in the unmapped.bam file.  This script requires ```pysam``` to be installed.

 ```Usage:

fix_tophat_unmapped_reads.py [-hv] [tophat_output_dir [result_dir]]

-h                 print this usage text and exit
-v                 print the script name and version, and exit
tophat_output_dir: directory containing accepted_hits.bam and unmapped.bam
result_dir:        directory to write unmapped_fixup.bam to (default: tophat_output_dir)
```

Note: unmapped.bam is read into memory, so make sure your computer has enough RAM to fit it.

Specifically, the script does the following (see SAM format specification for details on the fields in capital letters):

- Fixes a bug in TopHat (unfixed as of v2.0.12):
  * For paired reads where both reads are unmapped, TopHat does not set the 0x8 flag ("mate is unmapped") flag on either read.

- Removes /1 and /2 suffixes from read names (QNAME), if present.

- Sets mapping quality (MAPQ) for unmapped reads to 0.  TopHat sets it to 255 which some downstream tools don't like.

- If an unmapped read's paired read is mapped, set the following fields in the unmapped read (apparently downstream tools like Picard don't like the values TopHat fills in for those fields):
  * RNAME: RNAME of the paired read
  * RNEXT: RNAME of the paired read
  * POS:   POS of the paired read
  * PNEXT: 0
