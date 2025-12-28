# Metadata Correction System Design Document

## Overview

The CZI Stitcher currently uses idealized stage metadata to determine initial tile positions. However, systematic errors exist in the stage positioning system (backlash, scale errors, skew, thermal drift). This design implements an adaptive correction system that:

1. **Learns from stitching results** to improve future positioning accuracy
2. **Applies corrections** based on movement patterns (direction changes, distance)
3. **Reduces stitching computation time** by providing more accurate initial positions
4. **Maintains correction state** across sessions via settings file

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   METADATA CORRECTION SYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  Correction  │      │    State     │      │   Position   │  │
│  │    Matrix    │      │   Machine    │      │  Calculator  │  │
│  │              │      │              │      │              │  │
│  │ • Backlash   │─────▶│ • Direction  │─────▶│ • Apply      │  │
│  │ • Scale      │      │ • Distance   │      │   Correction │  │
│  │ • Skew       │      │ • Previous   │      │ • Metadata   │  │
│  │ • Thermal    │      │   State      │      │   Adjustment │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                                            │          │
│         │                                            │          │
│         ▼                                            ▼          │
│  ┌──────────────┐                            ┌──────────────┐  │
│  │   Settings   │                            │  Stitching   │  │
│  │     File     │                            │   Feedback   │  │
│  │              │                            │              │  │
│  │ • Persist    │◀───────────────────────────│ • Extract    │  │
│  │ • Load       │                            │   Errors     │  │
│  │ • Update     │                            │ • Update     │  │
│  └──────────────┘                            └──────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Coordinate System Convention

**Important**: The CZI microscope coordinate system follows this convention:
- **Down** (in visual space) = **Y increases** (positive Y direction)
- **Right** (in visual space) = **X increases** (positive X direction)
- **Up** movements are **NOT** defined as a primary case (only for exceptions/special cases)

This differs from typical screen coordinates where Y increases downward.

---

## Empirical Measurements from Real System (UPDATED v2.0)

The following values have been measured from a **251-tile dataset** and provide refined baseline corrections. This replaces earlier values that were "nearly worse than uncorrected metadata."

### System Calibration (Refined)

| Factor | Value | Unit | Description | Change from v1.0 |
|--------|-------|------|-------------|------------------|
| **Pixel Size** | 0.345 | μm/px | Physical sensor calibration | No change |
| **Scaling X** | 1.03265 | Scalar | 3.265% under-travel in X | Refined (+0.00015) |
| **Scaling Y** | 1.00210 | Scalar | 0.21% under-travel in Y | **Independent Y scale** |
| **Gantry Skew** | 0.38° | Degrees | Rotational non-orthogonality | No change |
| **M_scale_x** | 1.03265 | Matrix Diagonal | Linear travel expansion factor (X) | Refined |
| **M_scale_y** | 1.00210 | Matrix Diagonal | Linear travel expansion factor (Y) | **New (was same as X)** |
| **M_rot** | 0.0066 | Matrix Off-Diagonal | Cross-talk (skew) factor | No change |
| **Sweep Limit** | 500.0 | px | Threshold for rapid move detection | New parameter |

### State-Dependent Offsets (LUT-Based, v2.0)

**Note:** All values verified across 251 tiles. Completely revised from v1.0.

| Mask | Binary | State Name | X-Offset (px) | Y-Offset (px) | Context | Samples |
|------|--------|------------|---------------|---------------|---------|---------|
| **0** | 000 | LEFT | -5.12 | -3.80 | Steady-state horizontal (←) | 95 |
| **1** | 001 | DOWN_LEFT | -6.30 | +18.60 | Downward with left (backlash + rail skew) | 42 |
| **2** | 010 | RIGHT | +0.84 | -5.20 | Steady-state horizontal (→) | 98 |
| **3** | 011 | DIAG_RIGHT_DOWN | +15.00 | +15.00 | Short diagonal (row transitions) | 39 |
| **5** | 101 | SWEEP_LEFT_DOWN | +36.20 | +24.00 | High-momentum flyback (rapids) | 8 |
| **7** | 111 | SWEEP_RIGHT_DOWN | +14.50 | +12.20 | Advance jump (rapids) | 6 |
| **9** | 1001 | FIRST_DOWN | -30.40 | +18.60 | Initial downward (gravity + stiction break) | 5 |
| **10** | 1010 | FIRST_RIGHT | +18.37 | -5.20 | Initial rightward (lead-screw wind-up) | 5 |

**OLD v1.0 values (REMOVED - nearly worse than uncorrected):**
- ~~RIGHT: (+37.16, +8.15) px~~
- ~~LEFT: (-37.12, -8.37) px~~
- ~~Y_FIRST: (-6.10, +33.90) px~~
- ~~Y_SUBSEQ: (-20.70, +28.90) px~~

### Boolean Mask Classification

Movement is classified using a simple bit mask:

```
mask = (is_sweep << 2) | (is_right << 1) | is_down

Where:
  is_sweep = 1 if abs(delta_x_px) > 500.0 else 0
  is_right = 1 if delta_x_um > 0 else 0
  is_down  = 1 if delta_y_um > 0 else 0
  
For first movements, add bit 3:
  mask |= 8  (adds 8 to mask value)
```

### Correction Formula (v2.0)

The true position is computed using matrix transformation with LUT-based offsets:

