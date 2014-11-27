TopHat Recondition
==================

tophat-recondition (formally known as fix_tophat_unmapped_reads) modifies unmapped TopHat reads (contained in *unmapped.bam*) to make them compatible with downstream tools
(i.e., the Picard suite, samtools, GATK).  It also works around a bug in TopHat where
the "mate is unmapped" SAM flag is not set on any reads in the unmapped.bam file.

This script was developed as part of a PhD research project in the
[laboratory of Lao H. Saal, Translational Oncogenomics Unit, Department of Oncology and Pathology, Lund University, Sweden](http://www.med.lu.se/english/klinvetlund/oncology_and_pathology/research/canceromics_branch/research_units/translational_oncogenomics/).


Requirements
------------

- Python 2 (>= 2.6) or Python 3
- [pysam](https://github.com/pysam-developers/pysam)


Usage
-----

```
Usage:

tophat-recondition.py [-hv] tophat_output_dir [result_dir]

-h                 print this usage text and exit
-v                 print the script name and version, and exit
tophat_output_dir: directory containing accepted_hits.bam and unmapped.bam
result_dir:        directory to write unmapped_fixup.bam to (default: tophat_output_dir)
```

Please make sure *tophat_output_dir* contains both, the *accepted_hits.bam* and *unmapped.bam* file.  The fixed
reads will be written to the file *unmapped_fixup.bam* in *result_dir*.

**Note:** *unmapped.bam* is read into memory, so make sure your computer has enough RAM to fit it.


Details
-------

Specifically, the script does the following (see [SAM format specification](http://samtools.github.io/hts-specs/SAMv1.pdf)
for details on the fields in capital letters):

- Fixes a bug in TopHat (unfixed as of v2.0.13):
  * For paired reads where both reads are unmapped, TopHat does not set the 0x8 flag ("mate is unmapped") on either read.

- Removes /1 and /2 suffixes from read names (QNAME), if present.

- Sets mapping quality (MAPQ) for unmapped reads to 0.  TopHat sets it to 255 which some downstream tools don't like (even though it is a valid value according to the SAM specification).

- If an unmapped read's paired read is mapped, set the following fields in the unmapped read (downstream tools like Picard AddOrReplaceReadGroups get confused by the values TopHat fills in for those fields):
  * RNAME: RNAME of the paired read
  * RNEXT: RNAME of the paired read
  * POS:   POS of the paired read
  * PNEXT: 0

Examples of error messages emitted by downstream tools when trying to process unmapped reads without some or all of these
modifications can be found in [this thread in the SEQanswers forum](http://seqanswers.com/forums/showthread.php?t=28155),
which lead to the development of this software.


Citation
--------

We are in the process of publishing a manuscript involving tophat-recondition.
For now, if you use this software in your research, please cite it by its URL: https://github.com/cbrueffer/tophat-recondition
