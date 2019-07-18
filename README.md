TopHat-Recondition
==================

[![bioconda-badge](https://img.shields.io/badge/install%20with-bioconda-brightgreen.svg?style=flat-square)](http://bioconda.github.io)

tophat-recondition is a post-processor for TopHat unmapped reads (contained in *unmapped.bam*), making them compatible with downstream tools
(e.g., the Picard suite, samtools, GATK) ([TopHat issue #17](https://github.com/DaehwanKimLab/tophat/issues/17)).  It also works around bugs in TopHat:

- the "mate is unmapped" SAM flag is not set on any reads in the unmapped.bam file ([TopHat issue #3](https://github.com/DaehwanKimLab/tophat/issues/3))
- the mapped mate of an unmapped read can be absent from *accepted_hits.bam*, creating a mismatch between the file and the unmapped read's flags ([TopHat issue #16](https://github.com/DaehwanKimLab/tophat/issues/16))

This software was developed as part of a PhD research project in the
[laboratory of Lao H. Saal, Translational Oncogenomics Unit, Department of Oncology and Pathology, Lund University, Sweden](http://www.med.lu.se/saalgroup).

A detailed description of the software can be found in [Brueffer and Saal (2016)](http://dx.doi.org/10.1186/s12859-016-1058-x).


Requirements
------------

- Python 2.7 or Python 3
- [pysam](https://github.com/pysam-developers/pysam)

TopHat-Recondition is available for installation with the conda package manager via the [bioconda](http://bioconda.github.io/) channel: ```conda install -c bioconda tophat-recondition```


Usage
-----

```
usage: tophat-recondition.py [-h] [-l LOGFILE] [-m MAPPED_FILE] [-q]
                             [-r RESULT_DIR] [-u UNMAPPED_FILE] [-v]
                             tophat_result_dir

Post-process TopHat unmapped reads. For detailed information on the issues
this software corrects, please consult the software homepage:
https://github.com/cbrueffer/tophat-recondition

positional arguments:
  tophat_result_dir     directory containing TopHat mapped and unmapped read
                        files.

optional arguments:
  -h, --help            show this help message and exit
  -l LOGFILE, --logfile LOGFILE
                        log file (optional, (default: result_dir/tophat-
                        recondition.log)
  -m MAPPED_FILE, --mapped-file MAPPED_FILE
                        Name of the file containing mapped reads (default:
                        accepted_hits.bam)
  -q, --quiet           quiet mode, no console output
  -r RESULT_DIR, --result_dir RESULT_DIR
                        directory to write unmapped_fixup.bam to (default:
                        tophat_output_dir)
  -u UNMAPPED_FILE, --unmapped-file UNMAPPED_FILE
                        Name of the file containing unmapped reads (default:
                        unmapped.bam)
  -v, --version         show program's version number and exit
```


Please make sure *tophat_output_dir* contains both, the mapped file (default: *accepted_hits.bam*) and the unmapped file (default: *unmapped.bam*).  The fixed
reads will be written to a file with the unmapped file name stem and the suffix *_fixup*, e.g. *unmapped_fixup.bam*, in *result_dir*.

**Note:** The unmapped file is read into memory, so make sure your computer has enough RAM to fit it.


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