$$P_{true} = \begin{bmatrix} 1.03265 & -0.0066 \\ 0.0066 & 1.00210 \end{bmatrix} \cdot \begin{bmatrix} x_{meta} \\ y_{meta} \end{bmatrix} + \text{LUT}[\text{mask}] + \vec{V}_{thermal}$$

Where:
- **M_scale_x** (1.03265) and **M_scale_y** (1.00210) form independent axis scaling
- **M_rot** (0.0066) provides the skew/cross-talk factor
- **LUT[mask]** provides state-dependent offset from lookup table above
- **V_thermal** is thermal drift correction (currently 0.0, reserved for future)
- **mask** is computed from movement boolean flags

**Key improvements over v1.0:**
- Independent X/Y scaling (Y was over-corrected in v1.0)
- LUT-based approach (simpler, more maintainable)
- State-specific offsets (not generic backlash penalties)
- Verified across 251 tiles (not estimated)

---

## Data Structures

### 1. Correction Matrix (Per-Microscope) - v2.0

The correction matrix stores systematic error correction factors for each microscope. **Updated to LUT-based approach.**

```python
correction_matrix = {
    # Microscope identifier
    'microscope_id': 'default',  # e.g., 'zeiss_axio_1', 'zeiss_axio_2'
    
    # Calibration
    'pixel_size_um': 0.345,  # Sensor calibration (μm/px)
    
    # Thermal state (preheated vs cold run)
    'thermal_state': 'unknown',  # 'cold', 'preheated', 'unknown'
    
    # Affine transformation matrix (from 251-tile empirical measurements)
    # [x']   [scale_x    -skew_xy ] [x]
    # [y'] = [skew_yx     scale_y ] [y]
    'scale_x': 1.03265,   # 3.265% under-travel (refined)
    'scale_y': 1.00210,   # 0.21% under-travel (independent Y scale)
    'skew_xy': 0.0066,    # Gantry skew component (0.38° rotation)
    'skew_yx': 0.0066,    # Symmetric skew
    
    # Sweep detection threshold (for rapid move classification)
    'sweep_limit': 500.0,  # Pixels
    
    # State-dependent correction lookup table (LUT)
    # Key = mask value (from boolean classification)
    # Value = [x_offset_px, y_offset_px]
    'correction_lut': {
        0: (-5.12, -3.80),      # LEFT (000)
        1: (-6.30, 18.60),      # DOWN_LEFT (001)
        2: (0.84, -5.20),       # RIGHT (010)
        3: (15.00, 15.00),      # DIAG_RIGHT_DOWN (011)
        5: (36.20, 24.00),      # SWEEP_LEFT_DOWN (101)
        7: (14.50, 12.20),      # SWEEP_RIGHT_DOWN (111)
        9: (-30.40, 18.60),     # FIRST_DOWN (1001)
        10: (18.37, -5.20)      # FIRST_RIGHT (1010)
    },
    
    # Thermal drift (function of z-stack, channels, tiles) - Reserved for future
    'thermal_drift_x': 0.0,       # Thermal drift in X (currently unused)
    'thermal_drift_y': 0.0,       # Thermal drift in Y (currently unused)
    'thermal_decay_rate': 0.95,   # Exponential decay per tile
    
    # Metadata
    'last_updated': '',  # ISO 8601 timestamp
    'num_sessions': 0,   # Number of stitching sessions
    'dataset_size': 251  # Number of tiles used for calibration
}
```

### 2. Microscope Configuration

Support for multiple microscopes with independent correction matrices.

```python
microscope_configs = {
    'default': correction_matrix,  # Default/unknown microscope
    'zeiss_axio_1': correction_matrix.copy(),
    'zeiss_axio_2': correction_matrix.copy(),
    # ... additional microscopes
}
```

### 3. Movement State (v2.0 - Simplified)

Tracks the movement pattern for each tile to determine which corrections to apply.

```python
movement_state = {
    'prev_x': None,  # Previous tile X position (μm)
    'prev_y': None,  # Previous tile Y position (μm)
    'first_right_done': False,  # Has first rightward movement occurred?
    'first_down_done': False,   # Has first downward movement occurred?
    'tiles_processed': 0,       # Number of tiles processed
}
```

**Changes from v1.0:**
- Removed `prev_dir_x` and `prev_dir_y` (not needed for LUT approach)
- Added `first_right_done` to track first rightward movement separately
- Simpler state tracking with boolean masks

---

## Truth Table for Correction Application

The system uses a matrix-based state machine to determine which corrections to apply.

### Movement Classification

Per microscope coordinate convention (Down = Y+, Right = X+):

- **X Direction:**
  - `'right'`: Moving in positive X (X increases)
  - `'left'`: Moving in negative X (X decreases)  
  - `None`: No X movement or first tile

- **Y Direction:**
  - `'down'`: Moving in positive Y (Y increases, visual down)
  - `None`: No Y movement or first tile
  - **Note:** Up movements (Y decreases) are NOT primary cases

- **Distance:**
  - `'short'`: Normal tile spacing (~1 tile width/height)
  - `'long_right'`: Long X+ jump (>threshold, circle tracing)
  - `'long_left'`: Long X- jump (>threshold, circle tracing)

### Grid Traversal Properties

- Grid is **closed without holes** (contiguous tiles)
- Grid **CAN be traversed without diagonal moves** (topologically possible with only orthogonal moves)
- **Real data DOES use diagonal moves** at row ends to jump to next row start position
- **Long X jumps** occur for circle tracing patterns (discontinuous moves with rapids)
- **Idle time does NOT affect backlash** (mechanical property, not time-dependent)

