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
- **Size:** ~92 KB, ~2300 lines
- **Purpose:** Main stitching workflow
- **Language:** Jython (Python 2.7 compatible with Java)
- **Runs in:** Fiji/ImageJ

### metadata_correction.py (Correction Module)
- **Size:** ~12 KB, ~340 lines
- **Purpose:** Metadata correction algorithms
- **Language:** Pure Python (Jython compatible)
- **Import from:** main.jy

### Configuration File Format

The `.specialised_czi_stitcher_config.json` file looks like:

```json
{
  "last_input_dir": "/path/to/input",
  "last_output_dir": "/path/to/output",
  "last_processing_dir": "/path/to/processing",
  "metadata_correction": {
    "default": {
      "enabled": false,
      "microscope_id": "default",
      "pixel_size_um": 0.345,
      "scale_x": 1.0326,
      "scale_y": 1.0326,
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

## Version Information

- Script Version: v37.5
- Correction System Version: 1.0
- Compatible with: Fiji/ImageJ with Bio-Formats plugin
- Requires: Java 8+, Jython 2.7+
