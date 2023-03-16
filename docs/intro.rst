

.. Welcome!
.. As you can see, these are comments: they start with two dots and a space
.. Sphinx is very sensitive to spaces, empty lines, etc. so it can sometimes be frustrating
.. Two dots and a space are also used for special tagging, inclusion, etc.  Like here, where we are creating an internal link:

.. _intro:

.. So, lets start writing the documentation
.. Title fonts are written like this:

Intro
=====

*Doing Python Multiprocessing The Right Way*

Beware - doing multiprocessing in Python has certain pitfalls that can result in poor performance
and leaky/crashy programs.

When building a serious application, you should *never* do this:

.. code:: python

    p = Process(target=foo)

Writing code like that will make your program susceptible to nasty bugs (combining thread and fork, etc.)
and also - if it is anything beyond a simple machine learning hack - make it poorly organized and a headache
to maintain and understand.

For more details, I recommend that you read my original 
`Medium article <https://medium.com/@sampsa.riikonen/doing-python-multiprocessing-the-right-way-a54c1880e300>`_
on the subject.  If you don't have Medium subscription, the same article
is included :ref:`in this documentation <article>`.

Once you've read it, you will:

- Understand the dangers of mixing multiprocessing (forking) and threading
- Get the grips on writing `a proper multiprocessing class <https://docs.python.org/3/library/multiprocessing.html#the-process-class>`_
- Understand the important concepts of **multiprocessing front- and backend**.

In short, "multiprocessing frontend" is the context of the main python process, while "multiprocessing backend" is the context of the
forked multiprocess that toils around in it's own virtual memory space.  

This python module provides classes that extend the standard `python multiprocessing class <https://docs.python.org/3/library/multiprocessing.html>`_, introducing clearly 
separated multiprocessing front- and backend methods and a seamless intercommunication between them.

I also discuss how you can orchestrate the main process with a bunch of multiprocesses and intercommunication between them.
You can also throw into this mix the i/o waiting for devices and tcp ports.

This is a typical problem that arises when writing **machine learning / ai solutions for industrial systems**: i/o waits needs to be combined
with multiprocesses that do parallel heavy lifting / analysis on data obtained from i/o devices (cameras, triggers, etc.)

Using yet another example module I provide in here (TBA), you can read i/o devices at the cpp side and communicate the results to python
side, where you can then do all the programming logic and take advantage of multiprocessing.

Exciting, right..!? 

Your next step is to read the :ref:`tutorial <tutorial>`





