### Movement Types in Real Data

1. **Orthogonal moves** (within rows/columns):
   - Horizontal: left/right within same row
   - Vertical: up/down within same column
   - Speed: Normal scanning speed
   - Backlash: Full backlash penalties on direction changes

2. **Short diagonal moves** (normal row transitions):
   - Combined X+Y movement at row ends
   - Example: End of row → start of next row (left+down or right+down)
   - Distance: ~1 tile spacing in each axis
   - Speed: **Similar to regular R/L/down movement** (no rapids)
   - Backlash: Full backlash penalties (same as orthogonal moves)
   - Common in serpentine scanning patterns

3. **Long diagonal moves** (large row/column jumps):
   - Combined X+Y movement with large displacement
   - Example: Jump to distant tile position
   - Distance: >threshold in X or Y axis
   - Speed: **Considerable rapids** (rapid acceleration/deceleration)
   - Backlash: **Reduced backlash** due to rapid movement allowing settling
   - Less common, used for repositioning

4. **Long orthogonal jumps** (circle tracing):
   - Large X displacement only (>2x tile width)
   - Speed: **Considerable rapids** (rapid repositioning)
   - Backlash: **Reduced backlash** due to slowdown after rapid movement
   - Used for circle tracing patterns

### Truth Table (Empirically-Driven State Machine)

Based on real stitching data, each movement state has measured offsets and backlash penalties:

| State Code | Scenario | Distance | Speed | Applied Corrections | Empirical Offset (px) | Backlash (px) |
|------------|----------|----------|-------|---------------------|----------------------|---------------|
| `START` | **First tile** | N/A | N/A | `affine_transform` + `thermal_drift` | (0, 0) | None |
| `RIGHT` | **Moving right** | Short | Normal | `affine_transform` + `offset_right` + `thermal_drift` | (+37.16, +8.15) | None (continuing) |
| `LEFT` | **Moving left** | Short | Normal | `affine_transform` + `offset_left` + `thermal_drift` | (-37.12, -8.37) | None (continuing) |
| `R_TO_L` | **Right → Left** | Short | Normal | `affine_transform` + `offset_left` + `backlash_x` + `reversal` | (-37.12, -8.37) | X: 3.50, Rev: 0.70 |
| `L_TO_R` | **Left → Right** | Short | Normal | `affine_transform` + `offset_right` + `backlash_x` + `reversal` | (+37.16, +8.15) | X: 3.50, Rev: 0.70 |
| `Y_FIRST` | **First down** | Short | Normal | `affine_transform` + `first_down_offset` | (-6.10, +33.90) | None (high stiction) |
| `Y_SUBSEQ` | **Subsequent down** | Short | Normal | `affine_transform` + `subseq_down_offset` + `backlash_y` | (-20.70, +28.90) | Y: 1.20 |
| `DIAG_SHORT` | **Short diagonal** | Short | **Normal** | `affine_transform` + `offset_X` + `offset_Y` + `backlash_full` | Combined X+Y | **Full backlash** |
| `LONG_R` | **Long right** | Long X | **Rapids** | `affine_transform` + `backlash_long_x_right` | TBD | **Reduced** (0.0 default) |
| `LONG_L` | **Long left** | Long X | **Rapids** | `affine_transform` + `backlash_long_x_left` | TBD | **Reduced** (0.0 default) |
| `LONG_Y` | **Long Y** | Long Y | **Rapids** | `affine_transform` + `backlash_long_y` | TBD | **Reduced** (0.0 default) |
| `LONG_DIAG` | **Long diagonal** | Long X+Y | **Rapids** | `affine_transform` + `offset_X` + `offset_Y` + `backlash_long_diag` | Combined X+Y | **Reduced** (0.0 default) |

**Key distinction - Speed and Backlash:**
- **Short moves** (distance ~1 tile): **Normal scanning speed**, similar to regular R/L/down movement
  - Full backlash penalties apply (backlash_x: 3.50px, backlash_y: 1.20px)
  - No rapids involved
  
- **Long moves** (distance >threshold × tile size): **Considerable rapids** involved
  - Reduced backlash penalties (default 0.0, can be tuned)
  - Rapid acceleration/deceleration allows settling
  - Examples: Circle tracing, repositioning to distant tiles

**Move type detection:**
- Short: `abs(delta_x) ≤ threshold_x × tile_width AND abs(delta_y) ≤ threshold_y × tile_height`
- Long: `abs(delta_x) > threshold_x × tile_width OR abs(delta_y) > threshold_y × tile_height`
- Default thresholds: threshold_x = 2.0, threshold_y = 2.0

**Key:**
- **affine_transform**: Apply the 2x2 matrix `[[1.0326, -0.0066], [0.0066, 1.0326]]`
- **offset_X**: State-dependent steady-state bias (converted from pixels to μm)
- **backlash_X**: Direction-change penalty
- **reversal**: Additional 180° flip penalty (row changes)
- **thermal_drift**: Exponentially decaying drift based on cold/preheated state

### Correction Application Formula

