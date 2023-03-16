
.. _article:

Article
=======

*Appeared originally in Medium* `[link] <https://medium.com/@sampsa.riikonen/doing-python-multiprocessing-the-right-way-a54c1880e300>`_

Doing Python Mutiprocessing The Right Way
-----------------------------------------

*Learn how to combine multiprocessing- and threading, and how to organize your multiprocessing classes in the right way*

.. image:: images/stranger.jpeg
   :width: 80 %

*A posix fork has taken place*

Not a day goes by in Medium articles without someone complaining that Python is not the future of machine learning.

For example, things like "I can write a GPU kernel in Julia but not in Python".  However, most of us data scientists/engineers are just dummy *engineers* who use ready-made libraries.
95% of us are not interested in "writing a GPU kernel".

Another complain is about multiprocessing: on many occasions, you need to use multiprocessing instead of multithreading.  People find this cumbersome (especially because of interprocess communication). Also, multiprocessing is very prone to errors if you're not carefull.

Although cumbersome at first sight, multiprocessing does have several advantages.

Keeping processes separated in their own (virtual memory) "cages" can actually help in debugging and avoids confusion.  Once you sort out the intercommunication problem in a systematic way and avoid
some common pitfalls, programming with python multiprocesses becomes a joy.

One frequent error is to mix multithreading and multiprocessing together, creating a crashy/leaky program and then conclude that python sucks.  More on this later.

Some beginners prefer, instead of writing a proper multiprocessing class, to do things like this:

.. code:: python

    p = Process(target=foo)

This obfuscates completely what you are doing with processes and threads (see below).

I have even seen people using ``multiprocessing.Pool`` to spawn single-use-and-dispose multiprocesses at high frequency and then complaining that "python multiprocessing is inefficient".

After this article you should be able to avoid some common pitfalls and write well-structured, efficient and rich python multiprocessing programs.

This is going to be different what you learned in that `python multiprorcessing tutorial <https://docs.python.org/3/library/multiprocessing.html>`_.  
No Managers, Pools or Queues, but more of an under-the-hood approach.

Let's start with the basics of posix fork.

Forking vs. Threading
---------------------

Forking/multiprocessing means that you "spawn" a new process into your system.  It runs in its own (virtual) memory space.  
Imagine that after a fork, a copy of your code is now running "on the other side of the fork".  Think of "Stranger Things".

On the contrary, threading means you are creating a new running instance/thread, toiling around in the same memory space with your current python process.  
They can access the same variables and objects.

Confusing bugs arise when you mix forking and threading together, as creating threads first and then forking, leaves "dangling"/"confused" threads in the spawned multiprocesses.  
Talk about mysterious freezes, segfaults and all that sort of nice things.  But combining forking and threading can be done, if it's done in the right order: fork first and then threading.

This problem is further aggravated by the fact that many libraries which you use in your python programs may start threads sneakily in the background 
(many times, directly in their C source code), while you are completely unaware of it.

Said all that, this is the correct order of doing things:

.. code:: text

    0. import libraries that do not use multithreading

    1. create interprocess communication primitives and shared resources that are 
    shared between multiprocesses (however, not considered in this tutorial)

    2. create interprocess communication primitives and shared resources that 
    are shared with the main process and your current multiprocess

    3. fork (=create multiprocesses)

    4. import libraries that use multithreading

    5. if you use asyncio in your multiprocess, create a new event loop

Let's take a closer look on these steps:

.. code:: text

    0. import libraries that do not use multithreading
        - say, standard libraries

    (1. create interprocess communication primitives and shared resources that are 
    shared between multiprocesses
        - This is the subject of another tutorial)
        
    2. create interprocess communication primitives and shared resources that 
    are shared with the main process and your current multiprocess
        - Multiprocess' intercommunication pipes
        - These will be visible to your current process and 
        also to the code running "on the other-side of the fork"
        
    3. fork (=create multiprocesses)
        - Creates that process running "on the other side"
        - Triggered when you call your multiprocessing.Process classes 
        start() method

    4. import libraries that use multithreading
        - As mentioned, quite many libraries _might_ use multithreading under-the-hood.  
        Even your belowed tensorflow and pytorch.
        - Instantiate objects from those libraries

    5. if you use asyncio, remember to create a new event loop

Next, let's blend these steps with an actual code:

