.. highlight:: python
.. module:: fontParts.base

Component
*********

Must Override
-------------
.. automethod:: BaseComponent._decompose
.. automethod:: BaseComponent._get_baseGlyph
.. automethod:: BaseComponent._get_identifier
.. automethod:: BaseComponent._get_transformation
.. automethod:: BaseComponent._set_baseGlyph
.. automethod:: BaseComponent._set_index
.. automethod:: BaseComponent._set_transformation

May Override
------------
.. automethod:: BaseComponent._draw
.. automethod:: BaseComponent._drawPoints
.. automethod:: BaseComponent._get_bounds
.. automethod:: BaseComponent._get_index
.. automethod:: BaseComponent._get_offset
.. automethod:: BaseComponent._get_scale
.. automethod:: BaseComponent._init
.. automethod:: BaseComponent._moveBy
.. automethod:: BaseComponent._pointInside
.. automethod:: BaseComponent._rotateBy
.. automethod:: BaseComponent._round
.. automethod:: BaseComponent._scaleBy
.. automethod:: BaseComponent._set_offset
.. automethod:: BaseComponent._set_scale
.. automethod:: BaseComponent._skewBy
.. automethod:: BaseComponent._transformBy
.. automethod:: BaseComponent.copyData