```python
def apply_corrections(x_meta, y_meta, state_code, prev_state, correction_matrix):
    """
    Apply empirical corrections to metadata position.
    
    P_true = M_affine · P_meta + V_state + V_backlash + V_thermal
    """
    px_um = correction_matrix['pixel_size_um']  # 0.345 μm/px
    
    # 1. Affine transformation (scale + skew)
    scale_x = correction_matrix['scale_x']  # 1.0326
    scale_y = correction_matrix['scale_y']  # 1.0326
    skew_xy = correction_matrix['skew_xy']  # -0.0066 (note: negative for Y from X)
    skew_yx = correction_matrix['skew_yx']  # 0.0066
    
    x_scaled = scale_x * x_meta - skew_xy * y_meta
    y_scaled = skew_yx * x_meta + scale_y * y_meta
    
    # 2. State-dependent offset (convert px to μm)
    offset_x_um = 0.0
    offset_y_um = 0.0
    
    if state_code == 'RIGHT':
        offset_x_um = correction_matrix['offset_right_x'] * px_um  # +37.16 px
        offset_y_um = correction_matrix['offset_right_y'] * px_um  # +8.15 px
    elif state_code == 'LEFT':
        offset_x_um = correction_matrix['offset_left_x'] * px_um   # -37.12 px
        offset_y_um = correction_matrix['offset_left_y'] * px_um   # -8.37 px
    elif state_code == 'Y_FIRST':
        offset_x_um = correction_matrix['first_down_x_offset'] * px_um  # -6.10 px
        offset_y_um = correction_matrix['first_down_y_offset'] * px_um  # +33.90 px
    elif state_code == 'Y_SUBSEQ':
        offset_x_um = correction_matrix['subseq_down_x_offset'] * px_um  # -20.70 px
        offset_y_um = correction_matrix['subseq_down_y_offset'] * px_um  # +28.90 px
    
    # 3. Backlash penalties on direction changes
    backlash_x_um = 0.0
    backlash_y_um = 0.0
    
    if state_code in ['R_TO_L', 'L_TO_R']:
        backlash_x_um = correction_matrix['backlash_x'] * px_um  # 3.50 px
        # Additional reversal penalty for row flips
        backlash_x_um += correction_matrix['backlash_reversal'] * px_um  # 0.70 px
    
    if state_code == 'Y_SUBSEQ' and prev_state != 'Y_SUBSEQ':
        # Y backlash only on direction change
        backlash_y_um = correction_matrix['backlash_y'] * px_um  # 1.20 px
    
    # 4. Thermal drift (exponentially decaying)
    thermal_x, thermal_y = calculate_thermal_drift(correction_matrix)
    
    # Final position
    x_corrected = x_scaled + offset_x_um + backlash_x_um + thermal_x
    y_corrected = y_scaled + offset_y_um + backlash_y_um + thermal_y
    
    return x_corrected, y_corrected
```

### State Machine Debug Output

The system outputs a visual grid representation and state sequence for debugging:

```python
# Example debug output for 10-tile grid in 4x5 bounding box:
log(u"=== GRID LAYOUT ===")
log(u"0x00")  # Tile 0 at (0,0), tile 1 at (1,0)
log(u"xxxx")  # Tiles 2-5 filling row
log(u"00xx")  # Tiles 6-7 at start, 8-9 at end
log(u"00xx")  # Similar pattern
log(u"000x")  # Partial row

log(u"=== STATE SEQUENCE ===")
log(u"start, down, long_right, left, left, left, down, right, long, down, left, down, right")
```

### Special Cases

1. **First Down (Unknown backlash state)**
   - **Problem:** Backlash state is unknown for first Y+ movement
   - **Solution:** Use `first_down_y_offset` learned from previous sessions
   - **Why:** Can't determine prior stage direction before scan started
   - **Learning:** Extract from first Y-direction neighbor pairs with confidence weighting

2. **Long X Moves (Circle tracing with rapids)**
   - **Phenomenon:** Distance-based slowdown affects backlash differently
   - **Detection:** `distance > long_move_threshold_x * tile_width`
   - **Correction:** Use `backlash_long_x_left` or `backlash_long_x_right`
   - **Note:** Only discontinuous move in typical grid traversal

---

## Thermal Load Calculation

Thermal drift is a function of z-stack height, number of channels, and number of tiles.

```python
def calculate_thermal_load_factor(z_stack_height_um, num_channels, num_tiles):
    """
    Calculate thermal load factor based on acquisition parameters.
    
    Thermal load increases with:
    - Z-stack height (more stage movement, more heat)
    - Number of channels (more LED/laser activation, more heat)
    - Number of tiles (longer acquisition time, more cumulative heat)
    
    Args:
        z_stack_height_um: Total Z-stack height in micrometers
        num_channels: Number of imaging channels
        num_tiles: Total number of tiles in scan
    
    Returns:
        thermal_load_factor: Scalar value (0.0 = minimal, 1.0+ = high thermal load)
    """
    # Normalize factors (adjust coefficients based on empirical data)
    z_factor = z_stack_height_um / 100.0  # Normalize to ~100μm baseline
    ch_factor = num_channels / 3.0        # Normalize to 3-channel baseline
    tile_factor = num_tiles / 50.0        # Normalize to 50-tile baseline
    
    # Combined thermal load (weighted sum)
    # Adjust weights based on actual thermal behavior
    thermal_load = 0.4 * z_factor + 0.3 * ch_factor + 0.3 * tile_factor
    
    return thermal_load

def select_thermal_drift(correction_matrix, thermal_load_factor):
    """
    Select appropriate thermal drift correction based on system state.
    
    Args:
        correction_matrix: Correction matrix with thermal parameters
        thermal_load_factor: Computed thermal load (from calculate_thermal_load_factor)
    
    Returns:
        (thermal_drift_x, thermal_drift_y): Selected drift corrections in μm
    """
    thermal_state = correction_matrix['thermal_state']
    
    if thermal_state == 'cold':
        # Cold run: full thermal drift
        drift_x = correction_matrix['thermal_drift_x_cold'] * thermal_load_factor
        drift_y = correction_matrix['thermal_drift_y_cold'] * thermal_load_factor
    elif thermal_state == 'preheated':
        # Preheated: reduced thermal drift
        drift_x = correction_matrix['thermal_drift_x_preheated'] * thermal_load_factor
        drift_y = correction_matrix['thermal_drift_y_preheated'] * thermal_load_factor
    else:
        # Unknown: assume cold (conservative)
        drift_x = correction_matrix['thermal_drift_x_cold'] * thermal_load_factor
        drift_y = correction_matrix['thermal_drift_y_cold'] * thermal_load_factor
    
    return drift_x, drift_y
```

