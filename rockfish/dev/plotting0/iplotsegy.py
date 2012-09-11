"""
Interactive viewing and picking for SEG-Y data.

"""
import os
import wxversion
wxversion.ensureMinimal('2.8')

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx, StatusBarWx
from matplotlib.backends.backend_wx import _load_bitmap 
import matplotlib.pyplot as plt

# Must be imported after matplotlib
import wx

from rockfish.segy.segy import readSEGY,SEGYError
from rockfish.plotting.plotsegy import SEGYPlotter, SEGYPlotItems
from rockfish.picking.picksegy import SEGYPickDatabase



class MainFrame(wx.Frame):
    
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs) 
            
        self.dbfile = None
        self.pickdb = None
        self.segy = None
        self.pick_events = None
        self.active_pick_event = None
        
        # Plot items and layer manager
        self.splt_items = SEGYPlotItems()
        self.pick_items = {}
        self.plt_layers = PlotLayers()

        self.plot_param = { 'active_pick_marker':'.',
                            'active_pick_color':'blue',
                            'inactive_pick_marker':'.',
                            'inactive_pick_color':'green'}
        self.PLT_XLIMITS = None
        self.PLT_TLIMITS = None

        # UI items
        self._active = None                 # active mode
        self._lastCursor = None
        self.plot_obj = None
        self.PICK_EVENTS = {}
        self.SELECT_EVENT = wx.NewId()
        
        self.InitUI()

  
    def InitUI(self):
        #--------------------------------------------------
        # Build menus
        #--------------------------------------------------
        menubar = wx.MenuBar()

        # File Menu
        fileMenu = wx.Menu()
        self.file_open_segy = fileMenu.Append(wx.ID_ANY, '&Open SEG-Y...',
                                         'Open a new SEG-Y file')
        self.Bind(wx.EVT_MENU, self.OpenSEGY, self.file_open_segy)

        menubar.Append(fileMenu, '&File')

        # Edit Menu
        self.editMenu = wx.Menu()
        self.scaling = self.editMenu.Append(wx.ID_ANY,
                                                       '&Scaling',
                                                    'Edit data scaling parameters')
        self.Bind(wx.EVT_MENU, self.dlg_edit_scaling,
                  self.scaling)
        menubar.Append(self.editMenu, '&Edit')

        # View Menu
        self.viewMenu = wx.Menu()
        self.refresh = self.viewMenu.Append(wx.ID_ANY, '&Refresh Plot',
                                       'Replot the data')
        self.Bind(wx.EVT_MENU, self.ReplotAll, self.refresh)
        self.viewMenu.AppendSeparator()
        self.shst = self.viewMenu.Append(wx.ID_ANY, '&Show status bar', 
            'Show status bar', kind=wx.ITEM_CHECK)
        self.viewMenu.Check(self.shst.GetId(), True)
        self.Bind(wx.EVT_MENU, self.ToggleStatusBar, self.shst)
        self.shtl = self.viewMenu.Append(wx.ID_ANY, 'Show toolbar', 
            'Show toolbar', kind=wx.ITEM_CHECK)
        self.viewMenu.Check(self.shtl.GetId(), True)
        self.Bind(wx.EVT_MENU, self.ToggleToolBar, self.shtl)
        # Data plot items 
        self.viewMenu.AppendSeparator()
        self.plot_wiggles = self.viewMenu.Append(wx.ID_ANY, '&Wiggles',
                                            'Plot wiggle traces',
                                            kind=wx.ITEM_CHECK)
        self.viewMenu.Check(self.plot_wiggles.GetId(), False)
        self.Bind(wx.EVT_MENU, self.plot_segy, self.plot_wiggles)
        self.plot_positive_fills = self.viewMenu.Append(wx.ID_ANY, '&Positive Fills',
                                            'Plot positive wiggle fills',
                                            kind=wx.ITEM_CHECK)
        self.viewMenu.Check(self.plot_positive_fills.GetId(), True)
        self.Bind(wx.EVT_MENU, self.plot_segy, self.plot_positive_fills)
        self.plot_negative_fills = self.viewMenu.Append(wx.ID_ANY, '&Negative Fills',
                                            'Plot negative wiggle fills',
                                            kind=wx.ITEM_CHECK)
        self.viewMenu.Check(self.plot_negative_fills.GetId(), False)
        self.Bind(wx.EVT_MENU, self.plot_segy, self.plot_negative_fills)
        # Pick plot items 
        self.viewMenu.AppendSeparator()
        self.PLOT_ACTIVE_PICKS = wx.NewId()
        self.plot_active_picks = self.viewMenu.Append(self.PLOT_ACTIVE_PICKS,
                                                 '&Active Picks',
                                    'Plot picks for the current pick event',
                                            kind=wx.ITEM_CHECK)
        self.viewMenu.Check(self.plot_active_picks.GetId(), True)
        self.Bind(wx.EVT_MENU, self.plot_picks, self.plot_active_picks)
        self.PLOT_INACTIVE_PICKS = wx.NewId()
        self.viewMenu.Enable(self.PLOT_ACTIVE_PICKS,False)
        self.plot_inactive_picks = self.viewMenu.Append(self.PLOT_INACTIVE_PICKS,
                                                   '&Inactive Picks',
                                    'Plot picks for other pick events',
                                            kind=wx.ITEM_CHECK)
        self.viewMenu.Check(self.plot_inactive_picks.GetId(), True)
        self.Bind(wx.EVT_MENU, self.plot_picks, self.plot_inactive_picks)
        self.viewMenu.Enable(self.PLOT_INACTIVE_PICKS,False)
        menubar.Append(self.viewMenu, '&View')
            

        # Picking Menu
        self.pickingMenu = wx.Menu()
        self.picking_enable = self.pickingMenu.Append(wx.ID_ANY, 'Enable Picking',
                                                'Start/stop picking',
                                                kind=wx.ITEM_CHECK)
        self.pickingMenu.Check(self.picking_enable.GetId(),False)
        self.Bind(wx.EVT_MENU, self.TogglePicking, self.picking_enable)

        # Picking > Database submenu
        self.pickingMenu.AppendSeparator()
        dbMenu = wx.Menu()
        self.picking_db_connect = dbMenu.Append(wx.ID_ANY, 
                                                'Connect to Database...',
                                        'Connect to a SQLite pick database')
        self.Bind(wx.EVT_MENU, self.GetExistingDBFile, self.picking_db_connect)
        self.picking_db_create = dbMenu.Append(wx.ID_ANY, 
                                                'Create New Database...',
                                        'Create a new SQLite pick database')
        self.Bind(wx.EVT_MENU, self.CreateNewDBFile, self.picking_db_create)
        self.pickingMenu.AppendMenu(wx.ID_ANY, 'Database', dbMenu)
        
        # Picking Menu: event selection
        self.pickingMenu.AppendSeparator()
        self.add_new_event = self.pickingMenu.Append(wx.ID_ANY,
                                                 'Add New Event...',
                                        'Add a new event to the pick database')
        self.Bind(wx.EVT_MENU, self.AddPickingEvent, self.add_new_event)
        self.selectEventMenu = wx.Menu()
        self.SELECT_EVENT = wx.NewId()
        self.pickingMenu.AppendMenu(self.SELECT_EVENT, 'Select Event',
                                    self.selectEventMenu)
        self.pickingMenu.Enable(self.SELECT_EVENT,False)

        menubar.Append(self.pickingMenu, '&Picking')
        
        # Build menubar
        self.SetMenuBar(menubar)

        #--------------------------------------------------
        # Initialize status bar 
        #--------------------------------------------------
        #self.statusbar = self.CreateStatusBar()
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

        #--------------------------------------------------
        # Initialize frame and plot axes 
        #--------------------------------------------------
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.NamedColor("WHITE"))
        self.SetTitle('Rockfish SEG-Y Plotter')

        self.fig = plt.figure() 
        self.ax = self.fig.add_subplot(1,1,1)
        self.canvas = FigureCanvas(self, -1, self.fig)

        self.splt = SEGYPlotter()
        self.OpenSEGY(None)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        #--------------------------------------------------
        # Build toolbars 
        #--------------------------------------------------
        #self.toolbar = self.CreateToolBar()
        #self.toolbar.AddLabelTool(1, '', wx.Bitmap('texit.png'))
        #self.toolbar.Realize()
        self.add_toolbar()

        #--------------------------------------------------
        # Connect to events 
        #--------------------------------------------------
        self._idMove = self.canvas.mpl_connect('motion_notify_event',
                                                 self.navigation_mouse_move)

        
    #--------------------------------------------------
    # Menu updaters
    #--------------------------------------------------

    def UpdateSelectPickingEventMenu(self,new_events=None):
        """
        Adds or updates the list of event names in the select pick menu.
        """
        
        if(not self.pickingMenu.IsEnabled(self.SELECT_EVENT) and new_events):
            self.pickingMenu.Enable(self.SELECT_EVENT,True)

        if(new_events):
            for event in new_events:
                if event not in self.PICK_EVENTS:
                    _id = wx.NewId()
                    self.PICK_EVENTS[event] = _id
                    self.selectEventMenu.Append(_id,
                                            event,
                                            "Select event name '" + event + "'",
                                            kind=wx.ITEM_CHECK)
                    self.Bind(wx.EVT_MENU,Curry(self.SetActivePickingEvent,event),id=_id)


    def SetActivePickingEvent(self,event_name,e):
        """
        Sets the active picking event name.
        """
        self.active_pick_event = event_name
        if(self.pickingMenu.IsEnabled(self.SELECT_EVENT)):
            for event in self.PICK_EVENTS:
                if event == self.active_pick_event:
                    self.selectEventMenu.Check(self.PICK_EVENTS[event],True)
                else:
                    self.selectEventMenu.Check(self.PICK_EVENTS[event],False)

        # plot picks to change colors
        self.plot_picks(None)

        self.statusbar.SetStatusText("Set pick event name to '" + event_name\
                                     + "'")

    def AddPickingEvent(self,e):
        """
        Add a new event to the select event list.
        """
        valid_name = False
        new_event_name = None
        new_event_name = self.GetTextValue(self,'Enter new event name:',
                                           'Add Event')
        if not new_event_name: return

        while(not valid_name):
            if new_event_name in self.PICK_EVENTS:
                new_event_name = None
                new_event_name = self.GetTextValue(self,
                    'Event name already exists.'\
                    + ' Please enter a new event name:',
                                           'Add Event')
                if not new_event_name: return
            elif(new_event_name.strip(' ') == ''):
                new_event_name = None
                new_event_name = self.GetTextValue(self,
                    'Event names must contain characters other than spaces.'\
                    + ' Please enter a new event name:',
                                           'Add Event')
                if not new_event_name: return
            else:
                valid_name = True

        if(not self.pick_events):
            # this is the first event name
            self.pick_events = new_event_name
        else:
            self.pick_events.append(new_event_name)
        self.UpdateSelectPickingEventMenu(new_events=[new_event_name])
        self.SetActivePickingEvent(new_event_name,None)

    #--------------------------------------------------
    # Toolbar methods 
    #--------------------------------------------------
    def add_toolbar(self):
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        #self.toolbar = MainToolbar(self.canvas)
        self.toolbar.Realize()
        if wx.Platform == '__WXMAC__':
            # Mac platform (OSX 10.3, MacPython) does not seem to cope with
            # having a toolbar in a sizer. This work-around gets the buttons
            # back, but at the expense of having the toolbar at the top
            self.SetToolBar(self.toolbar)
        else:
            # On Windows platform, default window size is incorrect, so set
            # toolbar width to figure width.
            tw, th = self.toolbar.GetSizeTuple()
            fw, fh = self.canvas.GetSizeTuple()
            # By adding toolbar in sizer, we are able to put it at the bottom
            # of the frame - so appearance is closer to GTK version.
            # As noted above, doesn't work for Mac.
            self.toolbar.SetSize(wx.Size(fw, th))
            self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()

    def ReplotAll(self,e):
        """
        Replot everything.
        """
        # Remove everything from the plot without loosing current plot limits
        del self.ax.lines[:]     
        del self.ax.patches[:]
        
        # Clear limits, so they are reset
        #self.PLT_XLIMITS = None
        #self.PLT_TLIMITS = None

        # Replot
        if(self.segy):
            self.plot_segy(None)
        if(self.pickdb):
            self.plot_picks(None)


    def plot_segy(self,e):
        """
        Plots the segy data.

        This shoud only be called when the data are first loaded, or when the
        plot is refreshed using ``ReplotAll()``.
        """
        self.statusbar.SetStatusText('Plotting data...')
        # Data Layer 1: negative wiggle fills
        if self.plot_negative_fills.IsChecked():
            if(self.splt_items.wiggle_negative_fills and \
               not self.plt_layers.wiggle_negative_fills):
                # Just re-add existing artists
                self.ax.patches.append(self.splt_items.wiggle_negative_fills)
            else:
                # Redraw the wiggles
                self.splt_items.wiggle_negative_fills = \
                         self.splt.plot_wiggle_negative_fills(
                                                     self.ax,self.segy.traces)
            self.plt_layers.wiggle_negative_fills = True   # layer is on
        else:
            if(self.splt_items.wiggle_negative_fills and \
               self.plt_layers.wiggle_negative_fills):
                # Just remove existing wiggles 
                self.ax.patches.remove(self.splt_items.wiggle_negative_fills)
            self.plt_layers.wiggle_negative_fills = False  # layer is off

        # Data Layer 2: positive wiggle fills
        if self.plot_positive_fills.IsChecked():
            if(self.splt_items.wiggle_positive_fills and \
               not self.plt_layers.wiggle_positive_fills):
                # Just re-add existing artists
                self.ax.patches.append(self.splt_items.wiggle_positive_fills)
            else:
                # Redraw the wiggles
                self.splt_items.wiggle_positive_fills = \
                        self.splt.plot_wiggle_positive_fills(
                                                     self.ax,self.segy.traces)
            self.plt_layers.wiggle_positive_fills = True   # layer is on
        else:
            if(self.splt_items.wiggle_positive_fills and \
               self.plt_layers.wiggle_positive_fills):
                # Just remove existing wiggles 
                self.ax.patches.remove(self.splt_items.wiggle_positive_fills)
            self.plt_layers.wiggle_positive_fills = False  # layer is off

        # Data Layer 3: wiggle traces
        if self.plot_wiggles.IsChecked():
            if(self.splt_items.wiggle_traces and \
               not self.plt_layers.wiggle_traces):
                # Just re-add existing artists
                self.ax.lines.append(self.splt_items.wiggle_traces)
            else:
                # Redraw the wiggles
                self.splt_items.wiggle_traces = self.splt.plot_wiggle_traces(
                                                     self.ax,self.segy.traces)
            self.plt_layers.wiggle_traces = True   # layer is on
        else:
            if(self.splt_items.wiggle_traces and \
               self.plt_layers.wiggle_traces):
                # Just remove existing wiggles 
                self.ax.lines.remove(self.splt_items.wiggle_traces)
            self.plt_layers.wiggle_traces = False  # layer is off

        # set limits
        if(not self.PLT_XLIMITS or not self.PLT_TLIMITS):
            # only set on 1st plot, or when plot has been cleared
            self.splt.set_limits(self.ax)
            self.PLT_XLIMITS = self.ax.get_xlim
            self.PLT_TLIMITS = self.ax.get_ylim
        
        # add labels
        self.splt.label_axes(self.ax)
        self.ax.set_title(os.path.basename(self.segy.file.name))

        # Force a redraw of the canvas
        self.canvas.draw()

        self.statusbar.SetStatusText('Ready')

    def plot_picks(self,event,pick_events=None):
        """
        Plots picks in a SEGYPickDatabase object.
        """
        self.statusbar.SetStatusText('Plotting picks...')

        if(not self.segy):
            self.Error('Please open a SEG-Y file before plotting picks.')
            return
        if(not self.pickdb):
            self.Error('Please connect to a pick database before plotting picks.')
            return

        if(not pick_events):
            pick_events = self.pick_events

        if(not pick_events):
            self.statusbar.SetStatusText('No picks to plot.')
            return

        for event_name in self._iterable(pick_events):
            if event_name in self.pick_items:
                if self.pick_items[event_name] in self.ax.lines:
                    self.ax.lines.remove(self.pick_items[event_name])

            self.pick_items[event_name] = self.splt.plot_picks(self.ax,
                                                               self.pickdb,
                                                          self.segy.traces,
                                                        events=[event_name])
            if(self.pick_items[event_name]):
                if(event_name == self.active_pick_event):
                    self.pick_items[event_name].set_marker(
                            self.plot_param['active_pick_marker'])
                    self.pick_items[event_name].set_color(
                            self.plot_param['active_pick_color'])
                else:
                    self.pick_items[event_name].set_marker(
                            self.plot_param['inactive_pick_marker'])
                    self.pick_items[event_name].set_color(
                            self.plot_param['inactive_pick_color'])

        self.canvas.draw()  
        self.statusbar.SetStatusText('Ready')


    #--------------------------------------------------
    # Menu/toolbar Event handlers 
    #--------------------------------------------------
    def OpenSEGY(self, e):
        """ 
        Load data from a SEGY file
        """
        new_segy = None
        dirname= ''
        wildcards = "SEGY file (*.segy; *.sgy)|*.segy; *.sgy|"\
                    "All files |*.*"
        dlg = wx.FileDialog(self, "Choose a SEG-Y file", dirname, "",
                            wildcards, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            dirname = dlg.GetDirectory()
            filename = dlg.GetFilename()
        
            if(not new_segy):
                try:
                    self.statusbar.SetStatusText("Reading data... ")
                    self.segy = readSEGY(dirname + '/' + filename)
                    self.ntrc = len(self.segy.traces)
                    self.statusbar.SetStatusText("Read " + str(self.ntrc) +\
                                             " traces from " +\
                                             filename)

                    self.ax.clear()
                    self.plot_segy(None)
                except SEGYError:
                    self.Error(self,'Error reading ' + filename +\
                             ' as a SEG-Y formatted file.')
        dlg.Destroy()

    def GetExistingDBFile(self, e):
        """ 
        Connect to a SQLite database.
        """
        dirname = ''
        wildcards = "SQLite files (*.sqlite; *.db)|*.sqlite;*.db|"\
                    "All files |*.*"
        dlg = wx.FileDialog(self, "Choose a SQLite database", dirname , "",
                            wildcards, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            self.dbfile = dirname + '/' + filename
            self.ConnectToDatabase(None)
                
        dlg.Destroy()

    def CreateNewDBFile(self,e):
        """
        Create a new SQLite database.
        """
        dirname = ''
        wildcards = "SQLite files (*.sqlite; *.db)|*.sqlite;*.db|"\
                    "All files |*.*"
        dlg = wx.FileDialog(self, "Create a new SQLite database", dirname , "",
                            wildcards, wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            self.dbfile = dirname + '/' + filename
            self.ConnectToDatabase(None)
        dlg.Destroy()

    def ConnectToDatabase(self,e):
        """
        Establish a database connection.
        """
        try:
            self.pickdb = SEGYPickDatabase(self.dbfile)
            self.pick_events = self.pickdb.get_event_names()

            if(self.pick_events):
                self.statusbar.SetStatusText('Connected to ' + self.dbfile \
                                             + ', found event names: ' \
                                             + ', '.join(self.pick_events) )
                self.UpdateSelectPickingEventMenu(new_events=self.pick_events)
            else:
                self.statusbar.SetStatusText('Connected to ' + self.dbfile)
        except:
            self.Error(self,'Error connecting to ' + self.dbfile)

        # Enable pick plotting
        self.viewMenu.Enable(self.PLOT_ACTIVE_PICKS,True)
        self.viewMenu.Enable(self.PLOT_INACTIVE_PICKS,True)

        # Plot picks according to menu defaults
        self.plot_picks(None)


    def GetTextValue(self,parent, message, caption='Rockfish SEGY Plotter'):
        dlg = wx.TextEntryDialog(parent,message,caption=caption)
        dlg.ShowModal()
        dlg.Destroy()
        return dlg.GetValue()


    def TogglePicking(self, e):
        """
        Turns picking mode on and off.
        """
        
        if self.picking_enable.IsChecked():
            # Set active mode to PICKING
            self._last_active = self._active
            self._active = 'PICKING'
            
            # Make sure that we have data plotted
            if(not self.segy):
                self.OpenSEGY(None)

            # Make sure we have a database
            if(not self.dbfile):
                self.Error(self,'Please connect to a pick database before picking.')
                self.pickingMenu.Check(self.picking_enable.GetId(),False)
                return
            # Make sure we have a pick event name
            if(not self.active_pick_event):
                # Try to get an event name
                self.AddPickingEvent(None) 
                if(not self.active_pick_event):
                    # User selected 'cancel', disable picking
                    self.pickingMenu.Check(self.picking_enable.GetId(),False)
                    return

            # Disconnect from navigation's mouse move event
            self._idMove = self.canvas.mpl_disconnect(self._idMove)

            # Connect to picking's mouse move and click events
            self._idMove = self.canvas.mpl_connect('motion_notify_event',
                                                 self.picking_mouse_move)
            self._idClick = self.canvas.mpl_connect('button_press_event',
                                                    self.picking_on_click)

            # Lock MPL navigation tools
            self._last_navigate = self.ax.get_navigate()
            self.ax.set_navigate(False)
            self.toolbar.EnableTool(self.toolbar._NTB2_PAN,False)
            self.toolbar.EnableTool(self.toolbar._NTB2_ZOOM,False)
            self.statusbar.SetStatusText('Picking enabled, navigation is locked.')
        else:
            # Restore active mode to previous mode
            self._active = self._last_active

            # Disconnect from mouse move and click events
            self._idMove = self.canvas.mpl_disconnect(self._idMove)
            self._idClick = self.canvas.mpl_disconnect(self._idClick)
            
            # Reconnect to navigation's mouse move event
            self._idMove = self.canvas.mpl_connect('motion_notify_event',
                                                 self.navigation_mouse_move)

            # Unlock MPL navigation tools
            self.ax.set_navigate(self._last_navigate)
            self.toolbar.EnableTool(self.toolbar._NTB2_PAN,True)
            self.toolbar.EnableTool(self.toolbar._NTB2_ZOOM,True)
            self.statusbar.SetStatusText('Picking disabled, navigation is unlocked.')
        
    def ToggleStatusBar(self, e):
        
        if self.shst.IsChecked():
            self.statusbar.Show()
        else:
            self.statusbar.Hide()

    def ToggleToolBar(self, e):
        
        if self.shtl.IsChecked():
            self.toolbar.Show()
        else:
            self.toolbar.Hide()

    def Info(self, parent, message, caption = 'Info'):
        dlg = wx.MessageDialog(parent, message, caption, \
            wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def Error(self, parent, message, caption = 'Error'):
        dlg = wx.MessageDialog(parent, message, caption, \
            wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def dlg_edit_scaling(self,event):

        dlg = wx.Dialog(self)
        dlg.SetSize((250,200))
        dlg.SetTitle('Edit Parameters')

        pnl = wx.Panel(dlg)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.txt_box_ids = {}
        self.txt_boxes = []

        sb = wx.StaticBox(pnl, label='Scaling')
        sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)        

        params = ['gain','offset_gain_power','clip','normalization',]
        hbox = wx.GridSizer(len(params),2,0,0)
        ids = {}
        txt_ctrls = {}
        for k in params:
            ids[k]=wx.NewId()
            label = (k[0].upper() + k[1:]).replace("_"," ")
            txt_ctrls[k] = wx.TextCtrl(pnl,ids['gain'])
            txt_ctrls[k].ChangeValue(str(self.splt.PARAM[k]))

            hbox.Add(wx.StaticText(pnl, -1, label), flag=wx.RIGHT, border=5)
            hbox.Add(txt_ctrls[k], flag=wx.LEFT, border=5)

        sbs.Add(hbox)
        pnl.SetSizer(sbs)
       
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(dlg, label='OK')
        applyButton = wx.Button(dlg, label='Apply')
        closeButton = wx.Button(dlg, label='Close')
        hbox2.Add(closeButton, flag=wx.LEFT, border=5)
        hbox2.Add(applyButton)
        hbox2.Add(okButton)

        vbox.Add(pnl, proportion=1, 
            flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(hbox2, 
            flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        dlg.SetSizer(vbox)

        applyButton.Bind(wx.EVT_BUTTON,
                         Curry(self.on_apply_plot_param_edits,txt_ctrls))
        okButton.Bind(wx.EVT_BUTTON,
                         Curry(self.on_ok_plot_param_edits,dlg,txt_ctrls))
        closeButton.Bind(wx.EVT_BUTTON,Curry(self.on_close_plot_param_edits,dlg))
        
        dlg.ShowModal()

    def on_close_plot_param_edits(self,dlg,event):
        """
        Close the dialog and leave parameters unchanged.
        """
        dlg.Destroy()


    def on_ok_plot_param_edits(self,dlg,txt_ctrls,event):
        """
        Apply edits and close.
        """
        dlg.Destroy()
        self.on_apply_plot_param_edits(txt_ctrls,None)
        
    def on_apply_plot_param_edits(self,txt_ctrls,event):
        """
        Gets current value from text control boxes, updates the plot
        parameter dictionary, and replots all data.
        """
        for k in txt_ctrls:
            v = txt_ctrls[k].GetValue()
            if(type(self.splt.PARAM[k]) is str):
                self.splt.PARAM[k] = str(v)
            else:
                self.splt.PARAM[k] = float(v)
        
        self.statusbar.SetStatusText('Updated plot parameters.')
        self.ReplotAll(None)



    #--------------------------------------------------
    # Mouse event handlers 
    #--------------------------------------------------
    def navigation_mouse_move(self,event):
        """
        Event handler for a mouse move when navigation is enabled.
        """
        msg = 'Navigate' + self.get_statbar_coordinates(event) 
        self.statusbar.SetStatusText(msg)

    def picking_on_click(self,event):
        """
        Base event handler for a mouse click when picking is enabled.
        """
        # Get trace index
        try:
            idx = int(self.splt.xplt2trace(event.xdata))
            tr = self.segy.traces[idx]
        except ValueError:
            self.statusbar.SetStatusText('Ignoring pick that is outside the'\
                                         +' data range.')
            return

        # Do something with the trace and pick time
        if(event.button == 1):
            # Add the new pick to the database
            pick = {'ensemble':self.get_header_value(tr,'ensemble_number'),
                    'trace':self.get_header_value(tr,'trace_number_within_the_ensemble'),
                    'event':self.active_pick_event,
                    'time':event.ydata}
            self.pickdb.add_pick_event(pick,replace=True,commit=True)

        elif(event.button == 2):
            pick = {'ensemble':self.get_header_value(tr,'ensemble_number'),
                    'trace':self.get_header_value(tr,'trace_number_within_the_ensemble'),
                    'event':self.active_pick_event}
            self.pickdb.remove_pick_event(pick,commit=True)

        elif(event.button == 3):
            # TODO interpolate between picks
            print "Mouse Button 3: interpolate between picks coming soon"
        else:
            # Your mouse is too fancy for this program.
            pass

        # Update the pick plot
        self.plot_picks(None,pick_events=[self.active_pick_event])

    def picking_mouse_move(self, event):
        """
        Event handler for a mouse move when picking is enabled.

        Based on: matplotlib/backend_bases.NavigationToolbar2.mouse_move
        """
        if not event.inaxes:
            if self._lastCursor != cursors.POINTER:
                self.change_cursor(cursors.POINTER)
                self._lastCursor = cursors.POINTER
            msg = 'Picking ' + self.active_pick_event
        else:
            if self._lastCursor != cursors.CROSS_HAIRS:
                self.change_cursor(cursors.CROSS_HAIRS)
                self._lastCursor = cursors.CROSS_HAIRS
            self._lastCursor = cursors.CROSS_HAIRS
            msg = 'Picking ' + self.active_pick_event + \
                                self.get_statbar_coordinates(event) 
        self.statusbar.SetStatusText(msg)

    def get_statbar_coordinates(self,event):
        """
        Get coordinate data for the status bar.
        
        :param event: A ``matplotlib`` mouse event.
        :returns : A string with coordinate data.  If outside axis, returns an
            empty string.
        """
        if event.inaxes:
            msg = ': (%f, %f)' %(event.xdata, event.ydata)
            try:
                idx = int(self.splt.xplt2trace(event.xdata))
                tr = self.segy.traces[idx]
                ensemble = self.get_header_value(tr,'ensemble_number')
                trace = self.get_header_value(tr,
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

    
    #--------------------------------------------------
    # Other methods 
    #--------------------------------------------------
    def change_cursor(self, cursor):
        """
        Set the current cursor to one of the :class:`Cursors`
        enums values
        """
        self.canvas.SetCursor(wx.StockCursor(cursor))
    def get_header_value(self,trace,key):
        """
        Gets a value from trace header.
        
        This function ensures that unpacked values are read, in case they have
        been modified without updating the packed header.
        """
        try:   
            # use the unpacked value
            return trace.header.__getattribute__(key)
        except AttributeError:
            return trace.header.__getattr__(key)

    def _iterable(self,values):
        """
        Ensures that a variable is iterable.
        """
        try:
            any_item = iter(values)
            return values
        except TypeError:
            return [values]





class Cursors:
    """
    Conveince class for managing cursors.
    """
    POINTER = wx.CURSOR_ARROW
    CROSS_HAIRS = wx.CURSOR_CROSS
cursors = Cursors()

class PlotLayers():
    """
    Conveince class for managing plot layers.
    """

    def __init__(self):
        """
        Initializes all plot layer to False
        """
        self.wiggle_traces = False
        self.wiggle_positive_fills = False 
        self.wiggle_negative_fills = False 
        self.active_picks = False
        self.inactive_picks = False



class Curry:
    """
    Tie up a function with some default parameters so it can be called later. 
    
    Taken from the Python Cookbook.
    See <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52549>_.
    """
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.pending = args[:]
        self.kwargs = kwargs
    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs
        return self.func(*(self.pending + args), **kw)

class App(wx.App):
    def OnInit(self):
        frame = MainFrame(None, -1)
        frame.Centre()
        frame.Show(True)
        self.SetTopWindow(frame)

        return True

if __name__ == '__main__':
    app = App(0)
    app.MainLoop()
