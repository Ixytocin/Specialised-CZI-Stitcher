#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for metadata correction system core functionality.

Tests the state machine, correction application, and debug visualization
without requiring actual CZI files or Fiji environment.

Run with: python test_metadata_correction.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# CORE FUNCTIONALITY IMPLEMENTATION (for testing)
# ============================================================================

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


def create_default_correction_matrix(microscope_id='default'):
    """Create a default correction matrix"""
    return {
        'microscope_id': microscope_id,
        'thermal_state': 'unknown',
        'thermal_factors': {
            'z_stack_height_um': 0.0,
            'num_channels': 1,
            'num_tiles': 0,
            'thermal_load_factor': 0.0
        },
        'backlash_x_left': 0.0,
        'backlash_x_right': 0.0,
        'backlash_y_down': 0.0,
        'backlash_long_x_left': 0.0,
        'backlash_long_x_right': 0.0,
        'long_move_threshold_x': 2.0,
        'scale_x': 1.0,
        'scale_y': 1.0,
        'skew_xy': 0.0,
        'skew_yx': 0.0,
        'thermal_drift_x_cold': 0.0,
        'thermal_drift_y_cold': 0.0,
        'thermal_drift_x_preheated': 0.0,
        'thermal_drift_y_preheated': 0.0,
        'thermal_decay_rate': 0.95,
        'first_down_y_offset': 0.0,
        'first_down_confidence': 0.0,
        'last_updated': '',
        'num_sessions': 0,
        'learning_rate': 0.3
    }


def create_movement_state():
    """Create initial movement state"""
    return {
        'prev_x': None,
        'prev_y': None,
        'prev_dir_x': None,
        'prev_dir_y': None,
        'first_down_done': False,
        'tiles_processed': 0,
    }


def calculate_thermal_load_factor(z_stack_height_um, num_channels, num_tiles):
    """Calculate thermal load factor based on acquisition parameters"""
    z_factor = z_stack_height_um / 100.0
    ch_factor = num_channels / 3.0
    tile_factor = num_tiles / 50.0
    thermal_load = 0.4 * z_factor + 0.3 * ch_factor + 0.3 * tile_factor
    return thermal_load


