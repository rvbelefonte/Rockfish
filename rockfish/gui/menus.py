"""
Menus for the Rockfish applications.

Individual menus are divided into separate classes to make it easier to pick and
choose what menus to include in applications.
"""
import os
import logging
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import os
import matplotlib.pyplot as plt
import wx
from rockfish.segy.segy import readSEGY,SEGYError
from rockfish.picking.database import PickDatabaseConnection
from rockfish.plotting.plotters import SEGYPlotManager, SEGYPlotter,\
        SEGYPickPlotter
from rockfish.gui.dialogs import PlotSegyEventDialogs
from rockfish.gui.toolbars import PlotSegyToolbar
from rockfish.gui.cursors import PlotSegyCursors

class PlotSegyEditMenu(wx.Frame,PlotSegyEventDialogs):
    """
    Edit menu for the SEG-Y Plotter.
    """
    def AppendEditMenu(self):
        self.Edit = wx.Menu()
        self.MenuBar.Append(self.Edit,'&Edit')

class PlotSegyViewMenu(wx.Frame,PlotSegyEventDialogs,PlotSegyToolbar):
    """
    View menu for the SEG-Y Plotter.
    """
    def AppendViewMenu(self):
        self.View = wx.Menu()

        # X Enable picking
        self.ID_SHOW_TOOLBAR = wx.NewId()
        self.ShowToolbar = wx.MenuItem(self.View,self.ID_SHOW_TOOLBAR,
                                         '&Show Toolbar',
                                         'Show/hide the toolbar.',
                                         kind=wx.ITEM_CHECK)
        self.View.AppendItem(self.ShowToolbar)
        self.Bind(wx.EVT_MENU, self.OnShowToolbar, id=self.ID_SHOW_TOOLBAR)
        self.MenuBar.Append(self.View,'&View')

    def AddToolbar(self):
        self.InitToolbar()
        self.View.Check(self.ID_SHOW_TOOLBAR, True)

    def OnShowToolbar(self,event):
        self.ToggleToolbar()

    def ToggleToolbar(self):
        if self.View.IsChecked(self.ID_SHOW_TOOLBAR):
            self.Toolbar.Show()
        else:
            self.Toolbar.Hide()

