# Specialised CZI Stitcher for Fiji/ImageJ

## ✅ Current Version: v36.0 (Stable - December 2024)

**Status:** Production-ready with full ImageJ Grid/Collection stitching integration

**Recommendation:** Use `main_v36_standalone` - single-file, full-featured, tested with large datasets

---

A specialized Fiji/ImageJ batch processing pipeline for Zeiss .czi files with accurate stage position-based stitching, metadata preservation, and multi-tile support optimized for large-scale imaging.

## Features

### Core Functionality (v36.0)
- ✅ **ImageJ Grid/Collection Stitching** - 2D phase correlation matching with sub-pixel accuracy
- ✅ **3D Linear Blending Fusion** - Smooth tile transitions, optimized for speed
- ✅ **Stage Position Integration** - Accurate tile placement from CZI metadata (no manual adjustment)
- ✅ **Multi-Tile Support** - Tested with 100+ tiles, 40+ z-layers, 10k×10k output
- ✅ **Channel Color Preservation** - Automatic LUT application from OME-XML metadata
- ✅ **Pixel Calibration** - Correct scaling (e.g., 0.345 µm/pixel, not 3.45 µm)
- ✅ **Unicode Support** - Handles German characters (ä, ü, ö) and µ symbols in paths
- ✅ **Completion Jingle** - Audio notification when processing complete

### Technical Specifications
- **Scalability:** 40+ z-layers, 100+ tiles per file, 10,000×10,000 pixel output
- **Channels:** Multi-channel composite support (4+ channels tested)
- **Bit Depth:** 16-bit preservation
- **File Sizes:** Multi-GB CZI files (tested with 1.4GB + 5GB + 3.1GB)
- **Performance:** ~1267 seconds for 9.5GB total (3 files) = ~21 minutes

### Architecture
- **Single standalone file:** `main_v36_standalone` (692 lines, clean and maintainable)
- **No external dependencies:** Embedded OMEMetadataAccessor class
- **Works everywhere:** Any Fiji installation with Bio-Formats + Stitching plugin

## Installation & Quick Start

### Requirements
- Fiji/ImageJ with Bio-Formats plugin (included in standard Fiji)
- ImageJ Stitching plugin (included in standard Fiji)
- Java 8 or higher

### Usage

1. **Download** `main_v36_standalone` from this repository
2. **Open Fiji** and navigate to: Plugins → Scripting → Run...
3. **Select** the `main_v36_standalone` file
4. **Configure in dialog:**
   - Input folder: Directory containing .czi files
   - Output folder: Destination for stitched results
   - ☑ Show stitched result (display in Fiji)
   - ☐ Save stitched result (write to disk as TIFF)
   - ☑ Cleanup temporary files (remove intermediate files)
   - ☐ Verbose mode (detailed logging for troubleshooting)
   - ☑ Play completion jingle (audio notification)
5. **Click OK** to start batch processing

### Output

**Stitched results include:**
- Proper pixel calibration (e.g., 0.345 µm/pixel from metadata)
- Channel colors as RGB LUTs from CZI metadata
- Multi-channel composite if source has >1 channel
- Full z-stack preserved if multiple z-layers present

**File naming:** `[original_filename]_stitched.tif`

## Version History

### v36.0 (Current - December 2024)

**Major Changes:**
- Full ImageJ Grid/Collection stitching pipeline integration
- Stage position-based tile placement with default parameters (no manual tuning)
- 2D phase correlation matching + 3D linear blending fusion
- Sub-pixel accuracy alignment
- Optimized for large datasets (40+ layers, 100+ tiles)
- Streamlined dialog (removed unnecessary parameter inputs)

**Features:**
- LUT/Color detection and application from OME-XML
- Correct pixel size scaling (fixed 10× error from v34.8)
- Completion jingle with MIDI notes
- Unicode-safe file path handling
- Embedded metadata accessor (no import issues)

**Performance:**
- Single-threaded tile extraction (Bio-Formats library limitation)
- Multi-threaded stitching computation (ImageJ plugin handles this automatically)
- Memory-efficient: tiles loaded on-demand during stitching
- Automatic temp file cleanup

**Stitching Pipeline:**
1. Extract tiles from CZI using Bio-Formats (each series = one tile)
2. Read stage positions from CZI metadata (micrometers)
3. Create TileConfiguration.txt with pixel coordinates
4. Run ImageJ stitching with Linear Blending and sub-pixel accuracy
5. Apply channel colors and pixel calibration from metadata
6. Display and/or save result

**Known Limitations:**
- No Rolling Ball background subtraction (removed for performance)
- No z-projection options (focused on core stitching functionality)
- Bio-Formats tile extraction is single-threaded (library limitation)

### v35.0 (Superseded - Development Phase)

Minimal rebuild for testing 3 core features (LUTs, pixel size, jingle) without stitching. Development version that:
- Identified DummyMetadata issue when Bio-Formats reader created without explicit metadata store
- Established clean OMEMetadataAccessor pattern for metadata handling
- Fixed MetadataTools import location (loci.formats not loci.formats.meta)
- Created diagnostic tools (pixel_size_checker.py) to isolate metadata problems

