#!/usr/bin/env python
"""
Plotting and picking of SEG-Y seismic data.
"""
import wx
import logging
from rockfish.gui.menus import PlotSegyFileMenu, PlotSegyPickingMenu
from rockfish.plotting.plotters import SEGYPlotter

logging.basicConfig(level=logging.WARN)

class PlotSegyUI(PlotSegyFileMenu,PlotSegyPickingMenu):
    """
    Main frame for the SEG-Y Plotter.
    """
    def __init__(self, parent, id, title):
        # Setup the frame
        self.PLOT_WINDOW_SIZE = (800, 600)
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition,
                          self.PLOT_WINDOW_SIZE)
        self.CreateStatusBar()
        self.SetStatusText('Ready.')
        # Init. values
        self._lastCursor = None
        # XXX this is now handled in the openers
        # XXX self.splt = SEGYPlotter()
        self.pickdb = None
        self.PLOT_ITEMS = {}
        self.PICK_EVENTS = {}
        # Build menus
        self.MenuBar = wx.MenuBar()
        self.AppendFileMenu()
        self.AppendViewMenu()
        self.AppendPlottingMenu()
        self.AppendPickingMenu()
        self.SetMenuBar(self.MenuBar)
        # Set default plot items
        self.SelectPlotItem('Positive Wiggle Fills')
        self.SelectPlotItem('Picks')
        # Init. plot window and get and plot initial data
        self.InitPlotWindow()
        self.AddToolbar()
        self.OnOpenSegy(None)
        self.Centre()

class PlotSegyApp(wx.App):
    def OnInit(self):
        frame = PlotSegyUI(None, -1, 'SEG-Y Plotter')
        frame.Show(True)
        return True

if __name__ == "__main__":
    app = PlotSegyApp(0)
    app.MainLoop()

