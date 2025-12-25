# Pitfalls & Lessons Learned - Zeiss CZI Stitching

> **Purpose**: Document hard-won knowledge from developing and debugging this tool.
> Save future developers (and users) from repeating our mistakes.

---

## Table of Contents
1. [Jython & ImageJ Pitfalls](#jython--imagej-pitfalls)
2. [Zeiss CZI Format Pitfalls](#zeiss-czi-format-pitfalls)
3. [Stitching Algorithm Pitfalls](#stitching-algorithm-pitfalls)
4. [Metadata Extraction Pitfalls](#metadata-extraction-pitfalls)
5. [CompositeImage & LUT Pitfalls](#compositeimage--lut-pitfalls)
6. [Unicode & File Path Pitfalls](#unicode--file-path-pitfalls)
7. [Development Process Lessons](#development-process-lessons)

---

## Jython & ImageJ Pitfalls

### Pitfall #1: Encoding Declarations Are Fatal

**The Problem**:
```python
# -*- coding: utf-8 -*-  # THIS CRASHES IN JYTHON 2.7!
```

**The Error**:
```
org.python.antlr.ParseException: encoding declaration in Unicode string
```

**Why It Happens**:
- Jython 2.7 doesn't support encoding declarations like Python 2.7
- Even though CPython 2.7 requires them for non-ASCII characters
- This is a Jython-specific limitation

**The Solution**:
- **Never** use encoding declarations in Jython scripts
- **All** source files must be pure ASCII
- Use unicode escape sequences in strings: `u"\u00b5m"` not `u"µm"`

**The Catch-22**:
- Non-ASCII characters without declaration → ParseException
- Encoding declaration in Jython → ParseException
- **Only solution**: Pure ASCII source files

**Lesson**: When writing for Jython, pretend you're coding in 1980s ASCII-only C.

---

### Pitfall #2: String Concatenation Breaks with Unicode

**The Problem**:
```python
# This crashes with German characters
path = u"C:\\Users\\" + username + u"\\data"  # BREAKS

# This works
path = u"C:\\Users\\{}\\data".format(username)  # WORKS
```

**Why It Happens**:
- Jython string concatenation with `+` doesn't handle mixed encoding well
- Java strings (from APIs) + Python unicode strings = encoding errors
- `.format()` properly handles type conversion

**The Solution**:
- **Always** use `.format()` for string building
- **Never** use `+` for strings that might contain non-ASCII
- Wrap API returns in `ensure_unicode()` before using

**Lesson**: `.format()` is not just style, it's necessary for correctness.

---

### Pitfall #3: Silent Exceptions Are Invisible

**The Problem**:
```python
try:
    # Complex operation that might fail
    result = do_something()
except:
    pass  # SILENTLY SWALLOWS ERRORS!

# Code continues, using broken/None result
return result  # Causes weird failures later
```

**Why It Happens**:
- Fiji's log window doesn't show unlogged exceptions
- Exception might occur but nothing indicates it
- Later code fails mysteriously because early step failed silently

**The Solution**:
```python
try:
    result = do_something()
except Exception as e:
    log(u"ERROR: do_something failed: {}".format(e))
    # Either re-raise or return safe default
    raise
```

**Real Example from v37.4**:
```python
# This was SILENTLY failing:
IJ.saveAs(imp, "Tiff", path)  # No try-except!

# Fixed in v37.4:
try:
    IJ.saveAs(imp, "Tiff", path)
except Exception as e:
    log(u"!!! EXCEPTION during 3D stack save: {}".format(e))
    raise  # Re-raise because this is CRITICAL
```

**Lesson**: Every critical operation needs try-except with logging, even if you re-raise.

---

### Pitfall #4: HyperStack ≠ CompositeImage

**The Problem**:
```python
# This creates a HyperStack (basic multi-channel stack)
imp = HyperStackConverter.toHyperStack(imp, c, z, t)

# This returns False!
if imp.isComposite():  # False - it's NOT a CompositeImage yet
    print("This never prints")
```

**Why It Happens**:
- HyperStack: Basic ImageJ stack with C/Z/T dimensions
- CompositeImage: Subclass that supports custom LUTs per channel
- toHyperStack() creates HyperStack, NOT CompositeImage
- Two different classes with different capabilities

**The Solution**:
```python
# Step 1: Create HyperStack
imp = HyperStackConverter.toHyperStack(imp, c, z, t)

# Step 2: Convert to CompositeImage (if needed for custom LUTs)
cimp = CompositeImage(imp, CompositeImage.COMPOSITE)

# Now this returns True
if cimp.isComposite():  # True
    cimp.setChannelLut(lut, channel)
```

**Lesson**: Know your ImageJ image types. HyperStack → multi-dimensional stack. CompositeImage → stack with custom colors.

---

### Pitfall #5: Exception Handling Can Return Wrong Image

**The Problem**:
```python
def apply_luts(imp):
    try:
        cimp = CompositeImage(imp)
        cimp.setChannelLut(lut, 1)
        return cimp  # Success path
    except Exception as e:
        log("Error: {}".format(e))
    
    return imp  # FALLS THROUGH - returns wrong image even on success!
```

**Why It Happens**:
- If ANY exception occurs (even minor), code falls through
- Returns original `imp` instead of modified `cimp`
- Even though the operation might have succeeded

**The Solution**:
```python
def apply_luts(imp):
    try:
        cimp = CompositeImage(imp)
        cimp.setChannelLut(lut, 1)
        return cimp  # Explicit return on success
    except Exception as e:
        log("Error: {}".format(e))
        return imp  # Only return original on actual error
```

**Lesson**: Every code path needs explicit return. Don't rely on fall-through after try-except.

---

## Zeiss CZI Format Pitfalls

### Pitfall #6: RGBA vs ARGB Color Format

**The Problem**:
```python
# Zeiss uses RGBA, not ARGB!
color_int = -16771841  # From Zeiss metadata

# WRONG: Treating as ARGB
A = (color_int >> 24) & 0xFF  # This is actually R!
R = (color_int >> 16) & 0xFF  # This is actually G!
G = (color_int >> 8) & 0xFF   # This is actually B!
B = color_int & 0xFF          # This is actually A!

# Result: RGB(255, 0, 20) becomes (255, 0, 20, 255) → looks correct by accident!
# But RGB(0, 255, 51) becomes (0, 255, 51, 255) → still works!
# Only fails with certain color combinations
```

**Why It Happens**:
- Zeiss stores colors as signed 32-bit integers in RGBA format
- Many imaging formats use ARGB (Alpha-Red-Green-Blue)
- Easy to assume ARGB is "standard"

**The Solution**:
```python
# Correct RGBA parsing
u = int(color_int) & 0xFFFFFFFF  # Convert signed to unsigned
hex8 = "%08X" % u  # e.g., "FF0014FF"
R = int(hex8[0:2], 16)  # RR
G = int(hex8[2:4], 16)  # GG
B = int(hex8[4:6], 16)  # BB
A = int(hex8[6:8], 16)  # AA (usually ignore)
```

**How to Verify**:
- Test with known colors from Zeiss ZEN software
- User provided actual values that confirmed RGBA format
- Cross-reference with Image.sc forum posts about Zeiss format

**Lesson**: Never assume color format. Verify with actual data from target system.

---

### Pitfall #7: Signed Integer Colors

**The Problem**:
```python
color_int = -16771841  # Negative number from Zeiss metadata

# This gives wrong result:
hex8 = "%08X" % color_int  # Python formats negative differently
# Result: "-FFFABC" (wrong) or huge positive (wrong)

# This works:
unsigned = color_int & 0xFFFFFFFF  # Convert to unsigned 32-bit
hex8 = "%08X" % unsigned  # Now formats correctly as "FF0014FF"
```

**Why It Happens**:
- Java/Zeiss uses signed 32-bit integers (range: -2^31 to 2^31-1)
- Negative values have high bit set
- Python needs explicit conversion to unsigned for correct hex formatting

**The Solution**:
Always mask to 32-bit unsigned: `color & 0xFFFFFFFF`

**Lesson**: When interfacing with Java, remember signed vs unsigned integer differences.

---

### Pitfall #8: Pixel Size in Wrong Units

**The Problem**:
```python
# OME-XML says: PhysicalSizeX="0.345"
# What units? Meters? Millimeters? Micrometers?

# Global metadata says: "ScalingX = 3.45"
# What units? No indication!

# If you assume both are in µm:
# 0.345 µm → Correct (subpixel for 20x objective)
# 3.45 µm → 10x too large!
```

**Why It Happens**:
- OME-XML units are typically micrometers but not always explicit
- Global metadata has no unit information
- Different metadata sources return different scales

**The Solution**:
```python
# Trust OME-XML (most reliable)
px_um = extract_from_ome_xml()  # Typically in µm, correct scale

# Fallback sources may need correction
px_fallback = extract_from_global_metadata()  # Often 10x too large
px_corrected = px_fallback / 10.0  # Apply correction factor

# Sanity check (20x objective → ~0.3-0.5 µm/pixel)
if not (0.1 <= px_um <= 1.0):
    log("WARNING: Pixel size {} seems unrealistic".format(px_um))
```

**Lesson**: Always validate pixel size against known physical reality. For 20x-40x objectives, expect 0.3-0.5 µm/pixel.

---

### Pitfall #9: Channel Count vs Z-Slice Interleaving

**The Problem**:
```python
# CZI file has: 3 channels, 4 z-slices
# Expected stack size: 3 × 4 = 12

# But Bio-Formats reports:
# getSizeC() → 12  # WRONG - treating all as channels!
# getSizeZ() → 1   # WRONG - no z-slices detected!

# Result: 12-channel 2D image instead of 3-channel 4-slice 3D image
```

**Why It Happens**:
- CZI format can interleave channels and z-slices
- Bio-Formats sometimes misinterprets the interleaving
- Dimension detection heuristics fail on certain acquisition patterns

**The Solution**:
```python
# Method 1: Force read from OME-XML
c_count = extract_from_ome_xml("SizeC")  # More reliable
z_count = extract_from_ome_xml("SizeZ")

# Method 2: Sanity check Bio-Formats
reported_c = reader.getSizeC()
reported_z = reader.getSizeZ()
total = reader.getImageCount()

if reported_c * reported_z != total:
    log("WARNING: Dimension mismatch - using OME-XML")
    # Use OME-XML values instead
```

**Lesson**: Don't trust Bio-Formats dimension detection blindly. Cross-check with OME-XML and total image count.

---

## Stitching Algorithm Pitfalls

### Pitfall #10: 3D Stitching Loses Channels

**The Problem**:
```python
# Direct 3D stitching on multi-channel stack:
IJ.run("Grid/Collection stitching", "...fusion_method=[Linear Blending]")

# Result: Stitched image has only 1 channel (or wrong number)
# All 4 channels merged into grayscale or one channel lost
```

**Why It Happens**:
- Fiji's stitching plugin doesn't always preserve channel dimension
- 3D stitching focuses on XYZ, may flatten C dimension
- CompositeImage format not preserved through fusion

**The Solution** (2D→3D Hybrid):
```python
# Step 1: Create 2D MIP (Maximum Intensity Projection) per tile
for tile in tiles:
    mip = create_mip(tile)  # Collapse Z, keep channels
    save(mip, "tile_MIP.tif")

# Step 2: Stitch 2D MIPs (fast, preserves channels better)
stitch_2d()  # Computes positions only

# Step 3: Transfer positions to 3D
transfer_coords_to_3d()

# Step 4: Fuse 3D with known positions
fuse_3d_with_positions()  # No re-calculation, just fusion
```

**Lesson**: 2D stitching is more reliable for channel preservation. Use 2D for registration, 3D only for fusion.

---

### Pitfall #11: Correlation Threshold Too Strict

**The Problem**:
```python
# Default regression threshold: 0.7 (70% correlation required)
stitch(regression_threshold=0.7)

# Result: Only 50% of tiles stitch, many valid matches rejected
# Correlation values: 0.65, 0.68, 0.62 → All rejected!
```

**Why It Happens**:
- Real microscopy data is noisy
- ApoTome grid patterns reduce correlation
- Out-of-focus regions lower correlation
- 0.7 is too strict for biological samples

**The Solution**:
```python
# Use 0.3 (30%) as default - much more forgiving
stitch(regression_threshold=0.3)

# Still rejects obvious mismatches (R < 0.3)
# Accepts most valid matches (R = 0.4-0.9)
```

**How to Tune**:
- Check correlation values in log
- If many matches with R = 0.4-0.6 rejected: Lower threshold
- If false matches with R = 0.2-0.3 accepted: Raise threshold

**Lesson**: Default parameters from clean test data often don't work on real biological samples.

---

### Pitfall #12: Stage Coordinates Are Wrong

**The Problem**:
```python
# Use stage coordinates from Zeiss metadata:
x_stage = 1000.0  # micrometers
y_stage = 500.0

# Convert to pixels:
x_pixels = x_stage / pixel_size  # 1000 / 0.345 = 2899 pixels

# But tiles are only 1024×1024!
# Overlap would be: 1024 - (2899 - 1024) = -851 pixels → NEGATIVE OVERLAP!
```

**Why It Happens**:
- Stage coordinates in absolute lab frame
- Stage zero-point arbitrary
- Stage positioning not pixel-perfect
- Mechanical backlash and drift

**The Solution**:
```python
# Use stage coordinates as ROUGH GUIDE only
# Let correlation-based stitching compute actual positions
stitch(compute_overlap=True, use_stage_coords=False)

# Or use stage coords to set search region:
max_displacement = 20  # Search ±20 pixels around stage position
```

**Lesson**: Stage coordinates are a starting point, not ground truth. Always use correlation-based registration.

---

## Metadata Extraction Pitfalls

### Pitfall #13: Multiple Metadata Sources Disagree

**The Problem**:
```python
# Method 1: OME-XML
px_ome = 0.345  # From <Pixels PhysicalSizeX="0.345">

# Method 2: OME Metadata object
px_meta = 0.345  # From omeMeta.getPixelsPhysicalSizeX()

# Method 3: Global metadata
px_global = 3.45  # From reader.getGlobalMetadata()

# Which is correct? They disagree by 10x!
```

**Why It Happens**:
- Different metadata layers in CZI format
- Bio-Formats extracts from multiple sources
- Sources may have different units or precision
- Some values are derived/calculated vs original

**The Solution** (Priority Order):
```python
# 1. OME-XML <Pixels> tag (MOST RELIABLE)
px = extract_from_ome_xml()
if px and 0.1 < px < 1.0:  # Sanity check
    return px

# 2. OME Metadata object
px = omeMeta.getPixelsPhysicalSizeX()
if px and 0.1 < px < 1.0:
    return px

# 3. Global metadata (LEAST RELIABLE, may need correction)
px = reader.getGlobalMetadata("ScalingX")
if px:
    return px / 10.0  # Often needs 10x correction

# 4. Give up
return None
```

**Lesson**: Establish a clear priority order and document it. Always sanity-check against physical reality.

---

### Pitfall #14: µ Character Breaks Everything

**The Problem**:
```python
# Metadata returns: "µm" (micrometer)
unit = reader.getMetadata("Unit")  # Returns "µm"

# Try to use it:
log(u"Size: {} {}".format(value, unit))  # CRASHES!
# 'ascii' codec can't decode byte 0xc2 in position 0

# Try to compare:
if unit == "µm":  # CRASHES!
# UnicodeDecodeError
```

**Why It Happens**:
- µ is Unicode character U+00B5
- Java/Bio-Formats returns it as UTF-8 bytes
- Jython string operations choke on it
- Even comparison operations fail

**The Solution**:
```python
# Wrap in ensure_unicode()
unit = ensure_unicode(reader.getMetadata("Unit"))

# Strip µ before using in comparisons
unit_clean = unit.replace(u"\u00b5", u"u")  # µm → um
if unit_clean == "um":
    # Now safe to compare

# Or just remove from log output:
log(u"Size: {} micrometers".format(value))  # Don't include unit at all
```

**Lesson**: Never trust that strings from Java APIs are safe to use in Python. Always wrap in ensure_unicode().

---

### Pitfall #15: Color Metadata Missing

**The Problem**:
```python
# Try to extract channel colors:
colors = extract_colors_from_ome_xml()

# Returns: []  (empty list)
# No error, just no colors!

# Check metadata:
# <Channel Name="DAPI" /> → No Color attribute!
```

**Why It Happens**:
- Not all CZI files have color information in metadata
- Depends on how acquisition was configured
- Older Zeiss software versions may not save colors
- Some acquisition modes don't have channel colors

**The Solution**:
```python
# Try multiple methods:
colors = extract_colors_from_ome_xml()
if not colors:
    colors = extract_colors_from_global_metadata()
if not colors:
    colors = extract_colors_from_displaySettings()
if not colors:
    log("WARNING: No color information found - using grayscale")
    return None  # Don't make up colors
```

**Lesson**: Metadata is optional. Always have a fallback (even if it's "do nothing").

---

## CompositeImage & LUT Pitfalls

### Pitfall #16: setChannelLut() Doesn't Persist

**The Problem**:
```python
cimp = CompositeImage(imp, CompositeImage.COMPOSITE)
cimp.setChannelLut(lut, 1)  # Sets LUT for channel 1

# Save the image:
IJ.saveAs(cimp, "Tiff", path)

# Reopen the image:
imp2 = IJ.openImage(path)

# Colors are wrong! LUT didn't save!
```

**Why It Happens**:
- setChannelLut() sets display LUT (temporary)
- TIFF saver may not save LUT information
- Or saves it in format that reopen doesn't restore

**The Solution**:
```python
# Method 1: Call updateAndDraw() after setting LUT
cimp.setChannelLut(lut, 1)
cimp.updateAllChannelsAndDraw()  # Forces LUT to be "baked in"

# Method 2: Check image before returning
if cimp.isComposite():
    # Verify LUT was applied
    actual_lut = cimp.getChannelLut(1)
    if actual_lut is None:
        log("WARNING: LUT not applied correctly")

# Method 3: Use setPosition() before setChannelLut()
cimp.setPosition(1, 1, 1)  # Channel, Z, Time
cimp.setChannelLut(lut, 1)
```

**Current Status in v37.4**:
We do all three methods. Still reports that colors don't persist correctly. May be fundamental TIFF format limitation.

**Lesson**: ImageJ LUT handling is fragile. May need to store colors in separate metadata file.

---

### Pitfall #17: Double-Wrapping CompositeImage

**The Problem**:
```python
# Create HyperStack with "Composite" mode:
imp = HyperStackConverter.toHyperStack(imp, c, z, t, "grayscale", "Composite")

# Think: "It says Composite, so it's a CompositeImage"
# But imp.isComposite() → False!

# So wrap it:
cimp = CompositeImage(imp, CompositeImage.COMPOSITE)

# Set LUTs:
cimp.setChannelLut(lut, 1)

# Later code calls setDisplayMode():
imp.setDisplayMode(IJ.COMPOSITE)  # Wait, which imp?

# Used wrong variable! Created ANOTHER CompositeImage!
# Result: LUTs applied to one instance, displaying another
```

**Why It Happens**:
- HyperStack vs CompositeImage confusion
- Variable name reuse (imp for multiple types)
- Multiple points of CompositeImage creation
- Easy to lose track of which object has LUTs

**The Solution**:
```python
# Create plain HyperStack (no "Composite" mode confusion)
imp = HyperStackConverter.toHyperStack(imp, c, z, t)

# Check if already CompositeImage (it won't be):
if imp.isComposite():
    cimp = imp  # Reuse
else:
    cimp = CompositeImage(imp, CompositeImage.COMPOSITE)  # Create

# Apply LUTs to cimp:
cimp.setChannelLut(lut, 1)

# Only call setDisplayMode on the cimp with LUTs:
if cimp.isComposite():
    cimp.setDisplayMode(IJ.COMPOSITE)

# Return cimp (not imp):
return cimp
```

**Lesson**: One CompositeImage creation point. Check isComposite() before wrapping. Use descriptive variable names.

---

### Pitfall #18: updateAndDraw() vs updateAllChannelsAndDraw()

**The Problem**:
```python
cimp = CompositeImage(imp)
cimp.setChannelLut(lut1, 1)
cimp.setChannelLut(lut2, 2)
cimp.setChannelLut(lut3, 3)

cimp.updateAndDraw()  # Only updates current channel!

# Result: Channel 1 has custom LUT, channels 2-3 have default colors
```

**Why It Happens**:
- `updateAndDraw()` only updates currently displayed channel
- CompositeImage has concept of "current channel"
- Other channels not refreshed

**The Solution**:
```python
cimp.updateAllChannelsAndDraw()  # Updates ALL channels
```

**Lesson**: For multi-channel images, always use `updateAllChannelsAndDraw()`.

---

## Unicode & File Path Pitfalls

### Pitfall #19: German Characters in Paths

**The Problem**:
```python
path = "C:\\Users\\Müller\\data\\Färbung.czi"

# This crashes:
f = open(path, 'r')  # UnicodeDecodeError

# This also crashes:
IJ.open(path)  # Can't find file (encoding issue)
```

**Why It Happens**:
- Windows uses different encoding (cp1252 or UTF-16)
- Java uses UTF-8
- Python/Jython uses ASCII by default
- Characters ü, ä get mangled in conversion

**The Solution**:
```python
import codecs

# For Python file operations:
with codecs.open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# For ImageJ operations:
path_unicode = ensure_unicode(path)
imp = IJ.openImage(path_unicode)

# For Java File objects:
from java.io import File
f = File(path_unicode)
```

**Lesson**: All file paths need explicit encoding handling. Never use raw Python open() for files with non-ASCII names.

---

### Pitfall #20: Spaces in Paths

**The Problem**:
```python
path = "C:\\Program Files\\Fiji\\data.tif"

# Pass to command line:
command = "convert {} output.tif".format(path)
os.system(command)
# Breaks: Sees "C:\\Program" as path, "Files\\Fiji\\data.tif" as separate args
```

**Why It Happens**:
- Shell interprets spaces as argument separators
- Need explicit quoting

**The Solution**:
```python
# Method 1: Quote the path
command = "convert \"{}\" output.tif".format(path)

# Method 2: Use list-based commands (no shell)
import subprocess
subprocess.call(["convert", path, "output.tif"])

# Method 3: Avoid command line entirely
imp = IJ.openImage(path)  # ImageJ handles quoting internally
```

**Lesson**: Avoid shell/command-line execution if possible. Use APIs directly.

---

## Development Process Lessons

### Lesson #1: User Testing Beats Assumptions

**What We Assumed**:
- Colors would be in ARGB format (industry standard)
- Pixel size from any metadata source would be correct
- Creating CompositeImage would be straightforward

**What User Testing Revealed**:
- Zeiss uses RGBA format (not industry standard)
- Pixel size varies 10x between metadata sources
- CompositeImage has 4 different failure modes

**Takeaway**: Build minimal version, test with real data, iterate. Don't build complete solution based on documentation alone.

---

### Lesson #2: Complexity Kills

**The Anti-Pattern**:
```
v31.16h: Working stitching
  ↓ Add advanced features
v32-v33: Broken stitching, but more features
  ↓ Add LUT detection
v34-v36: Working LUT detection
  ↓ Integrate stitching
v37.0-v37.3: Broken LUT display
```

**What Happened**:
- Each refinement added complexity
- Complexity created new failure modes
- Working features broke under integration
- Had to go back to basics and rebuild

**The Solution**:
- Identify proven working components
- Combine ONLY those components
- Don't add "improvements" during integration
- Test each integration step

**Takeaway**: Working code > elegant code. Ship simple working version before adding features.

---

### Lesson #3: Debug Early, Debug Often

**v37.0-v37.3 Problem**:
- LUTs not applying correctly
- No visibility into what was failing
- Had to add debug logging after the fact

**v37.4 Solution**:
- Comprehensive debug logging from start
- Visual markers (>>>, !!!) for success/failure
- Every critical operation logged

**Result**:
- Can now diagnose failures from user logs
- Don't need to reproduce bugs to understand them
- User can self-diagnose common issues

**Takeaway**: Debug logging is not "extra". It's essential infrastructure. Add it from day one.

---

### Lesson #4: Document Failures, Not Just Successes

**Standard Documentation**:
- "Here's how to use it"
- "Here's what it does"
- "Here are the parameters"

**This Documentation** (Pitfalls doc):
- "Here's what fails and why"
- "Here's what we tried that didn't work"
- "Here's how to recognize and fix problems"

**Value**:
- Future developers don't repeat mistakes
- Users understand limitations
- Saves countless hours of debugging

**Takeaway**: Document the journey, not just the destination. Failures are more educational than successes.

---

### Lesson #5: Version Everything

**What Gets Versioned in v37.4**:
- Script version (v37.4)
- Component versions (v31.16h workflow, v34.8 UTF-8, v36.5 LUTs)
- Splash screen shows versions
- Log output shows versions
- Documentation specifies versions

**Why This Matters**:
- "It doesn't work" → Which version?
- "Colors broke" → Was it working before? Which version?
- "I'm running v37.0" → You need v37.4 (4 critical fixes)

**Takeaway**: Can't debug if you don't know what code is running. Version everything.

---

## Quick Reference: Checklist for Avoiding Pitfalls

### Before Writing Code:
- [ ] Source file is pure ASCII (no µ, ä, ö, etc.)
- [ ] No encoding declaration
- [ ] All strings use u"..." prefix
- [ ] All string operations use .format()

### When Extracting Metadata:
- [ ] Try OME-XML first (most reliable)
- [ ] Sanity-check values against physical reality
- [ ] Wrap all strings in ensure_unicode()
- [ ] Have fallback for missing metadata

### When Handling Colors:
- [ ] Verify RGBA vs ARGB format
- [ ] Handle signed integers (& 0xFFFFFFFF)
- [ ] Test with known colors from Zeiss ZEN

### When Creating CompositeImage:
- [ ] Only one creation point in code
- [ ] Check imp.isComposite() before wrapping
- [ ] Use setPosition() before setChannelLut()
- [ ] Call updateAllChannelsAndDraw()
- [ ] Verify with imp.isComposite() after

### When Adding Exception Handling:
- [ ] Log the exception message
- [ ] Explicit return on each path
- [ ] Re-raise if operation is critical
- [ ] Visual marker (!!!) for errors

### When Testing:
- [ ] Test with real CZI files, not samples
- [ ] Test with German characters in paths
- [ ] Test with spaces in paths
- [ ] Test with 3+ channels
- [ ] Check colors match Zeiss ZEN
- [ ] Verify pixel size is realistic
- [ ] Check log for !!! markers

---

## Conclusion

These pitfalls represent hundreds of hours of debugging, testing, and iteration. They're hard-won knowledge from:
- Jython 2.7 limitations
- ImageJ/Fiji API quirks
- Zeiss CZI format oddities
- Bio-Formats behavior
- Real-world data challenges

**The good news**: They're all documented now. You don't have to repeat our mistakes.

**The bad news**: There are probably more pitfalls we haven't discovered yet.

**The request**: If you find new pitfalls, document them! Add to this file. Help the next person.

---

**Remember**: Every pitfall documented is one less bug for the next developer.
