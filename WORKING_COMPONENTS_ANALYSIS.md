# Working Components Analysis - Based on User Feedback

## Purpose
This document identifies which code patterns WORK vs which ones BREAK, based on extensive user testing feedback from PR #2.

## Critical User Insights

> "We had working stitching, then broke it under refinement. Then had working LUT structure, broke it implementing stitching."

This confirms **complexity-induced regression** - the core problem we're solving.

## ✅ PROVEN WORKING Components

### 1. RGBA Color Format (CRITICAL - User Confirmed)
**What works:**
```python
# Zeiss uses SIGNED 32-bit integers in RGBA format
u = int(color_value) & 0xFFFFFFFF  # Convert signed to unsigned
hex8 = "%08X" % u
# RGBA format: RR GG BB AA (skip alpha)
rgb = (int(hex8[0:2],16), int(hex8[2:4],16), int(hex8[4:6],16))
```

**User's actual data:**
- Ch1 (Hoechst): 7798783 → 0x0076FFFF → RGB(0, 118, 255) = Blue ✓
- Ch2 (AF488): 16724991 → 0x00FF33FF → RGB(0, 255, 51) = Green ✓  
- Ch3 (AF647): -16771841 → 0xFF0014FF → RGB(255, 0, 20) = Red ✓

**What DOESN'T work:**
- ARGB format (swaps bytes)
- BGR format (swaps Red/Blue)
- Not handling negative signed integers

### 2. Pixel Size Extraction (WITH CRITICAL FIX)
**User's problem:**
```
OME-XML says: PhysicalSizeX="0.345" µm  ← CORRECT
Global metadata returns: 3.45 µm       ← 10x TOO LARGE
```

**What works:**
```python
px_um = get_pixel_size_um_strict(ome_xml, omeMeta, reader, gMeta)
# v34.8 fix: Only apply correction if NOT from OME-XML
if px_um and 0.01 <= px_um <= 50.0:
    # Pixel size from OME-XML is already correct
    px_um_eff = px_um
    log(u"px = {} µ (from XML, correction factor NOT applied)".format(px_um_eff))
else:
    # Pixel size from fallback methods, apply correction
    px_um_eff = px_um / cf if cf != 1.0 else px_um
```

**What DOESN'T work:**
- Always applying correction factor (breaks OME-XML values)
- Trusting global metadata over OME-XML

### 3. Dual 2D→3D Stitching Workflow (v31.16h - PROVEN)
**What works:**
```python
# Step 1: Extract both 3D and 2D MIP for each tile
for tile in tiles:
    save_3d_stack(tile, "S000_3D.tif")
    save_2d_mip(tile, "S000_MIP.tif")

# Step 2: Stitch 2D MIPs (fast registration)
stitch_2d_mips()  # Creates TileConfiguration.registered.txt

# Step 3: Transfer coordinates to 3D
transfer_2d_coords_to_3d()  # Creates TileConfiguration_3D.txt

# Step 4: Stitch 3D stacks using transferred coordinates
stitch_3d_with_known_positions()  # No overlap computation, just fusion
```

**Why it works:**
- 2D registration is fast (no z-dimension overhead)
- 3D fusion preserves all z-slices
- No dimension confusion (channels vs z-slices)

### 4. Unicode Handling (ESSENTIAL)
**User's environment:** German file paths with `ä, ö, ü, ß, µ`

**What works:**
```python
def ensure_unicode(o):
    if isinstance(o, unicode):
        return o
    try:
        return unicode(bytearray(o.getBytes("UTF-8")), 'utf-8', 'replace')
    except:
        return unicode(o, 'utf-8', 'replace')

# Use .format() NOT + for string concatenation
log(u"File: {}".format(path))  # ✓ Works
# log(u"File: " + path)  # ✗ Crashes with German chars

# Use codecs.open for files
with codecs.open(path, 'w', encoding='utf-8') as f:
    f.write(u"content")
```

### 5. LUT Application to CompositeImage
**User reported:** "All channels have Cy3 tint" = CompositeImage not created

**What works:**
```python
def apply_channel_luts_to_image(imp, ome_xml, gMeta):
    # Convert to CompositeImage FIRST
    if imp.getStackSize() > 1 and imp.getNChannels() > 1:
        cimp = CompositeImage(imp)
        # Apply LUTs to CompositeImage
        for i in range(min(nchan, len(luts))):
            cimp.setChannelLut(luts[i], i+1)
        cimp.updateAndDraw()
        return cimp  # Return NEW image
    return imp
```

**Critical:** Must return the NEW CompositeImage, not original imp

### 6. Sharp-Slice Detection (User Requested Feature)
**User's requirements:**
- Binary search from center of stack
- n×n ROI grid for non-coplanar samples  
- Hole-filling for gaps
- Filename includes z-range

**What works:**
```python
# Binary search optimization
start_z = n_slices // 2  # Start at center
check_thirds = [n_slices//3, 2*n_slices//3]
# Progress outward from known sharp regions

# ROI-based detection
for roi in grid:
    sharp_range = detect_sharp_slices_in_roi(roi)
    all_ranges.append(sharp_range)
merged_range = merge_overlapping_ranges(all_ranges)

# Filename
output = "file_stitched_z{}-{}_max_projection.tif".format(z_start, z_end)
```

## ❌ BROKEN Components (Avoid These)

### 1. Standard LUT Override
**User rejected:** "Don't assume everyone sets up channels the same way"

**What DOESN'T work:**
```python
# Automatically replacing colors with "standard" microscopy LUTs
if ch1_looks_wrong:
    use_standard_luts()  # ✗ User rejected this approach
```

