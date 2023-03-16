import time
import logging
import numpy as np
from valkka.multiprocess import MessageProcess, MessageObject, \
    EventGroup, SyncIndex
from multiprocessing import shared_memory

class MyProcess(MessageProcess):
    """<rtf>
    Create "server-side" shared memory first in the frontend with the unique name ``my-shm-1``
    <rtf>"""
    def __init__(self, name):
        super().__init__(name)
        self.eg = EventGroup(10)
        self.shmem_name = "my-shm-1"
        # create a dummy model array;
        self.model = np.zeros((100,100), dtype=float)
        # create frontend-side shared memory array:
        self.shmem = shared_memory.SharedMemory(
            name=self.shmem_name, create=True, size=self.model.nbytes
        )
        self.array = np.ndarray(
            self.model.shape, dtype=self.model.dtype, buffer=self.shmem.buf
        )
        self.array[:,:] = 1.0

    """<rtf>
    Close the "server-side" shared memory, for example, at garbage collection of ``MyProcess``
    <rtf>"""
    def __del__(self):
        self.shmem.close()

    """<rtf>
    Backend methods are: ``preRun__``, ``postRun__`` and ``c__readWrite``.

    ``preRun__`` is executed in the forked process (backend) before the main
    execution loop kicks in: create "client-side" shared memory in the backend 
    with the correct unique name ``my-shm-1``.
    <rtf>"""
    def preRun__(self):
        self.logger.info("preRun__ : ")
        # create backend-side shared memory array:
        self.shmem__ = shared_memory.SharedMemory(
            name=self.shmem_name, create=False, size=self.model.nbytes
        )
        self.array__ = np.ndarray(
            self.model.shape, dtype=self.model.dtype, buffer=self.shmem__.buf
        )

    """<rtf>
    ``postRun__`` is executed in the forked process (backend) just before the
    process exists and shuts down: close "client-side" shared memory:
    <rtf>"""
    def postRun__(self):
        self.logger.info("postRun__ : ")
        # release backend-side shared memory array:
        self.shmem__.unlink()

    def c__readWrite(self, sync_index: int =None):
        self.logger.info("c__readWrite: will change array values from %s to %s",
            self.array__[0,0], 3.0)
        self.array__[:,:] = 3.0
        self.logger.info("c__readWrite: ..did that!")
        self.eg.set(sync_index) # tell frontend that it's done

    """<rtf>
    Frontend methods: ``readWrite``
    <rtf>"""
    def readWrite(self):
        self.logger.info("readWrite : calling backend")
        with SyncIndex(self.eg) as i:
            self.sendMessageToBack(MessageObject(
                "readWrite", 
                sync_index = i
            ))
        self.logger.info("readWrite: array values now %s", self.array[0,0])

p = MyProcess(name="my-process")
p.formatLogger()
"""<rtf>
Calling ``start``, forks and creates the backend
<rtf>"""
p.start()
time.sleep(1)
p.readWrite()
"""<rtf>
Tell the backend to stop and exit
<rtf>"""
p.stop()
"""<rtf>

Resulting output:

.. code:: text

    MyProcess.my-process - INFO - preRun__ : 
    MyProcess.my-process - INFO - readWrite : callin backend
    MyProcess.my-process - INFO - c__readWrite: will change array values from 1.0 to 3.0
    MyProcess.my-process - INFO - c__readWrite: ..did that!
    MyProcess.my-process - INFO - readWrite: array values now 3.0
    MyProcess.my-process - INFO - postRun__ :
    
<rtf>"""

