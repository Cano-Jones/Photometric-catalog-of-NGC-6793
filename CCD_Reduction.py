'''
CCD_Reduction.py

:Author: Cano Jones, Alejandro
:Date: May 2023
:LinkedIn: https://www.linkedin.com/in/alejandro-cano-jones-5b20a7136/
:GitHub: https://github.com/Cano-Jones
'''

###################################################################################################
#                                   Used Libraries
from colorama import Fore
from pathlib import Path
from ccdproc import ImageFileCollection
import ccdproc as ccdp
from astropy import units as u
import numpy as np
from astropy.stats import mad_std
import os
import sys

###################################################################################################
#                                      FUNCTIONS

def inv_median(a):  return 1 / np.median(a)

def Closest_Dark(T):
    DARKS_path = Path('Results/DARKS')
    DARKS_collection = ccdp.ImageFileCollection(DARKS_path)
    dark_times=list(DARKS_collection.summary['exptime'])
    MIN_d=max(dark_times)
    MIN=MIN_d
    for dark in dark_times:
        if abs(T-dark)<MIN_d:
            MIN_d= abs(T-dark)
            MIN=dark
    return ccdp.CCDData.read('Results/DARKS/masterdark_'+str(int(MIN))+'s.fit', unit=u.adu)


##################################################################################################

##################################BIAS############################################################
print('\n \t\tCCD_Reduction.py : Cano Jones, Alejandro')
print(' \t\t________________________________________\n')

sys.stdout = open("log.txt", "w")
sys.stderr = open("log.txt", "w")

sys.stdout = sys.__stdout__
print( '  \t\t ~$ << Bias calibration initiated.')
sys.stdout = open("log.txt", "a")

BIAS_path = Path('DATA/BIAS')

if not os.listdir(BIAS_path):
    sys.stderr = sys.__stderr__  
    exit(Fore.RED+'  \t\t ~$ >> ERROR: No Bias images.')
BIAS_collection = ImageFileCollection(BIAS_path)
Results_path = Path('Results')

Empty=False
if not os.listdir(Results_path):   Empty=True

BIAS_collection = BIAS_collection.files_filtered(imagetyp='BIAS', include_path=True)

masterbias = ccdp.combine(BIAS_collection,
                             method='average',
                             sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
                             sigma_clip_func=np.ma.median, sigma_clip_dev_func=mad_std,
                             mem_limit=350e6, unit=u.adu
                            )

masterbias.meta['combined'] = True

if Empty: masterbias.write(Results_path / 'masterbias.fit')
else: masterbias.write(Results_path / 'masterbias.fit', overwrite=True)

sys.stdout = sys.__stdout__
print( '  \t\t ~$ >> Bias image completed.')
sys.stdout = open("log.txt", "a")



#################################DARKS###############################################################3

sys.stdout = sys.__stdout__
print( '  \t\t ~$ << Dark calibration initiated.')
sys.stdout = open("log.txt", "a")

Darks_path = Path('DATA/DARKS')
if not os.listdir(Darks_path):
    sys.stderr = sys.__stderr__
    exit(Fore.RED+'  \t\t ~$ >> ERROR: No Dark images.')
DARKS_collection = ccdp.ImageFileCollection(Darks_path)
dark_times = set(DARKS_collection.summary['exptime'])
Results_path = Path('Results/DARKS')
Empty=False
if not os.listdir(Results_path):   Empty=True

for exp_time in sorted(dark_times):
    calibrated_darks = DARKS_collection.files_filtered(imagetyp='dark', exptime=exp_time,
                                                     include_path=True)

    combined_dark = ccdp.combine(calibrated_darks,
                                 method='average',
                                 sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
                                 sigma_clip_func=np.ma.median, sigma_clip_dev_func=mad_std,
                                 mem_limit=350e6, unit=u.adu
                                )

    combined_dark.meta['combined'] = True

    dark_file_name = 'masterdark_'+str(int(exp_time))+'s.fit'
    if Empty: combined_dark.write(Results_path / dark_file_name)
    else: combined_dark.write(Results_path / dark_file_name, overwrite=True)

sys.stdout = sys.__stdout__
print( '  \t\t ~$ >> Dark images completed.')
sys.stdout = open("log.txt", "a")

#########################FLATS##################################################################

sys.stdout = sys.__stdout__
print( '  \t\t ~$ << Flat calibration initiated.')
sys.stdout = open("log.txt", "a")

