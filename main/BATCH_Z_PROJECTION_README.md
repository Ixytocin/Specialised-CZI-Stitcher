# Batch Z-Projection Tool v1.1

> **Purpose**: Batch process multiple TIFF stacks with flexible Z-layer selection and advanced noise filtering
> 
> **NEW in v1.1**: Optimized for Apotome/Structured Illumination Microscopy with Otsu & Triangle thresholding

---

## Features

### Core Functionality
- **Batch Processing**: Process entire directories of TIFF stacks automatically
- **File Filtering**: Process only files matching a pattern (e.g., `*stitched`, `*projection`)
- **6 Projection Methods**: Max, Average, Sum, Standard Deviation, Median, Min
- **3 Layer Selection Modes**:
  1. **Use All Layers**: Process entire Z-stack (fastest)
  2. **Discard Top/Bottom**: Manually trim specific number of slices
  3. **Threshold-Based**: Automatically select layers above noise level
- **Advanced Noise Detection Methods (NEW in v1.1)**:
  - **Otsu on Z-profile** - RECOMMENDED for Apotome (scale-invariant, parameter-free)
  - **Triangle on focus scores** - RECOMMENDED for Apotome (detects peak vs tail)
  - **Coefficient of Variation (CV)** - For structured detail detection
  - Fast (histogram min) - Simple baseline
  - Mean + sigma - DEPRECATED (fails for Apotome data)
  - Sample center - Fast alternative
  - User-defined threshold - Full control
- **Automatic Artifact Rejection (NEW in v1.1)**: Filters out slices with mean=0 (fusion artifacts)
- **LUT Preservation**: Maintains original channel colors
- **Auto Brightness/Contrast**: Optimizes visibility automatically
- **Detailed Filenames**: Records exact operation performed

### Output Filename Format

The script creates descriptive filenames that record the exact operation:

**Format**: `basename_<method>_<operation>_<slicecount>.tif`

**Examples**:
- `sample_stitched_max_all_32.tif` - Max projection of all 32 slices
- `sample_stitched_avg_z6to22_17.tif` - Average projection of slices 6-22 (17 slices total)
- `sample_stitched_sum_z1to30_discard0-2_30.tif` - Sum projection, discarded 2 bottom slices (30 slices used)

**Method Abbreviations**:
- `max` = Max Intensity
- `avg` = Average Intensity
- `sum` = Sum Slices
- `sd` = Standard Deviation
- `med` = Median
- `min` = Min Intensity

---

## Installation

1. Copy `batch_z_projection.jy` to your `Fiji.app/scripts/` folder (or any folder)
2. Open Fiji
3. Use File → Open or drag the .jy file into Fiji window
4. Click "Run" in the script editor

---

## Usage

### Basic Workflow

1. **Start the script**
   - Splash screen shows version v1.0
   - "Initializing..." message appears

2. **Configure directories**
   - **Input Folder**: Folder containing TIFF stacks to process
   - **Output Folder**: Where projections will be saved

3. **Set file filter** (optional)
   - Default: `stitched` (processes files containing "stitched")
   - Examples:
     - `stitched` - matches `*stitched*.tif`
     - `projection` - matches `*projection*.tif`
     - `sample01` - matches `*sample01*.tif`
     - Leave empty - processes ALL .tif files

4. **Choose projection method**
   - **Max Intensity** (default): Brightest pixel at each position - best for fluorescence
   - **Average Intensity**: Mean value - smoother, reduces noise
   - **Sum Slices**: Total intensity - increases signal and noise
   - **Standard Deviation**: Shows variation across Z
   - **Median**: Middle value - robust to outliers
   - **Min Intensity**: Darkest pixel - rarely used

5. **Select layer mode**
   - **Use all layers**: Simplest, fastest - uses entire Z-stack
   - **Discard top/bottom**: Manual trimming - specify slices to remove
   - **Threshold-based**: Automatic - only uses slices above noise

6. **Configure mode-specific options**

   **For "Discard top/bottom" mode:**
   - Discard top N slices: 0-10 typically (removes out-of-focus top)
   - Discard bottom N slices: 0-10 typically (removes out-of-focus bottom)

   **For "Threshold-based" mode:**
   - **Noise detection method**:
     - **Fast (histogram min)**: Fastest, uses minimum pixel value
     - **Mean + sigma (thorough)**: Traditional 3-sigma above mean
     - **Sample center (fast)**: Analyzes 10% center region only
     - **User-defined threshold**: You provide exact threshold value
   - **User threshold**: Only used if "User-defined threshold" selected
   - **Sigma multiplier**: Default 3.0 (for mean method)
   - **Analyze channel**: Which channel to use for threshold (1-based)

