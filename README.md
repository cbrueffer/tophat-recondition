misc_bioinf
===========

Repository for miscellaneous bioinformatics scripts I developed that may be useful to others.

fix_tophat_unmapped_reads.py
----------------------------

Fixes unmapped TopHat reads (contained in unmapped.bam) to make them compatible with other tools,
e.g. the Picard suite and samtools.  It also works around a bug in TopHat where
the "mate is unmapped" SAM flag is not set on any reads in the unmapped.bam file.  This script requires ```pysam``` to be installed.

Usage: ```$ ./fix_tophat_unmapped_reads.py input_bam_dir [output_bam_dir]```

input_bam_dir should be a directory containing both accepted_hits.bam and unmapped.bam.
output_bam_dir (default: input_bam_dir) is the directory to write the fixed input BAM file to.

Note: unmapped.bam is read into memory, so make sure your computer has enough RAM to fit it.