Flats_path = Path('DATA/FLATS')
if not os.listdir(Flats_path):
    sys.stderr = sys.__stderr__
    exit(Fore.RED+'  \t\t ~$ >> ERROR: No Skyflat images.')
FLATS_collection = ccdp.ImageFileCollection(Flats_path)
DARKS_path = Path('Results/DARKS')
Results_path = Path('Results/FLATS')
Empty=False
if not os.listdir(Results_path):  Empty=True


FILTER_set = set(FLATS_collection.summary['filter'])

masterbias = ccdp.CCDData.read('Results/masterbias.fit', unit=u.adu)


for Filter in FILTER_set:
    Flat_list=[]
    for Flat in FLATS_collection.files_filtered(filter=Filter):
        rawflat = os.path.join (Flats_path, Flat)
        ccd_flat = ccdp.CCDData.read(rawflat, unit=u.adu)
        ccd_flat = ccdp.subtract_bias(ccd_flat , masterbias)
        closest_Dark=Closest_Dark(ccd_flat.header['exptime'])
        ccd_flat=ccdp.subtract_dark(ccd_flat, closest_Dark, exposure_time='exptime', exposure_unit=u.second, scale=True)
                                    
        Flat_list.append(ccd_flat)

    combined_flat = ccdp.combine(Flat_list,
                                 method='average', scale=inv_median,
                                 sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
                                 sigma_clip_func=np.ma.median, signma_clip_dev_func=mad_std,
                                 mem_limit=350e6
                                )
    
    
    combined_flat.meta['combined'] = True
    dark_file_name = 'masterflat_'+str(Filter)+'.fit'
    if Empty: combined_flat.write(Results_path / dark_file_name)
    else: combined_flat.write(Results_path / dark_file_name, overwrite=True)

sys.stdout = sys.__stdout__
print( '  \t\t ~$ >> Skyflat images completed.')
sys.stdout = open("log.txt", "a")



################################################################################################
#                           Science Images

sys.stdout = sys.__stdout__
print( '  \t\t ~$ << Science calibration initiated.')
sys.stdout = open("log.txt", "a")

SCIENCE_path = Path('DATA/SCIENCE')
if not os.listdir(SCIENCE_path): 
    sys.stderr = sys.__stderr__
    exit(Fore.RED+'  \t\t ~$ >> ERROR: No Science images.')
DARKS_path=Path('Results/DARKS')
FLATS_path=Path('Results/FLATS')
Results_path=Path('Results/SCIENCE')
Empty=False
if not os.listdir(Results_path):  Empty=True

SCIENCE_collection = ImageFileCollection(SCIENCE_path)
DARKS_collection = ImageFileCollection(DARKS_path)
FLATS_collection = ImageFileCollection(FLATS_path)

masterbias=ccdp.CCDData.read('Results/masterbias.fit', unit=u.adu)
FILTER_set = set(FLATS_collection.summary['filter'])

for Filter in FILTER_set:
    n=1
    for science in SCIENCE_collection.files_filtered(filter=Filter):
        raw_sci_image = os.path.join (SCIENCE_path, science)
        ccd_image = ccdp.CCDData.read(raw_sci_image, unit=u.adu)
        ccd_image = ccdp.subtract_bias(ccd_image, masterbias)
        closest_Dark=Closest_Dark(ccd_image.header['exptime'])
        closest_Dark = ccdp.subtract_bias(closest_Dark, masterbias)
        ccd_image= ccdp.subtract_dark(ccd_image, closest_Dark, exposure_time='exptime', exposure_unit=u.second, scale=True)   

        flat=ccdp.CCDData.read('Results/FLATS/masterflat_'+str(Filter)+'.fit', unit=u.adu)
        ccd_image = ccdp.flat_correct(ccd_image, flat)
        
        if Empty: ccd_image.write('Results/SCIENCE/'+str(ccd_image.header['object'])+'_'+str(Filter)+'_'+str(n)+'.fit')
        else: ccd_image.write('Results/SCIENCE/'+str(ccd_image.header['object'])+'_'+str(Filter)+'_'+str(n)+'.fit', overwrite=True)
        n+=1



sys.stdout = sys.__stdout__
print( '  \t\t ~$ >> Science images completed.')
print( '\n  \t\t ~$ >> IMAGE REDUCTION COMPLETED.\n')
sys.stdout = open("log.txt", "a")