7. **Set output options**
   - **Save Projections**: Save to output folder (recommended)
   - **Show Projections**: Display in Fiji (uses memory)

8. **Monitor progress**
   - Log shows file-by-file progress
   - Look for `>>>` (success) or `!!!` (error) markers
   - Memory usage logged periodically

9. **Check results**
   - Projections saved in output directory
   - Filenames include operation details
   - Check log for any errors or skipped files

---

## Layer Selection Modes - Detailed Guide

### Mode 1: Use All Layers

**When to use:**
- Z-stack is already optimized
- No noise layers at top/bottom
- Want fastest processing
- Trust the entire acquisition range

**How it works:**
- Uses slices 1 to N (entire stack)
- No analysis or trimming
- Fastest option

**Example output:**
- `brain_section_max_all_45.tif` (all 45 slices, max projection)

---

### Mode 2: Discard Top/Bottom

**When to use:**
- Know exactly which slices are out of focus
- Want consistent trimming across all files
- Manual QC already performed
- Top/bottom slices always noisy

**How it works:**
- Discards specified number of slices from top
- Discards specified number of slices from bottom
- Uses remaining slices

**Examples:**
- Discard top 2, bottom 3:
  - Input: 30 slices
  - Uses: slices 3-27 (25 slices)
  - Output: `sample_max_z3to27_discard2-3_25.tif`

**Recommendations:**
- Start with 1-2 slices top/bottom
- Increase if edges still show noise
- Keep at least 50% of slices

---

### Mode 3: Threshold-Based Selection

**When to use:**
- Variable noise levels between files
- Want automatic noise filtering
- Don't know exact slices to discard
- Z-stacks have different optimal ranges

**How it works:**
1. Analyzes each Z-slice
2. Calculates mean pixel value per slice
3. Compares to noise threshold
4. Keeps only slices above threshold
5. Uses contiguous range (first to last valid slice)

**Noise Detection Methods:**

#### A. Fast (Histogram Min) - DEFAULT
**Speed**: ⚡⚡⚡ Fastest  
**Accuracy**: Good for most cases  
**Method**: Uses minimum pixel value from middle slice  
**Best for**: Quick processing, uniform backgrounds

**How it works:**
```
1. Pick middle Z-slice
2. Find minimum pixel value
3. Use as threshold
4. Keep slices with mean > min
```

#### B. Mean + Sigma (Thorough)
**Speed**: ⚡ Slower (calculates mean + std dev)  
**Accuracy**: Most reliable, traditional approach  
**Method**: Threshold = mean + (3 × standard deviation)  
**Best for**: Scientific accuracy, varying noise levels

**How it works:**
```
1. Pick middle Z-slice
2. Calculate mean and std dev
3. Threshold = mean + 3*sigma
4. Keep slices with mean > threshold
```

**Sigma multiplier guide:**
- 3.0 (default): Standard 3-sigma (99.7% confidence)
- 2.0: More lenient (includes 95% of normal distribution)
- 4.0: Stricter (excludes more slices)

#### C. Sample Center (Fast Alternative)
**Speed**: ⚡⚡ Fast  
**Accuracy**: Good, assumes center is representative  
**Method**: Analyzes only 10% center region of image  
**Best for**: Large images, center focus, speed priority

**How it works:**
```
1. Pick middle Z-slice
2. Calculate 10% center region
3. Calculate mean of center pixels only
4. Use as threshold
5. Keep slices with mean > threshold
```

**Why sample center?**
- Edges often have artifacts
- Center typically has best signal
- Much faster than full image analysis
- Good for large tiles (>2000×2000 pixels)

#### D. User-Defined Threshold
**Speed**: ⚡⚡⚡ Fastest (no calculation)  
**Accuracy**: Depends on user knowledge  
**Method**: You provide exact threshold value  
**Best for**: Known noise levels, consistent acquisitions

**How to determine threshold:**
1. Open sample stack in Fiji
2. Use Image → Adjust → Threshold
3. Find value that separates signal from noise
4. Use that value in script

**Example output:**
- Input: 40 slices, slices 5-35 above threshold
- Output: `sample_avg_z5to35_thr_31.tif`

---

## Performance Comparison

### Noise Detection Speed (relative):

