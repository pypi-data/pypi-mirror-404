import pyqtgraph as pg
from qtpy.QtCore import QRectF
import logging

logger = logging.getLogger("PRIMEVIEW")


class PrimaryView(pg.ViewBox):
    """A special view box that always reports a non-overlapping screen geometry

    The scope class needs this to work around a pyqtgraph "feature" that tries to line up
    linked x axes for differently sized plots that overlap somewhere within their widths.

    See https://pyqtgraph.readthedocs.io/en/latest/_modules/pyqtgraph/graphicsItems/ViewBox/ViewBox.html
     and look for linkedViewChanged to see how this feature works.
    """

    def __init__(self, *args, **kwargs):
        pg.ViewBox.__init__(self, *args, **kwargs)

    def screenGeometry(self):
        """Create a fake screen geometry that doesn't overlap anything"""
        return QRectF(-1000000, -1000000, 500, 500)
