# Change Log
All notable changes to this project will be documented in this file.

## [1.3] - 2016-08-15
### Fixed
- Fixed logging warnings when using Python 2.7

## [1.2] - 2016-07-20
### Added
- New commandline switches (-m and -u) to allow specifying different
  names for the mapped and unmapped file (relative to the specified
  "tophat_output_dir").  The defaults are the standard TopHat names
  accepted_hits.bam and unmapped.bam.
- Added logging of the directory that the result file is written to.

## [1.1] - 2016-07-18
### Added
- Logging of how many reads were fixed in each problem category

### Changed
- Utilizes the argparse module for commandline parsing
- As a consequence of the above, the argument "result_dir" was converted
  into a proper optional argument under the -r flag.  If you use this
  feature, the commandline invocation has changed a little.
- Support for Python 2.6 was dropped.

### Fixed
- Fixed some issues under Python 3
- Debug messages go to STDERR

## [1.0] - 2015-11-03
### Changed
- Fixed log output to say BAM when BAM is meant.

### Fixed
- Do not print log output in case only the usage message is printed.

## [0.4] - 2015-08-18
### Added
- Added logging support.  A log file different from the default can be
  specified with the -l flag.
- Added a -q (quiet) option that suppresses console output.

### Changed
- Lots of internal refactoring.

### Fixed
- Fixed a problem with the "unmapped reads which have a mapped mate" fix in
  version 0.3.  This fix collided with the 0x8 flag fix, resulting in overzealous
  unpairing of unmapped reads.

## [0.3] - 2015-08-13
### Added
- Fixed an issue with unmapped reads which have a mapped mate.  Some of these reads
  do not have an actual mate in the TopHat BAM files (TopHat seems to discard them),
  thus leading to errors in downstream tools.  For these unmapped reads, unset the
  mate-related flags to effectively make them unpaired.
  This has been reported as TopHat issue #16: https://github.com/infphilo/tophat/issues/16
  Reported and tested by: Chris Cole (@drchriscole at GitHub)
- A SAM PG header is appended to the *unmapped_fixup.bam* file to note processing by this software.
- Added CHANGELOG.md (this file).

### Changed
- Updated citation information.
- Updated usage instructions.

### Fixed
- Debug mode now actually works.

## [0.2] - 2014-10-29
### Added
- Python 3 compatibility.
- Added more information to README.md.

### Changed
- Renamed the software to *TopHat-Recondition*.

## 0.1 - 2014-10-16
### Added
- First release of the software as *fix_tophat_unmapped_reads*.

[unreleased]: https://github.com/cbrueffer/tophat-recondition/compare/v1.3...HEAD
[1.3]: https://github.com/cbrueffer/tophat-recondition/compare/v1.2...v1.3
[1.2]: https://github.com/cbrueffer/tophat-recondition/compare/v1.1...v1.2
[1.1]: https://github.com/cbrueffer/tophat-recondition/compare/v1.0...v1.1
[1.0]: https://github.com/cbrueffer/tophat-recondition/compare/v0.4...v1.0
[0.4]: https://github.com/cbrueffer/tophat-recondition/compare/v0.3...v0.4
[0.3]: https://github.com/cbrueffer/tophat-recondition/compare/v0.2...v0.3
[0.2]: https://github.com/cbrueffer/tophat-recondition/compare/v0.1...v0.2