| Method | Speed | Use Case |
|--------|-------|----------|
| Fast (histogram min) | 100% | Default, fastest |
| Sample center | 95% | Slightly slower |
| Mean + sigma | 60% | Most thorough |
| User-defined | 100% | No calculation |

**Recommendation**: Use "Fast" unless you need scientific accuracy, then use "Mean + sigma"

---

## Common Use Cases

### Case 1: Quick Projections of Stitched Data
**Goal**: Create max projections of all stitched files

**Settings:**
- File Filter: `stitched`
- Method: Max Intensity
- Layer Mode: Use all layers
- Save: Yes, Show: No

**Result**: `*_stitched_max_all_<N>.tif`

---

### Case 2: Remove Out-of-Focus Top/Bottom
**Goal**: Discard 2 top and 3 bottom slices from all files

**Settings:**
- File Filter: (leave empty or specific pattern)
- Method: Average Intensity
- Layer Mode: Discard top/bottom
- Discard top: 2
- Discard bottom: 3
- Save: Yes, Show: No

**Result**: `*_avg_z3to<N-3>_discard2-3_<M>.tif`

---

### Case 3: Automatic Noise Filtering
**Goal**: Only use slices above noise threshold, let script decide

**Settings:**
- File Filter: `sample`
- Method: Max Intensity
- Layer Mode: Threshold-based
- Noise method: Fast (histogram min)
- Analyze channel: 1
- Save: Yes, Show: No

**Result**: `*_max_z<X>to<Y>_thr_<N>.tif`

---

### Case 4: Scientific Analysis with 3-Sigma
**Goal**: High-accuracy projections for quantification

**Settings:**
- File Filter: `experiment`
- Method: Average Intensity (or Sum for total signal)
- Layer Mode: Threshold-based
- Noise method: Mean + sigma (thorough)
- Sigma multiplier: 3.0
- Analyze channel: 1
- Save: Yes, Show: No

**Result**: `*_avg_z<X>to<Y>_thr_<N>.tif`

---

## Understanding the Log Output

### Success Markers
```
>>> Saved: sample_max_all_32.tif
>>> Displayed projection
>>> LUTs applied successfully
>>> Auto B&C applied to all channels
```

### Error Markers
```
!!! Failed to load image, skipping
!!! Invalid discard parameters, skipping
!!! No slices meet threshold, skipping
!!! Projection creation failed, skipping
!!! Save failed: <reason>
```

### Threshold-Based Selection Log
```
=== THRESHOLD-BASED LAYER SELECTION ===
  Total slices: 40
  Method: fast
  Calculated fast threshold: 125.50
    Slice 1: mean=95.30 <= threshold=125.50 [DISCARD]
    Slice 2: mean=110.20 <= threshold=125.50 [DISCARD]
    Slice 3: mean=145.80 > threshold=125.50 [KEEP]
    ...
    Slice 38: mean=140.25 > threshold=125.50 [KEEP]
    Slice 39: mean=105.10 <= threshold=125.50 [DISCARD]
    Slice 40: mean=90.45 <= threshold=125.50 [DISCARD]

  Selected slices: 3 to 38 (total: 36)
  Discarded: 2 top, 2 bottom
```

---

## Troubleshooting

### No Files Found
**Error**: `!!! No TIFF files found matching filter: stitched`

**Causes:**
- No .tif files in input directory
- Filter doesn't match any filenames
- Wrong input directory

**Solutions:**
1. Check input directory is correct
2. Try empty filter (process all .tif files)
3. Check filter matches actual filenames (case-insensitive)
4. Example: File is `Sample_Stitched.tif`, filter `stitched` works

---

### All Slices Discarded by Threshold
**Error**: `!!! No slices meet threshold, skipping`

**Causes:**
- Threshold too high for signal
- Very noisy data
- Wrong channel selected for analysis

**Solutions:**
1. Try "User-defined threshold" with lower value
2. Use "Discard top/bottom" mode instead
3. Check which channel has signal (try channel 2, 3, etc.)
4. Open file in Fiji manually to inspect

---

### Projection Failed
**Error**: `!!! Robust projection failed: <reason>`

**Causes:**
- Memory overflow (stack too large)
- Corrupted file
- Invalid slice range

**Solutions:**
1. Close other Fiji windows
2. Increase Fiji memory: Edit → Options → Memory & Threads
3. Try single file first to test
4. Check input file opens in Fiji manually

---

### Wrong Colors in Output
**Issue**: Colors don't match original

**Diagnosis:**
- Look for `>>> LUTs applied successfully` in log
- If missing, LUT preservation failed

