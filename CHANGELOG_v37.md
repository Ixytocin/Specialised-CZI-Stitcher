# Changelog - v37.x Series (Beta Development)

## Purpose
This changelog documents the evolution from broken code to first stable beta (v37.4), tracking all critical fixes applied during the consolidation process.

---

## v37.4 (2025-12-25) - First Stable Beta
**Status**: First Minimal Viable Beta

### Added
- Comprehensive debug logging for image conversion workflow
- Visual markers for success (>>>) and errors/warnings (!!!)
- Detailed logging of HyperStack creation process
- Detailed logging of LUT application process
- Detailed logging of CompositeImage status
- Exception logging for stage label extraction
- Exception logging for unicode path conversion
- Exception logging for correction factor parsing

### Fixed
- **CRITICAL**: Added exception handling to IJ.saveAs() for 3D stacks (line 887)
  - Previously would crash silently on disk full or permission errors
  - Now logs error and re-raises exception
  - Essential: Cannot continue stitching without 3D stack files
- Silent exceptions in try_ome_stage_labels_from_xml() now logged
- Silent exceptions in unicode conversion now logged
- Silent exceptions in correction factor parsing now logged

### Changed
- All critical operations now have proper exception logging
- Debug output format standardized with visual markers
- Improved visibility into workflow state at each step

### Testing Status
- Exception handling validated
- Debug logging validated on test files
- Visual markers working correctly in Fiji log window

---

## v37.3 (2025-12-24)
**Status**: Critical Bug Fix

### Fixed
- **CRITICAL BUG #3**: setDisplayMode() called unconditionally after LUT application
  - Problem: If LUT application failed, imp was still a HyperStack
  - Calling setDisplayMode(IJ.COMPOSITE) on HyperStack could create new CompositeImage
  - This would overwrite custom LUTs with default colors
  - Fix: Check imp.isComposite() before calling setDisplayMode()
  - Only set display mode if image IS a CompositeImage

### Changed
- Store LUT application result in separate variable (imp_with_luts)
- Only update imp if LUT application succeeded
- Added defensive check before setDisplayMode()

### Testing Status
- Validated that setDisplayMode only called on CompositeImage
- Confirmed prevents overwriting of custom LUTs

---

## v37.2 (2025-12-24)
**Status**: Major Bug Fixes

### Fixed
- **CRITICAL BUG #1**: Exception handling returning wrong image
  - Problem: Outer try-except was falling through to return original image
  - Even if LUTs applied successfully, any exception would return imp instead of cimp
  - Fix: Added explicit return statements on all code paths
  - Now returns cimp on success, imp only on actual error

- **CRITICAL BUG #2**: HyperStack creation confusion
  - Problem: HyperStackConverter.toHyperStack() creates HyperStack, NOT CompositeImage
  - Was passing "grayscale", "Composite" parameters (unclear effect)
  - This created a basic HyperStack that needed CompositeImage wrapping
  - Fix: Create plain HyperStack only, let apply_channel_luts_to_image handle CompositeImage
  - Ensures single point of CompositeImage creation

### Changed
- Restructured exception handling in apply_channel_luts_to_image()
- Removed confusing parameters from toHyperStack() call
- Clear separation: HyperStack creation vs CompositeImage+LUT application

### Testing Status
- Validated exception handling preserves CompositeImage
- Confirmed single point of CompositeImage creation

---

## v37.1 (2025-12-24)
**Status**: User Experience Improvements

### Added
- ASCII art splash screen with version tracking
- Component version display (v31.16h workflow, v34.8 UTF-8, v36.5 LUTs)
- Filesystem loading message: "Loading filesystem... This might take a while with sleeping HDDs"
- Extra spacing in splash for proportional fonts (I, i, t characters)

### Changed
- Auto-adjust default changed from ON to OFF
- User preference for manual brightness/contrast control
- Splash screen layout adjusted for better alignment in Fiji log

### Fixed
- Splash screen spacing improved for narrow characters
- Better visual alignment in proportional font environments

### Testing Status
- Splash screen verified in Fiji log window
- Filesystem message displays correctly after config load
- Auto-adjust default OFF confirmed

---

## v37.0 (2025-12-24)
**Status**: Foundation - Compilation & Critical Fixes

### Fixed
- **COMPILATION ERROR**: Jython ParseException on encoding declaration
  - Problem: # -*- coding: utf-8 -*- is invalid in Jython 2.7
  - Problem: Non-ASCII characters (µ, ä, ö, ü, ß, →, —) without declaration also fail
  - Fix: Removed encoding declaration
  - Fix: Replaced all non-ASCII characters in comments/docstrings with ASCII
  - Kept unicode escape sequences (\u00b5, \u03bc) in string literals (valid ASCII)
  - Result: File is pure ASCII, loads without ParseException

- **PIXEL SIZE ERROR**: Always falling back to global metadata (3.45 um instead of 0.345 um)
  - Problem: µ character in unit string "µm" triggered ASCII codec errors
  - This caused Method 1 (OME-XML) to fail, falling back to Method 4 (global metadata)
  - Global metadata returns 10x larger values
  - Fix: Wrap unit string processing with ensure_unicode()
  - Fix: Add comprehensive try-except in _unit_to_um() function
  - Fix: Handle both Java Double and Python float from Bio-Formats API
  - Result: Method 1 succeeds, extracts correct 0.345 um from OME-XML