---

## Jython-Compatible Matrix Operations

Since we cannot use NumPy (not available in Jython), we implement pure Python matrix operations.

**Design Note:** While if-then loops are avoided where possible for performance, the actual performance impact for <1000 tiles is negligible. The matrix-based approach is preferred for conceptual clarity and maintainability.

### Required Operations

```python
# 2D transformation matrix for position correction
# [x']   [scale_x    skew_xy  ] [x]   [offset_x]
# [y'] = [skew_yx    scale_y  ] [y] + [offset_y]

class MatrixOps:
    """Pure Python matrix operations for Jython compatibility"""
    
    @staticmethod
    def apply_2d_transform(x, y, scale_x, scale_y, skew_xy, skew_yx, offset_x, offset_y):
        """
        Apply 2D affine transformation to point (x, y)
        
        Returns: (x', y') corrected coordinates
        """
        x_prime = scale_x * x + skew_xy * y + offset_x
        y_prime = skew_yx * x + scale_y * y + offset_y
        return x_prime, y_prime
    
    @staticmethod
    def interpolate(old_value, new_value, learning_rate):
        """
        Exponential moving average for learning
        
        new_estimate = old_estimate * (1 - learning_rate) + observation * learning_rate
        """
        return old_value * (1.0 - learning_rate) + new_value * learning_rate
```

---

## Correction Application Algorithm

### Pseudocode

```python
def apply_corrections_to_tile(tile_x_um, tile_y_um, tile_index, correction_matrix, movement_state):
    """
    Apply systematic error corrections to tile position
    
    Args:
        tile_x_um: Ideal X position from metadata (micrometers)
        tile_y_um: Ideal Y position from metadata (micrometers)
        tile_index: Index of this tile in processing order
        correction_matrix: Dict of correction factors
        movement_state: Dict tracking previous tile movement
    
    Returns:
        (corrected_x_um, corrected_y_um): Corrected position in micrometers
    """
    
    # Initialize for first tile
    if movement_state['prev_x'] is None:
        movement_state['prev_x'] = tile_x_um
        movement_state['prev_y'] = tile_y_um
        movement_state['tiles_processed'] = 0
        
        # First tile: only scale, skew, initial thermal drift
        x_corrected, y_corrected = MatrixOps.apply_2d_transform(
            tile_x_um, tile_y_um,
            correction_matrix['scale_x'],
            correction_matrix['scale_y'],
            correction_matrix['skew_xy'],
            correction_matrix['skew_yx'],
            correction_matrix['thermal_drift_x'],
            correction_matrix['thermal_drift_y']
        )
        
        return x_corrected, y_corrected
    
    # Calculate movement
    delta_x = tile_x_um - movement_state['prev_x']
    delta_y = tile_y_um - movement_state['prev_y']
    
    # Classify direction
    curr_dir_x = 'pos' if delta_x > 0.5 else ('neg' if delta_x < -0.5 else None)
    curr_dir_y = 'pos' if delta_y > 0.5 else ('neg' if delta_y < -0.5 else None)
    
    # Detect long jumps (>2x normal tile spacing)
    normal_spacing_x = 1000.0  # Typical tile width in μm (adjust based on actual data)
    normal_spacing_y = 800.0   # Typical tile height in μm
    is_long_jump = (abs(delta_x) > 2 * normal_spacing_x) or (abs(delta_y) > 2 * normal_spacing_y)
    
    # Initialize correction offsets
    offset_x = 0.0
    offset_y = 0.0
    
    # Apply backlash corrections (if not a long jump)
    if not is_long_jump:
        # X-axis backlash
        if movement_state['prev_dir_x'] == 'pos' and curr_dir_x == 'neg':
            offset_x += correction_matrix['backlash_x_pos_to_neg']
        elif movement_state['prev_dir_x'] == 'neg' and curr_dir_x == 'pos':
            offset_x += correction_matrix['backlash_x_neg_to_pos']
        
        # Y-axis backlash (with special first-down case)
        if not movement_state['first_y_negative_done'] and curr_dir_y == 'neg':
            # First down: use special offset
            offset_y += correction_matrix['first_down_y_offset']
            movement_state['first_y_negative_done'] = True
        elif movement_state['prev_dir_y'] == 'pos' and curr_dir_y == 'neg':
            # Subsequent down: use normal backlash
            offset_y += correction_matrix['backlash_y_pos_to_neg']
        elif movement_state['prev_dir_y'] == 'neg' and curr_dir_y == 'pos':
            # Up: use normal backlash
            offset_y += correction_matrix['backlash_y_neg_to_pos']
    
    # Apply thermal drift (decays exponentially)
    tiles_processed = movement_state['tiles_processed']
    decay_factor = correction_matrix['thermal_decay_rate'] ** tiles_processed
    offset_x += correction_matrix['thermal_drift_x'] * decay_factor
    offset_y += correction_matrix['thermal_drift_y'] * decay_factor
    
    # Apply scale and skew corrections
    x_corrected, y_corrected = MatrixOps.apply_2d_transform(
        tile_x_um, tile_y_um,
        correction_matrix['scale_x'],
        correction_matrix['scale_y'],
        correction_matrix['skew_xy'],
        correction_matrix['skew_yx'],
        offset_x,
        offset_y
    )
    
    # Update state for next tile
    movement_state['prev_x'] = tile_x_um
    movement_state['prev_y'] = tile_y_um
    movement_state['prev_dir_x'] = curr_dir_x if curr_dir_x is not None else movement_state['prev_dir_x']
    movement_state['prev_dir_y'] = curr_dir_y if curr_dir_y is not None else movement_state['prev_dir_y']
    movement_state['tiles_processed'] += 1
    
    return x_corrected, y_corrected
```