**What DOES work:**
- Respect metadata colors by default
- Optional checkbox to override (but not automatic)

### 2. ImageJ BGR Color Order
**User confirmed:** ImageJ expects BGR when passing colors to LUT

**Fix needed:**
```python
# Must swap R↔B when creating ImageJ LUT
lut = build_lut_from_rgb((B, G, R))  # Swap R and B for ImageJ
```

### 3. Correction Factor Applied to All Sources
**What broke:**
```python
# Always applying correction factor
px_um_eff = px_um / 10.0  # ✗ Breaks OME-XML values
```

**What works:**
```python
# Only apply to fallback sources, trust OME-XML
if source == "OME-XML":
    px_um_eff = px_um  # No correction
else:
    px_um_eff = px_um / correction_factor
```

## 📋 User Feature Requests (PR #2)

### Implemented and Working
1. ✅ Startup message: "Initializing, please wait..."
2. ✅ Branding: "Specialised CZI Stitcher"
3. ✅ Z-projection view option (separate from save)
4. ✅ Enhanced filenames: `file_rb50_stitched_max_projection.tif`
5. ✅ 2×2 grid layout for show/save options
6. ✅ Help button with comprehensive docs
7. ✅ Debug mode checkbox
8. ✅ ASCII art completion banner
9. ✅ Jingle with "call me when finished" loop
10. ✅ Time formatting (ms→s/m/h)
11. ✅ Credits: Bio-Formats, Stitching plugin
12. ✅ Modest development disclaimer
13. ✅ Sharp-slice detection (global + ROI)
14. ✅ Hole-filling for gaps
15. ✅ n×n ROI grid (user configurable)

### Rejected by User
1. ❌ Auto-override to "standard" microscopy LUTs
2. ❌ Dynamic GUI (not supported by Fiji's GenericDialog)
3. ❌ Localization (not needed for scientific community)
4. ❌ Multi-file fusion (feature creep)

## Key Design Principles

### 1. Trust the Metadata
**User's philosophy:** Let Zeiss metadata define colors and scaling
- Don't assume standard conventions
- Don't auto-fix "wrong-looking" values
- User knows their setup better than we do

### 2. Unicode Safety Everywhere
**Critical for German microscopy labs:**
- All string literals: `u"..."`
- All string operations: `.format()` not `+`
- All file I/O: `codecs.open(..., encoding='utf-8')`
- All metadata: `ensure_unicode()`

### 3. Proven Patterns Only
**Complexity kills:**
- v31.16h: Working stitching → broke under refinement
- Early versions: Working LUTs → broke implementing stitching
- **Solution:** Only use code that's been user-tested

### 4. User is the Expert
**Development method:**
- User identifies problem: "Colors are wrong"
- User tests and reports: "Ch2 should be green, shows magenta"
- User analyzes: "Signed 32-bit integers in RGBA format"
- We implement their analysis, not our assumptions

## Code Patterns to Follow

### Pattern 1: Safe Unicode Logging
```python
def log(msg):
    try:
        IJ.log(u"[CZI-Stitcher] {}".format(safe_unicode(msg)))
    except UnicodeEncodeError:
        IJ.log("[CZI-Stitcher] <message contains unsupported characters>")
```

### Pattern 2: Safe Pixel Size Extraction
```python
px_um = get_pixel_size_um_strict(ome_xml, omeMeta, reader, gMeta)
if px_um and 0.01 <= px_um <= 50.0:
    # OME-XML value is correct (realistic range)
    px_um_eff = px_um
    log(u"px = {} µm (from XML, no correction)".format(px_um_eff))
else:
    # Fallback value needs correction
    px_um_eff = px_um / correction_factor
    log(u"px = {} µm (fallback, corrected)".format(px_um_eff))
```

### Pattern 3: Safe RGBA Color Parsing
```python
def parse_rgba_color(color_int):
    u = int(color_int) & 0xFFFFFFFF  # Handle signed integers
    hex8 = "%08X" % u
    # RGBA format: RR GG BB AA
    rgb = (int(hex8[0:2],16), int(hex8[2:4],16), int(hex8[4:6],16))
    return rgb
```

### Pattern 4: Safe CompositeImage Creation
```python
def apply_luts(imp, luts):
    if imp.getStackSize() > 1 and imp.getNChannels() > 1:
        cimp = CompositeImage(imp)  # Create new
        for i, lut in enumerate(luts):
            cimp.setChannelLut(lut, i+1)
        cimp.updateAndDraw()
        imp.close()  # Close old image
        return cimp  # Return new image
    return imp
```

## Testing Strategy

### What User Tested
1. Real CZI files with German characters in paths ✓
2. Multi-channel files (Hoechst, AF488, AF647) ✓
3. Multi-tile acquisitions (20+ tiles) ✓
4. Large files (>2GB requiring BigTIFF) ✓
5. Non-coplanar samples (tilted mounting) ✓

### What Still Needs Testing
- [ ] Sharp-slice detection performance on 40+ slice stacks
- [ ] ROI-based detection with 10×10 grid
- [ ] Memory usage with 100+ tiles
- [ ] RAM disk optimization on workstations

## Conclusion

**The unified script MUST:**
1. Use RGBA format for colors (user confirmed working)
2. Trust OME-XML pixel size, only correct fallbacks
3. Implement v31.16h 2D→3D stitching workflow
4. Handle Unicode throughout (µ, ä, ö, ü, ß)
5. Create proper CompositeImage for multi-channel
6. Include user-requested features from PR #2
7. **NOT** include experimental features
8. **NOT** assume standard microscopy conventions

**The goal:** Combine ONLY proven working pieces without adding complexity that causes regression.
