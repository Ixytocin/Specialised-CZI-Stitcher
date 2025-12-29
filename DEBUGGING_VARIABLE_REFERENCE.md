# CZI-Stitcher Debugging Variable Reference

**Version:** 37.5  
**Last Updated:** 2025-12-29  
**Purpose:** Complete reference of all variables, their types, purposes, and relationships for debugging

---

## Table of Contents

1. [Global Configuration Variables](#global-configuration-variables)
2. [TileWorker Class Variables](#tileworker-class-variables)
3. [UltimateStitcher Class Variables](#ultimatestitcher-class-variables)
4. [Processing Pipeline Variables](#processing-pipeline-variables)
5. [Metadata Correction Variables](#metadata-correction-variables)
6. [Fallback Recovery Variables](#fallback-recovery-variables)
7. [File I/O Variables](#file-io-variables)
8. [Critical Data Structures](#critical-data-structures)

---

## Global Configuration Variables

### Debug Flags (Lines 63-71)

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `VERBOSE` | bool | True | Enable verbose logging output |
| `LOG_TILE_POS` | bool | True | Log tile positions during processing |
| `LUT_DEBUG` | bool | True | Enable LUT (lookup table) debug output |
| `DUMP_DEBUG` | bool | True | Enable debug dump of data structures |
| `DEBUG_METADATA` | bool | True | Log metadata extraction details |
| `DEBUG_STITCHING` | bool | True | Log stitching algorithm progress |
| `DEBUG_FILE_OPS` | bool | True | Log file operations (read/write/delete) |
| `DEBUG_MEMORY` | bool | True | Log memory usage statistics |
| `PLAY_JINGLE_ON_DONE` | bool | True | Play audio notification when complete |

### Constants (Lines 60, 74-80)

| Variable | Type | Value | Purpose |
|----------|------|-------|---------|
| `VERSION` | str | "v37.5" | Current script version |
| `MICRO` | unicode | "\u00b5" | Unicode micro symbol (μ) |
| `FLOAT_RE` | regex | `r"([-+]?\d*\.\d+..."` | Match floating point numbers |
| `ATTR_RE` | regex | `r'([A-Za-z_:]..."` | Match XML attributes |
| `STAGELABEL_RE` | regex | `r'<(?:[A-Za-z0-9_]+:)?StageLabel..."` | Match StageLabel XML tags |
| `_PIXELS_TAG_RE` | regex | `r'<Pixels\b([^>]*)>'` | Match Pixels XML tags |
| `_PHYSICAL_X_RE` | regex | `r'PhysicalSizeX\s*=..."` | Extract PhysicalSizeX attribute |
| `_PHYSICAL_XUNIT_RE` | regex | `r'PhysicalSizeXUnit..."` | Extract PhysicalSizeXUnit attribute |
| `_CHANNEL_COLOR_RE` | regex | `r'<(?:[A-Za-z0-9_]+:)?Channel..."` | Match Channel XML tags |
| `_CONFIG_PATH` | str | `~/.specialised_czi_stitcher_config.json` | User config file path |

---

## TileWorker Class Variables

**Class:** `TileWorker(Callable)` (Lines 947-1015)  
**Purpose:** Worker thread for processing individual tiles in parallel

### Instance Variables (Lines 950-955)

| Variable | Type | Source | Purpose |
|----------|------|--------|---------|
| `self.czi_path` | str | Constructor arg | Path to CZI input file |
| `self.i` | int | series_index | Series index in CZI (tile number) |
| `self.x` | float | x | Stage X position in micrometers |
| `self.y` | float | y | Stage Y position in micrometers |
| `self.out_dir` | str | out_dir | Output directory for tile files |
| `self.rb_radius` | int | rb_radius | Rolling ball background subtraction radius (0=disabled) |

### Return Tuple (Line 1012)

**Structure:** `(mip_name, 3d_name, series_idx, x, y, dimensions)`

| Index | Variable | Type | Example | Purpose |
|-------|----------|------|---------|---------|
| [0] | `nm` | str | "S000_MIP.tif" | 2D MIP filename for stitching |
| [1] | `nr` | str | "S000_3D.tif" | 3D stack filename |
| [2] | `self.i` | int | 0 | Series index (CRITICAL for prediction matching) |
| [3] | `self.x` | float | 1148.5 | Stage X position in pixels |
| [4] | `self.y` | float | 2.0 | Stage Y position in pixels |
| [5] | `d` | tuple | (1216, 1028, 4, 31, 1) | ImagePlus dimensions (width, height, channels, slices, frames) |

**CRITICAL BUG FIX (Commit 6402ba5):** Added `self.i` at index [2]. Previously missing, causing prediction storage to fail because matching code compared positions against series indices.

---

## UltimateStitcher Class Variables

**Class:** `UltimateStitcher` (Lines 1081-1953)  
**Purpose:** Main stitcher orchestrating the complete 2D→3D workflow

### Instance Variables (Lines 1086-1099)

| Variable | Type | Purpose | Default/Example |
|----------|------|---------|-----------------|
| `self.src` | str | Source CZI file path | User selected |
| `self.dst` | str | Output directory path | User selected |
| `self.t_limit` | int | Thread pool size limit | Computed from CPU |
| `self.temp_root` | str | Temporary directory root | System temp dir |
| `self.fusion_method` | str | Fiji stitching fusion method | "Linear Blending" |
| `self.rb_radius` | int | Background subtraction radius | 50 |
| `self.reg_thresh` | float | Registration threshold | 0.3 |
| `self.disp_thresh` | float | Max displacement (pixels) | 20.0 |
| `self.do_show` | bool | Show result image | True |
| `self.do_save` | bool | Save result image | True |
| `self.do_clean` | bool | Clean temp files | True |
| `self.auto_adjust` | bool | Auto-adjust LUTs | True |
| `self.corr_factor` | float | Pixel size correction factor | 10.0 |
| `self.correction_matrix` | dict | Metadata correction config | From config or None |

---

## Processing Pipeline Variables

### Main Workflow Variables (Lines 1183-1199)

| Variable | Type | Scope | Purpose |
|----------|------|-------|---------|
| `tiles` | list[dict] | process_file() | List of tile metadata dictionaries |
| `tiles[i]['i']` | int | per-tile | Series index |
| `tiles[i]['x_s']` | float | per-tile | Raw stage X position (micrometers) |
| `tiles[i]['y_s']` | float | per-tile | Raw stage Y position (micrometers) |
| `tiles[i]['method']` | str | per-tile | Position source ("StageLabel-order-map", "fallback-zero") |
| `fx` | list[float] | process_file() | List of all X stage positions (for bounds calculation) |
| `fy` | list[float] | process_file() | List of all Y stage positions (for bounds calculation) |

### Parallel Processing Variables (Lines 1326-1365)

| Variable | Type | Scope | Purpose |
|----------|------|-------|---------|
| `pool` | ThreadPoolExecutor | process_file() | Thread pool for parallel tile processing |
| `futures` | list[Future] | process_file() | List of submitted worker tasks |
| `res` | list[tuple] | process_file() | Results from TileWorker threads |
| `res[i][0]` | str | per-result | MIP filename ("S000_MIP.tif") |
| `res[i][1]` | str | per-result | 3D filename ("S000_3D.tif") |
| `res[i][2]` | int | per-result | Series index (for matching) |
| `res[i][3]` | float | per-result | X position in pixels |
| `res[i][4]` | float | per-result | Y position in pixels |
| `res[i][5]` | tuple | per-result | Dimensions (w, h, c, z, t) |

**CRITICAL:** Index [2] added in commit 6402ba5. All code accessing `res[]` must use correct indices!

### Grid Estimation Variables (Lines 1367-1393)

| Variable | Type | Purpose | Calculation |
|----------|------|---------|-------------|
| `sorted_unique_x` | list[float] | Unique X positions sorted | `sorted(set(fx))` |
| `sorted_unique_y` | list[float] | Unique Y positions sorted | `sorted(set(fy))` |
| `cols_est` | int | Estimated grid columns | `len(sorted_unique_x)` |
| `rows_est` | int | Estimated grid rows | `len(sorted_unique_y)` |
| `pos_to_grid` | dict | Map (x,y) → (col, row) | Built from sorted positions |
| `avg_tile_w` | float | Average tile width (pixels) | Mean of res[i][5][0] |
| `avg_tile_h` | float | Average tile height (pixels) | Mean of res[i][5][1] |

---

## Metadata Correction Variables

**Module:** `metadata_correction.py`  
**Integration:** Lines 1200-1305

### Correction Configuration (Lines 854-890)

| Variable | Type | Purpose |
|----------|------|---------|
| `correction_matrix` | dict | Full correction configuration |
| `correction_matrix['enabled']` | bool | Whether corrections are active |
| `correction_matrix['scale_x']` | float | X-axis scale factor (1.03265) |
| `correction_matrix['scale_y']` | float | Y-axis scale factor (1.00210) |
| `correction_matrix['sweep_limit']` | float | Pixel threshold for sweep moves (2000.0) |
| `correction_matrix['offsets']` | dict | Movement-specific corrections |

### Movement State Variables (Lines 1219-1246)

| Variable | Type | Purpose | Values |
|----------|------|---------|--------|
| `movement_state` | str | Current tile movement type | "start", "right", "left", "down", etc. |
| `delta_x_um` | float | X movement from previous tile (μm) | Calculated |
| `delta_y_um` | float | Y movement from previous tile (μm) | Calculated |
| `delta_x_px` | float | X movement in pixels | `delta_x_um / px_um_eff` |
| `delta_y_px` | float | Y movement in pixels | `delta_y_um / px_um_eff` |
| `is_sweep` | bool | Is this a sweep move? | `abs(delta_x_px) > sweep_limit` |
| `is_right` | bool | Moving right? | `delta_x_um > threshold` |
| `is_down` | bool | Moving down? | `delta_y_um > threshold` |

### Mask Classification (Lines 1247-1276)

| Variable | Type | Purpose | Range |
|----------|------|---------|-------|
| `mask` | int | Movement classification bitmask | 0-10 |
| `mask bit 0` | bool | Down movement | `is_down` |
| `mask bit 1` | bool | Right movement | `is_right` |
| `mask bit 2` | bool | Sweep movement | `is_sweep` |
| `mask bit 3` | bool | First axis activation | `first_x_move` or `first_y_move` |

**Mask values:**
- 0 = LEFT (000)
- 1 = LEFT_DOWN (001) or DOWN
- 2 = RIGHT (010)
- 3 = RIGHT_DOWN (011) or DIAG_RIGHT_DOWN
- 4 = SWEEP_LEFT (100)
- 5 = SWEEP_LEFT_DOWN (101)
- 6 = SWEEP_RIGHT (110)
- 7 = SWEEP_RIGHT_DOWN (111)
- 9 = FIRST_DOWN (1001)
- 10 = FIRST_RIGHT (1010)

### Applied Corrections (Lines 1278-1305)

| Variable | Type | Purpose |
|----------|------|---------|
| `offset_x` | float | X correction offset (pixels) |
| `offset_y` | float | Y correction offset (pixels) |
| `x_corrected_um` | float | Corrected X position (μm) |
| `y_corrected_um` | float | Corrected Y position (μm) |
| `x_corrected_px` | float | Corrected X position (pixels) |
| `y_corrected_px` | float | Corrected Y position (pixels) |

---

## Fallback Recovery Variables

**Section:** Lines 1540-1750  
**Purpose:** Recover failed tile alignments using neighbor-constrained prediction

### Detection Variables (Lines 1544-1560)

| Variable | Type | Purpose |
|----------|------|---------|
| `failed_tiles` | list[dict] | Tiles that failed 2D alignment |
| `failed_tiles[i]['mip_name']` | str | MIP filename of failed tile |
| `failed_tiles[i]['idx']` | int | Series index |
| `failed_tiles[i]['grid_pos']` | tuple | (col, row) in grid |
| `failed_tiles[i]['failed']` | bool | Always True (marker) |
| `failed_tiles[i]['correlation']` | float | Alignment correlation (0.0-1.0) |

### Prediction Storage (Lines 1562-1596)

**CRITICAL SECTION - Bug fixed in commit 6402ba5**

| Variable | Type | Purpose |
|----------|------|---------|
| `tile_positions` | dict | Maps MIP filename → position data |
| `tile_positions[mip_name]['predicted_xy']` | tuple | (x_pred, y_pred) from metadata |
| `tile_positions[mip_name]['registered_xy']` | tuple | (x_reg, y_reg) from stitching |
| `tile_positions[mip_name]['correlation']` | float | Stitching correlation score |
| `tile_positions[mip_name]['failed']` | bool | Whether tile failed alignment |
| `tile_positions[mip_name]['series_idx']` | int | Series index (for matching) |
| `tile_positions[mip_name]['grid_pos']` | tuple | (col, row) position |
| `tile_positions[mip_name]['state']` | str | Movement state |

**Storage Loop (Lines 1569-1593):**
```python
for t in tiles:
    for r in res:
        if r[2] == t['i']:  # Match series index (fixed in 6402ba5)
            mip_name = r[0]
            tile_positions[mip_name] = {
                'predicted_xy': (r[3], r[4]),  # Use positions from res
                'series_idx': t['i'],
                # ... etc
            }
```

### Neighbor Analysis Variables (Lines 1631-1710)

| Variable | Type | Purpose |
|----------|------|---------|
| `neighbors` | list[dict] | Candidate neighbor tiles |
| `neighbors[i]['mip_name']` | str | Neighbor's MIP filename |
| `neighbors[i]['correlation']` | float | Neighbor's correlation |
| `neighbors[i]['grid_dist']` | float | Grid distance to failed tile |
| `neighbors[i]['idx_dist']` | int | Index distance in sequence |
| `neighbors[i]['error_x']` | float | Neighbor's prediction error (X) |
| `neighbors[i]['error_y']` | float | Neighbor's prediction error (Y) |
| `neighbors[i]['state']` | str | Neighbor's movement state |
| `neighbors[i]['weight']` | float | IDW weight for averaging |

### Weighting Calculation (Lines 1665-1695)

| Variable | Type | Purpose | Formula |
|----------|------|---------|---------|
| `grid_dist` | float | Euclidean grid distance | `sqrt((col1-col2)² + (row1-row2)²)` |
| `idx_dist` | int | Sequence distance | `abs(idx1 - idx2)` |
| `base_weight` | float | Inverse distance weight | `1.0 / (grid_dist²)` |
| `correlation_weight` | float | Confidence weight | `neighbor['correlation']` |
| `move_compat` | float | Movement compatibility | 1.0 or 0.6 (mismatch) |
| `final_weight` | float | Combined weight | `base_weight × correlation_weight × move_compat` |

### Recovery Output Variables (Lines 1696-1720)

| Variable | Type | Purpose |
|----------|------|---------|
| `avg_error_x` | float | Weighted average X error |
| `avg_error_y` | float | Weighted average Y error |
| `sum_weights` | float | Total weight (for normalization) |
| `corrected_x` | float | Final recovered X position |
| `corrected_y` | float | Final recovered Y position |
| `avg_correlation` | float | Average neighbor confidence |
| `confidence` | float | Recovery confidence score | `avg_correlation × 0.75` |

### Safety Constraints (Lines 1675-1680)

| Constraint | Value | Purpose |
|------------|-------|---------|
| Correlation filter | R > 0.3 | Reject noise matches |
| Grid distance | ≤ 2 | Use adjacent/near tiles |
| Index distance | ≤ 3 | Use nearby in sequence |
| Confidence penalty | × 0.75 | Conservative estimate |
| Magnitude limit | None | Trust weighted consensus |

---

## File I/O Variables

### Configuration File Variables (Lines 89-112)

| Variable | Type | Purpose |
|----------|------|---------|
| `cfg` | dict | Loaded configuration |
| `cfg['last_input_dir']` | str | Last used input directory |
| `cfg['last_output_dir']` | str | Last used output directory |
| `cfg['last_processing_dir']` | str | Last used temp directory |
| `cfg['performance_scale']` | float | Performance scaling factor |
| `cfg['metadata_correction']` | dict | Correction matrix config |

### TileConfiguration Files (Lines 1422-1452)

| Variable | Type | Purpose |
|----------|------|---------|
| `tc_2d_path` | str | Path to 2D TileConfiguration.txt |
| `tc_3d_path` | str | Path to 3D TileConfiguration.txt |
| `tc_reg_path` | str | Path to registered TileConfiguration |

**TileConfiguration.txt format:**
```
dim = 2
S000_MIP.tif; ; (0.0, 0.0)
S001_MIP.tif; ; (1148.5, 2.0)
...
```

**Access pattern (Line 1432):**
```python
cfg_f.write(u"{0}; ; ({1:.6f}, {2:.6f})\n".format(r[0], r[3], r[4]))
#                                                   MIP   X     Y
```

### Output Files (Lines 1800-1853)

| Variable | Type | Purpose |
|----------|------|---------|
| `final_output_path` | str | Final stitched image path |
| `imp` | ImagePlus | Final stitched image object |
| `c_cnt` | int | Number of channels | `res[0][5][2]` |
| `z_cnt` | int | Number of Z slices | `res[0][5][3]` |

**CRITICAL (Line 1820):** Dimensions access fixed in commit 45c9166:
```python
c_cnt, z_cnt = res[0][5][2], res[0][5][3]  # Was res[0][4][2], res[0][4][3]
```

---

## Critical Data Structures

### Correlation Parsing (Lines 1467-1538)

**Purpose:** Extract correlation scores from Fiji stitching plugin output

| Variable | Type | Purpose |
|----------|------|---------|
| `stitch_log` | list[str] | Captured stitching output lines |
| `correlations` | dict | Maps tile pair → correlation |
| `correlations[(tile1, tile2)]` | float | R-value (0.0-1.0) |

**Parsing pattern:**
```
"S000_MIP.tif[1] <- S001_MIP.tif[1]: ... correlation (R)=0.9053513"
```

### 3D Configuration Transfer (Lines 1752-1798)

| Variable | Type | Purpose |
|----------|------|---------|
| `mip_to_3d` | dict | Maps MIP filename → 3D filename |
| `reg_lines` | list[str] | Lines from registered TileConfiguration |
| `tile_name` | str | Parsed tile name |
| `x_3d` | float | Registered X position |
| `y_3d` | float | Registered Y position |
| `z_3d` | float | Z position (always 0.0) |

---

## Common Debugging Scenarios

### Scenario 1: Predictions Not Stored

**Symptoms:** "Has prediction: 0" in fallback logs

**Check:**
1. `res[]` tuple structure (should have 6 elements)
2. Index [2] is series index (not X position)
3. `if r[2] == t['i']` comparison (line 1569)

**Debug output (Line 1574-1592):**
```
[DEBUG] Matching tiles to MIP names for predictions...
[DEBUG] tiles[] has X entries, res[] has Y entries
[DEBUG] Stored prediction for S000_MIP.tif (idx 0): (x, y)
```

### Scenario 2: Dimension Access Crash

**Symptoms:** IndexError or TypeError at "IMAGE CONVERSION AND LUT APPLICATION"

**Check:**
1. `res[0][5]` for dimensions (not `res[0][4]`)
2. Tuple has 6 elements: `(mip, 3d, idx, x, y, dims)`

**Debug line (Line 1820):**
```python
c_cnt, z_cnt = res[0][5][2], res[0][5][3]  # [5] = dimensions tuple
```

### Scenario 3: Fallback Not Recovering

**Symptoms:** Tiles remain at (0, 0) despite "Found N confident neighbors"

**Check:**
1. `tile_positions[mip_name]['predicted_xy']` exists
2. Neighbors have R > 0.3
3. Grid distance ≤ 2
4. Weighted error calculation (lines 1685-1700)

**Debug output (Lines 1615-1720):**
```
[ANALYZING] Tile S002_MIP.tif (idx 2, grid pos (2, 0))
  Has prediction: 1
  Found 4 confident neighbors (R>0.3)
  Weighted error correction: (+X, +Y)
  [SUCCESS] Final: (x, y) [confidence: 0.XX]
```

### Scenario 4: Movement State Misclassification

**Symptoms:** Normal moves classified as "sweep" or "unknown"

**Check:**
1. `sweep_limit` = 2000.0 (not 500.0) - Line 1235
2. Normal tile spacing ~1094 pixels
3. Mask calculation (lines 1247-1276)

**Debug output (Lines 1215-1220):**
```
Tile N: (x1, y1) -> (x2, y2) [delta: (dx, dy) um] state: right
```

---

## Variable Relationships Diagram

```
CZI File
  ↓
reader → ome_xml → stage_labels → tiles[] → TileWorker
                                     ↓
                                   res[] → tile_positions{}
                                     ↓              ↓
                         TileConfiguration.txt  Fallback
                                     ↓              ↓
                              Fiji Stitching   Recovery
                                     ↓              ↓
                         RegisteredConfig ← corrections
                                     ↓
                              3D Configuration
                                     ↓
                              Final Image
```

---

## Quick Reference: Most Common Variables

**File Processing:**
- `czi_path`: Input CZI file path
- `base_name`: Filename without extension
- `file_dst`: Temporary processing directory

**Tile Data:**
- `tiles[i]['i']`: Series index
- `tiles[i]['x_s']`, `tiles[i]['y_s']`: Stage positions (μm)
- `res[i][2]`: Series index (CRITICAL)
- `res[i][3]`, `res[i][4]`: Pixel positions

**Stitching:**
- `tc_2d_path`: 2D configuration for registration
- `tc_reg_path`: Registered configuration from Fiji
- `correlations{}`: Tile pair correlations

**Fallback:**
- `tile_positions{}`: Complete tile metadata
- `failed_tiles[]`: Tiles needing recovery
- `neighbors[]`: Candidate tiles for recovery

---

## Version History

- **v37.5** (2025-12-29): All bugs fixed, system operational
- **Commit 45c9166**: Fixed dimensions access (res[0][5] not res[0][4])
- **Commit 6402ba5**: CRITICAL - Added series index to TileWorker return
- **Commit 163c877**: Added extensive debug logging
- **Commit 7b10c1e**: Balanced safety constraints restored
- **Commit 1a32c9b**: Fixed sweep threshold (500→2000px)
- **Commit 557bd1c**: UTF-8 encoding + mask values fixed

---

**For additional debugging assistance, see:**
- METADATA_CORRECTION_README.md - Correction system details
- TECHDOC - Technical architecture documentation
- HELP.md - User guide and troubleshooting
