import time
import logging
from valkka.multiprocess import MessageProcess, MessageObject
"""<rtf>
We are going to use quite some the select module:
<rtf>"""
import select
"""<rtf>
so you might want to read 
`this tutorial <https://docs.python.org/3/howto/sockets.html#non-blocking-sockets>`_
<rtf>"""

class MyProcess(MessageProcess):

    def __init__(self, name):
        super().__init__(name)

    """<rtf>
    We're sending a message, this time from backend to frontend
    <rtf>"""
    def c__ping(self, parameter=None):
        self.logger.info("c__ping: got parameter %s - will do some", parameter)
        time.sleep(1.0) # do something time consuming..
        self.logger.info("c__ping: ..did that!")
        self.send_out__(MessageObject(
            "pong", result="pudding"
        ))

    def ping(self, parameter=None):
        self.logger.info("ping: sending ping to backend")
        self.sendMessageToBack(MessageObject(
            "ping", 
            parameter=parameter
        ))

p = MyProcess(name="my-process")
p.formatLogger()
"""<rtf>
Get the pipe (``multiprocessing.Pipe``) for listening messages from ``MyProcess`` ``p``.
Remember that you should use use pipe communication only for a small amount of data:
typically just short messages and maybe some tiny (numpy) arrays if you have to.
<rtf>"""
pipe = p.getPipe()
"""<rtf>
Calling ``start``, forks and creates the backend
<rtf>"""
p.start()
time.sleep(1)
p.ping(parameter="gotcha!")
print("main: waiting reply from multiprocessing backend")
"""<rtf>
Use select to wait for the message
<rtf>"""
select.select([pipe], [], [])
msg = pipe.recv()
print("main: got", msg(), "with some", msg["result"])
"""<rtf>
Tell the backend to stop and exit
<rtf>"""
p.stop()
"""<rtf>

We get this output:

.. code:: text

    MyProcess.my-process - INFO - ping: sending ping to backend
    main: waiting reply from multiprocessing backend
    MyProcess.my-process - INFO - c__ping: got parameter gotcha! - will do some
    MyProcess.my-process - INFO - c__ping: ..did that!
    main: got pong with some pudding
    
<rtf>"""