**Causes:**
- Original file is not CompositeImage
- Original file has no LUT information
- Single-channel image (no LUTs to preserve)

**Solutions:**
- This is expected for single-channel grayscale
- For multi-channel, check source file has colors
- Manual color adjustment: Image → Color → Channels Tool

---

## Advanced Tips

### Processing Large Datasets
1. **Close Fiji windows**: Free memory before starting
2. **Disable "Show Projections"**: Saves RAM
3. **Process in batches**: Split into smaller groups
4. **Use SSD**: Faster file I/O
5. **Monitor memory**: Check log for memory warnings

### Optimizing Threshold Detection
1. **Test on one file first**: Use "Show Projections" to verify
2. **Compare methods**: Try Fast vs Mean+sigma on same file
3. **Adjust sigma**: Start at 3.0, decrease to 2.0 if too strict
4. **Check channel**: If multi-channel, try different channels
5. **Use histogram**: Image → Adjust → Threshold in Fiji to find good value

### Filename Tips
- Output filenames are self-documenting
- `_all_` = used entire stack
- `_z6to22_` = used slices 6-22
- `_discard2-3_` = removed 2 top, 3 bottom
- `_thr_` = threshold-based selection
- Final number = actual slice count used

---

## Relationship to Main Stitcher

**This is a standalone tool** - completely independent from `main.jy`.

**Pipeline Position:**
```
Acquisition → main.jy (stitching) → batch_z_projection.jy (optional) → Analysis
              └─ Creates *_stitched.tif files
                                      └─ Creates *_max_all_N.tif projections
```

**When to use:**
- After stitching is complete
- As a separate processing step
- On any TIFF stacks (not just stitched files)
- When you need custom projection settings
- For re-processing existing files

**Main stitcher (main.jy) has its own projection feature:**
- This tool is NOT a replacement
- This tool is for **additional/custom** processing
- Use this tool when main.jy's projection doesn't meet your needs

**Common scenarios:**
1. **Workflow A**: Use main.jy with projection → Done
2. **Workflow B**: Use main.jy without projection → Use this tool separately
3. **Workflow C**: Use this tool on non-stitched stacks

---

## Known Limitations

- **Memory**: Large multi-channel stacks (>4GB) may cause memory issues
- **File Types**: Only processes TIFF files (.tif, .tiff)
- **Channels**: Tested up to 4 channels, may work with more
- **Slice Count**: No hard limit, but very large stacks (>200 slices) may be slow
- **Threshold Detection**: Assumes middle slice is representative
- **Contiguous Range**: Threshold mode uses first-to-last valid slice (doesn't skip middle slices)

---

## Technical Details

### Noise Detection Algorithms

**Fast Method (Histogram Min):**
```python
stats = image.getStatistics(MIN_MAX)
threshold = stats.min
# Use minimum as baseline
```

**Mean + Sigma Method:**
```python
stats = image.getStatistics(MEAN + STD_DEV)
threshold = stats.mean + (sigma * stats.stdDev)
# Traditional 3-sigma approach
```

**Sample Center Method:**
```python
# Calculate 10% center region
center_width = width * 0.1
center_height = height * 0.1
# Sample only center pixels
threshold = mean_of_center_pixels
```

### Channel-Splitting Projection
Based on proven pipeline from main.jy v37.5:
```
1. Duplicate source image
2. Split into individual channel images
3. Project each channel separately
4. Merge channels back together
5. Apply original LUTs
6. Set composite mode
```

**Why this approach?**
- Prevents composite-mode crashes (documented pitfall)
- Ensures LUTs are preserved
- More stable than direct projection
- Handles multi-channel correctly

---

## Version History

### v1.0 (Current)
- Initial release
- Three layer selection modes
- Four noise detection methods
- File filtering by pattern
- Detailed operation recording in filenames
- LUT preservation
- Auto brightness/contrast
- Comprehensive logging

---

## Credits

**Based on**: CZI-Stitcher v37.5 patterns and conventions  
**Follows**: TECHDOC/PITFALLS.md guidelines  
**Uses**: Proven channel-splitting projection method  

---

## Support

**Before asking for help:**
1. Check this README
2. Look at log output for `>>>` and `!!!` markers
3. Try one file manually in Fiji first
4. Verify input files are valid TIFF stacks

**When reporting issues, include:**
1. Version (v1.0)
2. Complete log output
3. Input file characteristics (slices, channels, size)
4. Expected vs actual behavior
5. Relevant log sections with markers

---

**Status**: v1.0 - Ready for testing and evaluation
