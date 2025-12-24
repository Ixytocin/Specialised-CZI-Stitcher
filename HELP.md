# Specialised CZI Stitcher - Help Documentation

## Overview
This tool stitches multi-tile CZI microscopy files from Zeiss systems, with advanced features for z-stack projection and intelligent focus detection.

## Folder Paths

### Input Folder
- Contains your source .czi files
- All CZI files in this folder will be processed

### Processing Folder  
- Temporary storage for extracted tiles during stitching
- Can be same as input folder unless you need separation
- Files are automatically cleaned up after processing (if cleanup enabled)

### Output Folder
- Where final stitched results are saved
- Can be different from input for better organization

## Stitching Parameters

### Fusion Method
- **Linear Blending**: Smooth transitions between tiles (recommended)
- **Max Intensity**: Takes brightest pixel from overlapping regions
- **Average**: Averages overlapping pixels
- **Median**: Takes median value of overlapping pixels

### Rolling Ball Radius
- Background subtraction radius in pixels
- **0 = OFF** (no background subtraction)
- **50 = Standard** for most samples
- **Larger values** (100-200) for samples with large bright features
- Rule: Should be **larger** than your largest object of interest

### Regression Threshold
- Controls how strictly tiles must align (0.0-1.0)
- **0.30 = Standard** (recommended starting point)
- **Lower values** (0.1-0.2) = More lenient, allows more mismatch
- **Higher values** (0.4-0.5) = Stricter alignment, rejects poor matches

### Max Displacement
- Maximum pixel distance tiles can shift during alignment
- **5.0px = Standard** for well-aligned stages
- **Increase** (10-20px) if stage positioning is inaccurate
- **Decrease** (2-3px) for very precise stages

## Stitched Volume Options

### Show Stitched Volume
- Opens the full 3D stitched volume in Fiji for viewing
- Useful for quality control before saving

### Save Stitched Volume  
- Saves the complete 3D stitched result as TIFF
- Automatically uses BigTIFF format for files >2GB
- File naming: `{original}_stitched.tif`

## Z-Projection Options

### Show Z-Projection
- Displays the 2D projection in Fiji without saving
- Useful for quick preview

### Save Z-Projection
- Saves the 2D projection as TIFF file
- File naming: `{original}_stitched_{method}_projection.tif`

### Z-Projection Method
- **Max Intensity**: Maximum pixel value across z-slices (best for fluorescence)
- **Average Intensity**: Average of all z-slices
- **Min Intensity**: Minimum pixel value
- **Sum Slices**: Total sum across z-slices
- **Standard Deviation**: Standard deviation across z-slices
- **Median**: Median value across z-slices

## Sharp-Slice Detection (Advanced)

### Enable Sharp-Slice Detection
- Automatically detects which z-slices are in focus
- Only includes sharp slices in final output
- Useful for:
  - Samples with limited depth of field
  - Non-coplanar samples (tilted mounting)
  - Reducing file size by excluding blurry slices

### Detection Mode

#### Global Mode (Recommended)
- Analyzes entire image to find sharp z-range
- Uses 3-phase Monte Carlo + Spreading-Fire optimization:
  1. **Monte Carlo Gatekeeper**: Quick triage with 50 random samples per slice
  2. **Spreading-Fire**: Efficient propagation from confirmed sharp slices
  3. **Targeted Analysis**: Only analyzes uncertain slices
- ~30-50% faster than naive full-analysis approach

#### ROI-based Mode (For Non-Coplanar Samples)
- Samples n×n grid points across image
- Finds sharp z-range at each sample point
- Merges all ranges to capture entire sample
- Use when: Sample is tilted or unevenly mounted

### Sharpness Threshold (0.0-1.0)
- Lower threshold = More slices included (more lenient)
- Higher threshold = Fewer slices included (only very sharp)
- **Recommended**: 0.3 (standard)
- **Typical range**: 0.2-0.4
- **Note**: Values NOT comparable between detection methods

### Detection Method
- **Laplacian Variance** (recommended): Edge-based sharpness
- **Tenengrad Gradient**: Gradient magnitude-based
- **Normalized Variance**: Intensity variation-based

### ROI Grid Size (n×n)
- Only applies to ROI-based mode
- Creates n×n grid of sample points
- **3×3 = Default** (9 sample points)
- **5×5 or 7×7** for tilted samples
- **Warning**: 10×10 = 100 sample points, may be slow

## Color Options

### Use Standard Microscopy LUTs
- Override metadata colors with standard fluorescence LUTs
- Use when metadata colors are incorrect or missing
- Standard colors based on common emission wavelengths

## Advanced Options

### Cleanup Temp Files
- Removes temporary tile files after stitching
- **Recommended**: Keep enabled unless debugging
- Saves disk space

### Auto-adjust Stitching Thresholds
- Automatically optimizes regression threshold and max displacement
- Based on tile overlap detected in metadata
- **Default**: OFF (manual control)
- **Enable** if you're unsure about optimal parameters

### Pixel Size Correction Factor
- Multiplier for pixel size from metadata
- **Default**: 10.0 (Zeiss convention)
- Only change if stage positions seem wrong

### Debug Mode
- Enables verbose logging for troubleshooting
- Shows:
  - Slice-by-slice sharpness scores
  - Monte Carlo classification results
  - LUT application details
  - Performance metrics

### Call Me When Finished
- Plays audio alert when batch completes
- Loops every 3 seconds until you click OK
- Useful for long processing jobs

## Output Files

### File Naming Convention
- Stitched volume: `{original}_stitched.tif`
- With rolling ball: `{original}_stitched_rb{radius}.tif`
- With z-projection: `{original}_stitched_rb{radius}_{method}_projection.tif`
- With sharp-slice detection: `{original}_stitched_rb{radius}_z{start}-{end}_{method}_projection.tif`

### Example
Original: `sample.czi`  
Output: `sample_stitched_rb50_z6-16_max_projection.tif`
- Rolling ball radius: 50
- Sharp slices: z6 through z16
- Projection method: Max Intensity

## Troubleshooting

### Colors Are Wrong
- Try enabling "Use Standard Microscopy LUTs"
- Check Debug Mode to see LUT application details
- Report color order in log for further diagnosis

### Stitching Fails
- Increase Max Displacement if tiles don't align
- Decrease Regression Threshold to be more lenient
- Enable Debug Mode to see detailed error messages

### Memory Issues
- Process fewer files at once
- Reduce number of concurrent threads (uses CPU cores - 1 by default)
- Save results more frequently to free memory

### R Values Show 1.79E308
- This is normal - it's Double.MAX_VALUE from ImageJ
- Indicates tiles haven't been registered yet or registration failed
- Not an error

## Performance Tips

- **Enable** Sharp-Slice Detection to reduce output file size
- **Use** Global mode for fastest sharp-slice detection
- **Enable** Cleanup Temp Files to save disk space
- **Disable** Show options if processing many files (reduces memory)

## Credits

Built using:
- Fiji/ImageJ
- Bio-Formats (OME)
- Stitching Plugin (Preibisch et al.)
- Based on Viveca tool by seiryoku-zenyo

## Support

For issues or questions:
https://github.com/Ixytocin/Specialised-CZI-Stitcher/issues
