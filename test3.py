# -*- coding: utf-8 -*-
"""
Created on Wed May 30 17:54:35 2018

@author: xici

#https://www.bjsxt.com/down/8468.html
"""

from time import sleep
from tqdm import tqdm
from multiprocessing import Pool, freeze_support

def progresser(n):
    text = "progresser #{}".format(n)
    for i in tqdm(range(5000), desc=text, position=n):
        sleep(0.001)

if __name__ == '__main__':
    freeze_support()  # for Windows support
    L = list(range(10))
    Pool(len(L)).map(progresser, L)
    