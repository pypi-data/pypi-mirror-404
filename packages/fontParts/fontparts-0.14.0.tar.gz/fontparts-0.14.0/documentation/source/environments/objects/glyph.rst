.. highlight:: python
.. module:: fontParts.base

Glyph
*****

Must Override
-------------
.. automethod:: BaseGlyph._addImage
.. automethod:: BaseGlyph._autoUnicodes
.. automethod:: BaseGlyph._clearImage
.. automethod:: BaseGlyph._getAnchor
.. automethod:: BaseGlyph._getComponent
.. automethod:: BaseGlyph._getContour
.. automethod:: BaseGlyph._getGuideline
.. automethod:: BaseGlyph._get_height
.. automethod:: BaseGlyph._get_image
.. automethod:: BaseGlyph._get_lib
.. automethod:: BaseGlyph._get_markColor
.. automethod:: BaseGlyph._get_name
.. automethod:: BaseGlyph._get_note
.. automethod:: BaseGlyph._get_unicodes
.. automethod:: BaseGlyph._get_width
.. automethod:: BaseGlyph._lenAnchors
.. automethod:: BaseGlyph._lenComponents
.. automethod:: BaseGlyph._lenContours
.. automethod:: BaseGlyph._lenGuidelines
.. automethod:: BaseGlyph._newLayer
.. automethod:: BaseGlyph._removeAnchor
.. automethod:: BaseGlyph._removeComponent
.. automethod:: BaseGlyph._removeContour
.. automethod:: BaseGlyph._removeGuideline
.. automethod:: BaseGlyph._removeOverlap
.. automethod:: BaseGlyph._set_height
.. automethod:: BaseGlyph._set_markColor
.. automethod:: BaseGlyph._set_name
.. automethod:: BaseGlyph._set_note
.. automethod:: BaseGlyph._set_unicodes
.. automethod:: BaseGlyph._set_width

May Override
------------
.. automethod:: BaseGlyph.__add__
.. automethod:: BaseGlyph.__div__
.. automethod:: BaseGlyph.__mul__
.. automethod:: BaseGlyph.__rmul__
.. automethod:: BaseGlyph.__sub__
.. automethod:: BaseGlyph._appendAnchor
.. automethod:: BaseGlyph._appendComponent
.. automethod:: BaseGlyph._appendContour
.. automethod:: BaseGlyph._appendGlyph
.. automethod:: BaseGlyph._appendGuideline
.. automethod:: BaseGlyph._clear
.. automethod:: BaseGlyph._clearAnchors
.. automethod:: BaseGlyph._clearComponents
.. automethod:: BaseGlyph._clearContours
.. automethod:: BaseGlyph._clearGuidelines
.. automethod:: BaseGlyph._decompose
.. automethod:: BaseGlyph._getLayer
.. automethod:: BaseGlyph._get_anchors
.. automethod:: BaseGlyph._get_bottomMargin
.. automethod:: BaseGlyph._get_bounds
.. automethod:: BaseGlyph._get_components
.. automethod:: BaseGlyph._get_contours
.. automethod:: BaseGlyph._get_guidelines
.. automethod:: BaseGlyph._get_leftMargin
.. automethod:: BaseGlyph._get_rightMargin
.. automethod:: BaseGlyph._get_topMargin
.. automethod:: BaseGlyph._get_unicode
.. automethod:: BaseGlyph._init
.. automethod:: BaseGlyph._interpolate
.. automethod:: BaseGlyph._isCompatible
.. automethod:: BaseGlyph._iterContours
.. automethod:: BaseGlyph._moveBy
.. automethod:: BaseGlyph._pointInside
.. automethod:: BaseGlyph._removeLayer
.. automethod:: BaseGlyph._rotateBy
.. automethod:: BaseGlyph._round
.. automethod:: BaseGlyph._scaleBy
.. automethod:: BaseGlyph._set_bottomMargin
.. automethod:: BaseGlyph._set_leftMargin
.. automethod:: BaseGlyph._set_rightMargin
.. automethod:: BaseGlyph._set_topMargin
.. automethod:: BaseGlyph._set_unicode
.. automethod:: BaseGlyph._skewBy
.. automethod:: BaseGlyph._transformBy