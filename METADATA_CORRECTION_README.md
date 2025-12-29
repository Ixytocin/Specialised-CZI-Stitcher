# Metadata Correction System - File Placement Guide

## Overview

The metadata correction system consists of multiple files that must be placed in specific locations for proper operation.

## File Structure

```
Specialised-CZI-Stitcher/
├── main.jy                           # Main stitcher script (run this in Fiji)
├── metadata_correction.py            # Correction module (place next to main.jy)
├── TECHDOC/
│   └── METADATA_CORRECTION_DESIGN.md # Technical documentation
├── tests/
│   └── test_metadata_correction.py   # Test suite (optional)
└── .specialised_czi_stitcher_config.json  # Auto-generated config (in home directory)
```

## Installation Instructions

### 1. Main Files (Required)

**Place these files in the SAME DIRECTORY:**

- **`main.jy`** - The main stitcher script
- **`metadata_correction.py`** - The correction module

**Location:** Both files MUST be in the same folder. This is typically:
- Your Fiji scripts folder, OR
- A custom directory where you keep your CZI processing scripts

**Example paths:**
```
Windows:  C:\Users\YourName\Fiji.app\scripts\main.jy
          C:\Users\YourName\Fiji.app\scripts\metadata_correction.py

macOS:    /Applications/Fiji.app/scripts/main.jy
          /Applications/Fiji.app/scripts/metadata_correction.py

Linux:    /home/yourname/Fiji.app/scripts/main.jy
          /home/yourname/Fiji.app/scripts/metadata_correction.py
```

### 2. How to Verify Correct Placement

Open `main.jy` in Fiji's Script Editor. When you run it, you should see in the log:

✅ **SUCCESS:** `[DEBUG] Metadata correction module loaded successfully`

❌ **ERROR:** `[DEBUG] Metadata correction module not available: ...`

If you see the error message, the files are NOT in the same directory!

### 3. Configuration File (Auto-Generated)

**File:** `.specialised_czi_stitcher_config.json`

**Location:** Your home directory (automatically created by the script)
- Windows: `C:\Users\YourName\.specialised_czi_stitcher_config.json`
- macOS: `/Users/yourname/.specialised_czi_stitcher_config.json`
- Linux: `/home/yourname/.specialised_czi_stitcher_config.json`

**Note:** This file is created automatically when you first run the script. It stores:
- Last used input/output directories
- Correction matrices for different microscopes
- Your preference settings

### 4. Optional Files

**Documentation (Reference Only):**
- `TECHDOC/METADATA_CORRECTION_DESIGN.md` - Technical design document
- Can be placed anywhere for reference

**Test Suite (For Developers):**
- `tests/test_metadata_correction.py` - Validation tests
- Can be placed anywhere for testing
- Run with: `python tests/test_metadata_correction.py`

## Quick Start

1. **Copy both files to the same folder:**
   ```
   main.jy
   metadata_correction.py
   ```

2. **Open `main.jy` in Fiji:**
   - Launch Fiji
   - File → Open → Select `main.jy`
   - OR drag `main.jy` onto Fiji window

3. **Run the script:**
   - Click "Run" button in Fiji Script Editor
   - OR press Ctrl+R (Windows/Linux) / Cmd+R (macOS)

4. **Verify in the log window:**
   - Look for: `[DEBUG] Metadata correction module loaded successfully`

## Troubleshooting

### Problem: "Metadata correction module not available"

**Solution 1:** Files not in same directory
- Move `metadata_correction.py` to the same folder as `main.jy`

