"""
Metadata Correction Module for CZI Stitcher

============================================================================
FILE PLACEMENT: IMPORTANT!
============================================================================
This file MUST be in the SAME DIRECTORY as main.jy

Correct placement:
  /your/scripts/folder/main.jy                    <-- Main script
  /your/scripts/folder/metadata_correction.py     <-- This file

Do NOT place this in:
  - A subdirectory
  - Python's site-packages
  - Fiji's plugins folder (unless main.jy is also there)

Verification:
  When you run main.jy in Fiji, check the log window:
    ✓ SUCCESS: "[DEBUG] Metadata correction module loaded successfully"
    ✗ ERROR:   "[DEBUG] Metadata correction module not available: ..."

If you see an error, this file is not in the correct location!
============================================================================

PURPOSE:
Implements adaptive correction system for systematic stage positioning errors
(backlash, scale drift, skew, thermal expansion).

FEATURES:
- 12-state movement classification (START, RIGHT, LEFT, R_TO_L, L_TO_R, 
  Y_FIRST, Y_SUBSEQ, DIAG_SHORT, LONG_R, LONG_L, LONG_Y, LONG_DIAG)
- Empirical measurements with confidence levels
- Speed-based backlash (short moves: full, long moves: reduced)
- Per-microscope configuration
- Thermal state support (cold/preheated)
- Jython-compatible (no NumPy, pure Python operations)

USAGE:
This module is imported by main.jy. Do not run it directly.

DOCUMENTATION:
See METADATA_CORRECTION_README.md for complete documentation
See TECHDOC/METADATA_CORRECTION_DESIGN.md for technical details
"""

# ==============================================================================
# MATRIX OPERATIONS (Jython-compatible)
# ==============================================================================

class MatrixOps:
    """Pure Python matrix operations for Jython compatibility"""
    
    @staticmethod
    def apply_2d_transform(x, y, scale_x, scale_y, skew_xy, skew_yx, offset_x, offset_y):
        """Apply 2D affine transformation to point (x, y)"""
        x_prime = scale_x * x + skew_xy * y + offset_x
        y_prime = skew_yx * x + scale_y * y + offset_y
        return x_prime, y_prime
    
    @staticmethod
    def interpolate(old_value, new_value, learning_rate):
        """Exponential moving average for learning"""
        return old_value * (1.0 - learning_rate) + new_value * learning_rate


# ==============================================================================
# CORRECTION MATRIX AND STATE
# ==============================================================================

def create_default_correction_matrix(microscope_id='default'):
    """
    Create correction matrix with empirical measurements
    
    Updated values based on 251-tile verification dataset.
    Uses LUT-based correction approach with movement masks.
    """
    return {
        'enabled': False,
        'microscope_id': microscope_id,
        'pixel_size_um': 0.345,
        'thermal_state': 'unknown',
        'thermal_factors': {
            'z_stack_height_um': 0.0,
            'num_channels': 1,
            'num_tiles': 0,
            'thermal_load_factor': 0.0
        },
        # Affine transformation (verified across 251 tiles)
        'scale_x': 1.03265,
        'scale_y': 1.00210,
        'skew_xy': 0.0066,
        'skew_yx': 0.0066,
        
        # State-dependent offsets (in pixels, NOT micrometers)
        # RIGHT: Steady state right movement
        'offset_right_x': 0.84,
        'offset_right_y': -5.20,
        
        # LEFT: Steady state left movement
        'offset_left_x': -5.12,
        'offset_left_y': -3.80,
        
        # First movements (higher inertia/stiction)
        'first_right_x_offset': 18.37,
        'first_right_y_offset': -5.20,
        'first_down_x_offset': -30.40,
        'first_down_y_offset': 18.60,
        
        # Subsequent down movements
        'subseq_down_x_offset': -6.30,
        'subseq_down_y_offset': 18.60,
        
        # Diagonal moves (short)
        'diag_right_down_x': 15.00,
        'diag_right_down_y': 15.00,
        'diag_left_down_x': -6.30,
        'diag_left_down_y': 18.60,
        
        # Long/sweep moves (high momentum)
        'sweep_right_down_x': 14.50,
        'sweep_right_down_y': 12.20,
        'sweep_left_down_x': 36.20,
        'sweep_left_down_y': 24.00,
        
        # Sweep detection threshold (in pixels)
        'sweep_limit': 500.0,
        
        # Legacy backlash values (not used in LUT approach)
        'backlash_x': 0.0,
        'backlash_y': 0.0,
        'backlash_reversal': 0.0,
        'backlash_long_x_left': 0.0,
        'backlash_long_x_right': 0.0,
        'backlash_long_y': 0.0,
        'backlash_long_diagonal': 0.0,
        
        'long_move_threshold_x': 2.0,
        'long_move_threshold_y': 2.0,
        'thermal_drift_x_cold': 0.0,
        'thermal_drift_y_cold': 0.0,
        'thermal_drift_x_preheated': 0.0,
        'thermal_drift_y_preheated': 0.0,
        'thermal_decay_rate': 0.95,
        
        'first_down_confidence': 0.92,
        'subseq_down_confidence': 0.88,
        'last_updated': '',
        'num_sessions': 0,
        'learning_rate': 0.3
    }