---

## Learning from Stitching Results

After the stitching plugin computes tile positions, we extract the position errors and update the correction matrix.

### Extracting Position Errors

```python
def extract_position_errors(ideal_positions, stitched_positions, confidence_scores):
    """
    Extract systematic errors from stitching results
    
    Args:
        ideal_positions: List of (x, y) positions from metadata
        stitched_positions: List of (x, y) positions from stitching plugin
        confidence_scores: List of confidence values from stitching (0-1)
    
    Returns:
        error_analysis: Dict containing categorized errors
    """
    
    error_analysis = {
        'backlash_x_pos_to_neg': [],
        'backlash_x_neg_to_pos': [],
        'backlash_y_pos_to_neg': [],
        'backlash_y_neg_to_pos': [],
        'first_down_y': [],
        'scale_x_errors': [],
        'scale_y_errors': [],
        'skew_xy_errors': [],
        'skew_yx_errors': [],
    }
    
    for i in range(1, len(ideal_positions)):
        # Calculate ideal and actual deltas
        ideal_dx = ideal_positions[i][0] - ideal_positions[i-1][0]
        ideal_dy = ideal_positions[i][1] - ideal_positions[i-1][1]
        
        actual_dx = stitched_positions[i][0] - stitched_positions[i-1][0]
        actual_dy = stitched_positions[i][1] - stitched_positions[i-1][1]
        
        error_x = actual_dx - ideal_dx
        error_y = actual_dy - ideal_dy
        
        # Classify movement and accumulate errors
        prev_dir_x = 'pos' if ideal_dx > 0.5 else ('neg' if ideal_dx < -0.5 else None)
        curr_dir_x = 'pos' if ideal_positions[i][0] > ideal_positions[i-1][0] else 'neg'
        
        # ... (categorize errors based on movement pattern)
        # Weight by confidence score
        weighted_error_x = error_x * confidence_scores[i]
        weighted_error_y = error_y * confidence_scores[i]
        
        # Accumulate into appropriate category
        # ...
    
    return error_analysis
```

### Updating Correction Matrix

```python
def update_correction_matrix(correction_matrix, error_analysis, learning_rate):
    """
    Update correction matrix using exponential moving average
    
    Args:
        correction_matrix: Current correction factors (modified in place)
        error_analysis: Categorized errors from stitching
        learning_rate: How quickly to adapt (0.0 = never, 1.0 = instant)
    """
    
    # Update each correction factor
    for error_type, errors in error_analysis.items():
        if len(errors) > 0:
            # Calculate weighted mean of errors
            total_weight = sum(e['confidence'] for e in errors)
            if total_weight > 0:
                weighted_mean = sum(e['error'] * e['confidence'] for e in errors) / total_weight
                
                # Update with exponential moving average
                old_value = correction_matrix[error_type]
                new_value = MatrixOps.interpolate(old_value, weighted_mean, learning_rate)
                correction_matrix[error_type] = new_value
    
    # Update metadata
    correction_matrix['num_sessions'] += 1
    correction_matrix['last_updated'] = datetime.now().isoformat()
```

---

## Settings File Integration

### File Format

The correction matrix is stored in the existing settings file (`.specialised_czi_stitcher_config.json`) under a new key.

```json
{
  "last_input_dir": "...",
  "last_output_dir": "...",
  "performance_scale": 1.0,
  
  "metadata_correction": {
    "enabled": true,
    "backlash_x_pos_to_neg": 0.0,
    "backlash_x_neg_to_pos": 0.0,
    "backlash_y_pos_to_neg": 0.0,
    "backlash_y_neg_to_pos": 0.0,
    "scale_x": 1.0,
    "scale_y": 1.0,
    "skew_xy": 0.0,
    "skew_yx": 0.0,
    "thermal_drift_x": 0.0,
    "thermal_drift_y": 0.0,
    "thermal_decay_rate": 0.95,
    "first_down_y_offset": 0.0,
    "first_down_confidence": 0.0,
    "last_updated": "2025-01-15T10:30:00",
    "num_sessions": 0,
    "learning_rate": 0.3
  }
}
```

### Loading and Saving

