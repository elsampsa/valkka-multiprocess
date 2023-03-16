Part I: Managing a multiprocess
===============================

In this part we create your first multiprocess and learn how to intercommunicate
and share resources with it.

1. Send message to a forked process
-----------------------------------

:download:`[download code]<ping.py>`

In this example, we call a method in the backend (forked multiprocess) seamlessly
by simply calling a method in the frontend (python main process context).

This is achieved with:

``MessageProcess``'s backend has an internal execution loop that listen's continuously
messages from the frontend.

When a ``MessageObject`` is sent with the command ``ping``, backend looks automagically
for the method ``c__ping`` in the backend and executes it:  execution of ``c__ping`` 
happens in the multiprocessing backend, i.e. in the forked process

.. include:: ping.py_

2. Send message and synchronize
-------------------------------

:download:`[download code]<ping2.py>`

So, we can call backend methods, i.e. tell the forked process *to do something* by simply
calling a frontend method.

Many times we need to synchronize between the main python process and the forked
multiprocess: i.e., the main process needs to wait that the forked process has completed
doing something.

.. include:: ping2.py_

3. Send and receive message
---------------------------

.. _example3:

:download:`[download code]<ping_pong.py>`

Next, we're going to call a backend method and then get some results
from the backend in the form of a message.

.. include:: ping_pong.py_

4. Using shared memory and forked resources
-------------------------------------------

.. _example4:

:download:`[download code]<shm1.py>`

NOTE: for the following examples, you need ``numpy`` installed.

Shared memory is a powerfull tool in multiprocessing: it allows you to
intercommunicate large blocks of data between the main python process (aka
frontend) and the forked multiprocess (aka backend).

Shared memory is used as follows:

Shared memory blocks are created *first in the frontend* and
after that *again in the backend*, using the same unique name.

You can think of the shared memory in the frontend as "server-side" and in the
backend as "client-side".

Shared memory is just memory, i.e. raw bytes, and is typically wrapped into a numpy
array.

In the other examples you learned how to subclass ``MessageProcess``.  Here we also
define the (virtual) methods ``preRun__`` and ``postRun__`` from the ``MessageProcess``
class:  both of them are executed *after the fork*, i.e. in the backend, but outside
``MessageProcess`` s main execution loops:  they are "startup" and "shutdown" functions
in the forked process.

.. include:: shm1.py_

Some additional observations are in place:

Now that you learned how to use ``preRun__``, that would be the typical
place where you would import heavy libraries that utilize threading
(remember: spawning threads should be done *after* fork).

That's also the place where you would instantiate your heavy neural net instances:
no need to fork all that stuff (as it might not like forking at all).  In general,
all libraries and object instances that might be sensitive to forking.

Similary, shutting down / releasing resources should be done in ``postRun__``.

5. Syncing server/client resources
----------------------------------

:download:`[download code]<shm2.py>`

In the previous example we played around with shared memory.  As discussed, there
is "server-side" and "client-side" shared memory.

In multiprocessing programming, the same goes for *any* resource: i.e. the main
python process (again, "frontend") instantiates some resource first and the forked
process ("backend") instantiates it's "client-side" / mirror image of the same resource.

After this, the resource (in this case shared memory) can be used to interchange
data between front- and backend.

Let's demonstrate all this by instantiating shared memory "on-demand":

.. include:: shm2.py_

Part II: Organizing workers
===========================

Time to ramp things up and to fire hundreds or even thousands of multiprocessing workers!

How do you manage and organize something like that?  You are about to find out just that.

A word of warning: if you're trying to "optimize"
and skip the Part I of the tutorial,
don't do that, as you'll miss important concepts and will not understand
what's going on (mainly, the concept of "front" and "backend" methods).

6. Planning it
--------------

Our goal is to create a main process and ``N`` subprocess workers that do some (heavy)
calculation and return results to the main process via a sharedmem numpy array.