def create_movement_state():
    """Create initial movement state for tracking"""
    return {
        'prev_x': None,
        'prev_y': None,
        'prev_dir_x': None,
        'prev_dir_y': None,
        'prev_state': None,
        'first_down_done': False,
        'first_right_done': False,
        'tiles_processed': 0,
    }


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def calculate_thermal_load_factor(z_stack_height_um, num_channels, num_tiles):
    """Calculate thermal load factor from acquisition parameters"""
    z_factor = z_stack_height_um / 100.0
    ch_factor = num_channels / 3.0
    tile_factor = num_tiles / 50.0
    thermal_load = 0.4 * z_factor + 0.3 * ch_factor + 0.3 * tile_factor
    return thermal_load


def select_thermal_drift(correction_matrix, thermal_load_factor):
    """Select thermal drift correction based on system state"""
    thermal_state = correction_matrix['thermal_state']
    
    if thermal_state == 'cold':
        drift_x = correction_matrix['thermal_drift_x_cold'] * thermal_load_factor
        drift_y = correction_matrix['thermal_drift_y_cold'] * thermal_load_factor
    elif thermal_state == 'preheated':
        drift_x = correction_matrix['thermal_drift_x_preheated'] * thermal_load_factor
        drift_y = correction_matrix['thermal_drift_y_preheated'] * thermal_load_factor
    else:
        drift_x = correction_matrix['thermal_drift_x_cold'] * thermal_load_factor
        drift_y = correction_matrix['thermal_drift_y_cold'] * thermal_load_factor
    
    return drift_x, drift_y


def classify_movement(tile_x_um, tile_y_um, movement_state, tile_width_um, tile_height_um, correction_matrix):
    """
    Classify movement type for current tile using LUT-based approach
    
    Returns tuple: (state_code, state_name, mask)
    Mask encoding: (is_sweep << 2) | (is_right << 1) | is_down
    Plus bit 3 for first-time axis activation (inertia/stiction)
    """
    if movement_state['prev_x'] is None:
        return 'START', 'start', 0
    
    delta_x = tile_x_um - movement_state['prev_x']
    delta_y = tile_y_um - movement_state['prev_y']
    
    px_um = correction_matrix['pixel_size_um']
    
    # Convert deltas to pixel space for sweep detection
    delta_x_px = delta_x / px_um
    delta_y_px = delta_y / px_um
    
    # Classify movement direction
    is_right = int(delta_x > 0.5)
    is_down = int(delta_y > 0.5)
    is_sweep = int(abs(delta_x_px) > correction_matrix['sweep_limit'])
    
    # Build basic mask
    mask = (is_sweep << 2) | (is_right << 1) | is_down
    
    # Check for first-time axis activation (inertia/stiction boost)
    is_first_move = False
    if not movement_state['first_right_done'] and is_right and not is_down:
        mask |= 8  # Set bit 3 for first right
        is_first_move = True
        movement_state['first_right_done'] = True
    elif not movement_state['first_down_done'] and is_down:
        mask |= 8  # Set bit 3 for first down
        is_first_move = True
        movement_state['first_down_done'] = True
    
    # Generate state code and name based on mask
    if mask == 0:  # 000: Left steady state
        return 'LEFT', 'left', mask
    elif mask == 1:  # 001: Down / Left-Down
        return 'DOWN_LEFT', 'down_left', mask
    elif mask == 2:  # 010: Right steady state
        return 'RIGHT', 'right', mask
    elif mask == 3:  # 011: Right-Down (short diagonal)
        return 'DIAG_RIGHT_DOWN', 'diag_right_down', mask
    elif mask == 5:  # 101: Sweep Left-Down (high-momentum flyback)
        return 'SWEEP_LEFT_DOWN', 'sweep_left_down', mask
    elif mask == 7:  # 111: Sweep Right-Down (advance jump)
        return 'SWEEP_RIGHT_DOWN', 'sweep_right_down', mask
    elif mask == 9:  # 1001: First Down (stiction break)
        return 'FIRST_DOWN', 'first_down', mask
    elif mask == 10:  # 1010: First Right (lead-screw wind-up)
        return 'FIRST_RIGHT', 'first_right', mask
    else:
        # Fallback for unexpected states
        return 'UNKNOWN', 'unknown', mask


