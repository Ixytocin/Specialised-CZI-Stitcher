"""
Metadata Correction Module for CZI Stitcher

Implements adaptive correction system for systematic stage positioning errors
(backlash, scale drift, skew, thermal expansion).

Jython-compatible (no NumPy, pure Python operations).
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
    """Create correction matrix with empirical measurements"""
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
        'scale_x': 1.0326,
        'scale_y': 1.0326,
        'skew_xy': 0.0066,
        'skew_yx': 0.0066,
        'offset_right_x': 37.16,
        'offset_right_y': 8.15,
        'offset_left_x': -37.12,
        'offset_left_y': -8.37,
        'backlash_x': 3.50,
        'backlash_y': 1.20,
        'backlash_reversal': 0.70,
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
        'first_down_x_offset': -6.10,
        'first_down_y_offset': 33.90,
        'first_down_confidence': 0.92,
        'subseq_down_x_offset': -20.70,
        'subseq_down_y_offset': 28.90,
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
    """Classify movement type for current tile"""
    if movement_state['prev_x'] is None:
        return 'START', 'start'
    
    delta_x = tile_x_um - movement_state['prev_x']
    delta_y = tile_y_um - movement_state['prev_y']
    
    curr_dir_x = None
    if abs(delta_x) > 0.5:
        curr_dir_x = 'right' if delta_x > 0 else 'left'
    
    curr_dir_y = None
    if abs(delta_y) > 0.5:
        curr_dir_y = 'down' if delta_y > 0 else None
    
    long_threshold_x = correction_matrix['long_move_threshold_x']
    long_threshold_y = correction_matrix.get('long_move_threshold_y', 2.0)
    is_long_x = abs(delta_x) > long_threshold_x * tile_width_um
    is_long_y = abs(delta_y) > long_threshold_y * tile_height_um
    
    if is_long_x and is_long_y:
        return 'LONG_DIAG', 'long_diagonal'
    
    if is_long_x and not is_long_y:
        if curr_dir_x == 'right':
            return 'LONG_R', 'long_right'
        elif curr_dir_x == 'left':
            return 'LONG_L', 'long_left'
    
    if is_long_y and not is_long_x:
        return 'LONG_Y', 'long_y'
    
    if curr_dir_x and curr_dir_y:
        return 'DIAG_SHORT', 'diagonal'
    
    if curr_dir_y == 'down' and not movement_state['first_down_done']:
        return 'Y_FIRST', 'down'
    
    if curr_dir_y == 'down':
        return 'Y_SUBSEQ', 'down'
    
    if movement_state['prev_dir_x'] == 'right' and curr_dir_x == 'left':
        return 'R_TO_L', 'left'
    elif movement_state['prev_dir_x'] == 'left' and curr_dir_x == 'right':
        return 'L_TO_R', 'right'
    
    if curr_dir_x == 'right':
        return 'RIGHT', 'right'
    elif curr_dir_x == 'left':
        return 'LEFT', 'left'
    else:
        return 'UNKNOWN', 'unknown'


def apply_metadata_corrections(tile_x_um, tile_y_um, tile_index, tile_width_um, tile_height_um,
                                 correction_matrix, movement_state):
    """Apply empirical corrections to tile metadata position"""
    
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
    
    state_code, state_name = classify_movement(
        tile_x_um, tile_y_um, movement_state, tile_width_um, tile_height_um, correction_matrix
    )
    
    px_um = correction_matrix['pixel_size_um']
    
    # 1. Affine transformation
    scale_x = correction_matrix['scale_x']
    scale_y = correction_matrix['scale_y']
    skew_xy = correction_matrix['skew_xy']
    skew_yx = correction_matrix['skew_yx']
    
    x_scaled = scale_x * tile_x_um - skew_xy * tile_y_um
    y_scaled = skew_yx * tile_x_um + scale_y * tile_y_um
    
    # 2. State-dependent offset
    offset_x_um = 0.0
    offset_y_um = 0.0
    
    if state_code == 'RIGHT':
        offset_x_um = correction_matrix['offset_right_x'] * px_um
        offset_y_um = correction_matrix['offset_right_y'] * px_um
    elif state_code == 'LEFT':
        offset_x_um = correction_matrix['offset_left_x'] * px_um
        offset_y_um = correction_matrix['offset_left_y'] * px_um
    elif state_code == 'Y_FIRST':
        offset_x_um = correction_matrix['first_down_x_offset'] * px_um
        offset_y_um = correction_matrix['first_down_y_offset'] * px_um
        movement_state['first_down_done'] = True
    elif state_code == 'Y_SUBSEQ':
        offset_x_um = correction_matrix['subseq_down_x_offset'] * px_um
        offset_y_um = correction_matrix['subseq_down_y_offset'] * px_um
    elif state_code == 'DIAG_SHORT':
        delta_x = tile_x_um - movement_state['prev_x']
        delta_y = tile_y_um - movement_state['prev_y']
        if delta_x > 0:
            offset_x_um = correction_matrix['offset_right_x'] * px_um
            offset_y_um = correction_matrix['offset_right_y'] * px_um
        else:
            offset_x_um = correction_matrix['offset_left_x'] * px_um
            offset_y_um = correction_matrix['offset_left_y'] * px_um
        if delta_y > 0:
            offset_y_um += correction_matrix['subseq_down_y_offset'] * px_um
    
    # 3. Backlash penalties
    backlash_x_um = 0.0
    backlash_y_um = 0.0
    
    if state_code in ['R_TO_L', 'L_TO_R']:
        backlash_x_um = correction_matrix['backlash_x'] * px_um
        backlash_x_um += correction_matrix['backlash_reversal'] * px_um
    
    if state_code == 'Y_SUBSEQ' and movement_state['prev_state'] != 'Y_SUBSEQ':
        backlash_y_um = correction_matrix['backlash_y'] * px_um
    
    if state_code == 'DIAG_SHORT':
        delta_x = tile_x_um - movement_state['prev_x']
        prev_dir_x = movement_state['prev_dir_x']
        curr_dir_x = 'right' if delta_x > 0 else 'left'
        if prev_dir_x and prev_dir_x != curr_dir_x:
            backlash_x_um = correction_matrix['backlash_x'] * px_um
            backlash_x_um += correction_matrix['backlash_reversal'] * px_um
        backlash_y_um = correction_matrix['backlash_y'] * px_um
    
    if state_code == 'LONG_R':
        backlash_x_um = correction_matrix['backlash_long_x_right'] * px_um
    elif state_code == 'LONG_L':
        backlash_x_um = correction_matrix['backlash_long_x_left'] * px_um
    elif state_code == 'LONG_Y':
        backlash_y_um = correction_matrix.get('backlash_long_y', 0.0) * px_um
    elif state_code == 'LONG_DIAG':
        backlash_x_um = correction_matrix.get('backlash_long_diagonal', 0.0) * px_um
        backlash_y_um = correction_matrix.get('backlash_long_diagonal', 0.0) * px_um
    
    # 4. Thermal drift
    tiles_processed = movement_state['tiles_processed']
    decay_factor = correction_matrix['thermal_decay_rate'] ** tiles_processed
    thermal_load = correction_matrix['thermal_factors']['thermal_load_factor']
    thermal_x, thermal_y = select_thermal_drift(correction_matrix, thermal_load)
    thermal_x *= decay_factor
    thermal_y *= decay_factor
    
    # Final position
    x_corrected = x_scaled + offset_x_um + backlash_x_um + thermal_x
    y_corrected = y_scaled + offset_y_um + backlash_y_um + thermal_y
    
    # Update state
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