class PlotSegyPlottingMenu(PlotSegyViewMenu):
    """
    Plotting menu for the SEG-Y Plotter.
    """
    def InitPlotWindow(self):
        self.SetSize(self.PLOT_WINDOW_SIZE)
        self.SetBackgroundColour(wx.NamedColor("WHITE"))
        self.fig = plt.figure() 
        self.ax = self.fig.add_subplot(1,1,1)
        self.canvas = FigureCanvas(self, -1, self.fig)
        self._idMove = None
        self._idClick = None
        self.ConnectToMouseEvents()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

    def ConnectToMouseEvents(self):
        self._idMove = self.canvas.mpl_disconnect(self._idMove)
        self._idClick = self.canvas.mpl_disconnect(self._idClick)
        self._idMove = self.canvas.mpl_connect('motion_notify_event',
                                               self.OnMouseMove)
        self._idClick = None

    def AppendPlottingMenu(self):
        self.Plotting = wx.Menu()
        # Update Layers
        self.ID_UPDATE_LAYERS = wx.NewId()
        self.UpdateLayers = wx.MenuItem(self.Plotting, self.ID_UPDATE_LAYERS,
                                        '&Update Layers',
                                        'Update plot items.')
        self.Plotting.AppendItem(self.UpdateLayers)
        self.Bind(wx.EVT_MENU, self.OnUpdateLayers,
                  id=self.ID_UPDATE_LAYERS)
        # Refresh
        self.ID_REFRESH = wx.NewId()
        self.Refresh = wx.MenuItem(self.Plotting, self.ID_REFRESH,
                                        '&Refresh',
                                        'Replot everything.')
        self.Plotting.AppendItem(self.Refresh)
        self.Bind(wx.EVT_MENU, self.OnRefresh,
                  id=self.ID_REFRESH)

        #-------------------------------
        self.Plotting.AppendSeparator()

        # Plot Parameters
        self.ID_PLOT_PARAMETERS = wx.NewId()
        self.PlotParameters = wx.MenuItem(self.Plotting,
                                          self.ID_PLOT_PARAMETERS,
                                          '&Plot Parameters...',
                                          'Edit plot parameters.')
        self.Plotting.AppendItem(self.PlotParameters)
        self.Bind(wx.EVT_MENU, self.OnPlotParameters, 
                  id=self.ID_PLOT_PARAMETERS)
        # Plot Items >
        self.ID_PLOT_ITEMS = wx.NewId()
        self.PlotItems = wx.Menu()
        for plot_item in ['Positive Wiggle Fills',
                          'Negative Wiggle Fills',
                          'Wiggle Traces',
                          'Picks']:
            self.AppendPlotItem(plot_item)
        self.Plotting.AppendMenu(self.ID_PLOT_ITEMS, '&Plot Items',
                                 self.PlotItems)
        self.EnablePlotItem('Picks',False)
        if len(self.PLOT_ITEMS) == 0:
            self.Plotting.Enable(self.ID_PLOT_ITEMS, False)
        self.MenuBar.Append(self.Plotting,'&Plotting')

    def OnUpdateLayers(self, event):
        self.Plot()
    
    def OnRefresh(self, event):
        self.ax.clear()
        # XXX this should be handled by force_new, but it does not seem to be
        # working
        self.splt.ACTIVE_LINES = {}
        self.splt.INACTIVE_LINES = {}
        self.splt.ACTIVE_PATCHES = {}
        self.splt.INACTIVE_PATCHES = {}
        self.Plot(force_new=True)

    def Plot(self, force_new=False):
        if self.segy:
            msg = 'Plotting %i traces from %s...' \
                    % (len(self.segy.traces),self.segy.file.name)
            self.SetStatusText(msg)
            # Plot data
            negative_fills = self.IsPlotItemActive('Negative Wiggle Fills')
            positive_fills = self.IsPlotItemActive('Positive Wiggle Fills')
            wiggle_traces = self.IsPlotItemActive('Wiggle Traces')
            msg = 'Showing wiggle trace items? neg (%s), pos (%s)'\
                + ', wig (%s)'
            logging.debug(msg, negative_fills, positive_fills, wiggle_traces)
            self.splt.plot_wiggles(force_new=force_new, 
                negative_fills=negative_fills,positive_fills=positive_fills,
                wiggle_traces=wiggle_traces)
            # Plot picks
            picks = self.IsPlotItemActive('Picks') 
            logging.debug('Showing picks? %s', picks)
            if picks and self.pickdb is not None:
                self.PlotPicks(force_new=force_new)
            self.ax.set_title(os.path.basename(self.segy.file.name))
            self.canvas.draw()
            self.SetStatusText('Ready')

    def PlotPicks(self, force_new=False, event=None):
        if event is None:
            # plot all available events
            self.splt.plot_picks(force_new=force_new)
        else:
            self.splt.plot_picks(force_new=force_new, event=event)

    def IsPlotItemChecked(self,plot_item):
        return self.PlotItems.IsChecked(self.PLOT_ITEMS[plot_item])
    
    def IsPlotItemEnabled(self,plot_item):
        return self.PlotItems.IsEnabled(self.PLOT_ITEMS[plot_item])

    def IsPlotItemActive(self,plot_item):
        if self.IsPlotItemChecked(plot_item)\
           and self.IsPlotItemEnabled(plot_item): 
            return True
        else:
            return False

    def TogglePlotItem(self,plot_item):
        self.PlotItems.Toggle(self.PLOT_ITEMS[plot_item])

    def SelectPlotItem(self,plot_item):
        self.PlotItems.Check(self.PLOT_ITEMS[plot_item], True)
        
    def OnPlotParameters(self,event):
        # TODO
        self.OnTodo(None)

    def OnMouseMove(self,event):
        self.SetStatusText('Navigate' + self.GetStatusBarCoordinates(event))

    def GetStatusBarCoordinates(self, event):
        if event.inaxes and self.segy:
            msg = ': (%f, %f)' %(event.xdata, event.ydata)
            try:
                idx = int(self.splt.abscissa2trace(event.xdata))
                tr = self.segy.traces[idx]
                ensemble = self.splt.get_header_value(tr.header, 'ensemble')
                trace = self.splt.get_header_value(tr.header, 'trace')
                offset = self.splt.get_header_value(tr.header, 'offset')
                msg += ', Ensemble=%i, Trace in ensemble=%i, Offset=%f %s'\
                    %(ensemble,trace,offset,self.splt.DISTANCE_UNIT)

            except ValueError:
                # Trace is outside the data range.
                pass
            return msg
        else:
            return ""

    def AppendPlotItem(self,plot_item):
        self.Plotting.Enable(self.ID_PLOT_ITEMS, True)
        if plot_item not in self.PLOT_ITEMS:
            self.PLOT_ITEMS[plot_item] = wx.NewId()
            self.PlotItems.Append(self.PLOT_ITEMS[plot_item],
                                        plot_item,
                                        kind=wx.ITEM_CHECK)

    def EnablePlotItem(self, plot_item, enable=True):
        self.PlotItems.Enable(self.PLOT_ITEMS[plot_item], enable)