**Solution 2:** Python path issue in Fiji
- Make sure both files are in a standard location (like Fiji's scripts folder)
- Restart Fiji after moving files

### Problem: "Mark invalid" error

**Solution:** This was fixed by separating the code into modules
- Make sure you have the latest version of both files
- If still occurring, the files might be corrupted - re-download

### Problem: Corrections not being applied

**Cause:** Corrections are disabled by default

**Solution:** Enable in the parameter dialog:
1. Run the script
2. In the parameter dialog, check: ☑ "Enable metadata correction"
3. Select your microscope from dropdown
4. Select thermal state (cold/preheated/unknown)
5. Click OK

## File Descriptions

### main.jy (Main Script)
- **Size:** ~97 KB, ~2400 lines
- **Purpose:** Main stitching workflow
- **Language:** Jython (Python 2.7 compatible with Java)
- **Runs in:** Fiji/ImageJ

### metadata_correction.py (Correction Module)
- **Size:** ~13 KB, ~400 lines
- **Purpose:** Metadata correction algorithms with LUT-based classification
- **Language:** Pure Python (Jython compatible)
- **Import from:** main.jy
- **Updated:** Version 2.0 with refined 251-tile dataset

### Configuration File Format

The `.specialised_czi_stitcher_config.json` file looks like:

```json
{
  "last_input_dir": "/path/to/input",
  "last_output_dir": "/path/to/output",
  "last_processing_dir": "/path/to/processing",
  "metadata_correction": {
    "default": {
      "enabled": true,
      "microscope_id": "default",
      "pixel_size_um": 0.345,
      "scale_x": 1.03265,
      "scale_y": 1.00210,
      "skew_xy": 0.0066,
      "sweep_limit": 500.0,
      "correction_lut": {
        "0": [-5.12, -3.80],
        "1": [-6.30, 18.60],
        "2": [0.84, -5.20],
        "3": [15.00, 15.00],
        "5": [36.20, 24.00],
        "7": [14.50, 12.20],
        "9": [-30.40, 18.60],
        "10": [18.37, -5.20]
      },
      ...
    },
    "zeiss_axio_1": {
      "enabled": false,
      ...
    }
  }
}
```

## Advanced: Multiple Microscopes

You can maintain separate correction matrices for different microscopes:

1. **First time setup per microscope:**
   - Run script
   - Select microscope from dropdown (e.g., "zeiss_axio_1")
   - Enable corrections
   - Process files

2. **Config file automatically stores:**
   - Separate correction matrix for each microscope
   - Last-used settings per microscope

3. **Next time:**
   - Just select the microscope from dropdown
   - Previous corrections are automatically loaded

## Support

If you encounter issues:

1. Check file placement (both files in same directory)
2. Check Fiji log for error messages
3. Verify files are not corrupted (check file sizes match documentation)
4. Try re-downloading files from the repository

## Tutorial: How to Update Correction Factors

### Overview

Correction factors can be derived by comparing:
1. **Metadata positions** (what the microscope thinks it moved)
2. **Stitching results** (where tiles actually ended up after image registration)

The delta between these values reveals systematic stage errors.

### Step-by-Step Guide

#### Step 1: Run Stitching with Debug Output

1. Enable metadata correction in the UI
2. Process your CZI files
3. Check the log for correction deltas:

```
Tile 0: (24384.63, 38272.20) -> (25163.45, 39497.26) [delta: (778.82, 1225.06) um] state: START
Tile 1: (24762.18, 38272.20) -> (25553.49, 39497.54) [delta: (791.31, 1225.34) um] state: RIGHT
```

4. Note the stitching plugin results in the log:

```
S000_MIP.tif: [3,3](AffineTransform[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
S001_MIP.tif: [3,3](AffineTransform[[1.0, 0.0, 1131.0], [0.0, 1.0, 8.5]])
```

#### Step 2: Calculate Metadata Delta

For each tile pair, calculate the **expected** pixel displacement from metadata:

```python
# Example: Tile 0 to Tile 1
metadata_x0 = 24384.631  # μm
metadata_y0 = 38272.202  # μm
metadata_x1 = 24762.178  # μm
metadata_y1 = 38272.202  # μm

# Delta in metadata (μm)
delta_x_metadata_um = metadata_x1 - metadata_x0  # = 377.547 μm
delta_y_metadata_um = metadata_y1 - metadata_y0  # = 0.0 μm

# Convert to pixels (assuming px_um = 0.345)
delta_x_metadata_px = delta_x_metadata_um / 0.345  # = 1094.3 px
delta_y_metadata_px = delta_y_metadata_um / 0.345  # = 0.0 px
```

#### Step 3: Get Actual Pixel Alignment

From stitching results (TileConfiguration.registered.txt or log):

```python
# Actual pixel positions from stitching plugin
actual_x0 = 0.0     # pixels (reference tile)
actual_y0 = 0.0     # pixels
actual_x1 = 1131.0  # pixels (from stitching)
actual_y1 = 8.5     # pixels

# Delta in actual alignment
delta_x_actual_px = actual_x1 - actual_x0  # = 1131.0 px
delta_y_actual_px = actual_y1 - actual_y0  # = 8.5 px
```

#### Step 4: Calculate Correction Factors

**Error = Actual - Expected:**

```python
error_x = delta_x_actual_px - delta_x_metadata_px  # = 1131.0 - 1094.3 = 36.7 px
error_y = delta_y_actual_px - delta_y_metadata_px  # = 8.5 - 0.0 = 8.5 px
```

**This error becomes your state-dependent offset!**

For a RIGHT move: `offset_right = (+36.7, +8.5) px`

#### Step 5: Classify Movement States

Determine the movement type based on deltas:

```python
# Boolean classification
is_sweep = abs(delta_x_metadata_px) > 500.0  # Threshold for rapid moves
is_right = delta_x_metadata_um > 0           # Moving right
is_down = delta_y_metadata_um > 0            # Moving down

# Create mask
mask = (int(is_sweep) << 2) | (int(is_right) << 1) | int(is_down)

# mask = 2 (binary: 010) means RIGHT steady state
# mask = 3 (binary: 011) means RIGHT+DOWN (short diagonal)
# mask = 7 (binary: 111) means sweep RIGHT+DOWN
```

#### Step 6: Collect Data Across Many Tiles

Repeat for **all tile pairs** in your dataset:

```python
corrections = {
    0: [],   # LEFT (000)
    1: [],   # DOWN_LEFT (001)
    2: [],   # RIGHT (010)
    3: [],   # DIAG_RIGHT_DOWN (011)
    5: [],   # SWEEP_LEFT_DOWN (101)
    7: [],   # SWEEP_RIGHT_DOWN (111)
    9: [],   # FIRST_DOWN (1001)
    10: []   # FIRST_RIGHT (1010)
}

for tile_pair in all_pairs:
    mask = classify_movement(tile_pair)
    error_x, error_y = calculate_error(tile_pair)
    corrections[mask].append((error_x, error_y))
```

#### Step 7: Calculate Average Offsets

```python
# Average for each state
for mask, errors in corrections.items():
    if errors:
        avg_x = sum(e[0] for e in errors) / len(errors)
        avg_y = sum(e[1] for e in errors) / len(errors)
        print(f"Mask {mask}: ({avg_x:.2f}, {avg_y:.2f}) px from {len(errors)} samples")
```

**Example output:**
```
Mask 2 (RIGHT): (0.84, -5.20) px from 98 samples
Mask 0 (LEFT): (-5.12, -3.80) px from 95 samples
Mask 3 (DIAG_RIGHT_DOWN): (15.00, 15.00) px from 42 samples
```

#### Step 8: Calculate Scale Factors

**Scale factor = Actual / Expected** (averaged across all moves):

```python
scale_x = avg(delta_x_actual_px / delta_x_metadata_px)  # = 1.03265
scale_y = avg(delta_y_actual_px / delta_y_metadata_px)  # = 1.00210
```

#### Step 9: Update metadata_correction.py

Edit the `create_default_correction_matrix()` function:

```python
def create_default_correction_matrix():
    return {
        'microscope_id': 'default',
        'pixel_size_um': 0.345,
        
        # UPDATE these values
        'scale_x': 1.03265,  # Your calculated scale
        'scale_y': 1.00210,  # Your calculated scale
        'skew_xy': 0.0066,
        
        # UPDATE the correction LUT
        'correction_lut': {
            0: (-5.12, -3.80),      # LEFT from your data
            1: (-6.30, 18.60),      # DOWN_LEFT
            2: (0.84, -5.20),       # RIGHT
            3: (15.00, 15.00),      # DIAG_RIGHT_DOWN
            5: (36.20, 24.00),      # SWEEP_LEFT_DOWN
            7: (14.50, 12.20),      # SWEEP_RIGHT_DOWN
            9: (-30.40, 18.60),     # FIRST_DOWN
            10: (18.37, -5.20)      # FIRST_RIGHT
        },
        # ... rest of configuration
    }
```

### Tips for Accurate Measurements

1. **Use many tiles** (100+ recommended, 251 used in current version)
2. **Include diverse movement patterns** (left, right, down, diagonals)
3. **Use well-focused, high-quality images** for accurate registration
4. **Process multiple CZI files** to average out random errors
5. **Exclude outliers** (>3σ from mean) before averaging
6. **Separate first movements** (FIRST_RIGHT, FIRST_DOWN) from steady state

### Verification

After updating values:
1. Process same dataset with new corrections
2. Check that pixel ranges match expected scales
3. Verify stitching quality improves
4. Log should show smaller correction deltas

## Version Information

- Script Version: v37.5
- Correction System Version: 2.0 (LUT-based, 251-tile dataset)
- Compatible with: Fiji/ImageJ with Bio-Formats plugin
- Requires: Java 8+, Jython 2.7+
