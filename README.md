misc_bioinf
===========

Repository for miscellaneous bioinformatics scripts I developed that may be useful to others.

fix_tophat_unmapped_reads.py
----------------------------

Fixes unmapped TopHat reads (contained in unmapped.bam) to make them compatible with other tools,
e.g. the Picard suite and samtools.  This script requires ```pysam``` to be installed.

Usage: ```$ ./fix_tophat_unmapped_reads.py tophat_output_dir```

tophat_output_dir should be a directory containing both accepted_hits.bam and unmapped.bam.