class PlotSegyPickingMenu(PlotSegyPlottingMenu,PlotSegyCursors):
    """
    Picking menu for the SEG-Y Plotter.
    """
    def AppendPickingMenu(self):
        self.Picking = wx.Menu()

        # X Enable picking
        self.ID_ENABLE_PICKING = wx.NewId()
        self.EnablePicking = wx.MenuItem(self.Picking,self.ID_ENABLE_PICKING,
                                         '&Enable Picking',
                                         'Turn picking mode on/off.',
                                         kind=wx.ITEM_CHECK)
        self.Picking.AppendItem(self.EnablePicking)
        self.Bind(wx.EVT_MENU, self.OnEnablePicking, id=self.ID_ENABLE_PICKING)
        self.Picking.Enable(self.ID_ENABLE_PICKING, False)
        
        #-------------------------------
        self.Picking.AppendSeparator()

        # Connect to Database >
        self.ID_CONNECT_TO_PICK_DATABASE = wx.NewId()
        self.ConnectToPickDatabase = wx.Menu()

        # > Connect to Existing Database...
        self.ID_CONNECT_TO_EXISTING_PICK_DATABASE = wx.NewId()
        self.ConnectToExistingPickDatabase = wx.MenuItem(
            self.ConnectToPickDatabase,
            self.ID_CONNECT_TO_EXISTING_PICK_DATABASE,
            'Connect to Existing Database...',
            'Connect to an existing pick database.')
        self.ConnectToPickDatabase.AppendItem(
            self.ConnectToExistingPickDatabase)
        self.Bind(wx.EVT_MENU, self.OnConnectExistingPickDatabase, 
                  id=self.ID_CONNECT_TO_EXISTING_PICK_DATABASE)
        # > Connect to New Database...
        self.ID_CONNECT_TO_NEW_PICK_DATABASE = wx.NewId()
        self.ConnectToNewPickDatabase = wx.MenuItem(self.ConnectToPickDatabase,
                                        self.ID_CONNECT_TO_NEW_PICK_DATABASE,
                                        'Connect to New Database...',
                                        'Create a new pick database.')
        self.ConnectToPickDatabase.AppendItem(self.ConnectToNewPickDatabase)
        self.Bind(wx.EVT_MENU, self.OnConnectNewPickDatabase, 
                  id=self.ID_CONNECT_TO_NEW_PICK_DATABASE)
        
        self.Picking.AppendMenu(self.ID_CONNECT_TO_PICK_DATABASE,
                                '&Connect to Pick Database',
                                self.ConnectToPickDatabase)

        #-------------------------------
        self.Picking.AppendSeparator()

        # Add Pick Event...
        self.ID_ADD_PICK_EVENT = wx.NewId()
        self.AddPickEvent = wx.MenuItem(self.Picking, 
                                        self.ID_ADD_PICK_EVENT,
                                        '&Add Pick Event...',
                                        'Add a pick event to the event list.')
        self.Picking.AppendItem(self.AddPickEvent)
        self.Bind(wx.EVT_MENU, self.OnAddPickEvent, id=self.ID_ADD_PICK_EVENT)
        self.Picking.Enable(self.ID_ADD_PICK_EVENT, False)

        # Select Pick Event > 
        self.ID_SELECT_PICK_EVENT = wx.NewId()
        self.SelectPickEvent = wx.Menu()

        for pick_event_name in self.PICK_EVENTS:
            self.AppendSelectPickEvent(pick_event_name)
        self.Picking.AppendMenu(self.ID_SELECT_PICK_EVENT, '&Select Event',
                           self.SelectPickEvent)
        if len(self.PICK_EVENTS) == 0:
            self.Picking.Enable(self.ID_SELECT_PICK_EVENT, False)

        self.MenuBar.Append(self.Picking,'&Picking')

    def AppendSelectPickEvent(self,pick_event_name):
        self.Picking.Enable(self.ID_SELECT_PICK_EVENT,True)
        if pick_event_name not in self.PICK_EVENTS:
            self.PICK_EVENTS[pick_event_name] = wx.NewId()
            self.SelectPickEvent.Append(self.PICK_EVENTS[pick_event_name],
                                  pick_event_name,
                                  kind=wx.ITEM_RADIO)
        else:
            self.ErrorDialog(self,"Pick event name '%s' already exists." %
                       pick_event_name)

    def OnAddPickEvent(self,event):
        msg = 'New pick event name:'
        new_pick_event_name = self.GetTextDialog(self, msg, 
                                                 caption='Add Pick Event')
        self.AppendSelectPickEvent(new_pick_event_name)
        self.SetStatusText("Added pick event '%s'." % new_pick_event_name)

    def GetActivePickEvent(self):
        for pick_event_name in self.PICK_EVENTS:
            _id = self.PICK_EVENTS[pick_event_name]
            if self.SelectPickEvent.IsChecked(_id):
                return pick_event_name
        return None

    def OnConnectExistingPickDatabase(self,event):
        self.ConnectPickDatabase(new=False)
    
    def OnConnectNewPickDatabase(self,event):
        self.ConnectPickDatabase(new=True)

    def ConnectPickDatabase(self,new=False):
        dbfile = self.GetSQLiteFileDialog(new=new)
        try:
            self.pickdb = PickDatabaseConnection(dbfile)
        except Exception, e:
            msg = "Could not connect to '%s'." % dbfile
            msg += "\n\nError is %s: %s" %(Exception.__name__, e)
            self.ErrorDialog(self, msg)
            return
        # Build a new plotter for plotting data and picks
        self.splt = SEGYPickPlotter(self.ax, self.segy, self.pickdb)
        if len(self.pickdb.events) > 0:
            self.SetStatusText('Connected to: ' + dbfile \
                                + '. Found event names: ' \
                                + ', '.join(self.pickdb.events))
            # add existing events from the database to the menu
            for pick_event_name in self.pickdb.events:
                self.AppendSelectPickEvent(pick_event_name)
        else:
            self.SetStatusText("Connected to empty database: %s" % dbfile)
        self.Picking.Enable(self.ID_ADD_PICK_EVENT, True)
        self.Picking.Enable(self.ID_ENABLE_PICKING, True)
        self.EnablePlotItem('Picks',True)
        self.OnRefresh(None)

    def OnEnablePicking(self, event):
        self.TogglePicking()

    def TogglePicking(self):
        if self.Picking.IsChecked(self.ID_ENABLE_PICKING):
            self.ConnectToMouseEventsPicking()
            self.EnableNavigationTools(False)
            self.SelectPlotItem('Picks')
            #XXX this resets plot axes! 
            #XXX self.OnUpdateLayers(None)
            self.SetStatusText('Picking is enabled, navigation is locked.')
        else:
            self.ConnectToMouseEvents()
            self.EnableNavigationTools(True)
            self.SetStatusText('Picking is disabled, navigation is unlocked.')

    def ConnectToMouseEventsPicking(self):
        self._idMove = self.canvas.mpl_disconnect(self._idMove)
        self._idClick = self.canvas.mpl_disconnect(self._idClick)
        self._idMove = self.canvas.mpl_connect('motion_notify_event',
                                               self.OnMouseMovePicking)
        self._idClick = self.canvas.mpl_connect('button_press_event',
                                                self.OnClickPicking)

    def ChangeCursor(self, cursor):
        self.canvas.SetCursor(wx.StockCursor(cursor))

    def OnMouseMovePicking(self, event):
        msg = 'Picking'
        active_pick_event = self.GetActivePickEvent()
        if active_pick_event:
            msg += ' %s' % active_pick_event
        if not event.inaxes:
            if self._lastCursor != self.POINTER:
                self.ChangeCursor(self.POINTER)
                self._lastCursor = self.POINTER
        else:
            if self._lastCursor != self.CROSS_HAIRS:
                self.ChangeCursor(self.CROSS_HAIRS)
                self._lastCursor = self.CROSS_HAIRS
            self._lastCursor = self.CROSS_HAIRS
            msg += self.GetStatusBarCoordinates(event)
        self.SetStatusText(msg)

    def OnClickPicking(self, event):

        active_pick_event = self.GetActivePickEvent()
        # Get trace index
        try:
            idx = int(self.splt.abscissa2trace(event.xdata))
            tr = self.segy.traces[idx]
        except ValueError:
            self.SetStatusText('Ignoring pick that is outside the'\
                                         +' data range.')
            return

        # Do something with the trace and pick time
        if(event.button == 1):
            # Add the new pick to the database
            pick = {'event':active_pick_event,
                'ensemble':tr.header.ensemble_number,
                'trace':tr.header.trace_number_within_the_ensemble,
                'time':event.ydata,
                # use default 'error':0.0
                'method':'manual',
                'source_x':tr.header.scaled_source_coordinate_x,
                'source_y':tr.header.scaled_source_coordinate_y,
                'source_z':tr.header.scaled_source_depth_below_surface,
                'receiver_x':tr.header.scaled_group_coordinate_x,
                'receiver_y':tr.header.scaled_group_coordinate_y,
                'receiver_z':-tr.header.scaled_receiver_group_elevation,
                'offset':tr.header.source_receiver_offset_in_m,
                'data_file':self.segy.file.name,
                'faz':tr.header.computed_azimuth_from_source_to_receiver}
            self.pickdb.update_pick(**pick)
            self.pickdb.commit()
            self.SetStatusText('Added %s pick' % active_pick_event\
                               + self.GetStatusBarCoordinates(event))
        elif(event.button == 2):
            # Remove pick
            pick = {'ensemble':self.splt.get_header_value(tr.header,
                                                          'ensemble'),
                    'trace':self.splt.get_header_value(tr.header, 'trace'),
                    'event':active_pick_event}
            self.pickdb.remove_pick(**pick)
            self.SetStatusText('Removed %s pick' % active_pick_event\
                               + self.GetStatusBarCoordinates(event)) 
            self.pickdb.commit()
        elif(event.button == 3):
            # TODO show pop-up for pick options?
            pass
        else:
            # Your mouse is too fancy for this program.
            pass
        # UpdateLayers the event that we are working on
        self.PlotPicks(force_new=True, event=active_pick_event)
        self.canvas.draw()


