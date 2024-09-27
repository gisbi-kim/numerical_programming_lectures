"""
study mateiral recommendation:
    2016 ICRA SLAM tutorial 
    http://www.diag.uniroma1.it/~labrococo/tutorial_icra_2016/icra16_slam_tutorial_grisetti.pdf
"""

import os 
import sys 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.pose import *

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def create_rotation_matrix(roll, pitch, yaw, rotmatname="R"):

    #
    # change this values for various experiements 
    init_bias_roll = np.deg2rad(180)
    init_bias_pitch = np.deg2rad(90)
    init_bias_yaw = np.deg2rad(10)
    #

    roll += init_bias_roll
    pitch += init_bias_pitch
    yaw += init_bias_yaw

    R_x = np.array([[1, 0, 0],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll), np.cos(roll)]])
    
    R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                    [0, 1, 0],
                    [-np.sin(pitch), 0, np.cos(pitch)]])
    
    R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                    [np.sin(yaw), np.cos(yaw), 0], 
                    [0, 0, 1]])
    
    R = np.dot(R_z, np.dot(R_y, R_x))

    print(f"{rotmatname}: \n {R}")

    return R

# Generate samples R1, R2, R3
roll1, pitch1, yaw1 = np.deg2rad(12.0), np.deg2rad(3.0), np.deg2rad(1.5)
roll2, pitch2, yaw2 = np.deg2rad(-1.0), np.deg2rad(5.5), np.deg2rad(-2.0)
roll3, pitch3, yaw3 = np.deg2rad(3.5), np.deg2rad(-12.5), np.deg2rad(4.0)

R1 = create_rotation_matrix(roll1, pitch1, yaw1, "R1")
R2 = create_rotation_matrix(roll2, pitch2, yaw2, "R2")
R3 = create_rotation_matrix(roll3, pitch3, yaw3, "R3")


# Initial solution
R0 = np.eye(3)
# R0 = R1.copy()

print(" ")

# Iterative Gauss-Newton opt
max_iters = 300
tolerance = 1e-6

for i in range(max_iters):
    H = np.zeros((3, 3))
    b = np.zeros(3)
    
    for R_i in [R1, R2, R3]:
        e_i = unskew(log_map(np.dot(R0.T, R_i)))  # residual
        J_i = -1*np.eye(3)  # approx. to -I
        """
        Derivation (why -I)
            see https://gsk1m.github.io/slam/2024/08/24/rot-avg1.html
        """

        H += J_i.T @ J_i 
        b += J_i.T @ e_i 
    
    # solve the normal equation H * dtheta = -b 
    dtheta = np.linalg.solve(H, -b)
    
    print(f"iter {i}: dtheta: {dtheta}")
    if np.linalg.norm(dtheta) < tolerance:
        print(f"The solution converged. terminate the GN opt at iteration {i}\n")
        break
    
    # update R0 
    R0 = R0 @ exp_map(dtheta)

    # check SO(3)ness: make det = 1
    U, _, Vt = np.linalg.svd(R0)
    R0 = np.dot(U, Vt)
    if np.linalg.det(R0) < 0:
        U[:, -1] *= -1
        R0 = np.dot(U, Vt)

R0_star = R0

print("The optimized averaged rotation R0*:")
print(R0_star)


#
# Visualize the reults
# 
def plot_rotation(R, color, label, ax):
    origin = np.zeros(3)
    for i in range(3):
        vec = R[:, i]
        ax.quiver(origin[0], origin[1], origin[2], vec[0], vec[1], vec[2], 
                  color=color[i], length=1.0, normalize=True, label=f"{label} Axis" if i == 0 else "")

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# frame axis with black color
ax.quiver(0, 0, 0, 1, 0, 0, color='k', linewidth=1, label='Original X')
ax.quiver(0, 0, 0, 0, 1, 0, color='k', linewidth=1, label='Original Y')
ax.quiver(0, 0, 0, 0, 0, 1, color='k', linewidth=1, label='Original Z')

# R1, R2, R3, R0_star 
plot_rotation(R1, ['r', 'r', 'r'], 'R1', ax)
plot_rotation(R2, ['c', 'c', 'c'], 'R2', ax)
plot_rotation(R3, ['orange', 'orange', 'orange'], 'R3', ax)
plot_rotation(R0_star, ['blue', 'blue', 'blue'], 'R0*', ax)

ax.set_xlim([-1, 1])
ax.set_ylim([-1, 1])
ax.set_zlim([-1, 1])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('Visualization of Rotation Matrices (R1, R2, R3, R0*)')
ax.legend()

plt.show()
