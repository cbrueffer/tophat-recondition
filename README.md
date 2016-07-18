TopHat-Recondition
==================

tophat-recondition is a post-processor for TopHat unmapped reads (contained in *unmapped.bam*), making them compatible with downstream tools
(e.g., the Picard suite, samtools, GATK) ([TopHat issue #17](https://github.com/infphilo/tophat/issues/17)).  It also works around bugs in TopHat:

- the "mate is unmapped" SAM flag is not set on any reads in the unmapped.bam file ([TopHat issue #3](https://github.com/infphilo/tophat/issues/3))
- the mapped mate of an unmapped read can be absent from *accepted_hits.bam*, creating a mismatch between the file and the unmapped read's flags ([TopHat issue #16](https://github.com/infphilo/tophat/issues/16))

This software was developed as part of a PhD research project in the
[laboratory of Lao H. Saal, Translational Oncogenomics Unit, Department of Oncology and Pathology, Lund University, Sweden](http://www.med.lu.se/saalgroup).

A detailed description of the software can be found in [Brueffer and Saal (2016)](http://dx.doi.org/10.1186/s12859-016-1058-x).


Requirements
------------

- Python 2.7 or Python 3
- [pysam](https://github.com/pysam-developers/pysam)


Usage
-----

```
Usage:

tophat-recondition.py [-hv] [-l logfile] tophat_output_dir [result_dir]

-h                 print this usage text and exit (optional)
-l                 log file (optional, default: result_dir/tophat-recondition.log)
-q                 quiet mode, no console output (optional)
-v                 print the script name and version, and exit (optional)
tophat_output_dir: directory containing accepted_hits.bam and unmapped.bam
result_dir:        directory to write unmapped_fixup.bam to (optional,
                   default: tophat_output_dir)
```

Please make sure *tophat_output_dir* contains both, the *accepted_hits.bam* and *unmapped.bam* file.  The fixed
reads will be written to the file *unmapped_fixup.bam* in *result_dir*.

**Note:** *unmapped.bam* is read into memory, so make sure your computer has enough RAM to fit it.


Details
-------

Specifically, the script does the following (see [SAM format specification](http://samtools.github.io/hts-specs/SAMv1.pdf)
for details on the fields in capital letters):

- Fixes wrong flags resulting from a bug in TopHat:
  * For paired reads where both reads are unmapped, TopHat does not set the 0x8 flag ("mate is unmapped") on either read.

- Removes /1 and /2 suffixes from read names (QNAME), if present.

- Sets mapping quality (MAPQ) for unmapped reads to 0.  TopHat sets it to 255 which some downstream tools don't like (even though it is a valid value according to the SAM specification).

- If an unmapped read's paired read is mapped, set the following fields in the unmapped read (downstream tools like Picard AddOrReplaceReadGroups get confused by the values TopHat fills in for those fields):
  * RNAME: RNAME of the paired read
  * RNEXT: RNAME of the paired read
  * POS:   POS of the paired read
  * PNEXT: 0

- For unmapped reads with missing mapped mates, unset the mate-related flags to effectively make them unpaired.  The following flags are unset:
  * 0x1  (mate is paired)
  * 0x2  (mate in proper pair)
  * 0x8  (mate is unmapped)
  * 0x20 (mate is reversed)
  * 0x40 (first in pair)
  * 0x80 (second in pair)

Examples of error messages emitted by downstream tools when trying to process unmapped reads without some or all of these
modifications can be found in [this thread in the SEQanswers forum](http://seqanswers.com/forums/showthread.php?t=28155),
which lead to the development of this software.


Citation
--------

If you use this software in your research and would like to cite it, please use the citation information in the [CITATION](https://github.com/cbrueffer/tophat-recondition/blob/master/CITATION) file.