**Purpose:** Establish working foundation before reintegrating stitching complexity.

**Result:** Clean metadata handling pattern successfully tested → integrated into v36.0

### v34.8 (Historical - Complex Implementation)

Previous version with many features but increasing complexity (2280 lines). Through 51 commits and 6 critical bug fixes, complexity reached unsustainable levels:

**Bugs Fixed in v34.x series:**
1. **Jython Boolean Conversion** - All checkboxes always True (v34.6-7)
2. **UTF-8 µ Character Crash** - ASCII codec errors in OME-XML parsing (v34.3-5)
3. **10× Pixel Size Error** - Correction factor wrongly applied to OME-XML values (v34.8)
4. **Log Visibility Loss** - Diagnostic info cleared before user could read (v34.5)
5. **Variable Name Error** - c_file undefined causing crashes (v34.8)
6. **German Characters** - Encoding errors with ä, ü, ö in paths (diagnostic tools)

See [BUGFIXES.md](BUGFIXES.md) for complete technical documentation of each bug.

**Why Superseded:** While individual bugs were fixed, codebase became too complex to maintain reliably. Led to v35.0 minimal rebuild → v36.0 with clean integration.

**Historical Value:** Reference implementation for advanced features, kept for code patterns.

## File Structure

```
Repository/
├── main_v36_standalone           # v36.0 (PRODUCTION ← USE THIS!)
│                                 # 692 lines, single file, full features
│
├── ome_metadata_accessor.py      # Metadata extraction module
│                                 # (standalone, for custom scripts)
│
├── pixel_size_checker.py         # Diagnostic: pixel size extraction test
├── xml_parser.py                 # Diagnostic: metadata viewer
├── xml_debug.py                  # Diagnostic: Bio-Formats comprehensive test
│
├── BUGFIXES.md                   # Historical bug documentation (v34.8)
├── README.md                     # This file
│
├── main                          # v34.8 (reference only, 2280 lines)
├── main_v35_standalone           # v35.0 (superseded, 587 lines)
└── main_v35                      # v35.0 (superseded, two-file version)
```

## Diagnostic Tools

**For troubleshooting metadata extraction issues:**

- **pixel_size_checker.py** - Tests pixel size extraction specifically
  - Identifies if getting DummyMetadata vs OMEXMLMetadataImpl
  - Shows which Bio-Formats approach works for your files
  - Provides exact code fix for metadata problems

- **xml_debug.py** - Comprehensive Bio-Formats API testing
  - Tests 15 unicode conversion methods
  - Tests 12 different Bio-Formats API calls
  - Shows which methods successfully extract metadata

- **xml_parser.py** - Human-readable metadata viewer
  - Displays all key OME-XML fields
  - Shows image info, stage positions, pixel sizes, channel data
  - Unicode-safe output with proper formatting

**For custom script development:**

- **ome_metadata_accessor.py** - Reusable metadata module
  - Can be imported by custom Jython scripts (Jython import limitations may apply)
  - Clean API for OME-XML access
  - Same code embedded in main_v36_standalone

## Known Issues & Bug Fixes

**Current Status:** v36.0 stable with all critical bugs from v34.8 fixed

**Historical Issues:** See [BUGFIXES.md](BUGFIXES.md) for:
- Complete technical explanation of 6 bugs fixed in v34.1-v34.8
- Root cause analysis for each issue
- Code examples (before/after)
- Impact analysis and testing procedures
- Lessons learned for Jython development

## Development History & Methodology

**Problem Identification & Testing:** [Ixytocin](https://github.com/Ixytocin)

**Implementation:** AI-assisted development using:
- ~20 iterations with Gemini (Google AI) for v34.x debugging
- GitHub Copilot for v35.0 rebuild and v36.0 integration

**Approach:** Iterative debugging and diagnostic tool development to identify root causes, followed by clean rebuilds when complexity became unmanageable.

**Evolution:**
1. v34.8: Complex implementation (2280 lines) - worked but fragile
2. v35.0: Minimal rebuild (587 lines) - established clean patterns
3. v36.0: Full integration (692 lines) - production-ready with all features

**Methodology Note:** The author cannot personally understand or debug the implementation. All credit belongs to the open-source tools being orchestrated and the training data of the LLMs used.

## Credits

- **Fiji/ImageJ** - Image processing platform
- **Bio-Formats** - OME-XML and CZI file handling
- **ImageJ Stitching Plugin** - Grid/Collection stitching with fusion
- **Development Tools:** Gemini AI, GitHub Copilot
- **Testing & Requirements:** Ixytocin

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
1. Check [BUGFIXES.md](BUGFIXES.md) for historical bug solutions
2. Run diagnostic tools (pixel_size_checker.py, xml_debug.py) to isolate problems
3. Open an issue on GitHub with log output and diagnostic results

---

**Last Updated:** December 2024 (v36.0 release)
