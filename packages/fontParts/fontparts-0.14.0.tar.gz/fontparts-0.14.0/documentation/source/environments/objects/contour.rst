.. highlight:: python
.. module:: fontParts.base

Contour
*******

Must Override
-------------
.. automethod:: BaseContour._getPoint
.. automethod:: BaseContour._get_clockwise
.. automethod:: BaseContour._get_identifier
.. automethod:: BaseContour._insertPoint
.. automethod:: BaseContour._lenPoints
.. automethod:: BaseContour._removePoint
.. automethod:: BaseContour._set_index

May Override
------------
.. automethod:: BaseContour._appendBPoint
.. automethod:: BaseContour._appendSegment
.. automethod:: BaseContour._autoStartSegment
.. automethod:: BaseContour._draw
.. automethod:: BaseContour._drawPoints
.. automethod:: BaseContour._get_bounds
.. automethod:: BaseContour._get_index
.. automethod:: BaseContour._get_points
.. automethod:: BaseContour._get_segments
.. automethod:: BaseContour._init
.. automethod:: BaseContour._insertBPoint
.. automethod:: BaseContour._insertSegment
.. automethod:: BaseContour._len__segments
.. automethod:: BaseContour._moveBy
.. automethod:: BaseContour._pointInside
.. automethod:: BaseContour._removeSegment
.. automethod:: BaseContour._reverse
.. automethod:: BaseContour._rotateBy
.. automethod:: BaseContour._round
.. automethod:: BaseContour._scaleBy
.. automethod:: BaseContour._setStartSegment
.. automethod:: BaseContour._set_clockwise
.. automethod:: BaseContour._skewBy
.. automethod:: BaseContour._transformBy