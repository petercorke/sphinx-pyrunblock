Test session
============

.. toctree::
   :hidden:

   other

.. runblock:: pycon
   :session:
   :linenos:

   >>> counter += 5
   >>> x = 41

Some prose between the blocks.

.. runblock:: pycon
   :session:
   :linenos:

   >>> x + 1
   >>> counter

.. runblock:: pycon
   :session: other

   >>> 'x' in globals()

.. runblock:: pycon

   >>> 'x' in globals()
