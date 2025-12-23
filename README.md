# Specialised Batch Stitcher

> **⚠️ DEVELOPMENT HISTORY**  
> **Vision, Requirements & Validation:** [Ixytocin](https://github.com/Ixytocin)  
> **Implementation Partnership:** ~20 iterations with Gemini (Google AI), followed by GitHub Copilot  
> **Methodology:** Vibe Coding - Rapid prototyping through iterative AI-assisted development for highly specialized microscopy workflows

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
1. Download `main` script.
2. Place it in your `Fiji.app/scripts/` folder (rename to `Specialised_Batch_Stitcher.py` if desired).
3. Restart Fiji and run the script from the menu.
4. Select Source and Target folders. Use 'Rolling Ball' (Radius ~50-100) if tiling artifacts are visible.

## Credits & Attribution
This tool is a specialized wrapper that orchestrates several powerful open-source components:
- **Core Stitching Logic:** [BigStitcher/Stitching Plugin](https://imagej.net/plugins/stitching/) by Stephan Preibisch et al.
- **Metadata Handling:** [Bio-Formats](https://www.glencoesoftware.com/bio-formats.html) by the Open Microscopy Environment (OME).
- **Inspiration:** [Viveca Stitching Tool](https://github.com/seiryoku-zenyo) by seiryoku-zenyo - used as a starting point.
- **Development:** Vibe Coding methodology by **Ixytocin** with AI implementation partners (Gemini, GitHub Copilot).

---

## Vibe Coding Philosophy
This project demonstrates the power of **Vibe Coding** - a development approach where:
- Domain experts (researchers/users) drive requirements and validation
- AI assistants handle implementation details and iteration
- Rapid prototyping addresses extremely specialized needs
- Solutions evolve through conversational development

Perfect for niche scientific tools where traditional development would be prohibitively expensive or time-consuming.
