"""
Dialog boxes for Rockfish applications.
"""
import wx

class PlotSegyEventDialogs(object):
    """
    Generic event dialog boxes.
    """
    def ErrorDialog(self, parent, message, caption = 'Error'):
        dlg = wx.MessageDialog(parent, message, caption,
                               wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def InfoDialog(self, parent, message, caption = 'Information'):
        dlg = wx.MessageDialog(parent, message, caption, \
            wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def GetSQLiteFileDialog(self,new=False):
        filename = None
        dirname = ''
        wildcards = "SQLite files (*.sqlite; *.db)|*.sqlite;*.db|"\
                    "All files |*.*"
        if not new:
            dlg = wx.FileDialog(self, "Choose a SQLite database", dirname , "",
                            wildcards, wx.OPEN)
        else:
            dlg = wx.FileDialog(self, "Create a new SQLite database", dirname , "",
                            wildcards, wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = '%s/%s' %(dlg.GetDirectory(), dlg.GetFilename())
        dlg.Destroy()
        return filename

    def GetSEGYFileDialog(self):
        filename = None
        dirname= ''
        wildcards = "SEGY file (*.segy; *.sgy)|*.segy; *.sgy|"\
                    "All files |*.*"
        dlg = wx.FileDialog(self, "Choose a SEG-Y file", dirname, "",
                            wildcards, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = '%s/%s' %(dlg.GetDirectory(), dlg.GetFilename())
        dlg.Destroy()
        return filename

    def GetTextDialog(self,parent, message, caption='Get text'):
        dlg = wx.TextEntryDialog(parent,message,caption=caption)
        dlg.ShowModal()
        dlg.Destroy()
        return dlg.GetValue()

    def OnTodo(self,event):
        """
        Menubar action placeholder.
        """
        self.ErrorDialog(self,'Not yet implemented')

