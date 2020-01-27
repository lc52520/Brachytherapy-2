###########################################################################################
#
#   Script name: Oncentra_FDR
#
#   Description: Tool for calculating the radial distribution function with respect to a position in the volume
#
#   Example usage: python Oncentra_FDR.py "/file/"
#
#   Author: Pedro Martinez
#   pedro.enrique.83@gmail.com
#   5877000722
#   Date:2019-05-10
#
###########################################################################################



import os
import sys
import pydicom
import numpy as np
import re
import csv
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from tqdm import tqdm
from matplotlib.backends.backend_pdf import PdfPages
from astropy.io import ascii
import pandas as pd
from openpyxl import Workbook, cell, load_workbook
from math import *
from scipy.interpolate import splrep, splev, interp1d
import scipy.integrate as integrate
from scipy.signal import find_peaks, peak_prominences, peak_widths
import PyPDF2
import argparse
import inquirer



def find_nearest(array, dim, value): # find the nearest element of the array to a certain value and return the index of that element
    idx = (np.abs(dim - value)).argmin()
    return array[idx], idx
    # return array[idx]




def find_nearest2D(array2D, dimx, dimy, xvalue, yvalue): # find the nearest element of the array to a certain value and return the index of that element
    idx = (np.abs(dimx - xvalue)).argmin()
    idy = (np.abs(dimy - yvalue)).argmin()
    return array2D[idy,idx], idx, idy
    # return array[idx]
    

# after we find the nearest we will have to perform a bilinear interpolation to find the appropriate value for the measured coordinates.



def fdr_source_weighted(dataset, meas_params):
    # Here we will calculate the TG-43 contribution to the dose at the measured point by all the other sources.
    # We first need to load F (anisotropy) and g (radial) tables for the mHDR source.
    with open("Tables/mHDR-v2_Anisotropy.csv", "r") as csv_aniso:  # reading the anisotropy function
        csvReader = csv.reader(csv_aniso, delimiter=',')
        x = list(csvReader)
        Dataset = np.array(x).astype(np.float)
        dimx = Dataset[0,1:]
        dimy = Dataset[1:,0]
        Aniso = Dataset[1:,1:]

    with open("Tables/mHDR-v2_Radial-Dose.csv", "r") as csv_radose:  # reading the radial dose function
        csvReader = csv.reader(csv_radose, delimiter=',')
        x = list(csvReader)
        Dataset = np.array(x).astype(np.float)
        dim = Dataset[:, 0]
        Radose = Dataset[:, 1]

    # Data for the Ir 192 HDR Brachy source by Nucletron
    L_active = 0.35 # cm (active size fo the source)
    DRC_mHDR_v2 = 1.109 # cm (dose rate constant)
    DRC_mHDR_v2r = 1.1121 # cm (dose rate constant)
    beta_0 = 2* atan(L_active/2) # In radians
    print(beta_0, 'rad')
    exit(0)





    x = meas_params[0]  # x coordinate of the measurement point
    y = meas_params[1]  # y coordinate of the measurement point
    z = meas_params[2]  # z coordinate of the measurement point
    r = meas_params[3]  # maximum radius
    inc = meas_params[4]  # radial increment
    delta = meas_params[4]  # radial increment
    print('x=', x)
    print('y=', y)
    print('z=', z)
    print('r=', r)
    print('inc=', inc)  # delta and increment must have the same value to avoid missreading data
    print('delta=', delta)

    print('number of catheters=', dataset[0x300a, 0x0230][0][0x300a, 0x0280].VM)
    radius = np.arange(0, r, inc)
    counts = np.zeros_like(radius)
    print('radius=', radius, len(radius))


    k = 0
    for step in radius:
        print('step=', step)
        for i in range(0, dataset[0x300a, 0x0230][0][0x300a, 0x0280].VM): # cycle through all catheters
            print(dataset[0x300a, 0x0230][0][0x300a, 0x0280][i][0x300a, 0x0286]) # this is the channel total time
            for j in range(1, dataset[0x300a, 0x0230][0][0x300a, 0x0280][i][0x300a,0x02d0].VM, 2):  # now we will cycle through all the sources
                xc, yc, zc = dataset[0x300a, 0x0230][0][0x300a, 0x0280][i][0x300a,0x02d0][j][0x300a, 0x02d4].value
                time = dataset[0x300a, 0x0230][0][0x300a, 0x0280][i][0x300a,0x02d0][j][0x300a, 0x02d6].value
                r_mm = sqrt((x - xc) * (x - xc) + (y - yc) * (y - yc) + (z - zc) * (z - zc))  # now we calculate the distance from the source to the measurement point
                r_cm = r_mm/10
                theta_rad = acos( abs(z - zc)/r_mm )
                theta_deg=degrees(theta_rad)
                # Now we retrieve the table information
                gl,_ = find_nearest(Radose, dim, r_cm)
                F,_,_= find_nearest2D(Aniso, dimx, dimy, r_cm, theta_deg)
                # GL =
                # GL_ref =
                print(time)
        #         now we need to subtract the time to get rid of the cumulative time and have a specific time



        k = k + 1
    # print('radius=', radius, 'counts=', counts)

    fdr = interp1d(radius, counts, kind='previous')
    #    print(radius,radius[-1])

    radius2 = np.linspace(0, radius[-1], 1001, endpoint=True)
    # bspl = splrep(radius,counts,s=3)

    return radius2, fdr















