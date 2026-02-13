# Migration History

This document tracks breaking changes and significant updates across versions.

---

# Migration Guide: v37.5 → v37.6

## Overview

Version 37.6 simplifies the stitching workflow by removing integrated Z-projection functionality and moving it to a dedicated tool (`batch_z_projection.jy`). This improves code maintainability, reduces complexity, and provides more advanced projection features through the specialized tool.

---

## What Changed

### 1. Z-Projection Removed from main.jy (BREAKING CHANGE)

**Old (v37.5)**: Integrated Z-projection with 6 methods in main.jy  
**New (v37.6)**: Z-projection removed, use separate batch_z_projection.jy tool

**Action Required**: 
- If you used the integrated Z-projection feature, switch to using `batch_z_projection.jy` after stitching
- Update any automated workflows that relied on automatic projection

**Why**: 
- **Simplified codebase**: Removed ~234 lines of projection code
- **Better tool separation**: Stitching and projection are independent workflows
- **Advanced features**: Dedicated tool has 9 detection methods, threaded processing, smart exclusion

### 2. Parameter Dialog Simplified

**Removed Parameters**:
- ❌ "Save Z-Projection" checkbox
- ❌ "Show Z-Projection" checkbox
- ❌ "Z-Projection Method" dropdown

**Unchanged Parameters**:
- ✅ All stitching parameters remain the same
- ✅ Directory selection unchanged
- ✅ Output options for stitched stacks unchanged

### 3. Output Files

**Old (v37.5)**: 
- `*_stitched.tif` (stitched 3D stack)
- `*_15z_Max.tif` (optional projection from main.jy)

**New (v37.6)**:
- `*_stitched.tif` (stitched 3D stack only)
- For projections: Run `batch_z_projection.jy` separately
  - Creates files like `*_max_all_32.tif`, `*_avg_z6to22_VEO_17.tif`, etc.

### 4. Version Number

**Old**: v37.5  
**New**: v37.6

**Splash Screen**: Now shows "CZI-STITCHER v37.6" with note about batch_z_projection.jy

---

## New Workflow

**Old Workflow (v37.5)**:
```
1. Run main.jy
2. Enable "Save Z-Projection" checkbox
3. Select projection method
4. Stitching + projection done automatically
```

**New Workflow (v37.6)**:
```
1. Run main.jy
2. Stitching completes → saves *_stitched.tif files
3. (Optional) Run batch_z_projection.jy
4. Select advanced projection options
5. Projection batch processes all *_stitched.tif files
```

---

## Advantages of New Approach

1. **More Advanced Features**: 9 detection methods vs 6 basic methods
2. **Better Performance**: Threaded processing with dynamic RAM allocation
3. **Smart File Management**: Intelligent exclusion of already-projected files
4. **Full Traceability**: Detection method acronyms in filenames (VEO, TT, CV)
5. **Cleaner Codebase**: Each tool does one thing well
6. **Flexibility**: Run projections only when needed

---

## Compatibility

- **Input Files**: No changes, same .czi compatibility
- **Output Files**: `*_stitched.tif` format unchanged
- **Settings**: No config file changes
- **Dependencies**: No new requirements

---

## Where to Get batch_z_projection.jy

The dedicated projection tool is included in the same repository:
```
your-folder/
├── main.jy                    ← Stitching tool (v37.6)
├── batch_z_projection.jy      ← Projection tool (v1.5)
├── metadata_correction.py     ← Required module
└── BATCH_Z_PROJECTION_README.md
```

📖 **Full documentation**: [main/BATCH_Z_PROJECTION_README.md](main/BATCH_Z_PROJECTION_README.md)

---

# Migration Guide: v37.4 → v37.5

## Overview

Version 37.5 introduces significant improvements to workflow organization, memory management, and output options while maintaining backward compatibility with existing .czi files.

---

## What Changed

### 1. File Names (BREAKING CHANGE)
**Old**: `main_unified_v37.jy`, `HELP_v37.4.md`  
**New**: `main.jy`, `HELP.md`

**Action Required**: Update your Fiji scripts/bookmarks to reference `main.jy`

**Why**: Version numbers in filenames make version control confusing. The version is tracked inside the file and in documentation.

---

### 2. Settings File Location
**Old**: `~/.ixytocin_stitcher.json`  
**New**: `~/.specialised_czi_stitcher_config.json`

**Impact**: First run of v37.5 will ask you to select folders again (previous settings not carried over)

**Why**: Unique name prevents conflicts with other tools

---

### 3. Directory Selection Workflow

**Old Workflow**:
1. Select source directory
2. Select target directory
3. (Temp files auto-placed in target or RAM disk R:\)

**New Workflow (v37.5)**:
1. Select **Input** folder (source .czi files)
2. Select **Output** folder (stitched results)
3. Select **Processing/Temp** folder (temporary files during stitching)

**Benefits**:
- Full control over temp file location
- Can use any RAM disk (not just R:\)
- Can separate processing from output (e.g., use fast SSD for temp, network drive for output)