- **LUT COLOR INITIAL FIX**: CompositeImage mode not set correctly
  - Problem: Creating CompositeImage without specifying mode defaults to COLOR
  - COLOR mode ignores custom LUTs and uses Fiji defaults (R/G/B/Gray)
  - Fix: Explicitly create with CompositeImage.COMPOSITE mode
  - Fix: Call updateAllChannelsAndDraw() instead of updateAndDraw()
  - Result: Partial fix (more issues discovered in v37.2-v37.3)

### Changed
- All unicode handling via explicit u"..." strings
- All file I/O via codecs.open(..., encoding='utf-8')
- All string operations via .format() not +
- Removed all hardcoded correction factors from pixel size handling

### Testing Status
- File loads in Jython without errors
- Pixel size extraction validated (0.345 um from OME-XML)
- LUT colors show improvement but still issues (fixed in later versions)

---

## Root Causes Identified

### Complexity-Induced Regression
**User Quote**: "We had working stitching, then broke it under refinement. Then had working LUT structure, broke it implementing stitching."

**Problem Pattern**:
1. v31.16h had working 2D→3D stitching workflow
2. Refinement attempts broke the working code
3. v36.x had working LUT detection
4. Integrating LUT detection into stitching broke both

**Solution**: Consolidate ONLY proven working components without experimental additions.

### Multiple Points of Failure in LUT Application

**Discovered Bugs** (fixed across v37.0-v37.4):
1. ❌ CompositeImage not created in COMPOSITE mode → Fixed v37.0
2. ❌ Exception handling returning wrong image → Fixed v37.2
3. ❌ HyperStack creation creating wrong image type → Fixed v37.2
4. ❌ setDisplayMode called on wrong image → Fixed v37.3
5. ❌ Silent exceptions hiding real problems → Fixed v37.4

**Each bug masked the others**, making it appear that fixes weren't working when actually each fix was necessary but insufficient alone.

---

## Validation Strategy

### What Changed Between Versions
Each version should be validated against the specific bugs it fixed:

- **v37.0**: Check script loads without ParseException, pixel size correct
- **v37.1**: Check splash screen appears, auto-adjust OFF
- **v37.2**: Check exception handling, HyperStack creation
- **v37.3**: Check setDisplayMode only called on CompositeImage
- **v37.4**: Check debug logging shows `>>>` markers, exceptions logged

### Regression Testing
After each version, verify previous fixes still work:
- Script still loads (v37.0)
- Pixel size still correct (v37.0)
- Splash still appears (v37.1)
- Exception handling still correct (v37.2)
- setDisplayMode still guarded (v37.3)

---

## Known Issues (v37.4)

### LUT Color Application
**Status**: Fixed to best of our knowledge, but needs user validation

**What we fixed**:
- CompositeImage created in COMPOSITE mode ✓
- Exception handling preserves CompositeImage ✓
- Single point of CompositeImage creation ✓
- setDisplayMode only called on CompositeImage ✓
- All exceptions logged with visual markers ✓

**What still might fail**:
- Non-standard color formats in OME-XML
- Edge cases in Bio-Formats metadata
- ImageJ/Fiji version differences

**How to diagnose**: Check debug log for `=== IMAGE CONVERSION AND LUT APPLICATION ===` section, look for `!!!` markers.

### Performance
**Status**: Not optimized

**Known limitations**:
- 100+ tiles not tested
- Large z-stacks (50+) may be slow
- No parallelization of tile extraction
- Temp files not cleaned up on exception

**Planned**: Performance optimization after core functionality validated.

---

## Development Methodology

### Vibe Coding Process
1. **User identifies problem**: "Colors show as red/green/blue/gray"
2. **User provides data**: Logs showing RGB values from debug output
3. **User analyzes root cause**: "It's RGBA format, signed 32-bit integers"
4. **We implement their analysis**: Not our assumptions
5. **User tests**: Reports if fix works or new issue discovered
6. **Iterate**: Repeat until working

### Why This Works
- **User is domain expert**: Knows Zeiss systems, microscopy, CZI format
- **We are code experts**: Know Jython, ImageJ API, exception handling
- **Separation of concerns**: User focuses on "what", we focus on "how"
- **Rapid iteration**: Each version addresses specific user-reported issues

---

## Migration Guide

### From v31.16h (Original Working Version)
- ✅ 2D→3D stitching workflow preserved
- ✅ Rolling ball background subtraction preserved
- ✅ Batch processing preserved
- ➕ LUT retention added
- ➕ Pixel size accuracy improved
- ➕ Exception handling improved
- ➕ Debug logging added

### From v36.x (LUT Detection Versions)
- ✅ RGBA color parsing preserved
- ✅ OME-XML metadata extraction preserved
- ➕ Stitching workflow re-integrated
- ➕ Exception handling fixed
- ➕ Multiple LUT application bugs fixed
- ➕ Debug logging added

---

## Future Work (Post-Beta)

### Planned for v38.x (if needed)
- Performance optimization for 100+ tiles
- Sharp-slice detection (user requested, not yet implemented)
- ROI-based sharp detection (user requested, not yet implemented)
- Memory usage optimization
- Temp file cleanup on exception

### Not Planned
- Multi-format support (keep focus on Zeiss .czi)
- GUI improvements (GenericDialog is sufficient)
- Auto-correction of "wrong" colors (user rejected)
- Localization (English is fine for scientific community)

---

**For detailed technical implementation, see WORKING_COMPONENTS_ANALYSIS.md**
**For usage instructions, see README_v37.4.md**