def fdr_source(dataset, meas_params):
    x = meas_params[0]  # x coordinate of the measurement point
    y = meas_params[1]  # y coordinate of the measurement point
    z = meas_params[2]  # z coordinate of the measurement point
    r = meas_params[3]  # maximum radius
    inc = meas_params[4]  # radial increment
    delta = meas_params[4]  # radial increment
    print('x=', x)
    print('y=', y)
    print('z=', z)
    print('r=', r)
    print('inc=', inc)  # delta and increment must have the same value to avoid missreading data
    print('delta=', delta)

    print('number of catheters=', dataset[0x300a, 0x0230][0][0x300a, 0x0280].VM)
    radius = np.arange(0, r, inc)
    counts = np.zeros_like(radius)
    print('radius=', radius, len(radius))


    k = 0
    for step in radius:
        print('step=', step)
        for i in range(0, dataset[0x300a, 0x0230][0][0x300a, 0x0280].VM):
            for j in range(1, dataset[0x300a, 0x0230][0][0x300a, 0x0280][i][0x300a,0x02d0].VM, 2):  # now we will cycle through all the catheters to see if they fit inside the search radius
                # print(i,step,dataset[0x300a, 0x0230][0][0x300a, 0x0280][i][0x1001, 0x1080][0][0x1001, 0x1083].value)
                xc, yc, zc = dataset[0x300a, 0x0230][0][0x300a, 0x0280][i][0x300a,0x02d0][j][0x300a, 0x02d4].value
                source_dist = sqrt((x - xc) * (x - xc) + (y - yc) * (y - yc) + (z - zc) * (z - zc))  # now we calculate the distance from the catheter to the measurement point
                # print(cath_dist, step, step + delta)
                if source_dist > step and source_dist < step + delta:
                    counts[k] = counts[k] + 1
        k = k + 1
    print('radius=', radius, 'counts=', counts)

    fdr = interp1d(radius, counts, kind='previous')
    #    print(radius,radius[-1])

    radius2 = np.linspace(0, radius[-1], 1001, endpoint=True)
    # print(radius, radius2)
    # bspl = splrep(radius,counts,s=3)

    return radius2, fdr















def fdr_cath(dataset,meas_params):

    x = meas_params[0] #x coordinate of the measurement point
    y = meas_params[1] #y coordinate of the measurement point
    z = meas_params[2] #z coordinate of the measurement point
    r = meas_params[3] #maximum radius
    inc = meas_params[4]  #radial increment
    delta = meas_params[4]  #radial increment
    print('x=',x)
    print('y=',y)
    print('z=',z)
    print('r=',r)
    print('inc=',inc) #delta and increment must have the same value to avoid missreading data
    print('delta=',delta)

    print('number of catheters=',dataset[0x300a, 0x0230][0][0x300a, 0x0280].VM)
    radius = np.arange(0,r,inc)
    counts=np.zeros_like(radius)
    # print('radius=',radius,len(radius))

    k=0
    for step in radius:
        print('step=',step)
        for i in range(0,dataset[0x300a, 0x0230][0][0x300a, 0x0280].VM):  # now we will cycle through all the catheters to see if they fit inside the search radius
            #print(i,step,dataset[0x300a, 0x0230][0][0x300a, 0x0280][i][0x1001, 0x1080][0][0x1001, 0x1083].value)
            xc,yc,zc=dataset[0x300a, 0x0230][0][0x300a, 0x0280][i][0x1001, 0x1080][0][0x1001, 0x1083].value
            cath_dist=sqrt((x-xc)*(x-xc)+(y-yc)*(y-yc)) #now we calculate the distance from the catheter to the measurement point
            # print(cath_dist,step,step+delta)
            if cath_dist > step and cath_dist < step + delta:
                counts[k]=counts[k]+1
        k=k+1
    # print('radius=',radius,'counts=',counts)

    
    fdr=interp1d(radius,counts, kind='previous')
#    print(radius,radius[-1])

    radius2 = np.linspace(0,radius[-1],1001,endpoint=True)
    print(radius,radius2)
    #bspl = splrep(radius,counts,s=3)


    return radius2, fdr













def process_plan(filename,meas_params):
    dataset = pydicom.dcmread(filename)
    print(filename, meas_params, type(meas_params))

    questions = [
        inquirer.List('type',
                      message="Select the type of FDR?",
                      choices=['Catheter', 'Source', 'Source weighted'],
                      ),
    ]
    answers = inquirer.prompt(questions)
    print(answers["type"])

    if answers["type"]=='Catheter':
        radius2, fdr2 = fdr_cath(dataset, meas_params)
    elif answers["type"] == 'Source':
        radius2, fdr2 = fdr_source(dataset, meas_params)
    elif answers["type"] == 'Source weighted':
        print(meas_params)
        radius2, fdr2 = fdr_source_weighted(dataset, meas_params)





    fig,ax = plt.subplots()
#    ax.plot(radius,counts)
    ax.plot(radius2,fdr2(radius2))
    ax.set_xlabel('radius [mm]')
    ax.set_ylabel('counts')
    ax.set_ylim(bottom=0)

    plt.show()
    exit(0)














def process_struct(filename):
    print('Starting struct calculation')
    dataset = pydicom.dcmread(filename)










parser = argparse.ArgumentParser()
parser.add_argument('plan',type=str,help="Input the plan file")
parser.add_argument('-s', '--structure', nargs='?', type=argparse.FileType('r'), help='structure file, in DICOM format')
parser.add_argument('-m' ,'--measurement' , nargs=5, metavar=('x', 'y', 'z', 'r', 'i'),
                        help="Specify point of measurement, radius and increment of the FDR in mm", type=float,
                        default=[0,0,0,30,5])
                        #default=None)
args=parser.parse_args()
planname=args.plan
meas_params=args.measurement


if args.plan:
    planname=args.plan
    process_plan(planname, meas_params)
if args.structure:
    structname = args.structure
    process_struct(structname.name)






