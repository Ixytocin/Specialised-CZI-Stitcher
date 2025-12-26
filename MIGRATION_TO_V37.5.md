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
