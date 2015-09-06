import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

from PRmm.io import BasecallsUnavailable

class Region(object):
    """
    A region, in *frame* coordinates
    """
    # These agree with regions enum defined for bas/bax files
    ADAPTER_REGION = 0
    INSERT_REGION  = 1
    HQ_REGION      = 2

    # This is new
    ALIGNMENT_REGION = 101

    def __init__(self, kind, startFrame, endFrame, name):
        self.kind       = kind
        self.startFrame = startFrame
        self.endFrame   = endFrame
        self.name       = name


class RegionsOverlayItem(pg.GraphicsObject):
    """
    Region display
    """
    def __init__(self, regions):
        pg.GraphicsObject.__init__(self)
        self.generatePicture()

    def generatePicture(self):
        pass


class PulsesOverlayItem(pg.GraphicsObject):
    """
    The pulses!
    """
    def __init__(self, plsZmw, plot):
        # The `plot` argument is just used to determine the
        # effective visible area.  Not sure if there is a better way!
        pg.GraphicsObject.__init__(self)
        self.plsZmw = plsZmw
        self.plot = plot
        self.generatePicture()
        self._textItems = []

    def generatePicture(self):
        # Precompute a QPicture object
        allPulses = self.plsZmw.pulses()
        startFrame    = allPulses.startFrame()
        widthInFrames = allPulses.widthInFrames()
        channel       = allPulses.channel()
        base          = allPulses.channelBases()

        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pens  = [ pg.mkPen((i, 4), width=2) for i in xrange(4) ]
        y = -5
        for i in xrange(len(channel)):
            c     = channel[i]
            start = startFrame[i]
            width = widthInFrames[i]
            end = start + width

            p.setPen(pens[c])
            p.drawLine(QtCore.QPointF(start, y), QtCore.QPointF(start+width, y))

    def pulsesToLabel(self):
        """
        Returns None, or a ZmwPulses if we are focused on a small enough window for labeling
        """
        viewRange = self.plot.viewRange()[0]
        if viewRange[1] - viewRange[0] >= 500:
            return None
        pulsesToDraw = self.plsZmw.pulsesByFrameInterval(viewRange[0], viewRange[1])
        if len(pulsesToDraw) > 20:
            return None
        else:
            return pulsesToDraw

    def labelPulses(self, pulsesToLabel):
        # Remove the old labels from the scene
        for ti in self._textItems:
            ti.scene().removeItem(ti)
        self._textItems = []

        if pulsesToLabel is None: return

        start      = pulsesToLabel.startFrame()
        width      = pulsesToLabel.widthInFrames()
        channel    = pulsesToLabel.channel()
        base       = pulsesToLabel.channelBases()
        mid        = start + width / 2.0
        try:
            isBase     = pulsesToLabel.isBase()
        except BasecallsUnavailable:
            isBase = np.ones_like(channel, dtype=bool)

        y = self.plot.pulseLabelY
        for i in xrange(len(base)):
            pulseLabel = base[i] if isBase[i] else "-"
            ti = pg.TextItem(pulseLabel)
            ti.setParentItem(self)
            ti.setPos(mid[i], y)
            self._textItems.append(ti)

    def paint(self, p, *args):
        # Draw the pulse blips
        p.drawPicture(0, 0, self.picture)
        # Draw pulse labels if the focus is small enough (< 500 frames)
        self.labelPulses(self.pulsesToLabel())

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())