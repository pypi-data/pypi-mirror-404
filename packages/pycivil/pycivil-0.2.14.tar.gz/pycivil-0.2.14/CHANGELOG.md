# Changelog

All notable changes to PyCivil will be documented in this file.

## Version 0.2.14

### Bug Fixes

1. Logo can now be changed in reports
2. Reports now display an alternative phrase when material is not set by code
3. Steel with id -1 is no longer printed in output
4. Improved assertion handling in fe.py
5. Fixed area properties calculation in RCTemplRectEC2
6. Fixed cracked parameters computation in RCTemplRectEC2

### Improvements

1. Added copyright notice to all Python files
2. File extensions are now handled as uppercase for consistency
3. Reorganized test_obj into separate shapes and geometry test files
4. Moved version history from README to dedicated CHANGELOG.md

### Documentation

1. Added comprehensive tutorials with Quick Start examples and Marimo notebook examples
2. Expanded Docs section in README with MkDocs build instructions

## Version 0.2.13

1. Type checking improvements with mypy
2. Updated pandas-stubs and dependencies

## Version 0.2.6

1. New features in FEAModel: support for frames and load combinations

## Version 0.2.0

1. Available on PyPI via `pip install pycivil`
2. Module xstrumodeler for generic shape RC section is a requirement
3. Separated sws-mind backend to separate module
4. Added Strand7 post-processor tool
