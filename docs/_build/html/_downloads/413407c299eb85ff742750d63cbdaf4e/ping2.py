import time
import logging
from valkka.multiprocess import MessageProcess, MessageObject, \
    EventGroup, SyncIndex

class MyProcess(MessageProcess):

    def __init__(self, name):
        super().__init__(name)
        self.eg = EventGroup(10)

    """<rtf>
    here we have created a group of multiprocessing ``Event`` objects
    `(link) <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Event>`_
    into the ``self.eg`` member.  
    
    As the ``Event`` s are created before fork (i.e. calling ``start``), they are visible
    both in the multiprocessing back- and frontend.
    <rtf>"""

    def c__ping(self, parameter=None, sync_index: int =None):
        self.logger.info("c__ping: got parameter %s - will do some", parameter)
        time.sleep(1.0) # do something time consuming..
        self.logger.info("c__ping: ..did that!")
        self.eg.set(sync_index) # tell frontend that it's done

    """<rtf>
    An index number is communicated to the multiprocessing backend,
    so that the forked process knows which ``Event`` it needs to set
    in order to sync with the frontend:
    <rtf>"""
    def ping(self, parameter=None):
        self.logger.info("ping: callin backend to do some stuff")
        with SyncIndex(self.eg) as i:
            self.sendMessageToBack(MessageObject(
                "ping", 
                parameter=parameter,
                sync_index = i
            ))
        self.logger.info("ping: backend seems to be ready")

p = MyProcess(name="my-process")
"""<rtf>
A helper method to quick-format the logger for ``MyProcess``:
<rtf>"""
p.formatLogger()
"""<rtf>
Calling ``start``, forks and creates the backend
<rtf>"""
p.start()
time.sleep(1)
p.ping(parameter="gotcha!")
"""<rtf>
Tell the backend to stop and exit
<rtf>"""
p.stop()
"""<rtf>

We get this output:

.. code:: text

    MyProcess.my-process - INFO - ping: callin backend to do some stuff
    MyProcess.my-process - INFO - c__ping: got parameter gotcha! - will do some
    MyProcess.my-process - INFO - c__ping: ..did that!
    MyProcess.my-process - INFO - ping: backend seems to be ready

<rtf>"""

