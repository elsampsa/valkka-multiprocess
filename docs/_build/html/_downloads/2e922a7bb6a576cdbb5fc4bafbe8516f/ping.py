import time
from valkka.multiprocess import MessageProcess, MessageObject

class MyProcess(MessageProcess):
    
    def c__ping(self, parameter=None):
        print("Regards from other side of the fork!  Got parameter", parameter)

    def ping(self, parameter=None):
        self.sendMessageToBack(MessageObject(
            "ping", parameter=parameter))

p = MyProcess(name="my-process")
"""<rtf>
Calling ``start``, forks and creates the backend
<rtf>"""
p.start()
"""<rtf>
Let multiprocessing backend run on it's own for one second
<rtf>"""
time.sleep(1)
"""<rtf>
Call frontend method with a parameter: it sends seamlessly a message to the backend
which executes ``c__ping`` in the backend:
<rtf>"""
p.ping(parameter="gotcha!")
"""<rtf>
Again, let multiprocessing backend run on it's own a while
<rtf>"""
time.sleep(1)
"""<rtf>
Finally, tell the backend to stop and exit
<rtf>"""
p.stop()
