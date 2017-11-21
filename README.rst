Messenger API: Unoffical Facebook Messenger API
===============================================


Installation
------------

Just use pip, as you would with all packages

.. code-block:: bash

    $ pip install messenger-api


Documentation
-------------

There are no docs, I'm sorry.
I'll do them... someday


Examples
--------

A simple example of sending message to the thread

.. code-block:: python

    >>> from messenger_api import Messenger
    >>> msg = Messenger('login', 'password')
    >>> thread = msg.get_thread(485734986798)
    >>> thread
    <messenger_api.Thread.GroupThread: "Random chat name" (485734986798)>
    >>> thread.send_message("TEST MESSAGE!")
    <messenger_api.Message.Message object at 0x000000262414AFD0>

Message sent! :)

Soon you will be able to find some examples in `examples` directory


Contribute
----------

I will appreciate pull requests, but if you want to help, you can just let me know if it stopped working..
I'm not using this library at everyday use and I don't have time to check if Facebook made any changes that break compatibility.
