# Specialised-CZI-Stitcher (Ixytocin-Stitcher)

> **⚠️ VIBE CODING DISCLAIMER** > This tool was built using the **Vibe Coding** methodology.  
> **Vision, Neuro-Logic & Validation:** [Ixytocin](https://github.com/Ixytocin)  
> **Implementation & API-Orchestration:** Gemini (AI Research Partner)  

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
- **Hyperstack Integrity:** Forces correct dimension mapping (C, Z, T) and recovers original Zeiss channel colors.
- **Shading Correction:** Integrated per-tile Rolling Ball background subtraction to ensure seamless transitions.
- **Batch Processing:** Handles entire directories of CZI files automatically.
- **Unicode Safety:** Robust handling of file paths containing spaces or special characters.
- **Audio Feedback:** Plays a MIDI triad (E-G#-C) on the system synthesizer upon completion.



## Requirements
- **Fiji (ImageJ)**
- **Bio-Formats Plugin**
- **Stitching Plugin** (Preibisch et al.)

## Installation & Usage
1. Download `Specialised_CZI_Stitcher.py`.
2. Place it in your `Fiji.app/scripts/` folder.
3. Restart Fiji and run the script from the menu.
4. Select Source and Target folders. Use 'Rolling Ball' (Radius ~50-100) if tiling artifacts are visible.

## Credits & Attribution
This tool is a wrapper that orchestrates several powerful open-source components:
- **Core Stitching Logic:** [BigStitcher/Stitching Plugin](https://imagej.net/plugins/stitching/) by Stephan Preibisch et al.
- **Metadata Handling:** [Bio-Formats](https://www.glencoesoftware.com/bio-formats.html) by the Open Microscopy Environment (OME).
- **Inspiration:** [Viveca Stitching Tool](https://github.com/seiryoku-zenyo) by seiryoku-zenyo.
- **Refinement:** Developed by **Ixytocin** using Vibe Coding methodologies.
