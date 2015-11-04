import sys
import os.path
sys.path.append(os.path.join('..', 'util'))

import set_compiler
set_compiler.install()

import pyximport
pyximport.install()

import numpy as np
from timer import Timer
from animator import Animator
from physics import update, preallocate_locks

def randcolor():
    return np.random.uniform(0.0, 0.89, (3,)) + 0.1

# from wiki on z-order curve
def less_msb(x, y):
    return x < y and (x ^ y)

# from wiki on z-order curve
def morton_order_sort(a, b):
    # a and b will be tuples, index followed by position tuple 
    j, x = 0, 0 
    for k in range(2): 
        y = a[1][k] ^ b[1][k]
        if less_msb(x, y):
            j = k
            x = y
    return a[1][j] - b[1][j]

if __name__ == '__main__':
    num_balls = 10000
    radius = 0.002
    positions = np.random.uniform(0 + radius, 1 - radius,
                                  (num_balls, 2)).astype(np.float32)

    # make a hole in the center
    while True:
        distance_from_center = np.sqrt(((positions - 0.5) ** 2).sum(axis=1))
        mask = (distance_from_center < 0.25)
        num_close_to_center = mask.sum()
        if num_close_to_center == 0:
            # everything is out of the center
            break
        positions[mask, :] = np.random.uniform(0 + radius, 1 - radius,
                                               (num_close_to_center, 2)).astype(np.float32)

    velocities = np.random.uniform(-0.25, 0.25,
                                   (num_balls, 2)).astype(np.float32)

    # Initialize grid indices:
    #
    # Each square in the grid stores the index of the object in that square, or
    # -1 if no object.  We don't worry about overlapping objects, and just
    # store one of them.
    grid_spacing = radius / np.sqrt(2.0)
    grid_size = int((1.0 / grid_spacing) + 1)
    grid = - np.ones((grid_size, grid_size), dtype=np.uint32)
    grid[(positions[:, 0] / grid_spacing).astype(int),
         (positions[:, 1] / grid_spacing).astype(int)] = np.arange(num_balls)

    # A matplotlib-based animator object
    animator = Animator(positions, radius * 2)

    # simulation/animation time variablees
    physics_step = 1.0 / 100  # estimate of real-time performance of simulation
    anim_step = 1.0 / 30  # FPS
    total_time = 0

    frame_count = 0

    # SUBPROBLEM 4: uncomment the code below.
    # preallocate locks for objects
    locks_ptr = preallocate_locks(num_balls)

    while True:
        with Timer() as t:
            update(positions, velocities, grid,
                   radius, grid_size, locks_ptr,
                   physics_step)

        # udpate our estimate of how fast the simulator runs
        physics_step = 0.9 * physics_step + 0.1 * t.interval
        total_time += t.interval

        frame_count += 1
        if total_time > anim_step:
            animator.update(positions)
            print("{} simulation frames per second".format(frame_count / total_time))
            frame_count = 0
            total_time = 0
            # SUBPROBLEM 3: sort objects by location.  Be sure to update the
            # grid if objects' indices change!  Also be sure to sort the
            # velocities with their object positions!

            # the wiki code only gives us relative orderings,
            # so we need to use pythons built in sort function 
            # the wiki code also expects integers, so we convert
            # to grid positions  
            # SUBPROBLEM 3
            grid_indices = zip(range(num_balls), (positions/grid_spacing).astype(int).tolist())
            grid_indices.sort(morton_order_sort)
            # want to get the sorted indices, don't care about positions 
            sorted_idx = [x[0] for x in grid_indices]
            
            # shuffle positions/velocities to the new oridering
            positions = positions[sorted_idx]
            velocities = velocities[sorted_idx]
            # clear grid as old indices are no longer valid 
            grid[:, :] = -1
            # update grid with new positions 
            for i in range(num_balls):
                # check fi the position is in bounds 
                if positions[i, 0] < 1 and positions[i, 0] >= 0:
                    if positions[i, 1] < 1 and positions[i, 0] >= 0:
                        ix = int(positions[i, 0]/grid_spacing)
                        iy = int(positions[i, 1]/grid_spacing)
                        grid[ix, iy] = i 
