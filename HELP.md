# Specialised CZI Stitcher v37.5 - User Guide

## Quick Start

1. Open Fiji
2. Load `main.jy` script
3. Click Run
4. Select input, output, and processing directories
5. Adjust parameters if needed (defaults usually work)
6. Click OK
7. Monitor log window for progress

---

## Parameter Explanations

### Directory Selection (NEW in v37.5)

#### Input Folder
**What it is**: Folder containing your .czi files

**Tips**:
- Can contain subdirectories (not processed)
- Will process all .czi files in this folder
- Path can contain spaces and German characters (ä, ö, ü, ß)

#### Output Folder
**What it is**: Where stitched images will be saved

**Tips**:
- Can be same as input (creates new files, doesn't overwrite)
- Must have write permissions
- Needs enough free space for stitched results

#### Processing/Temp Folder (NEW in v37.5)
**What it is**: Where temporary files are stored during processing

**Default**: Can be same as output folder

**Why change**:
- **Use RAM disk for speed**: `/dev/shm` (Linux), `R:\` (Windows), `/tmp` (macOS)
- **Use local SSD**: Much faster than network drives
- **Separate storage**: Keep temp files off slow drives

**Note**: Needs 2-3x space of largest .czi file

**Performance Tip**: Using a RAM disk can speed up processing by 2-5x!

### Fusion Method
**What it is**: How overlapping regions are blended

**Options**:
- **Linear Blending** (recommended): Smooth transitions
- Max Intensity: Takes brightest pixel (for sparse samples)
- Average: Simple average (faster but can show seams)

**Recommendation**: Use Linear Blending unless you have specific reason not to

### Rolling Ball Radius
**What it is**: Background correction to remove uneven illumination

**Range**: 0-200 pixels

**Recommended values**:
- 0 = No correction (use if illumination is even)
- 50 = Light correction (typical ApoTome)
- 100 = Moderate correction (uneven samples)
- 200 = Heavy correction (extreme gradients)

**How to choose**:
- Start with 50
- If you see visible tile edges, increase to 100
- If image looks over-corrected (dim regions too bright), decrease to 25

**Warning**: Too high radius can dim your signal, too low won't fix shading

### Regression Threshold
**What it is**: How well tiles must align to be considered valid

**Range**: 0.0-1.0

**Default**: 0.3 (30% correlation required)

**Recommendation**: Leave at 0.3 unless stitching fails

**Adjust if**:
- Tiles don't stitch: Lower to 0.2 (accept weaker matches)
- False matches: Increase to 0.4 (require stronger correlation)

### Max Displacement
**What it is**: How far (in pixels) to search for tile overlap

**Default**: 5.0 pixels

**Recommendation**: Leave at 5.0 unless stage positioning is very inaccurate

**Adjust if**:
- Tiles severely misaligned: Increase to 10 or 20
- Perfect stage positioning: Decrease to 2 (faster)


### Show Results (Preview)
**What it is**: Display stitched image in Fiji after processing

**Default**: Checked (ON)

**Turn OFF if**: Batch processing many files (saves memory)

### Save Results
**What it is**: Save stitched images to output folder

**Default**: Checked (ON)

**File Format**: Automatically chooses standard TIFF or BigTIFF based on size
- Files <3.5GB: Standard TIFF (faster, more compatible)
- Files >3.5GB: BigTIFF (handles large files)

**Turn OFF if**: Only want to preview without saving

### Create Z-Projection (NEW in v37.5)
**What it is**: Optionally create flattened 2D projection from 3D stack

**Default**: Unchecked (OFF)

**Turn ON if**: You want a 2D overview image in addition to 3D stack

**Output**: Saved as `*_projection.tif` in output folder

**Note**: Only created if stack has multiple z-slices

### Z-Projection Method (NEW in v37.5)
**What it is**: How to combine z-slices into single 2D image

**Options**:
- **Max Intensity** (default): Brightest pixel at each position
- **Average Intensity**: Mean intensity across slices
- **Sum Slices**: Total intensity (sum) across slices
- **Standard Deviation**: Variability across slices
- **Median**: Median intensity across slices
- **Min Intensity**: Dimmest pixel at each position

**Recommendation**: Use Max Intensity for most fluorescence microscopy

**When to use others**:
- Average: For quantification with less noise
- Sum: For total signal intensity
- SD: To visualize where signal varies across z
- Median: For robust average with outlier rejection
- Min: Rarely used (background levels)

### Output Options (NEW in v37.5)

**What they are**: Control what outputs are created

**Options**:
- **Save Stitched Stack**: Save the 3D stitched result to file
- **Show Stitched Stack**: Display the 3D stitched result in Fiji
- **Save Z-Projection**: Save a 2D flattened projection to file
- **Show Z-Projection**: Display the 2D projection in Fiji

**Requirements**:
- At least one option must be enabled
- To create projections, "Save Stitched Stack" MUST be enabled
- Projections are created from saved files in a separate batch after stitching

**Validation**:
- If no options selected → popup dialog with error, returns to parameters
- If projection enabled without save stack → popup dialog with error, returns to parameters

### Z-Projection Method (NEW in v37.5)

**What it is**: How z-slices are flattened into 2D projection

**Options**:
- **Max Intensity**: Brightest pixel at each position (default, best for most imaging)
- **Average Intensity**: Mean pixel value (smoother, reduces noise)
- **Sum Slices**: Adds all pixel values (increases signal but also noise)
- **Standard Deviation**: Shows variation across z-stack
- **Median**: Middle value (good for removing outliers)
- **Min Intensity**: Darkest pixel (rarely used)

**When projections are created**:
- AFTER all stitching completes
- Processes only `*_stitched.tif` files from output folder
- Uses robust channel-splitting method for color preservation
- Auto brightness/contrast adjustment applied for optimal visibility

**Output filename format**:
- `basename_<num>z_<method>.tif`
- Example: `Sample01_15z_Max.tif` (15 z-slices, Max Intensity projection)

**Recommendation**: Use Max Intensity for fluorescence microscopy
**What it is**: Delete temporary files after processing completes

**Default**: Checked (ON)

**Turn OFF if**: Want to inspect intermediate files for debugging

### Auto-adjust stitching thresholds
**What it is**: Automatically calculate regression and displacement thresholds from metadata

**Default**: OFF

**Turn ON if**: You have varying tile overlaps and want automatic parameter tuning

**Recommendation**: Leave OFF and use manual parameters for consistent results

### Pixel Size Correction Factor
**What it is**: Multiplier for pixel size from fallback metadata sources

**Default**: 10.0

**IMPORTANT**: Only applied to global metadata, NEVER to OME-XML

**Why 10.0**: Global metadata often returns values 10x too large

**Recommendation**: Leave at 10.0 (has no effect if OME-XML extraction succeeds)

---

## Understanding the Log Output

### Startup Messages
```
  +---+---+---+
  | C | Z | I  |    CZI-STITCHER v37.4
  +---+---+---+     ======================
  | S | t  | i  |   > Workflow: v31.16h
  +---+---+---+     > UTF-8:    v34.8
  | t  | c | h |    > LUTs:     v36.5
  +---+---+---+

  [Target] Zeiss Zen/CZI Analysis
  [Status] Initializing environment...

[CZI-Stitcher] [DEBUG] Config loaded: {...}
[CZI-Stitcher] Loading filesystem... This might take a while with sleeping HDDs.
```

**What this means**:
- v37.4 confirmed (check this matches your file)
- Config saved/loaded from previous run
- Filesystem warning = normal (HDDs spin up slowly)

### Processing Each File
```
[CZI-Stitcher] --- Processing: filename.czi ---
[CZI-Stitcher] [DEBUG] === PIXEL SIZE EXTRACTION START ===
[CZI-Stitcher] [DEBUG] Attempting method 1: OME-XML <Pixels> tag
[CZI-Stitcher] [DEBUG]   Parsed raw value: 0.345, unit: µm
[CZI-Stitcher] px = 0.345 µm (from XML, correction factor NOT applied)
```

**What to check**:
- Pixel size should be 0.3-0.5 um for typical 20x-40x objectives
- Should say "from XML, correction factor NOT applied"
- If says "MAY NEED CORRECTION", it used fallback metadata

### Image Conversion (Most Important)
```
=== IMAGE CONVERSION AND LUT APPLICATION ===
  Initial image state:
    - Stack size: 12
    - Is composite: False
  >>> HyperStack created: 3 channels, 4 slices
  >>> Is composite after HyperStack creation: False
  >>> LUTs applied successfully, CompositeImage created
  >>> Display mode set to COMPOSITE, image updated
=== IMAGE CONVERSION COMPLETE ===
```

**Visual Markers**:
- `>>>` = Success (good!)
- `!!!` = Warning or error (needs attention)

**What this section tells you**:
1. Initial image loaded correctly
2. HyperStack created (basic multi-channel stack)
3. LUTs applied (colors from metadata)
4. CompositeImage created (ImageJ format for custom colors)
5. Display mode set (ensures colors show correctly)

**If you see `!!!` markers**: Something failed, read the message carefully

### Stitching Progress
```
[CZI-Stitcher] Tiles: 6 | px-range x=[0.0,109.4] y=[0.0,185.0]
[CZI-Stitcher] === STEP 1: 2D REGISTRATION ===
[CZI-Stitcher]   Stitching 2D MIPs to compute tile positions...
Stitching internal version: 1.2
Loading: M:\test\temp_123\S000_MIP.tif ... (394 ms)
S000_MIP.tif[1] <- S001_MIP.tif[1]: (1131.0, 8.6) correlation (R)=0.73
Finished registration process (5850 ms).
[CZI-Stitcher]   2D registration completed in 7.9 seconds

[CZI-Stitcher] === STEP 2: TRANSFER TO 3D ===
[CZI-Stitcher]   Creating 3D configuration from 2D registration results...
[CZI-Stitcher]   Wrote 6 tiles to 3D configuration

[CZI-Stitcher] === STEP 3: 3D FUSION ===
[CZI-Stitcher]   Fusing 3D stacks using computed positions...
Finished fusion (33493 ms)
[CZI-Stitcher]   3D fusion completed in 52.7 seconds
[CZI-Stitcher]   Total stitching time: 60.6 seconds
```

**What to check**:
- **Correlation (R)** values: Should be 0.6-0.9 for good matches
  - R < 0.3: Weak match, might be wrong
  - R > 0.7: Strong match, likely correct
- **Times**: 2D registration is fast, 3D fusion takes most time
- **Tile count**: Should match your actual tile count

---

## Troubleshooting Common Issues

### Colors Show as Red/Green/Blue/Gray

**Expected**: Custom colors from your Zeiss acquisition

**What you see**: Default Fiji colors (pure red, green, blue, gray)

**Diagnosis**:
1. Find `=== IMAGE CONVERSION AND LUT APPLICATION ===` section in log
2. Look for `>>>` success markers or `!!!` error markers

**If you see**:
```
  !!! LUT application returned None
  !!! Image is NOT CompositeImage - skipping setDisplayMode
```

**This means**: LUT application failed

**Solutions**:
- Check if colors were parsed: Look for "Parsed RGBA: R=X, G=Y, B=Z" earlier in log
- If colors not parsed: OME-XML may lack color information
- If colors parsed but not applied: Report this as a bug with full log

**If you see all `>>>` markers but still wrong colors**:
- Close Fiji completely
- Reopen Fiji
- Load script from disk (not recent files)
- Verify splash shows v37.4
- Try again

### Tiles Don't Align Properly

**Symptom**: Gaps between tiles or massive overlap

**Diagnosis**: Check correlation (R) values in log

**If R values are low (< 0.3)**:
- Tiles might not actually overlap
- Image quality might be too low for matching
- Try lowering Regression Threshold to 0.2

**If R values are high (> 0.7) but still misaligned**:
- Check pixel size in log: Should be 0.3-0.5 um
- If pixel size is 3-5 um: 10x too large, stitching will fail
- If pixel size wrong: Check earlier exceptions in log

**Solutions**:
- Increase Max Displacement to 10 or 20
- Check Rolling Ball Radius (too high can distort features)
- Verify stage coordinates in Zeiss software

### Script Runs But No Output

**Check**:
1. Did any errors appear in log?
2. Look for `!!! EXCEPTION:` markers
3. Check target directory permissions
4. Check disk space (needs 2-3x input file size)

**Common causes**:
- Disk full during temp file creation
- No write permission on target directory
- Exception during 3D stack saving (check for `!!! EXCEPTION during 3D stack save`)

### Script Very Slow

**Expected times** (rough guide):
- 6 tiles, 20 z-slices, 3 channels: ~1-2 minutes
- 20 tiles, 30 z-slices, 4 channels: ~5-10 minutes
- 100 tiles: Can take 30-60 minutes

**Speed factors**:
- Number of tiles: Linear scaling
- Z-slices: Linear scaling
- File I/O: Network drives are much slower than local
- Temp storage: SSD much faster than HDD

**Speed tips**:
- Use local SSD for temp files
- Close other programs
- Don't run on network drives if possible
- Consider upgrading RAM for very large datasets

### Filesystem Loading Takes Forever

**Message**: "Loading filesystem... This might take a while with sleeping HDDs."

**What this means**: Operating system is waking up drives or accessing network

**Is this normal?**: Yes, especially with:
- External USB drives
- Network-attached storage (NAS)
- HDDs that spin down when idle

**How long is too long?**:
- 10-30 seconds: Normal for HDDs
- 1-2 minutes: Normal for NAS
- > 5 minutes: Check if drive is actually accessible

**Solutions**:
- Wait patiently (it's working)
- Keep drives active (disable sleep mode)
- Use local drives instead of network

---

## Best Practices

### Before Stitching
1. **Test on one file first**: Don't batch process until you verify settings
2. **Check one stitched result**: Open in Fiji, verify colors and alignment
3. **Compare with Zeiss ZEN**: Colors should match original acquisition

### During Stitching
1. **Monitor the log**: Look for `!!!` error markers
2. **Check correlation values**: Should be > 0.6 for most tiles
3. **Watch disk space**: Can fill up quickly with large datasets

### After Stitching
1. **Verify colors**: Should match original data
2. **Check pixel size**: Measure known structure, compare to expected size
3. **Inspect overlap regions**: Should be seamless (no visible tile edges)
4. **Check all z-slices**: Verify 3D structure is intact

### For Batch Processing
1. **All files same format**: Same number of channels, similar tile layout
2. **Enough disk space**: Calculate: (file size) × (number of files) × 3
3. **Monitor first few files**: Stop if you see repeated errors
4. **Check results periodically**: Don't wait until all files processed

---

## FAQ

### Q: Do I need to adjust parameters for each dataset?
**A**: Usually no. Defaults work for most Zeiss ApoTome data. Only adjust if:
- Tiles don't align (adjust Max Displacement)
- Visible tile edges (adjust Rolling Ball Radius)
- Stitching fails (adjust Regression Threshold)

### Q: Why does pixel size say "correction factor NOT applied"?
**A**: This is GOOD. It means pixel size came from OME-XML (trusted source). Correction factor only applies to fallback sources.

### Q: Can I process files during acquisition?
**A**: Not recommended. Wait until acquisition complete. Fiji may lock files or .czi might be incomplete.

### Q: How much RAM do I need?
**A**: Depends on file size:
- Small (< 1GB): 8GB RAM sufficient
- Medium (1-3GB): 16GB RAM recommended
- Large (> 3GB): 32GB+ RAM recommended

### Q: Can I cancel mid-processing?
**A**: Yes, close Fiji. Partial results in temp folder will be deleted (if cleanup works). No harm to original files.

### Q: What if colors don't match Zeiss ZEN?
**A**: Check debug log for `=== IMAGE CONVERSION AND LUT APPLICATION ===`. If you see all `>>>` markers but colors still wrong, this is a bug - report it with full log.

### Q: Does this work with non-Zeiss files?
**A**: Not tested. Designed specifically for Zeiss .czi from ApoTome systems. May or may not work with other .czi variants.

### Q: Can I stitch files from different acquisitions?
**A**: Not recommended. Each .czi file is stitched independently. Mixing tiles from different files not supported.

---

## Getting Help

### Before Asking for Help
1. Check this guide
2. Read the troubleshooting section
3. Look at your debug log for `!!!` markers
4. Try closing/reopening Fiji

### When Reporting Issues
**Please include**:
1. Version number from splash screen
2. Complete debug log from Fiji log window (copy/paste)
3. File characteristics:
   - Number of tiles
   - Number of channels
   - Number of z-slices
   - Approximate file size
4. What you expected vs what you got
5. Relevant sections with `>>>` or `!!!` markers

**Don't just say**: "Colors don't work"

**Instead say**: "Colors show as red/green/blue instead of custom colors. Log shows: !!! Image is NOT CompositeImage"

---

## Version Info

**Current Version**: v37.5 (Enhanced Beta)

**Release Date**: December 2025

**Status**: Beta - suitable for testing and evaluation

**What's New in v37.5**:
- Three-folder system for better organization
- Optional z-projection with 6 methods
- Automatic garbage collection for memory management
- Smart BigTIFF selection based on file size
- RAM disk support via manual folder selection

**Known Limitations**:
- Not tested with > 100 tiles
- Not tested with > 4 channels
- Not tested with non-Zeiss .czi files
- LUT color application works but needs user validation
- Z-projection not tested with >4 channels

**Recommended Use**:
- Research microscopy labs
- Zeiss ApoTome users
- Multi-tile brain section reconstruction
- Users comfortable reading debug logs

**Not Recommended For**:
- Production pipelines (until validated on your data)
- Clinical use (research only)
- Users who can't troubleshoot basic issues

---

**Remember**: v37.5 is a BETA. Test thoroughly before production use!
