# Specialised CZI Stitcher

> **⚠️ DEVELOPMENT DISCLAIMER**  
> **Problem Identification & Testing:** [Ixytocin](https://github.com/Ixytocin)  
> **Implementation:** ~20 iterations with Gemini (Google AI), followed by GitHub Copilot  
> **Methodology:** AI-assisted development - The author cannot personally understand or debug the implementation. All credit belongs to the open-source tools being orchestrated and the training data of the LLMs used.

---

A specialized Fiji/ImageJ batch processing pipeline for Zeiss .czi files. Engineered for the specific challenges of ApoTome imaging and large-scale brain section reconstruction.

## Problem Solved
Standard stitching routines often fail with Zeiss .czi files by:
- **Dimension Mismatch:** Misinterpreting channels as Z-slices (Interleaving error).
- **Metadata Loss:** Losing original LUTs (colors) and scaling.
- **ApoTome Artifacts:** Visible tiling edges due to grid-based illumination patterns.
- **Hardware Limits:** Crashing on large datasets (e.g., whole hamster brain slices).

## Features
- **Hybrid 2D/3D Alignment:** Calculates registration on fast 2D Maximum Intensity Projections (MIP) and applies coordinates to full 3D multichannel volumes.
- **Hyperstack Integrity:** Forces correct dimension mapping (C, Z, T) and recovers original Zeiss channel colors (RGBA format).
- **Z-Stack Projections:** 6 methods (Max, Average, Min, Sum, SD, Median) with save/view options.
- **Enhanced Filenames:** Output files include processing parameters (e.g., `sample_stitched_rb50_max_projection.tif`).
- **Shading Correction:** Integrated per-tile Rolling Ball background subtraction to ensure seamless transitions.
- **Batch Processing:** Handles entire directories of CZI files automatically with fail-fast ordering (largest first).
- **Automatic BigTIFF:** Detects when files exceed 2GB and switches format automatically.
- **Unicode Safety:** Robust handling of file paths containing spaces or special characters.
- **Audio Feedback:** Plays a MIDI triad (E-G#-C) on the system synthesizer upon completion.

### Technical Background: The Hybrid Solution
The decision to implement a **2D-Registration / 3D-Fusion Hybrid** was born out of necessity. 

Traditional 3D-stitching in Fiji often struggles with:
1. **Dimension Interleaving:** Losing the distinction between Channels and Z-Slices during the fusion process of raw .czi data.
2. **Computational Overhead:** Attempting to calculate overlaps on full 3D multichannel volumes is memory-intensive and prone to failure on standard workstations.

**The Specialized Approach:** By decoupling the *Registration* (using 2D Maximum Intensity Projections) from the *Fusion* (applying calculated coordinates to 3D volumes), we ensure 100% metadata integrity and significantly higher processing stability for large-scale brain sections.


## Requirements
- **Fiji (ImageJ)**
- **Bio-Formats Plugin**
- **Stitching Plugin** (Preibisch et al.)

## Installation & Usage
1. Download `Specialised_CZI_Stitcher` script.
2. Place it in your `Fiji.app/scripts/` folder.
3. Restart Fiji and run the script from the menu.
4. Select Source and Target folders. Use 'Rolling Ball' (Radius ~50-100) if tiling artifacts are visible.

## Processing Flow

The pipeline executes the following steps for each CZI file:

### 1. Metadata Extraction & Analysis
- **Read CZI metadata** using Bio-Formats to discover tile positions, dimensions, and channel information
- **Extract tile coordinates** from Zeiss acquisition metadata (grid positions, pixel sizes)
- **Detect channel colors** from RGBA metadata (common immunofluorescence wavelengths: DAPI/blue, AF488/green, AF647/red)
- **Log tile configuration** including number of tiles, pixel ranges, and effective pixel size after correction factor

### 2. Tile Preparation (Parallel Processing)
For each tile position, executed in parallel threads:
- **Load tile data** from CZI using Bio-Formats with specific series index
- **Optional: Rolling Ball background subtraction** (if enabled) to remove shading artifacts and ensure seamless stitching
  - Larger radius (50-100) = more aggressive background removal
  - Should be larger than features of interest
- **Create 2D Maximum Intensity Projection** (MIP) for fast registration
- **Save temporary MIPs** to processing directory for stitching plugin
- **Save 3D multichannel volumes** if 3D output requested

### 3. 2D Registration (Stitching Plugin)
- **Calculate tile overlaps** using 2D MIP images for computational efficiency
- **Phase correlation** to determine precise X,Y offsets between adjacent tiles
- **Quality metrics** computed (correlation coefficient R) for each tile pair
- **Generate fusion layout** with optimized tile positions

### 4. 3D Fusion
- **Apply 2D registration coordinates** to full 3D multichannel volumes
- **Fuse overlapping regions** using linear blending (default) or max intensity
- **Preserve all channels** and z-slices from original acquisition
- **Result:** Single stitched hyperstack (X, Y, C, Z dimensions)

### 5. Post-Processing
- **Convert to HyperStack** with correct dimension order (Channels, Z-slices, Timepoints)
- **Apply channel LUTs** from metadata or use standard microscopy colors (optional override)
  - Hoechst/DAPI → Blue
  - AF488 → Green  
  - AF647 → Magenta (far-red displayed as magenta for visibility)
- **Set composite display mode** for proper multi-channel visualization

### 6. Z-Stack Processing (Optional)
If sharp-slice detection enabled:
- **Phase 1: Monte Carlo Gatekeeper** - Quick triage using 50 random probes per slice
  - REJECT: Below noise floor (skip)
  - COMMIT: High quality (mark for spreading-fire)
  - INSPECT: Mixed quality (defer to detailed analysis)
- **Phase 2: Spreading-Fire** - Propagate from COMMIT slices to neighbors
- **Phase 3: Targeted Analysis** - Only analyze unvisited INSPECT slices
- **Hole-filling** - Merge nearby sharp ranges (gaps ≤2 slices)
- **Select z-range** containing in-focus content

If z-projection requested:
- **Create projection** using selected method (Max, Average, Min, Sum, SD, Median)
- **Apply from detected z-range** if sharp-slice detection enabled, otherwise entire stack
- **Inherit channel LUTs** from parent hyperstack
- **Display and/or save** based on user options

### 7. Output & Cleanup
- **Display stitched volume** (if Show Stitched enabled)
- **Save stitched volume** (if Save Stitched enabled) with automatic BigTIFF for files >2GB
- **Display z-projection** (if Show Z-Projection enabled)
- **Save z-projection** (if Save Z-Projection enabled)
- **Enhanced filenames** include processing parameters: `filename_stitched_rb50_z6-16_max_projection.tif`
- **Memory management** - Flush ImageJ memory and close temporary images
- **Log memory usage** - Report used/max memory after each file
- **Cleanup temp files** - Remove processing directory (optional, default: enabled)

### 8. Batch Completion
- **Progress tracking** - Shows [current/total] files with human-readable timing
- **Memory monitoring** - Logs memory usage after each file
- **Audio notification** - Plays musical jingle if enabled (repeats until acknowledged)
- **Summary logging** - Total batch time in human-readable format (s/m/h)

### Error Handling
- **Fail-fast strategy** - Process largest file first to catch errors early
- **Exception logging** - All errors logged with context (file, tile, operation)
- **Graceful degradation** - Continue batch processing after individual file failures
- **Debug mode** - Exhaustive logging of LUT application, tile processing, and performance metrics

## Roadmap & Future Features

### Stage 1: Advanced Z-Slice Detection ✅ **IMPLEMENTED**
**Status:** Complete in v33.0
- **Monte Carlo Gatekeeper:** Fast pre-screening using 50 random sample probes to classify slices as REJECT/COMMIT/INSPECT
- **Spreading-Fire Optimization:** Propagate from known-sharp slices to neighbors instead of exhaustive search (~30-50% performance gain)
- **REJECT/COMMIT/INSPECT Triage:** Efficient three-state classification before detailed analysis
- **Exhaustive Debug Logging:** Comprehensive performance metrics and slice-by-slice classification tracking

**Technical Details:**
- Phase 1: Monte Carlo sampling (50 probes per slice) for quick triage
- Phase 2: Spreading-fire propagation from COMMIT slices
- Phase 3: Targeted analysis of unvisited INSPECT slices
- Performance reporting shows % reduction in full slice analysis
- Debug mode provides detailed classification and score logging

### Planned Enhancements (Not Yet Implemented)

**Stage 2: True Focus Stacking (Extended Depth of Field)**
- **Fractal Tessellation Engine:** Recursive spatial subdivision with adaptive sharpness-based region selection
- **Per-Pixel Z-Selection:** Create single 2D composite from sharpest pixels at each x,y location across z-slices
- **Boundary Blending:** Seamless tile integration for artifact-free focus stacking

**Stage 3: Non-Coplanar Plane Fitting**
- **Geometric Tilt Detection:** 9-point "pillar" sampling to detect systematic sample tilt
- **Adaptive Z-Range Selection:** Compute intersection of focus plane with z-stack for optimal slice selection
- **Bed-Leveling Analogy:** Correct for coverslip tilt (e.g., 200µm over 50mm) without over-sampling

### Rejected/Deferred Ideas
- **Multi-File Fusion:** Out of scope - current focus is single-file stitching and projection
- **GPU Acceleration:** Bio-Formats and Stitching plugins don't expose GPU hooks
- **Dynamic Thread Allocation:** Too complex vs benefit - current (cores-1) approach is stable
- **Custom Stitching Algorithm:** Reimplementing Preibisch et al.'s work not justified given quality and stability

## Credits & Attribution
This tool is a specialized orchestration wrapper for several powerful open-source components. The author's role was identifying the problem and testing - not creating new solutions:

- **Core Stitching Logic:** [BigStitcher/Stitching Plugin](https://imagej.net/plugins/stitching/) by Stephan Preibisch et al.
- **Metadata Handling:** [Bio-Formats](https://www.glencoesoftware.com/bio-formats.html) by the Open Microscopy Environment (OME).
- **Platform:** [Fiji/ImageJ](https://fiji.sc/) - The indispensable image processing ecosystem
- **QuPath Integration:** [QuPath](https://qupath.github.io/) - For downstream analysis
- **Starting Point:** [Viveca Stitching Tool](https://github.com/seiryoku-zenyo) by seiryoku-zenyo
- **Implementation:** AI-assisted development via Gemini and GitHub Copilot

The author is merely "the spark" - the real fire comes from these exceptional tools and their creators.

---

## Development Approach
This project was developed through iterative AI-assisted prototyping - a method the author describes as "the blind following a guide that never drank to find water." 

**What this means:**
- The author identified a specific problem (cannot stitch CZI files at home without ZEN license)
- Existing tools (Fiji, QuPath, Stitching, BigStitcher, Bio-Formats) provided *almost* the right functionality
- AI assistants were used to wire these tools together in a specialized way
- The author cannot personally understand or fix the implementation code
- All achievements belong to the training data and the open-source tools being orchestrated

**This approach works when:**
- The problem is highly specialized
- Existing powerful tools need custom orchestration
- Traditional development would be prohibitively expensive or time-consuming
- The user can validate results even without understanding implementation

**Use with caution:** Errors and limitations reflect both the AI's training and the author's inability to debug.