```python
def load_correction_matrix(config):
    """Load correction matrix from settings file"""
    default_matrix = {
        'enabled': True,
        'backlash_x_pos_to_neg': 0.0,
        # ... (all correction factors with default values)
    }
    
    return config.get('metadata_correction', default_matrix)

def save_correction_matrix(config, correction_matrix):
    """Save correction matrix to settings file"""
    config['metadata_correction'] = correction_matrix
    _save_config(config)
```

---

## Integration Points

### 1. Pre-Stitching: Apply Corrections

**Location:** In `UltimateStitcher.process_file()`, after extracting stage positions

```python
# After this line:
for t in tiles:
    t['x'] = (t['x_s'] - min_x) / px_um_eff
    t['y'] = (t['y_s'] - min_y) / px_um_eff

# Add correction application:
if correction_matrix['enabled']:
    movement_state = initialize_movement_state()
    for i, t in enumerate(tiles):
        x_corrected, y_corrected = apply_corrections_to_tile(
            t['x_s'], t['y_s'], i, correction_matrix, movement_state
        )
        t['x'] = (x_corrected - min_x) / px_um_eff
        t['y'] = (y_corrected - min_y) / px_um_eff
```

### 2. Post-Stitching: Learn from Results

**Location:** In `UltimateStitcher.process_file()`, after 2D stitching completes

```python
# After stitching completes and TileConfiguration.registered.txt is written
if correction_matrix['enabled']:
    # Extract positions from registered configuration
    ideal_positions = extract_ideal_positions(tiles)
    stitched_positions = parse_registered_tile_config(reg_conf)
    confidence_scores = extract_confidence_scores(stitched_positions)  # From overlap quality
    
    # Analyze errors
    error_analysis = extract_position_errors(ideal_positions, stitched_positions, confidence_scores)
    
    # Update correction matrix
    update_correction_matrix(correction_matrix, error_analysis, correction_matrix['learning_rate'])
    
    # Save updated matrix
    save_correction_matrix(_config, correction_matrix)
```

---

## Special Case: First Down Y Offset

### Problem

The first time the stage moves from Y+ to Y- (typically after completing the first row), we don't know the previous movement direction. The backlash state is indeterminate:

- Did the stage previously move up (Y+) or down (Y-)?
- Was there backlash from a previous scan session?
- Has the stage been idle long enough that backlash doesn't apply?

### Solution

We maintain a separate `first_down_y_offset` value that represents the best estimate for this special case, learned from multiple stitching sessions.

### Learning First Down Offset

```python
def extract_first_down_offset(tiles, stitched_positions):
    """
    Extract Y-direction errors for first down movements
    
    This looks for the first Y+ → Y- transition in each scan
    and extracts the position error specific to that transition.
    """
    
    first_down_errors = []
    
    # Find first tile where Y decreases (moving down)
    prev_y = None
    for i, tile in enumerate(tiles):
        if prev_y is not None and tile['y_s'] < prev_y:
            # This is a down movement
            # Check if it's the first down movement (no previous down)
            is_first_down = all(
                tiles[j]['y_s'] >= tiles[j-1]['y_s'] 
                for j in range(1, i) if j < len(tiles)
            )
            
            if is_first_down:
                # Extract error
                ideal_dy = tile['y_s'] - prev_y
                actual_dy = stitched_positions[i][1] - stitched_positions[i-1][1]
                error_y = actual_dy - ideal_dy
                
                # Get confidence from stitching (higher = better overlap)
                confidence = get_overlap_confidence(i)
                
                first_down_errors.append({
                    'error': error_y,
                    'confidence': confidence
                })
                
                break  # Only first down per scan
        
        prev_y = tile['y_s']
    
    return first_down_errors
```

### Updating First Down Offset

```python
def update_first_down_offset(correction_matrix, first_down_errors):
    """
    Update first down offset with exponential moving average
    Requires multiple sessions to build confidence
    """
    
    if len(first_down_errors) == 0:
        return
    
    # Calculate weighted mean
    total_weight = sum(e['confidence'] for e in first_down_errors)
    if total_weight > 0:
        weighted_mean = sum(e['error'] * e['confidence'] for e in first_down_errors) / total_weight
        
        # Update offset
        old_offset = correction_matrix['first_down_y_offset']
        old_confidence = correction_matrix['first_down_confidence']
        
        # Blend with new observation
        new_offset = MatrixOps.interpolate(
            old_offset, 
            weighted_mean, 
            correction_matrix['learning_rate']
        )
        
        # Increase confidence (cap at 1.0)
        new_confidence = min(1.0, old_confidence + 0.1)
        
        correction_matrix['first_down_y_offset'] = new_offset
        correction_matrix['first_down_confidence'] = new_confidence
```

---

## User Interface Additions

### Dialog Additions

Add to the existing parameter dialog:

```python
gd.addMessage("=== Metadata Correction (Experimental) ===")
gd.addCheckbox("Enable metadata correction", True)
gd.addNumericField("Learning rate (0.1-0.5 recommended)", 0.3, 2)
gd.addButton("Reset Corrections", reset_corrections_callback)
gd.addMessage("Current correction status: " + get_correction_status_message())
```

### Status Messages

```python
def get_correction_status_message(correction_matrix):
    """Generate human-readable correction status"""
    if correction_matrix['num_sessions'] == 0:
        return "No corrections learned yet (first run)"
    
    confidence = correction_matrix['first_down_confidence']
    sessions = correction_matrix['num_sessions']
    last_updated = correction_matrix.get('last_updated', 'never')
    
    msg = "Corrections from {} session(s). ".format(sessions)
    msg += "First-down confidence: {:.0f}%. ".format(confidence * 100)
    msg += "Last updated: {}".format(last_updated[:10])  # Date only
    
    return msg
```