def apply_metadata_corrections(tile_x_um, tile_y_um, tile_index, tile_width_um, tile_height_um,
                                 correction_matrix, movement_state):
    """
    Apply empirical corrections to tile metadata position using LUT-based approach
    
    This implementation follows the cleaner boolean-based logic from the user's refined
    correction system, verified across 251 tiles.
    """
    
    if not correction_matrix.get('enabled', False):
        if movement_state['prev_x'] is not None:
            movement_state['prev_x'] = tile_x_um
            movement_state['prev_y'] = tile_y_um
            movement_state['tiles_processed'] += 1
        else:
            movement_state['prev_x'] = tile_x_um
            movement_state['prev_y'] = tile_y_um
            movement_state['tiles_processed'] = 0
        return tile_x_um, tile_y_um, 'passthrough'
    
    state_code, state_name, mask = classify_movement(
        tile_x_um, tile_y_um, movement_state, tile_width_um, tile_height_um, correction_matrix
    )
    
    px_um = correction_matrix['pixel_size_um']
    
    # 1. Affine transformation (scale + skew)
    scale_x = correction_matrix['scale_x']
    scale_y = correction_matrix['scale_y']
    skew_xy = correction_matrix['skew_xy']
    skew_yx = correction_matrix['skew_yx']
    
    x_scaled = scale_x * tile_x_um + skew_xy * tile_y_um
    y_scaled = skew_yx * tile_x_um + scale_y * tile_y_um
    
    # 2. State-dependent offset using LUT approach
    offset_x_px = 0.0
    offset_y_px = 0.0
    
    # LUT-based correction selection
    if state_code == 'LEFT':  # mask == 0
        offset_x_px = correction_matrix['offset_left_x']
        offset_y_px = correction_matrix['offset_left_y']
    elif state_code == 'DOWN_LEFT':  # mask == 1
        offset_x_px = correction_matrix['diag_left_down_x']
        offset_y_px = correction_matrix['diag_left_down_y']
    elif state_code == 'RIGHT':  # mask == 2
        offset_x_px = correction_matrix['offset_right_x']
        offset_y_px = correction_matrix['offset_right_y']
    elif state_code == 'DIAG_RIGHT_DOWN':  # mask == 3
        offset_x_px = correction_matrix['diag_right_down_x']
        offset_y_px = correction_matrix['diag_right_down_y']
    elif state_code == 'SWEEP_LEFT_DOWN':  # mask == 5
        offset_x_px = correction_matrix['sweep_left_down_x']
        offset_y_px = correction_matrix['sweep_left_down_y']
    elif state_code == 'SWEEP_RIGHT_DOWN':  # mask == 7
        offset_x_px = correction_matrix['sweep_right_down_x']
        offset_y_px = correction_matrix['sweep_right_down_y']
    elif state_code == 'FIRST_DOWN':  # mask == 9
        offset_x_px = correction_matrix['first_down_x_offset']
        offset_y_px = correction_matrix['first_down_y_offset']
    elif state_code == 'FIRST_RIGHT':  # mask == 10
        offset_x_px = correction_matrix['first_right_x_offset']
        offset_y_px = correction_matrix['first_right_y_offset']
    
    # Convert pixel offsets to micrometers
    offset_x_um = offset_x_px * px_um
    offset_y_um = offset_y_px * px_um
    
    # 3. Thermal drift (if needed)
    tiles_processed = movement_state['tiles_processed']
    decay_factor = correction_matrix['thermal_decay_rate'] ** tiles_processed
    thermal_load = correction_matrix['thermal_factors']['thermal_load_factor']
    thermal_x, thermal_y = select_thermal_drift(correction_matrix, thermal_load)
    thermal_x *= decay_factor
    thermal_y *= decay_factor
    
    # Final corrected position
    x_corrected = x_scaled + offset_x_um + thermal_x
    y_corrected = y_scaled + offset_y_um + thermal_y
    
    # Update state for next iteration
    if movement_state['prev_x'] is not None:
        delta_x = tile_x_um - movement_state['prev_x']
        delta_y = tile_y_um - movement_state['prev_y']
        
        if abs(delta_x) > 0.5:
            movement_state['prev_dir_x'] = 'right' if delta_x > 0 else 'left'
        if abs(delta_y) > 0.5:
            movement_state['prev_dir_y'] = 'down' if delta_y > 0 else None
    
    movement_state['prev_x'] = tile_x_um
    movement_state['prev_y'] = tile_y_um
    movement_state['prev_state'] = state_code
    movement_state['tiles_processed'] += 1
    
    return x_corrected, y_corrected, state_name


def visualize_grid_layout(tiles, grid_width, grid_height):
    """Generate ASCII visualization of tile grid for debugging"""
    grid = [['.' for _ in range(grid_width)] for _ in range(grid_height)]
    
    for i, tile_info in enumerate(tiles):
        x_grid = int(round(tile_info['x_grid']))
        y_grid = int(round(tile_info['y_grid']))
        if 0 <= x_grid < grid_width and 0 <= y_grid < grid_height:
            if i == 0:
                grid[y_grid][x_grid] = '0'
            else:
                grid[y_grid][x_grid] = 'x'
    
    return [''.join(row) for row in grid]
