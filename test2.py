# -*- coding: utf-8 -*-
"""
Created on Wed May 30 17:54:35 2018

@author: xici

#https://www.bjsxt.com/down/8468.html
"""
from multiprocessing.pool import ThreadPool
import time
import threading
from tqdm import tqdm


def demo(position, total):
    text = "progresser #{}".format(position)
    progress = tqdm(
        total=total,
        position=position,
        desc=text,
    )
    for _ in range(0, total, 5):
        progress.update(5)
        time.sleep(0.1)
    progress.close()


pool = ThreadPool(5)
tasks = range(50)
for i, url in enumerate(tasks, 1):
    pool.apply_async(demo, args=(i, 100))
pool.close()
pool.join()
