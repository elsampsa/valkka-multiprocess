import time, sys
import numpy as np
import logging
from random import randint
from multiprocessing import shared_memory
from valkka.multiprocess import MessageProcess, MessageObject, \
    MainContext, safe_select

"""<rtf>
First define the worker process that will do some calculation on a shared numpy array.

This is similar to examples :ref:`3 <example3>` and :ref:`4 <example4>`:
<rtf>"""
class WorkerProcess(MessageProcess):

    def __init__(self, name):
        super().__init__(name)
        self.shmem_name = "shm-"+self.name
        # create a dummy model array;
        self.model = np.zeros((100,100), dtype=float)
        # create frontend-side shared memory array:
        self.shmem = shared_memory.SharedMemory(
            name=self.shmem_name, create=True, size=self.model.nbytes
        )
        self.array = np.ndarray(
            self.model.shape, dtype=self.model.dtype, buffer=self.shmem.buf
        )
        self.array[:,:] = 0.0

    def __del__(self):
        self.shmem.close()

    # Backend methods
    def preRun__(self):
        self.logger.info("preRun__ : ")
        # create backend-side shared memory array:
        self.shmem__ = shared_memory.SharedMemory(
            name=self.shmem_name, create=False, size=self.model.nbytes
        )
        self.array__ = np.ndarray(
            self.model.shape, dtype=self.model.dtype, buffer=self.shmem__.buf
        )

    def postRun__(self):
        self.logger.info("postRun__ : ")
        # release backend-side shared memory array:
        self.shmem__.unlink()

    def c__doWork(self):
        self.logger.info("c__doWork: will change array values from %s to %s",
            self.array__[0,0], 3.0)
        r = randint(1,5)
        self.array__[:,:] = r
        time.sleep(r) # wait random secs
        self.logger.info("c__doWork: ..did that!")
        # send message when ready
        self.send_out__(MessageObject(
            "ready"
        ))

    # Frontend methods
    def doWork(self):
        self.logger.info("readWrite : calling backend")
        self.sendMessageToBack(MessageObject(
            "doWork"
        ))

    def getArray(self):
        return self.array