---

## Testing Strategy

### Phase 1: Basic Correction Application

1. **Test with known systematic error**
   - Manually inject 10μm X backlash into test data
   - Verify correction detects and applies opposite offset

2. **Test state machine**
   - Create tile grid: right, right, down, left, left, down
   - Verify correct corrections applied at each transition

3. **Test first-down special case**
   - Verify `first_down_y_offset` used on first down
   - Verify normal backlash used on subsequent downs

### Phase 2: Learning from Stitching

1. **Test error extraction**
   - Run stitching on test data
   - Verify errors correctly categorized by movement type

2. **Test learning convergence**
   - Inject systematic errors
   - Run multiple stitching sessions
   - Verify corrections converge toward true error

3. **Test confidence weighting**
   - Create test with low-confidence tiles
   - Verify they have less impact on learned corrections

### Phase 3: Integration Testing

1. **Full workflow test**
   - Process real CZI files over multiple sessions
   - Verify corrections improve over time
   - Verify stitching time decreases (better initial positions)

2. **Settings persistence test**
   - Process file, close Fiji
   - Reopen and process another file
   - Verify corrections loaded from settings

---

## Future Enhancements

### 1. Temporal State Tracking (Future Feature)

The problem statement mentions using acquisition timestamps to determine previous stage direction:

```python
# FUTURE: Determine if stage was moving up or down before scan started
# by looking at previous tile set's acquisition times and positions

def infer_previous_direction(current_tiles, previous_batch_metadata):
    """
    Use metadata from previous acquisition batch to determine stage direction
    before current batch started.
    
    Requires: Acquisition time and absolute position metadata
    """
    # This would eliminate the "first down" special case uncertainty
    # by allowing us to know the previous stage direction
    pass
```

### 2. Per-Objective Corrections

Different objectives may have different systematic errors:

```python
correction_matrices = {
    '10x': { /* ... */ },
    '20x': { /* ... */ },
    '40x': { /* ... */ },
}
```

### 3. Position-Dependent Corrections

Some stages have position-dependent errors (e.g., more backlash at edges):

```python
def get_position_dependent_correction(x_mm, y_mm, correction_matrix):
    """
    Apply corrections that vary with stage position
    
    Could use piecewise linear interpolation or polynomial fitting
    """
    pass
```

### 4. Automatic Calibration Mode

Dedicated calibration scan with known pattern to quickly learn corrections:

```python
def run_calibration_scan(calibration_pattern='grid'):
    """
    Run special scan pattern optimized for learning corrections
    
    - Dense grid with many direction changes
    - Multiple passes over same region
    - Automatic error extraction and correction update
    """
    pass
```

---

## Implementation Checklist

### Core Functionality
- [ ] Implement `MatrixOps` class with pure Python operations
- [ ] Implement `correction_matrix` data structure
- [ ] Implement `movement_state` tracking
- [ ] Implement truth table logic in `apply_corrections_to_tile()`
- [ ] Implement error extraction from stitching results
- [ ] Implement correction matrix update with exponential moving average
- [ ] Implement first-down special case handling

### Settings Integration
- [ ] Add correction matrix to settings file structure
- [ ] Implement `load_correction_matrix()`
- [ ] Implement `save_correction_matrix()`
- [ ] Add settings migration for existing users

### UI Integration
- [ ] Add correction enable checkbox to parameter dialog
- [ ] Add learning rate input field
- [ ] Add reset corrections button
- [ ] Add correction status display

### Main Script Integration
- [ ] Integrate correction application before stitching
- [ ] Integrate error extraction after stitching
- [ ] Integrate correction matrix updates
- [ ] Add logging for correction activities

### Testing
- [ ] Unit tests for matrix operations
- [ ] Unit tests for state machine logic
- [ ] Integration test with synthetic data
- [ ] Integration test with real CZI files
- [ ] Verify Jython compatibility (no NumPy dependencies)

### Documentation
- [ ] User guide for metadata correction feature
- [ ] Examples of correction improvements
- [ ] Troubleshooting guide
- [ ] API documentation for correction functions

---

## Open Questions

1. **Learning Rate Default:** What learning rate provides good convergence without overfitting? (Recommend: 0.3)

2. **Thermal Drift Decay:** What decay rate best models actual thermal stabilization? (Recommend: 0.95 per tile)

3. **Long Jump Threshold:** What distance qualifies as a "long jump" where backlash doesn't apply? (Recommend: 2x normal spacing)

4. **Confidence Threshold:** Should we ignore low-confidence stitching results? (Recommend: No, weight by confidence)

5. **First-Down Confidence Building:** How many sessions needed before first-down offset is reliable? (Recommend: 3-5 sessions)

---

## Conclusion

This design provides a comprehensive, Jython-compatible system for learning and applying systematic error corrections to microscope stage metadata. The system:

- **Learns from stitching results** without user intervention
- **Adapts over time** using exponential moving averages
- **Handles special cases** like first-down with unknown backlash state
- **Persists corrections** across sessions in settings file
- **Uses pure Python** matrix operations (Jython compatible)

The modular design allows incremental implementation and testing, starting with basic corrections and progressively adding more sophisticated features.