---

### 4. Parameter Dialog Changes

**Removed**:
- ❌ "Als BigTIFF speichern" checkbox

**Added**:
- ✅ "Create Z-Projection" checkbox
- ✅ "Z-Projection Method" dropdown (6 options)

**Changed**:
- Dialog now has section headers for better organization
- Title changed to "Specialised CZI Stitcher - Parameters v37.5"

---

### 5. BigTIFF Handling

**Old**: Optional via checkbox, default OFF  
**New**: Automatic based on estimated file size

**Logic**:
- File size < 3.5GB → Standard TIFF (faster, more compatible)
- File size > 3.5GB → BigTIFF (handles large files)
- Fallback: If one format fails, tries the other

**Benefit**: No need to guess, system chooses optimal format

---

### 6. Z-Projection Feature (NEW)

**What**: Optionally create flattened 2D projection from 3D stack

**Methods Available**:
1. Max Intensity (default, best for fluorescence)
2. Average Intensity
3. Sum Slices
4. Standard Deviation
5. Median
6. Min Intensity

**Output**: Saved as `*_projection.tif` in output folder

**When to Use**:
- Quick 2D overview of 3D data
- Creating figures for publications
- Quality control checks

---

### 7. Memory Management (NEW)

**Feature**: Automatic garbage collection at major steps

**When GC Runs**:
1. Before tile extraction
2. After 2D registration
3. After 3D fusion
4. After saving results

**Logging**: Memory usage shown before/after each GC

**Benefit**: Prevents RAM overflow when processing large files or batches

---

### 8. RAM Disk Support

**Old**: Automatically detected R:\ drive on Windows  
**New**: User manually selects RAM disk as processing folder

**How to Use**:
- When prompted for "Processing/Temp Folder", select your RAM disk:
  - Linux: `/dev/shm` or `/tmp`
  - Windows: `R:\` or other RAM disk drive
  - macOS: `/tmp` or third-party RAM disk

**Benefit**: Works on all platforms, not just Windows with R:\ drive

---

## Migration Checklist

### For Existing Users

- [ ] Download new `main.jy` file
- [ ] Remove or archive old `main_unified_v37.jy`
- [ ] First run: Select all three directories (input, output, processing)
- [ ] If using RAM disk: Select it as processing folder (no longer automatic)
- [ ] Review new parameter dialog (note z-projection options)
- [ ] Check first stitched file to verify BigTIFF selection is appropriate
- [ ] Monitor memory usage in log to see GC effectiveness

### For New Users

Just follow the updated README and HELP.md documentation. All defaults are sensible.

---

## Compatibility

### What's Compatible

✅ **All .czi files**: No change to file format handling  
✅ **Existing parameters**: All old parameters still work  
✅ **Stitching workflow**: Same proven 2D→3D approach  
✅ **LUT handling**: Same RGBA color parsing  
✅ **Output files**: Same file naming scheme

### What's NOT Compatible

❌ **Settings file**: Old `.ixytocin_stitcher.json` not read by v37.5  
❌ **File references**: Scripts pointing to `main_unified_v37.jy` need update

---

## Performance Comparison

### Memory Usage
- **v37.4**: Could accumulate temp files in RAM, potential overflow
- **v37.5**: Regular GC prevents buildup, more stable for batch processing

### Disk I/O
- **v37.4**: Automatic R:\ usage (Windows only)
- **v37.5**: Manual RAM disk selection (all platforms)

### File Size Handling
- **v37.4**: Manual BigTIFF checkbox (users often forgot)
- **v37.5**: Automatic based on size (one less decision)

---

## Troubleshooting

### "Where's my old config?"
Settings from v37.4 are not read by v37.5 (different file name). Just select directories again on first run.

### "I want automatic R:\ detection back"
Not supported. Select R:\ manually as processing folder. This gives you flexibility to use any RAM disk.

### "BigTIFF is too slow for my small files"
v37.5 automatically uses standard TIFF for files <3.5GB. Check the log to see which format was chosen.

### "I don't want z-projection"
Just leave the "Create Z-Projection" checkbox unchecked (default is OFF).

### "Where are my temp files?"
In the processing folder you selected. If you chose cleanup, they're deleted after successful processing.

---

## Rollback Instructions

If v37.5 doesn't work for you:

1. Download v37.4 from git history:
   ```
   git checkout v37.4 main_unified_v37.jy
   ```

2. Or access via GitHub releases (if tagged)

3. Note: v37.4 used `.ixytocin_stitcher.json` for settings

---

## Questions?

See:
- **README**: Overview and quick start
- **HELP.md**: Detailed parameter explanations
- **DOC/CHANGELOG_v37.md**: Complete change history

Report issues with:
- Version number (v37.5)
- Complete log output
- System info (OS, RAM, disk space)
- File characteristics (tiles, channels, z-slices)

---

**Updated**: 2025-12-26  
**Applies to**: v37.5 and later