.. code:: python

    # 0. import libraries that do not use multithreading:
    import os, sys, time
    from multiprocessing import Process, Pipe

    class MyProcess(Process):

        def __init__(self):
            super().__init__()
            # 2. create interprocess communication primitives and shared resources used by the current multiprocess:
            self.front_pipe, self.back_pipe = Pipe()

        def run(self):
            # 4. import libraries that use multithreading:
            #from SomeLibrary import Analyzer
            #self.analyzer = Analyzer()
            ...
            # 5. if you use asyncio, remember to create a new event loop
            print("MyProcess: run")
            # 
            # start running an infinite loop
            while True:
                time.sleep(1.0)

    p = MyProcess()
    # 3. fork (=create multiprocesses)
    p.start() # this performs fork & starts p.run() "on the other side" of the fork

Remember that concept of code running "on the other side of the fork"?  That "other side" with demogorgons (and the like) which is isolated 
from our universe is created when you say ``p.start()``.

The stuff that runs in that parallel universe is *defined* in the method ``run()``.

When creating complex multiprocess programs, you will have several multiprocesses (parallel universes) each one with a large codebase.

So, we'll be needing a "mental guideline" to keep our mind in check.  Let's introduce a concept for that purpose.

Our multiprocess class shall have a **frontend** and a **backend** (not to be confused with web development!!)

**Frontend** is the scope of your current running python interpreter.  The normal world.

**Backend** is the part of the code that runs "on the other side of the fork".  
It's a different process in its own memory space and universe.  Frontend needs to communicate with the backend in some way (think again of Stranger Things).

Let's once more emphasize that *everything that's inside/originates from method "run()", runs in the backend*.

From now on, we'll stop talking about demogorgons, parallel realities and stick strictly to **frontend** and **backend**.  Hopefully, you have made the idea by now.

The only things happening at the frontend in the current example are:

.. code::

    p = MyProcess() # code that is executed in MyProcess.__init__
    p.start() # performs the fork

In order to avoid confusion, we need to differentiate between frontend and backend methods.  We need a naming convention.  Let's use this one:

**All backend methods shall have a double-underscore in their name**

Like this:

.. code::

    def run(self):
        # 4. import libraries that use multithreading:
        #from SomeLibrary import Analyzer
        #self.analyzer = Analyzer()
        ...
        # 5. if you use asyncio, remember to create a new event loop
        ...
        # everything started from within run() is at the backend
        while True:
            self.listenFront__()
            time.sleep(1.0)

    def listenFront__(self)
        ...

Before we move on, one extra observation: multiprocesses are not supposed to be single-use-and-dispose.  
You don't want to create and start them at high frequency since creating them has considerable overhead.  
You should try to spawn your multiprocesses only once (or at *very* low frequency).

Let's Ping Pong
---------------

Next, let's demonstrate the frontend/backend scheme in more detail.

We do a classical multiprocessing example: sending a ping to the multiprocess, which then responds with a pong.

The frontend methods are ``ping()`` and ``stop()``.  You call these methods in your main python program (aka frontend).  Under-the-hood, these methods do seamless intercommunication between front- and backend.

Backend methods ``listenFront__()`` and ``ping__()`` run at the backend and they originate from the ``run()`` method.

Here is the code:

.. code:: python

    # 0. import libraries that do not use multithreading:
    import os, sys, time
    from multiprocessing import Process, Pipe

    class MyProcess(Process):

        def __init__(self):
            super().__init__()
            # 2. create interprocess communication primitives and shared resources used by the current multiprocess:
            self.front_pipe, self.back_pipe = Pipe()

        # BACKEND

        def run(self):
            # 4. import libraries that use multithreading:
            #from SomeLibrary import Analyzer
            #self.analyzer = Analyzer()
            ...
            # 5. if you use asyncio, remember to create a new event loop
            print("MyProcess: run")
            self.active = True
            while self.active:
                self.active = self.listenFront__()
            print("bye from multiprocess!")

        def listenFront__(self):
            message = self.back_pipe.recv()
            if message == "stop":
                return False
            elif message == "ping":
                self.ping__()
                return True
            else:
                print("listenFront__ : unknown message", message)
                return True

        def ping__(self):
            print("backend: got ping from frontend")
            self.back_pipe.send("pong")

        # FRONTEND

        def ping(self):
            self.front_pipe.send("ping")
            msg = self.front_pipe.recv()
            print("frontend: got a message from backend:", msg)

        def stop(self):
            self.front_pipe.send("stop")
            self.join()

Here is how you use it in the frontend (i.e. in your main python process):