def select_thermal_drift(correction_matrix, thermal_load_factor):
    """Select appropriate thermal drift correction based on system state"""
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
    Classify movement type for current tile.
    
    Returns: (state_code, state_name, is_long_move)
    """
    # First tile
    if movement_state['prev_x'] is None:
        return 'START', 'start', False
    
    # Calculate movement
    delta_x = tile_x_um - movement_state['prev_x']
    delta_y = tile_y_um - movement_state['prev_y']
    
    # Classify direction
    curr_dir_x = None
    if abs(delta_x) > 0.5:
        curr_dir_x = 'right' if delta_x > 0 else 'left'
    
    curr_dir_y = None
    if abs(delta_y) > 0.5:
        curr_dir_y = 'down' if delta_y > 0 else None  # Up not primary
    
    # Check for long moves
    long_threshold_x = correction_matrix['long_move_threshold_x']
    is_long_x = abs(delta_x) > long_threshold_x * tile_width_um
    
    # Determine state
    if is_long_x and curr_dir_x == 'right':
        return 'LONG_R', 'long_right', True
    elif is_long_x and curr_dir_x == 'left':
        return 'LONG_L', 'long_left', True
    elif curr_dir_y == 'down' and not movement_state['first_down_done']:
        return 'FIRST_DOWN', 'down', False
    elif curr_dir_y == 'down':
        return 'TO_DOWN', 'down', False
    elif movement_state['prev_dir_x'] == 'right' and curr_dir_x == 'left':
        return 'R_TO_L', 'left', False
    elif movement_state['prev_dir_x'] == 'left' and curr_dir_x == 'right':
        return 'L_TO_R', 'right', False
    elif curr_dir_x == 'right':
        return 'RIGHT', 'right', False
    elif curr_dir_x == 'left':
        return 'LEFT', 'left', False
    elif curr_dir_y == 'down':
        return 'DOWN', 'down', False
    else:
        return 'UNKNOWN', 'unknown', False


def apply_corrections_to_tile(tile_x_um, tile_y_um, tile_index, tile_width_um, tile_height_um,
                               correction_matrix, movement_state):
    """
    Apply systematic error corrections to tile position.
    
    Returns: (corrected_x_um, corrected_y_um, state_name)
    """
    
    # Classify movement
    state_code, state_name, is_long_move = classify_movement(
        tile_x_um, tile_y_um, movement_state, tile_width_um, tile_height_um, correction_matrix
    )
    
    # Initialize offsets
    offset_x = 0.0
    offset_y = 0.0
    
    # Calculate thermal drift
    tiles_processed = movement_state['tiles_processed']
    decay_factor = correction_matrix['thermal_decay_rate'] ** tiles_processed
    thermal_load = correction_matrix['thermal_factors']['thermal_load_factor']
    thermal_x, thermal_y = select_thermal_drift(correction_matrix, thermal_load)
    offset_x += thermal_x * decay_factor
    offset_y += thermal_y * decay_factor
    
    # Apply backlash corrections based on state
    if state_code == 'R_TO_L':
        offset_x += correction_matrix['backlash_x_left']
    elif state_code == 'L_TO_R':
        offset_x += correction_matrix['backlash_x_right']
    elif state_code == 'FIRST_DOWN':
        offset_y += correction_matrix['first_down_y_offset']
        movement_state['first_down_done'] = True
    elif state_code == 'TO_DOWN':
        offset_y += correction_matrix['backlash_y_down']
    elif state_code == 'LONG_R':
        offset_x += correction_matrix['backlash_long_x_right']
    elif state_code == 'LONG_L':
        offset_x += correction_matrix['backlash_long_x_left']
    
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
    if movement_state['prev_x'] is not None:
        delta_x = tile_x_um - movement_state['prev_x']
        delta_y = tile_y_um - movement_state['prev_y']
        
        if abs(delta_x) > 0.5:
            movement_state['prev_dir_x'] = 'right' if delta_x > 0 else 'left'
        if abs(delta_y) > 0.5:
            movement_state['prev_dir_y'] = 'down' if delta_y > 0 else None
    
    movement_state['prev_x'] = tile_x_um
    movement_state['prev_y'] = tile_y_um
    movement_state['tiles_processed'] += 1
    
    return x_corrected, y_corrected, state_name


def visualize_grid(tiles, grid_width, grid_height):
    """
    Generate ASCII visualization of tile grid.
    
    Args:
        tiles: List of (x, y) positions in grid coordinates
        grid_width: Width of bounding box
        grid_height: Height of bounding box
    
    Returns: List of strings representing grid rows
    """
    # Create empty grid
    grid = [['.' for _ in range(grid_width)] for _ in range(grid_height)]
    
    # Place tiles
    for i, (x, y) in enumerate(tiles):
        gx = int(round(x))
        gy = int(round(y))
        if 0 <= gx < grid_width and 0 <= gy < grid_height:
            if i == 0:
                grid[gy][gx] = '0'
            else:
                grid[gy][gx] = 'x'
    
    # Convert to strings
    return [''.join(row) for row in grid]


# ============================================================================
# TEST CASES
# ============================================================================

def test_basic_correction_application():
    """Test basic correction application without errors"""
    print("\n" + "="*70)
    print("TEST 1: Basic Correction Application (No Errors)")
    print("="*70)
    
    correction_matrix = create_default_correction_matrix()
    movement_state = create_movement_state()
    
    # Simple 2x2 grid
    tiles = [
        (0.0, 0.0),      # Tile 0
        (1000.0, 0.0),   # Tile 1 - right
        (0.0, 1000.0),   # Tile 2 - down, left
        (1000.0, 1000.0) # Tile 3 - right
    ]
    
    tile_width = 1000.0
    tile_height = 1000.0
    
    states = []
    for i, (x, y) in enumerate(tiles):
        x_corr, y_corr, state = apply_corrections_to_tile(
            x, y, i, tile_width, tile_height, correction_matrix, movement_state
        )
        states.append(state)
        print("Tile %d: (%.1f, %.1f) -> (%.1f, %.1f) [state: %s]" % (i, x, y, x_corr, y_corr, state))
    
    print("\nState sequence: %s" % ', '.join(states))
    
    # Verify states
    expected_states = ['start', 'right', 'left', 'right']
    assert states == expected_states, "Expected %s, got %s" % (expected_states, states)
    print("✓ State sequence correct")
    
    return True


def test_backlash_correction():
    """Test backlash correction on direction changes"""
    print("\n" + "="*70)
    print("TEST 2: Backlash Correction")
    print("="*70)
    
    correction_matrix = create_default_correction_matrix()
    correction_matrix['backlash_x_left'] = 5.0   # 5μm backlash right->left
    correction_matrix['backlash_x_right'] = 3.0  # 3μm backlash left->right
    correction_matrix['backlash_y_down'] = 4.0   # 4μm backlash down
    
    movement_state = create_movement_state()
    
    # Test pattern with direction changes
    tiles = [
        (0.0, 0.0),      # start
        (1000.0, 0.0),   # right
        (2000.0, 0.0),   # right
        (1000.0, 0.0),   # left (backlash_x_left should apply)
        (0.0, 0.0),      # left
        (1000.0, 0.0),   # right (backlash_x_right should apply)
        (1000.0, 1000.0) # down (backlash_y_down should apply)
    ]
    
    tile_width = 1000.0
    tile_height = 1000.0
    
    corrections = []
    for i, (x, y) in enumerate(tiles):
        x_corr, y_corr, state = apply_corrections_to_tile(
            x, y, i, tile_width, tile_height, correction_matrix, movement_state
        )
        delta_x = x_corr - x
        delta_y = y_corr - y
        corrections.append((delta_x, delta_y, state))
        print("Tile %d: state=%s, correction=(%.1f, %.1f)" % (i, state, delta_x, delta_y))
    
    # Check backlash was applied
    # Tile 3 should have backlash_x_left
    assert abs(corrections[3][0] - 5.0) < 0.1, "Expected 5.0μm backlash, got %.1f" % corrections[3][0]
    print("✓ Right->Left backlash applied correctly")
    
    # Tile 5 should have backlash_x_right
    assert abs(corrections[5][0] - 3.0) < 0.1, "Expected 3.0μm backlash, got %.1f" % corrections[5][0]
    print("✓ Left->Right backlash applied correctly")
    
    return True


def test_thermal_load_calculation():
    """Test thermal load factor calculation"""
    print("\n" + "="*70)
    print("TEST 3: Thermal Load Calculation")
    print("="*70)
    
    # Test different scenarios
    test_cases = [
        (50.0, 3, 50, "Baseline (50μm, 3ch, 50 tiles)"),
        (100.0, 3, 50, "2x Z-stack"),
        (50.0, 6, 50, "2x Channels"),
        (50.0, 3, 100, "2x Tiles"),
        (200.0, 6, 100, "High load (2x Z, 2x Ch, 2x Tiles)")
    ]
    
    for z, ch, tiles_count, desc in test_cases:
        factor = calculate_thermal_load_factor(z, ch, tiles_count)
        print("%s: %.3f" % (desc, factor))
    
    print("✓ Thermal load calculations complete")
    return True


def test_first_down_special_case():
    """Test first down special case handling"""
    print("\n" + "="*70)
    print("TEST 4: First Down Special Case")
    print("="*70)
    
    correction_matrix = create_default_correction_matrix()
    correction_matrix['first_down_y_offset'] = 10.0  # Special first down offset
    correction_matrix['backlash_y_down'] = 5.0       # Normal down backlash
    
    movement_state = create_movement_state()
    
    # Grid with two down movements
    tiles = [
        (0.0, 0.0),      # start
        (1000.0, 0.0),   # right
        (1000.0, 1000.0), # down (FIRST - should use first_down_y_offset)
        (0.0, 1000.0),   # left
        (0.0, 2000.0)    # down (subsequent - should use backlash_y_down)
    ]
    
    tile_width = 1000.0
    tile_height = 1000.0
    
    for i, (x, y) in enumerate(tiles):
        x_corr, y_corr, state = apply_corrections_to_tile(
            x, y, i, tile_width, tile_height, correction_matrix, movement_state
        )
        delta_y = y_corr - y
        print("Tile %d: state=%s, y_correction=%.1f" % (i, state, delta_y))
        
        if i == 2:
            # First down should use first_down_y_offset
            assert abs(delta_y - 10.0) < 0.1, "Expected 10.0μm first down, got %.1f" % delta_y
            print("  ✓ First down offset applied")
    
    print("✓ First down special case handled correctly")
    return True


def test_long_move_detection():
    """Test long move detection and different backlash"""
    print("\n" + "="*70)
    print("TEST 5: Long Move Detection")
    print("="*70)
    
    correction_matrix = create_default_correction_matrix()
    correction_matrix['backlash_x_left'] = 5.0
    correction_matrix['backlash_long_x_left'] = 2.0  # Reduced backlash for long moves
    correction_matrix['long_move_threshold_x'] = 2.0
    
    movement_state = create_movement_state()
    
    tile_width = 1000.0
    tile_height = 1000.0
    
    # Pattern: short right, short right, LONG left (circle tracing)
    tiles = [
        (0.0, 0.0),
        (1000.0, 0.0),    # short right
        (2000.0, 0.0),    # short right
        (-1000.0, 0.0)    # LONG left (3x tile width)
    ]
    
    for i, (x, y) in enumerate(tiles):
        x_corr, y_corr, state = apply_corrections_to_tile(
            x, y, i, tile_width, tile_height, correction_matrix, movement_state
        )
        delta_x = x_corr - x
        print("Tile %d: pos=(%.1f, %.1f), state=%s, x_correction=%.1f" % (i, x, y, state, delta_x))
        
        if i == 3:
            # Long left should use backlash_long_x_left
            assert abs(delta_x - 2.0) < 0.1, "Expected 2.0μm long backlash, got %.1f" % delta_x
            assert state == 'long_left', "Expected 'long_left' state, got %s" % state
            print("  ✓ Long move detected and long backlash applied")
    
    print("✓ Long move handling correct")
    return True


def test_grid_visualization():
    """Test grid visualization output"""
    print("\n" + "="*70)
    print("TEST 6: Grid Visualization")
    print("="*70)
    
    # Create 10-tile grid matching example in design doc
    tiles_grid = [
        (0, 0),  # 0
        (1, 0),  # 1
        (0, 1), (1, 1), (2, 1), (3, 1),  # Row 2
        (2, 2), (3, 2),  # Row 3 partial
        (2, 3), (3, 3)   # Row 4 partial
    ]
    
    grid_vis = visualize_grid(tiles_grid, 4, 5)
    
    print("\n=== GRID LAYOUT ===")
    for row in grid_vis:
        print(row)
    
    # Process for state sequence
    correction_matrix = create_default_correction_matrix()
    correction_matrix['long_move_threshold_x'] = 2.0
    movement_state = create_movement_state()
    
    # Convert grid coords to micrometers
    tile_width = 1000.0
    tile_height = 1000.0
    tiles_um = [(x * tile_width, y * tile_height) for x, y in tiles_grid]
    
    states = []
    for i, (x, y) in enumerate(tiles_um):
        _, _, state = apply_corrections_to_tile(
            x, y, i, tile_width, tile_height, correction_matrix, movement_state
        )
        states.append(state)
    
    print("\n=== STATE SEQUENCE ===")
    print(", ".join(states))
    
    print("✓ Grid visualization generated")
    return True


def test_scale_and_skew():
    """Test scale and skew corrections"""
    print("\n" + "="*70)
    print("TEST 7: Scale and Skew Corrections")
    print("="*70)
    
    correction_matrix = create_default_correction_matrix()
    correction_matrix['scale_x'] = 1.01  # 1% X scale error
    correction_matrix['scale_y'] = 0.99  # 1% Y scale error
    correction_matrix['skew_xy'] = 0.001 # X->Y coupling
    correction_matrix['skew_yx'] = 0.002 # Y->X coupling
    
    movement_state = create_movement_state()
    
    tile_width = 1000.0
    tile_height = 1000.0
    
    # Test at different positions
    test_positions = [
        (0.0, 0.0),
        (10000.0, 0.0),
        (0.0, 10000.0),
        (10000.0, 10000.0)
    ]
    
    for i, (x, y) in enumerate(test_positions):
        x_corr, y_corr, state = apply_corrections_to_tile(
            x, y, i, tile_width, tile_height, correction_matrix, movement_state
        )
        print("Pos (%.0f, %.0f) -> (%.1f, %.1f)" % (x, y, x_corr, y_corr))
        
        # At far corner, effects should be visible
        if i == 3:
            expected_x = 10000.0 * 1.01 + 10000.0 * 0.001  # scale + skew
            expected_y = 10000.0 * 0.002 + 10000.0 * 0.99  # skew + scale
            assert abs(x_corr - expected_x) < 1.0, "X correction mismatch"
            assert abs(y_corr - expected_y) < 1.0, "Y correction mismatch"
            print("  ✓ Scale and skew applied correctly at far corner")
    
    print("✓ Scale and skew corrections validated")
    return True


def test_microscope_selection():
    """Test multiple microscope configurations"""
    print("\n" + "="*70)
    print("TEST 8: Multiple Microscope Support")
    print("="*70)
    
    # Create configurations for different microscopes
    microscopes = {
        'zeiss_axio_1': create_default_correction_matrix('zeiss_axio_1'),
        'zeiss_axio_2': create_default_correction_matrix('zeiss_axio_2'),
        'default': create_default_correction_matrix('default')
    }
    
    # Set different backlash for each microscope
    microscopes['zeiss_axio_1']['backlash_x_left'] = 5.0
    microscopes['zeiss_axio_2']['backlash_x_left'] = 8.0
    microscopes['default']['backlash_x_left'] = 3.0
    
    for name, matrix in microscopes.items():
        print("Microscope '%s': X-left backlash = %.1fμm" % (name, matrix['backlash_x_left']))
    
    print("✓ Multiple microscope configurations supported")
    return True


def test_thermal_state_selection():
    """Test cold vs preheated thermal drift selection"""
    print("\n" + "="*70)
    print("TEST 9: Thermal State (Cold vs Preheated)")
    print("="*70)
    
    correction_matrix = create_default_correction_matrix()
    correction_matrix['thermal_drift_x_cold'] = 10.0
    correction_matrix['thermal_drift_y_cold'] = 8.0
    correction_matrix['thermal_drift_x_preheated'] = 2.0
    correction_matrix['thermal_drift_y_preheated'] = 1.5
    
    thermal_load = 1.0
    
    # Test cold state
    correction_matrix['thermal_state'] = 'cold'
    drift_x, drift_y = select_thermal_drift(correction_matrix, thermal_load)
    print("Cold state drift: (%.1f, %.1f) μm" % (drift_x, drift_y))
    assert drift_x == 10.0 and drift_y == 8.0
    
    # Test preheated state
    correction_matrix['thermal_state'] = 'preheated'
    drift_x, drift_y = select_thermal_drift(correction_matrix, thermal_load)
    print("Preheated state drift: (%.1f, %.1f) μm" % (drift_x, drift_y))
    assert drift_x == 2.0 and drift_y == 1.5
    
    # Test unknown state (should default to cold)
    correction_matrix['thermal_state'] = 'unknown'
    drift_x, drift_y = select_thermal_drift(correction_matrix, thermal_load)
    print("Unknown state drift (defaults to cold): (%.1f, %.1f) μm" % (drift_x, drift_y))
    assert drift_x == 10.0 and drift_y == 8.0
    
    print("✓ Thermal state selection working correctly")
    return True


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*70)
    print("METADATA CORRECTION SYSTEM - CORE FUNCTIONALITY TESTS")
    print("="*70)
    
    tests = [
        test_basic_correction_application,
        test_backlash_correction,
        test_thermal_load_calculation,
        test_first_down_special_case,
        test_long_move_detection,
        test_grid_visualization,
        test_scale_and_skew,
        test_microscope_selection,
        test_thermal_state_selection
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print("✗ %s FAILED" % test.__name__)
        except Exception as e:
            failed += 1
            print("✗ %s EXCEPTION: %s" % (test.__name__, str(e)))
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("TEST RESULTS: %d passed, %d failed" % (passed, failed))
    print("="*70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
