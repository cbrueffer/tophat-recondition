# Change Log
All notable changes to this project will be documented in this file.

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

[unreleased]: https://github.com/cbrueffer/tophat-recondition/compare/v0.2...HEAD
[0.2]: https://github.com/cbrueffer/tophat-recondition/compare/v0.1...v0.2
