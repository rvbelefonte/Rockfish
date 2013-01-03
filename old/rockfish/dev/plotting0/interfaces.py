"""
User interfaces for interactive plotting.
"""
from collections import OrderedDict
import os
import wxversion
wxversion.ensureMinimal('2.8')
#import matplotlib
#matplotlib.use('WXAgg')
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx, StatusBarWx
from matplotlib.backends.backend_wx import _load_bitmap 
import matplotlib.pyplot as plt
import wx
from rockfish.segy.segy import readSEGY,SEGYError
from rockfish.plotting.plotsegy import SEGYPlotter, SEGYPlotItems
from rockfish.picking.picksegy import SEGYPickDatabase
from rockfish.utils.curry import Curry
from rockfish.plotting.menus import PlotSegyMenuBuilder
from rockfish.plotting.toolbars import PlotSegyToolbar

class PlotSegyCursors:
    """
    Conveince class for managing cursors.
    """
    POINTER = wx.CURSOR_ARROW
    CROSS_HAIRS = wx.CURSOR_CROSS


class PlotSegyUI(wx.Frame, PlotSegyMenuBuilder, PlotSegyToolbar):
    """
    Main user interface for plotting SEG-Y data.
    """
    
    def __init__(self, *args, **kwargs):
        super(PlotSegyUI, self).__init__(*args, **kwargs)
        self._idMove = None
        self._idClick = None
        self.sgy = None
        self.splt = SEGYPlotter()
        self.cursors = PlotSegyCursors()

        self.pickdb = None
        self.PICK_EVENTS = []
        self.ACTIVE_PICK_EVENT = None
        self.init_ui()

    def init_ui(self):

        # Initialize status bar
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

        # Add menu bar
        self.menubar = self.build_menu_bar()
        self.SetMenuBar(self.menubar)

        # Initialize frame
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.NamedColor("WHITE"))
        self.SetTitle('SEG-Y Plotter')

        # Initalize canvas and plot first data file
        self.init_canvas()

        # Setup sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()
        
        # Add toolbar
        self.init_toolbar()

        # Set the mode to navigation
        self.enable_navigation(True)

    def init_canvas(self):
        """
        Creates a new canvas and asks for data to plot.
        """
        self.fig = plt.figure() 
        self.ax = self.fig.add_subplot(1,1,1)
        self.canvas = FigureCanvas(self, -1, self.fig)
        self.on_file_open_segy(None)
        self.statusbar.SetStatusText('Ready')

    def plot(self,new=False):

        if new:
            self.splt.manager.remove_all(axes=self.ax)

        if self.sgy:
            msg = 'Plotting %i traces from %s...' \
                    % (len(self.sgy.traces),self.sgy.file.name)
            self.statusbar.SetStatusText(msg)

            (negative_fill, positive_fill, wiggle_trace) = self._is_plotting()
            self.splt.plot(self.sgy.traces,axes=self.ax,use_manager=True,
                           negative_fill=negative_fill,positive_fill=positive_fill,
                           wiggle_trace=wiggle_trace)
            self.ax.set_title(os.path.basename(self.sgy.file.name))
            self.statusbar.SetStatusText('Ready')
            self.canvas.draw()

        else:
            return None

    def _is_plotting(self):
        """
        Checks if a plot item is checked in the menu.
        """
        statuses = []
        for item in ['&Negative Wiggle Fills',
                     '&Positive Wiggle Fills',
                     '&Wiggle Traces']:
            statuses.append(self.menu['&View'][item]['menuobject'].IsChecked())
        return statuses

    def on_toggle_enable_picking(self,event):
        """
        Turns picking mode on/off.
        """
        is_picking = self.menu['&Picking']['&Enable Picking']['menuobject'].IsChecked()

        if is_picking:
            self.enable_navigation(False)
            self.statusbar.SetStatusText('Picking enabled, navigation is locked.')
        else:
            self.enable_navigation(True)
            self.statusbar.SetStatusText('Picking disabled, navigation is unlocked.')


    def on_select_pick_event(self,event_name,wxevent):
        """
        Set the active pick event and uncheck all others.
        """
        # set the active pick event and uncheck all others
        self.ACTIVE_PICK_EVENT = event_name
        for event_name in self.PICK_EVENTS:
            if event_name != self.ACTIVE_PICK_EVENT:
                self.menu['&Picking']['Select Event']\
                         [event_name]['menuobject'].Toggle()
        self.statusbar.SetStatusText("Set active pick event to '%s'."\
                                     % self.ACTIVE_PICK_EVENT)

        # Enable picking, if we also have a pick database
        if self.pickdb:
            id = self.menu['&Picking']['&Enable Picking']['id']
            self.menubar.Enable(id,True)

    def add_pick_events(self,new_event_names):
        """
        Adds a new pick event to the pick event list and menu.
        """
        self.PICK_EVENTS.extend(new_event_names)
        Menu = self.menu['&Picking']['Select Event']['menuobject']
        #self.build_pick_events_menu_dict(new_event_names)


    def connect_to_pickdb(self,dbfile):
        """
        Establish a connection a pick database.
        """
        try:
            self.pickdb = SEGYPickDatabase(dbfile)
            self.pick_events = self.pickdb.get_event_names()

            if(self.pick_events):
                self.statusbar.SetStatusText('Connected to: ' + dbfile \
                                             + '. Found event names: ' \
                                             + ', '.join(self.pick_events) )
                #TODO self.UpdateSelectPickingEventMenu(new_events=self.pick_events)
            else:
                self.statusbar.SetStatusText('Connected to: ' + dbfile)
        except:
            self.error(self,'Error connecting to ' + dbfile)

        # Enable select pick event
        id = self.menu['&Picking']['Select Event']['id']
        self.menubar.Enable(id,True)

        # Plot picks according to menu defaults
        #TODO self.plot_picks(None)


    def enable_navigation(self,enable=True):
        self.ax.set_navigate(enable)
        self.enable_navigation_tools(enable)
        if enable:
            self._idMove = self.canvas.mpl_disconnect(self._idMove)
            self._idClick = self.canvas.mpl_disconnect(self._idClick)
            self._idMove = self.canvas.mpl_connect('motion_notify_event',
                                                    self.on_mouse_move_navigation)

    def get_statbar_coordinates(self,event):
        """
        Get coordinate data for the status bar.
        
        :param event: A ``matplotlib`` mouse event.
        :returns : A string with coordinate data.  If outside axis, returns an
            empty string.
        """
        if event.inaxes and self.sgy:
            msg = ': (%f, %f)' %(event.xdata, event.ydata)
            try:
                idx = int(self.splt.xplt2trace(event.xdata))
                tr = self.sgy.traces[idx]
                ensemble = self.splt.get_header_value(tr.header,'ensemble_number')
                trace = self.splt.get_header_value(tr.header,
                                              'trace_number_within_the_ensemble')
                offset = self.splt.get_header_value(tr.header,\
                            'distance_from_center_of_the_source_point_to_'\
                            + 'the_center_of_the_receiver_group')
                
                msg += ', Ensemble=%i, Trace in ensemble=%i, Offset=%f %s'\
                        %(ensemble,trace,offset,self.splt.PARAM['distance_units'])

            except ValueError:
                # Trace is outside the data range, don't show the trace no.
                pass
            return msg
        else:
            return ""

    def on_mouse_move_navigation(self, event):
        """
        Event handler for a mouse move when navigation is enabled.
        """
        msg = 'Navigate' + self.get_statbar_coordinates(event) 
        self.statusbar.SetStatusText(msg)

    def on_mouse_move_picking(self, event):
        """
        Event handler for a mouse move when picking is enabled.

        Based on: matplotlib/backend_bases.NavigationToolbar2.mouse_move
        """
        if not event.inaxes:
            if self._lastCursor != self.cursors.POINTER:
                self.change_cursor(self.cursors.POINTER)
                self._lastCursor = self.cursors.POINTER
            msg = 'Picking '
        else:
            if self._lastCursor != self.cursors.CROSS_HAIRS:
                self.change_cursor(self.cursors.CROSS_HAIRS)
                self._lastCursor = self.cursors.CROSS_HAIRS
            self._lastCursor = self.cursors.CROSS_HAIRS
            msg = 'Picking: ' + self.get_statbar_coordinates(event) 
        self.statusbar.SetStatusText(msg)

    def change_cursor(self, cursor):
        """
        Set the current cursor to one of the :class:`Cursors`
        enums values
        """
        self.canvas.SetCursor(wx.StockCursor(cursor))


class App(wx.App):
    def OnInit(self):
        frame = PlotSegyUI(None, -1)
        frame.Centre()
        frame.Show(True)
        self.SetTopWindow(frame)

        return True

if __name__ == '__main__':
    app = App(0)
    app.MainLoop()

