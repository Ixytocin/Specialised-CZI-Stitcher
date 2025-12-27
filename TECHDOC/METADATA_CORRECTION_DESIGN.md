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

## Data Structures

### 1. Correction Matrix

The correction matrix stores systematic error correction factors. All values are stored in micrometers (μm).

```python
correction_matrix = {
    # Backlash corrections (applied after direction changes)
    'backlash_x_pos_to_neg': 0.0,  # X+ → X- direction change
    'backlash_x_neg_to_pos': 0.0,  # X- → X+ direction change
    'backlash_y_pos_to_neg': 0.0,  # Y+ → Y- direction change (down in CZI)
    'backlash_y_neg_to_pos': 0.0,  # Y- → Y+ direction change (up in CZI)
    
    # Scale corrections (multiplicative factors)
    'scale_x': 1.0,  # X-axis scale correction (1.0 = no correction)
    'scale_y': 1.0,  # Y-axis scale correction
    
    # Skew corrections (cross-axis coupling in μm per μm)
    'skew_xy': 0.0,  # X movement causes Y displacement
    'skew_yx': 0.0,  # Y movement causes X displacement
    
    # Thermal drift (μm per tile, applied cumulatively)
    'thermal_drift_x': 0.0,  # Cold startup drift in X
    'thermal_drift_y': 0.0,  # Cold startup drift in Y
    'thermal_decay_rate': 0.95,  # Exponential decay per tile (0.0 = instant, 1.0 = never)
    
    # First down special case
    'first_down_y_offset': 0.0,  # Special offset for first Y+ → Y- transition
    'first_down_confidence': 0.0,  # Confidence in this measurement (0-1)
    
    # Metadata
    'last_updated': '',  # ISO 8601 timestamp
    'num_sessions': 0,   # Number of stitching sessions used for learning
    'learning_rate': 0.3  # How quickly to adapt (0.0 = never, 1.0 = instant)
}
```

### 2. Movement State

Tracks the movement pattern for each tile to determine which corrections to apply.

```python
movement_state = {
    'prev_x': None,  # Previous tile X position (μm)
    'prev_y': None,  # Previous tile Y position (μm)
    'prev_dir_x': None,  # Previous X direction: 'pos', 'neg', or None
    'prev_dir_y': None,  # Previous Y direction: 'pos', 'neg', or None
    'first_y_negative_done': False,  # Has first Y+ → Y- transition occurred?
    'tiles_processed': 0,  # Number of tiles processed (for thermal drift)
}
```

---

## Truth Table for Correction Application

The system uses a truth table to determine which corrections to apply based on movement patterns.

### Movement Classification

For each tile, classify movement relative to previous tile:

- **X Direction:**
  - `'pos'`: Moving in positive X (right)
  - `'neg'`: Moving in negative X (left)  
  - `None`: No X movement or first tile

- **Y Direction:**
  - `'pos'`: Moving in positive Y (up in CZI coordinate system)
  - `'neg'`: Moving in negative Y (down in CZI coordinate system)
  - `None`: No Y movement or first tile

- **Distance:**
  - `'short'`: Normal tile spacing (~1 tile width/height)
  - `'long'`: Large jump (>2x normal spacing)

### Truth Table

| Scenario | Prev X | Curr X | Prev Y | Curr Y | Applied Corrections |
|----------|--------|--------|--------|--------|---------------------|
| **First tile** | None | Any | None | Any | `scale`, `skew`, `thermal_drift` (start) |
| **Continue right** | pos | pos | Any | Any | `scale`, `skew`, `thermal_drift` (decay) |
| **Continue left** | neg | neg | Any | Any | `scale`, `skew`, `thermal_drift` (decay) |
| **Continue down** | Any | Any | neg | neg | `scale`, `skew`, `thermal_drift` (decay) |
| **Continue up** | Any | Any | pos | pos | `scale`, `skew`, `thermal_drift` (decay) |
| **Right → Left** | pos | neg | Any | Any | `scale`, `skew`, `backlash_x_pos_to_neg`, `thermal_drift` |
| **Left → Right** | neg | pos | Any | Any | `scale`, `skew`, `backlash_x_neg_to_pos`, `thermal_drift` |
| **Down → Up** | Any | Any | neg | pos | `scale`, `skew`, `backlash_y_pos_to_neg`, `thermal_drift` |
| **Up → Down (first)** | Any | Any | pos/None | neg | `scale`, `skew`, `first_down_y_offset`, `thermal_drift` |
| **Up → Down (subsequent)** | Any | Any | pos | neg | `scale`, `skew`, `backlash_y_pos_to_neg`, `thermal_drift` |
| **Long jump** | Any | Any | Any | Any | `scale`, `skew`, NO backlash, `thermal_drift` |

### Special Cases

1. **First Down (Up → Down transition when `first_y_negative_done == False`)**
   - **Problem:** Backlash state is unknown for the first down movement
   - **Solution:** Use `first_down_y_offset` learned from previous stitching sessions
   - **Why:** We can't determine if the stage was previously moving up or down before the scan started
   - **Learning:** Extract from first Y-direction neighbor pairs in stitching results

2. **Long Jumps (Distance > 2x normal spacing)**
   - **No backlash correction** (stage has time to settle)
   - **Only apply scale and skew corrections**

---

## Jython-Compatible Matrix Operations

Since we cannot use NumPy (not available in Jython), we implement pure Python matrix operations.

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