When having a main process and workers, we have a *hierarchy* and it is 
always a good idea to 
`write it down as a hierarchical list <https://medium.com/p/d5161dc19052>`_,
so we will do just that:

.. code:: text

    Manager (main process)
        - IN:
            - MessageObject (from SUB WorkerProcess-N)
        - SUB:
            WorkerProcess-1
                - UP: 
                    - MessageObject
                    - method: getArray()
                - IN: 
                    - method doWork()
            WorkerProcess-2
                - UP: 
                    - MessageObject
                    - method: getArray()
                - IN: 
                    - method doWork()
            WorkerProcess-3
                ...
            WorkerProcess-4
                ...
        ...
        
In this notation, there is a ``Manager`` (the main process) that get's input
messages in the form of ``MessageObject`` s from the individual workers which
are ``WorkerProcess-1``, ``WorkerProcess-2``, etc.

Each ``WorkerProcess-N`` is commanded *in* by the upper-level object (``Manager``)
by the method ``doWork`` that tells the ``WorkerProcess`` to launch a calculation.

Information is passed from the lower-level objects (``WorkerProcess``) to *up*per level
(``Manager``) with a ``MessageObject`` and by the method ``getArray()``.

You seldomly need to create any *deeper* nested hierarchies.  If you have to, then
you're probably doing something wrong.


.. _manager_imp:

7. Implementation
-----------------

:download:`[download code]<main1.py>`

.. include:: main1.py_


Part III: Miscellaneous
=======================

Development cleanup
-------------------

When you are developing your multiprocessing program, it might and will crash.  Many times, this has the practical effect
of leaving "dangling" multiprocesses running in your system.  So remember to kill them manually with

.. code:: bash

    killall -9 python3

Or whatever name they might use.

Forgetting this, will have all kinds of weird effects, as the "zombie" processes are still running in the background
and continue meddling with the same shmem arrays and files etc. while you start your program again.

If you're using sharedmem, sometimes you might need to clean up manually memory-mapped files from:

.. code:: bash

    /dev/shm/

Process debug
-------------

Use the `setproctitle python module <https://github.com/dvarrazzo/py-setproctitle>`_ to name your python multiprocesses.  This way you can find them easily using standard
linux monitoring tools, such as htop and smem.

Setting the name of the process should, of course, happen after the multiprocessing fork (i.e. in ``preRun__``).

Install smem and htop:

::

    sudo apt-get install smem htop

After that, run for example the script memwatch.bash in the aux/ directory.  Or just launch htop.  In htop, remember to go to ``setup => display`` options and enable "Hide userland process threads" to make
the output more readable.

Advanced topics
---------------

You learned how to exchange numpy arrays between processes using shared memory.

If you're wondering how to exchange *streaming data* in the same manner,
then the correct way to do that are synchronized sharedmem ringbuffers.
You might want to google that, or use the particular implementation done
in `libValkka <https://elsampsa.github.io/valkka-examples/_build/html/index.html>`_.

We also mentioned the possibility to create data at C++ side (say from specific industrial
equipment, etc.) and then passing it to the python side.  In such case, you would
simply add one more file descriptor (which is managed & set'ted at C++ side) in the
list that select listens to in your :ref:`manager implementation <manager_imp>`.

For C++ / python numpy interfacing, you might want to take a look
into `skeleton <https://github.com/elsampsa/skeleton>`_.  A more serious example will
be provided as well (TBA).

Qt related
----------

Using multiprocesses in the context of Qt (PyQt, PySide2) is straighforward.

If a multiprocess only receive signals, then the "slot" functions where the incoming
signals are connected, correspond to the multiprocessing "frontend" methods.

If the multiprocess should also launch signals into the Qt signal/slot system, I recommend
creating a ``MainContext`` subclass and running it using ``runAsThread`` (see above): in the event loop
of your ``MainContext``, you can then transform the multiprocessing messages into Qt signals.