class PlotSegyFileMenu(PlotSegyPlottingMenu):
    """
    File menu for the SEG-Y Plotter.
    """
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)

        self.splt = SEGYPlotter()
        self.pickdb = None
        self.PLOT_ITEMS = {}

        self.MenuBar = wx.MenuBar()
        self.AppendFileMenu()
        self.AppendPlottingMenu()
        self.SetMenuBar(self.MenuBar)

        self.InitPlotWindow()
        self.OnOpenSegy(None)
        self.Centre()

    def AppendFileMenu(self):
        self.File = wx.Menu()
        self.ID_OPEN_SEGY = wx.NewId()
        self.OpenSegy = wx.MenuItem(self.File, self.ID_OPEN_SEGY,
                                    '&Open SEG-Y...\tCrtl+O',
                                    'Open a new SEG-Y file.')
        self.File.AppendItem(self.OpenSegy)
        self.Bind(wx.EVT_MENU, self.OnOpenSegy, id=self.ID_OPEN_SEGY)
        
        self.ID_QUIT = wx.NewId()
        self.Quit = wx.MenuItem(self.File, self.ID_QUIT,
                                '&Quit\tCtrl+Q',
                                'Quit the application.')
        self.File.AppendItem(self.Quit)
        self.Bind(wx.EVT_MENU, self.OnQuit, id=self.ID_QUIT)
        self.MenuBar.Append(self.File,'&File')

    def OnOpenSegy(self, event):
        self.SEGY_FILE = self.GetSEGYFileDialog()
        if self.SEGY_FILE:
            # Read SEG-Y file and create a new plotter
            try:
                self.segy = readSEGY(self.SEGY_FILE, computed_headers=True,
                                     unpack_data=False)
                msg = 'Read %i traces from %s.' % (len(self.segy.traces),
                                                   self.SEGY_FILE)
                logging.debug(msg)
                self.SetStatusText(msg)
                # Create new plotter for plotting picks
                if self.pickdb is not None:
                    self.splt = SEGYPickPlotter(self.ax, self.segy, 
                                                self.pickdb)
                else:
                    self.splt = SEGYPlotter(self.ax, self.segy)

            except SEGYError:
                msg = "Error reading '%s' as a SEG-Y formatted file." \
                    % self.SEGY_FILE
                self.ErrorDialog(self,msg)
                return
            # Plot the new data
            self.OnUpdateLayers(None)

    def OnQuit(self, event):
        self.Close()

    def _open_segy(self, file):
        """
        Reads data from a SEG-Y file and sets up the plotter.

        :param file: Filename of SEG-Y file to open.
        """
        


