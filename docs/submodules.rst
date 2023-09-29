   
API documentation
=================

MessageObject
-------------

.. autoclass:: valkka.multiprocess.base.MessageObject

MessageProcess
--------------

The ``MessageProcess`` class implements a seamless intercommunication between the
forked multiprocess (aka "backend") and the main/current python process (aka "frontend").

Like this:

.. code:: python

    from valkka.multiprocess import MessageProcess, MessageObject

    class MyProcess(MessageProcess):
        
        def c__myStuff(self, parameter=None):
            print("Regards from other side of the fork!  Got parameter", parameter)

        def myStuff(self, parameter=None):
            self.sendMessageToBack(MessageObject(
                "myStuff", parameter=parameter))

    p = MyProcess(name="my-process")
    pipe = p.getPipe() # returns a multiprocessing.Pipe instance
    # ..that can be used as-is with select.select
    p.start()
    p.myStuff(parameter="gotcha!")
    ...
    p.stop()

In ``MessageProcess``'s ``run`` method, there is an event loop that listens
to ``MessageObject`` s, which are mapped to correct methods in the backend
(to method ``c__myStuff`` in this case).

Within ``MessageProcess``, you can use logger ``self.logger`` that
has the name ``classname.name``, in this example
case it is ``MyProcess.my-process``

.. autoclass:: valkka.multiprocess.base.MessageProcess
   :members: preRun__, postRun__, run, readPipes__, send_out__, c__ping, ignoreSIGINT,
             getPipe, sendMessageToBack, go, requestStop, waitStop, stop, sendPing,
             formatLogger

.. _asyncio:

AsyncBackMessageProcess
-----------------------

*Warning: understanding of asyncio required*

Identical to ``MessageProcess`` class, but now the forked process (aka backend) runs
asyncio:

.. code:: python

    from valkka.multiprocess import AsyncBackMessageProcess, MessageObject, exclog

    class MyProcess(AsyncBackMessageProcess):
        
        async def c__myStuff(self, parameter=None):
            # NOTE: this is a coroutine
            # so, here call other coroutine with await
            # send asyncio tasks, etc. etc.
            print("Regards from other side of the fork!  Got parameter", parameter)

        def myStuff(self, parameter=None):
            self.sendMessageToBack(MessageObject(
                "myStuff", parameter=parameter))

    p = MyProcess(name="my-process")
    pipe = p.getPipe() # returns a custom Duplex instance
    fd=pipe.getReadFd() # this can be used with select.select
    p.start()
    p.myStuff(parameter="gotcha!")
    ...
    p.stop()

The whole idea of using asyncio python, is to solve the problem of simultaneous, blocking i/o operations.  In the above example, we don't
yet achieve that i/o concurrency: if you would call ``myStuff`` consecutively twice, the asyncio backend will await the completion of ``c__myStuff`` before
executing and awaiting it for the second time.

To achieve non-blocking behaviour for i/o operations, you should use (background) tasks instead.  Here is one way to do that:

.. code:: python

    class MyProcess(AsyncBackMessageProcess):

        @exclog
        async def myStuff__(self, parameter=None):
            print("Regards from other side of the fork!  Got parameter", parameter)
            # DO SOME BLOCKING IO HERE
            print("Did that blocking io wait")

        async def c__myStuff(self, parameter=None):
            asyncio.get_event_loop().create_task(self.myStuff__(parameter=parameter))
            
        def myStuff(self, parameter=None):
            self.sendMessageToBack(MessageObject(
                "myStuff", parameter=parameter))

For a handy way to achieve asyncio concurrency (without ``asyncio.gather`` etc. techniques), please see `TaskThread <https://elsampsa.github.io/task_thread/_build/html/index.html>`_.

Finally, please, note the small "glitch" in the API when getting the file descriptor for reading: you need to call ``getReadFd`` to get the file descriptor.

.. autoclass:: valkka.multiprocess.base.AsyncBackMessageProcess
   :members: asyncPre__, asyncPost__, send_out__, c__ping,
             getPipe, getReadFd, getWriteFd


MainContext
-----------

.. autoclass:: valkka.multiprocess.base.MainContext
   :members: formatLogger, startProcesses, startThreads, close, __call__, 
             runAsThread, stopThread


EventGroup
----------

With this class you can:

- reserve and release (i.e. recycle) events
- access a certain reserved event, based on it's index

Motivation for these are:

When doing multiprocessing, the synchronization primitives (events in this case), must be reserved *before* forking - *after* forking you can't
create an event and then expect the forked process to see it.

However if you have created an event *before* forking, then the forked multiprocesses *can* see the event and it's state.  For this reason
we need to create it before anything else and then reuse it (instead of creating a new one) on-demand.

Furthermore, when communicating between the multiprocessing front- and backends, we can't expect that an Event object would be serialized correctly.  However,
as events were created and cached before forking, we can send the index/address of the event (just a simple integer) accross multiprocessing front-
and backend: now both front- and backend know what event in question we are using to synchronize.

An example:

::

    ...
    from multiprocessing import Event

    class YourProcess(MessageProcess):

        def __init__(self, name):
            ...
            self.event_group = EventGroup(10, Event) # create 10 multiprocessing.Event instances
            ...

        # multiprocessing backend methods

        def c__ping(self, event_index=None):
            # do something, then trigger the event to indicate that something's done
            self.event_group.set(event_index)

        # multiprocessing frontend methods

        def ping(self):
            i, event = self.event_group.reserve()
            self.sendMessageToBack(MessageObject(
                "ping",
                event_index = i
            ))
            event.wait() # wait until c__ping sets the event
            self.event_group.release(event)



.. autoclass:: valkka.multiprocess.sync.EventGroup
   :members: set, reserve, release, release_ind, fromIndex, asIndex


SyncIndex
---------

A context manager that reserves an event from EventGroup, wait's until it has been set'ted and finally
returns the event back to EventGroup.

An example:

::

    ...
    from multiprocessing import Event

    class YourProcess(MessageProcess):

        def __init__(self, name):
            ...
            self.event_group = EventGroup(10, Event) # create 10 multiprocessing.Event instances
            ...

        # multiprocessing backend methods

        def c__ping(self, event_index=None):
            # do something, then trigger the event to indicate that something's done
            self.event_group.set(event_index)

        # multiprocessing frontend methods

        def ping(self):
            with SyncIndex(self.event_group) as i:
                self.sendMessageToBack(MessageObject(
                    "ping",
                    event_index = i
                ))
                # SyncIndex context manager:
                # - reserves event from self.event_group
                # - waits until event has been set'ted
                # - releases event back to self.event_group

.. autoclass:: valkka.multiprocess.sync.SyncIndex

Other
-----

.. autofunction:: valkka.multiprocess.base.safe_select