.. code:: python

    p = MyProcess()
    # 3. fork (=create multiprocesses)
    p.start() # this performs fork & start p.run() "on the other side" of the fork
    print("front: sleepin 5 secs")
    time.sleep(5)
    p.ping()
    print("front: sleepin 5 secs")
    time.sleep(5)
    p.stop()

Note that we use only the frontend methods (start, ping and stop).

Note that we have successfully eliminated the mental load of needing to think about the fork at all.  
At the same time, the code has a clear distinction to and intercommunication with the forked process. We just need to think in terms of the front- and backend and their corresponding methods.

One more pitfall
----------------

Consider the following situations as your codebase grows:

- You have several fairly complex multiprocessing classes
- Several different multiprocesses are called and invoked within your main program

Then your main python code might look like this:

.. code:: python

    import SomeLibrary
    from YourLibrary import MyProcessClass1, MyProcessClass2
    ...
    obj = SomeLibrary.SomeClass()
    ...
    obj.call1()

    p1 = MyProcessClass1()
    p1.start()
    p2 = MyProcessClass2()
    p2.start()
    ...
    obj.call2()
    ...

``SomeLibrary`` is just some library that you need in your code but is not used/related to your multiprocesses in any way.

However, if that ``SomeLibrary`` uses multithreading under-the-hood (without you knowing about it), you have created yourself a big problem.

Still remember what we said earlier?  

**No threads before fork!**

As even just importing a library might silenty starts threads, to be *absolutely* on the safe side, do this instead:

.. code:: python

    from YourLibrary import MyProcessClass1, MyProcessClass2
    p1 = MyProcessClass1()
    p1.start()
    p2 = MyProcessClass2()
    p2.start()

    import SomeLibrary # could start threads?
    ...
    obj = SomeLibrary.SomeClass()
    ...
    obj.call()
    ...
    obj.call()
    ...

i.e. instantiate and start your multiprocesses before anything else.

If the logic in your program requires using multiprocesses "on-demand", consider this:

.. code:: python

    from YourLibrary import MyProcessClass1, MyProcessClass2
    ...
    processes_1 = []
    # start and cache processes
    for i in range(10):
        p1 = MyProcessClass1()
        p1.start()
        processes_1.append(p1)
    ...
    import SomeLibrary # could start threads?
    ...
    obj = SomeLibrary.SomeClass()
    ...
    obj.call()
    ...
    # program needs a multiprocess
    p=processes_1.pop()
    # call some frontend method of the multiprocess
    p.activate()
    p.doSomething()
    ...
    # return multiprocess to the cache
    p.deActivate()
    processes_1.append(p)
    ...
    # at the end of your program
    for p in processes_1:
        p.stop()

i.e., instead of creating and starting multiprocesses in the middle of your program, you create and start them at the very beginning and then cache them for future use.

Some Testing and debugging tips
-------------------------------

For test purposes, you can run your python multiprocessing classes without forking at all, by simply not using "start()" in your test code.  In this case you can call the backend methods directly in your tests/frontend, provided that you have structured your code correctly.

For python refleaks and resulting memory blowup issues you can use the following technique.  Import the setproctitle library with

.. code:: python

    from setproctitle import setproctitle

In your multiprocesses ``run()`` method, include this:

.. code:: python

    setproctitle("Your-Process-Name")

Now your process is tagged with a name, so that you can follow the memory consumption of that single process very easily with standard linux tools, say, with smem and htop 
(in htop, remember to go to ``setup => display options and enable “Hide userland process threads”`` in order to make the output more readable).

Finally
-------

In this tutorial I have given you some guidelines to succeed with your python multiprocessing program and not to fall into some typical pitfalls.

You might still have lot of questions: 

1. How to listen at several multiprocesses simultaneously at my main program? (hint: use the select module)
2. How do I send megabytes of streaming data to a running multiprocess?  I mean images and/or video (can be done perfectly, but not trivial)
3. Can I run asyncio in the back- or frontend or both? (sure)

These are, however, out of the scope of this tutorial.

Let's just mention that in the case (2) that:

- You would _not_ certainly use pipes (they are not for large streaming data)
- Use posix shared memory, mapped into numpy arrays instead
- Those arrays belong to a ring-buffer that is synchronized using posix semaphores across process boundaries
- You need to listen simultaneously to the intercommunication pipe and the ringbuffer.  Posix EventFd is a nice tool for this.

I've done this kind of stuff in a python multimedia framework I've written.  If you're interested, please see `here <https://elsampsa.github.io/valkka-examples/_build/html/index.html>`_

That's the end of the tutorial.  I hope it gave you some food for thought.