"""<rtf>
Next we create a convenience class that helps us in managing the main process
systematically.  It is subclassed from ``MainContext``, which is pretty simple
base class:   You only need to (re)define ``__init__()``, ``startProcesses()``,
``startThreads()``, ``close()`` and ``__call__`` methods.

``super().__init__()`` inits the logger and calls first ``startProcesses``
and then ``startThreads`` (i.e. forks before thread):
<rtf>"""
class Manager(MainContext):

    def __init__(self, n_workers = 10):
        self.n_workers = n_workers
        self.timeout = 2.0
        super().__init__()
        
    """<rtf>
    ``startProcesses`` (mandatory) creates and caches processes.

    Here we cache processes into the list
    ``self.cache`` and also into the
    dictionary ``self.process_by_pipe``, where key = ``multiprocessing.Pipe`` and
    value = the running multiprocess.  Reason for this will become obvious
    in method ``__call__`` (see below).

    All pipes we're going to listen, are also cached into ``self.read_pipes``.  That
    list should also always include ``self.aux_pipe_read`` (which is created in
    the base class ``super().__init__()``):
    <rtf>"""
    def startProcesses(self):
        self.logger.debug("startProcesses:")
        self.cache = [] # all multiprocesses
        self.avail_cache = [] # available multiprocesses for work
        self.process_by_pipe = {} # ditto
        self.read_pipes = [self.aux_pipe_read] # pipes / file descriptors to listen to
        for i in range(self.n_workers):
            p = WorkerProcess(name="worker-"+str(i))
            p.ignoreSIGINT()
            pipe = p.getPipe()
            self.cache.append(p)
            self.avail_cache.append(p)
            self.process_by_pipe[pipe] = p
            self.read_pipes.append(pipe)
        self.logger.info("startProcesses: starting multiprocesses")
        # forks!
        for p in self.cache:
            p.start()
        self.logger.info("startProcesses: all multiprocesses running")

    """<rtf>
    One more thing worth noticing: each multiprocesses ``ignoreSIGINT()`` method
    is called: this makes them to ignore ``SIGINT`` as that signal should be
    caught *only* by the main process, and processed accordingly (i.e. when
    receiving ``SIGINT`` main process should shutdown the multiprocesses
    in a clean way).

    ``startThreads`` (mandatory), creates and starts threads (if any):
    <rtf>"""
    def startThreads(self):
        self.logger.debug("startThreads:")
        pass # no threads in this app

    """<rtf>
    ``close`` (mandatory) stops all multiprocesses and threads in parallel:
    <rtf>"""
    def close(self):
        self.logger.debug("close: stopping processes")
        for p in self.cache:
            p.requestStop()
        for p in self.cache:
            p.waitStop()
        self.logger.debug("close: processes stopped")
        self.closed = True

    """<rtf>
    In ``__call__`` (mandatory) we have the main process startup and loop.

    First, we tell three multiprocesses from the cache to do some work
    and then start the execution loop:
    <rtf>"""
    def __call__(self):
        p1 = self.avail_cache.pop(0)
        p2 = self.avail_cache.pop(0)
        p3 = self.avail_cache.pop(0)
        p1.doWork()
        p2.doWork()
        p3.doWork()
        self.loop = True
        self.logger.debug("starting main loop")
        while self.loop:
            try:
                reads, writes, others = safe_select(
                    self.read_pipes, [], [], timeout=self.timeout)
            except KeyboardInterrupt:
                self.logger.warning("SIGTERM or CTRL-C: will exit asap")
                self.loop = False
                continue
            if len(reads) < 1: # reading operation timeout
                self.logger.debug("still alive")
                continue
            for pipe in reads:
                if pipe is self.aux_pipe_read:
                    self.logger.critical("debug mode exit")
                    self.loop = False
                    continue
                else:
                    try:
                        p = self.process_by_pipe[pipe]
                    except KeyError:
                        self.logger.critical("unknown pipe %s", p)
                        continue
                    obj = pipe.recv()
                    self.logger.debug("got message %s", obj)
                    self.handleMessage__(p, obj)
        self.close()
        self.logger.debug("bye!")

    """<rtf>
    So, we're listening *simultaneously* all running multiprocesses.  When
    any of them sends a message, ``safe_select`` is triggered and the message
    is processed by ``handleMessage__``.

    In addition to just the multiprocesses, as in this example, we could add
    in that *select* call the listening of **any file descriptor**, say, tcp sockets,
    unix named pipe and the like so that they would interact with our program
    and the multiprocesses.

    File descriptors can also be instantiated in C++ code (say, like 
    `EventFd <https://elsampsa.github.io/valkka-core/html/classEventFd.html>`_
    in libValkka) and listened here at the Python side.  This creates nice opportunities
    for interfacing i/o devices into this multiprocessing scheme.

    Messages coming from the worker processes are handled like this:
    <rtf>"""
    def handleMessage__(self, p: WorkerProcess, msg: MessageObject):
        # read the sharedmem:
        vals=p.getArray()[0, 0:5]
        self.logger.info("handleMessage__ : subprocess %s returned %s with values %s", 
            p, msg(), vals)
        # return the process back to cache
        self.avail_cache.append(p)
        # take a new process from the cache
        try:
            p_ = self.avail_cache.pop(0)
        except IndexError:
            self.logger.fatal("handleMessage__ : no more processes available!")
        else:
            # tell it to do some work
            p_.doWork()
    """<rtf>

    So, in this particular example, once a worker has done it's calculation, 
    another worker is launched to do another one.

    If you have many different kinds of multiprocesses running under your main
    process, it's a good idea to create dedicated ``MessageObject`` classes
    and ``handleMessage__`` methods for each one of them to keep the code readable.
    <rtf>"""
        

"""<rtf>
Behold: this is your apps main entry point.

When running interactively, just press CTRL-C to exit.
<rtf>"""
def main():
    Manager.formatLogger(logging.DEBUG) # of course in a real app, in some other way
    WorkerProcess.formatLogger(logging.DEBUG) # of course in a real app, in some other way
    manager = Manager(n_workers=5)
    manager()

"""<rtf>
For testing purposes, you can run the manager in background thread, while in the 
main code, you can interact with it in any way you want, say, create files it sees, or simulate the environment
where it is running somehow.

Here the only "interaction" we do, is just to sleep for 10 secs before terminating it.
<rtf>"""
def test():
    Manager.formatLogger(logging.DEBUG)
    WorkerProcess.formatLogger(logging.DEBUG)
    manager = Manager(n_workers=5)
    manager.runAsThread()
    print("running manager for 10 secs")
    time.sleep(10)
    # .. or alternative, interact with the manager somehow
    # as it runs in the background thread
    print("stopping manager")
    manager.stopThread()
    print("bye!")

"""<rtf>
Please do run this file interactively either with command line arg
"main" or "test" to run ``main()`` or ``test()`` above:
<rtf>"""
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("please give 'main' or 'test'")
    elif sys.argv[1] == "main":
        main()
    elif sys.argv[1] == "test":
        test()
    else:
        print("please give 'main' or 'test'")
