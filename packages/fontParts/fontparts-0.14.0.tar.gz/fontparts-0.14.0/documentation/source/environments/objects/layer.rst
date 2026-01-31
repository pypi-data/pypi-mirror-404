.. highlight:: python
.. module:: fontParts.base

Layer
*****

Must Override
-------------
.. automethod:: BaseLayer._getItem
.. automethod:: BaseLayer._get_color
.. automethod:: BaseLayer._get_lib
.. automethod:: BaseLayer._get_name
.. automethod:: BaseLayer._keys
.. automethod:: BaseLayer._newGlyph
.. automethod:: BaseLayer._removeGlyph
.. automethod:: BaseLayer._set_color
.. automethod:: BaseLayer._set_name

May Override
------------
.. automethod:: BaseLayer._autoUnicodes
.. automethod:: BaseLayer._contains
.. automethod:: BaseLayer._init
.. automethod:: BaseLayer._insertGlyph
.. automethod:: BaseLayer._interpolate
.. automethod:: BaseLayer._isCompatible
.. automethod:: BaseLayer._iter
.. automethod:: BaseLayer._len
.. automethod:: BaseLayer._round