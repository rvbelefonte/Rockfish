"""
Toolbars for Rockfish applications.
"""
import wx
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx, StatusBarWx

class PlotSegyToolbar(object):
    """
    Convienence class for the SEG-Y plotter toolbar.
    """
    def InitToolbar(self):
        self.Toolbar = NavigationToolbar2Wx(self.canvas)
        self.Toolbar.Realize()
        if wx.Platform == '__WXMAC__':
            # Mac platform (OSX 10.3, MacPython) does not seem to cope with
            # having a toolbar in a sizer. This work-around gets the buttons
            # back, but at the expense of having the toolbar at the top
            self.SetToolBar(self.Toolbar)
        else:
            # On Windows platform, default window size is incorrect, so set
            # toolbar width to figure width.
            tw, th = self.toolbar.GetSizeTuple()
            fw, fh = self.canvas.GetSizeTuple()
            # By adding toolbar in sizer, we are able to put it at the bottom
            # of the frame - so appearance is closer to GTK version.
            # As noted above, doesn't work for Mac.
            self.toolbar.SetSize(wx.Size(fw, th))
            self.sizer.Add(self.Toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.Toolbar.update()

    def EnableNavigationTools(self,enable=True):
        self.Toolbar.EnableTool(self.Toolbar._NTB2_PAN,enable)
        self.Toolbar.EnableTool(self.Toolbar._NTB2_ZOOM,enable)

