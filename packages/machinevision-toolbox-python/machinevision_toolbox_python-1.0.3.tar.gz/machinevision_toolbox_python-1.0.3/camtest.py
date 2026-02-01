import machinevisiontoolbox as mvtb
import matplotlib.pyplot as plt
import numpy as np
import scipy
from spatialmath import SE3
from spatialmath import base


def mkgrid(N, s, pose=None):
    
    s = base.getvector(s)
    if len(s) == 1:
        sx = s[0]
        sy = s[0]
    elif len(s) == 2:
        sx = s[0]
        sy = s[1]
    else:
        raise ValueError('bad s')

    N = base.getvector(N)
    if len(N) == 1:
        nx = N[0]
        ny = N[0]
    elif len(N) == 2:
        nx = N[0]
        ny = N[1]
    else:
        raise ValueError('bad N')

    if N == 2:
        # special case, we want the points in specific order
        p = np.array([
            [-sx, -sy, 0],
            [-sx,  sy, 0],
            [ sx,  sy, 0],
            [ sx, -sy, 0],
        ]).T / 2
    else:
        X, Y = np.meshgrid(np.arange(nx), np.arange(ny), sparse=False, indexing='ij')
        X = ( X / (nx-1) - 0.5 ) * sx
        Y = ( Y / (ny-1) - 0.5 ) * sy
        Z = np.zeros(X.shape)
        P = np.column_stack((X.flatten(), Y.flatten(), Z.flatten())).T
    
    # optionally transform the points
    if pose is not None:
        P = pose * P

    return P




cam = mvtb.CentralCamera(imagesize=(1280,1024), f=0.015, rho=10e-6)
print(cam)

P = [0.3, 0.4, 3]
print(cam.project(P))
print(cam.project(P, pose=SE3(0.1,0.2,0.3) * SE3.RPY([0.1,0.2,0.3])))
print(cam.K)
print(cam.C)

P = mkgrid([3], [0.2], pose=SE3(0, 0, 1))
print(P)
print(cam.project(P))

# C = cam.C
# f, s, K, R, t = invcamcal(C)
# print(f, s)
# print(K)
# print('pose')
# print(R, R@t)

# p = cam.project(P.T)
# print('image plane points\n', p)