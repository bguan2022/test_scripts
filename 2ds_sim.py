import math 
import numpy as np
import matplotlib.pyplot as plt
import time

def ls_compute(t,t0,a,b):
    mv = math.sin(a*(t-t0)+b)
    mh = math.sin(a/2*(t-t0)+b)
    return mv, mh

def mirror_normal(x,y):
    z = 0.0
    z2 = x**2+y**2
    z = math.sqrt(z2)
    x = x/z
    y = x/z
    return x, y

def calc_coeff():
    HRES = 1000
    VRES = 1280
    grid_x = []
    grid_y = []
    for i in range(0,HRES,10):
        for j in range(0,VRES,10):
            grid_x.append(i)
            grid_y.append(j)
    np.polyfit(grid_x,grid_y,2)
    plt.plot(grid_x,grid_y,'ro')
    plt.show()


def beam_trace(x_pos, y_pos):
    coeff_x = [[1,-2,0,8],[1,1,3,4],[2,0,4,5],[1,1,3,5]]
    coeff_y = [[1,-1,4,6],[1,2,2,3],[1,2,1,2],[2,1,2,1]]
    num_emitter = 24
    HRES = 1000
    VRES = 1280
    emitter_loc_x = [0]*24
    emitter_loc_y = [0]*24
    x_g = int(x_pos*HRES/2)
    y_g = int(y_pos*VRES/2)
    #using binary search to determin what grid the laser is at, and pick the corresponding poly coefficients 
    if x_g >= (HRES/2):
        if y_g >= (VRES/2):
            loc = 3
        else:
            loc = 2
    else:
        if y_g >= (VRES/2):
            loc = 1
        else:
            loc = 0
    #compute the polynomial for each emitter to approximate location of each emitter
    roi = 1
    for e in range(num_emitter): 
        fx = coeff_x[loc][0]*x_pos**3 + coeff_x[loc][1]*x_pos**2 + coeff_x[loc][2]*x_pos + coeff_x[loc][3]
        fy = coeff_y[loc][0]*y_pos**3 + coeff_y[loc][1]*y_pos**2 + coeff_y[loc][2]*y_pos + coeff_y[loc][3]
        emitter_loc_x[e] = fx
        emitter_loc_y[e] = fy
        if ((np.abs(fx) > (HRES/2)) | (np.abs(fy)>(VRES/2))):
            roi = 0
    return emitter_loc_x, emitter_loc_y, roi


def main():
    steps = 10000
    mv_array = []
    mh_array = []
    total_firing = steps*24
    emitter_x_arr = []
    emitter_y_arr = []
    s_array = []
    calc_coeff()
    for i in range(0,steps,2):
        phase_space = i/4*math.pi
        t0 = time.time()
        v, h = ls_compute(phase_space, math.pi/4, math.pi/4, 2*math.pi/2)
        t1 = time.time()
        x, y = mirror_normal(v, h)
        t2 = time.time()
        emitter_x24, emitter_y24, roi = beam_trace(x,y)
        t3 = time.time()
        
        if (roi == 1):
            mv_array.append(v)
            mh_array.append(h)
            emitter_x_arr = np.concatenate((emitter_x_arr,emitter_x24), axis=0)
            emitter_y_arr = np.concatenate((emitter_y_arr,emitter_y24), axis=0)
            s_array.append(phase_space)
    #print(emitter_x_arr)
    t_ls = t1 - t0
    t_mn = t2 - t1
    t_bt = t3 - t2
    t_total = t_ls + t_mn + t_bt

    print(t_ls/t_total, t_mn/t_total, t_bt/t_total)
    plt.plot(s_array,mv_array)
    plt.plot(s_array,mh_array,'bo')
    #plt.show()
    plt.plot(emitter_x_arr, emitter_y_arr,'ro')
    #plt.show()
main()
