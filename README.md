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
This project was developed through iterative AI-assisted prototyping - a method the author describes as "the blind following a guide that never drank water." 

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
