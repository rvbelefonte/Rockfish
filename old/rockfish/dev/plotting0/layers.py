"""
Layer managers for interactive plotting interfaces.
"""

class SEGYPlotLayerManager(object):
    """
    Layer manager for SEGYPlotter.
    """
    def __init__(self):

        self.ACTIVE_PLOT_ITEMS = {}
        self.INACTIVE_PLOT_ITEMS = {}
        self.PLOT_ITEM_TYPES = {'patches':['negfills','posfills'],
                                'lines':['wiggles','picks']}

    def status(self,plot_item):
        """
        Returns the status of a plot item.

        ============== ===================================
        Status         Description
        ============== ===================================
        ``'active'``   Plot item is in the active list.
        ``'inactive'`` Plot item is in the inactive list.
        ``None``       Plot item does not exist.
        ============== ===================================

        .. rubric: Examples:

        >>> manager = SEGYPlotLayerManager()
        >>> manager.add('foobar','negfills')
        >>> manager.add('foobar','posfills',active=False)
        >>> print manager.status('negfills')
        active
        >>> print manager.status('posfills')
        inactive
        >>> print manager.status('plot item that does not exist')
        None
        >>> manager.toggle('negfills')
        >>> print manager.status('negfills')
        inactive
        >>> manager.toggle('posfills')
        >>> print manager.status('posfills')
        active

        """
        if self._is_active(plot_item):
            return 'active'
        elif self._is_inactive(plot_item):
            return 'inactive'
        else:
            return None

    def exists(self,plot_item):
        """
        Checks if a plot item exists.
        
        .. rubric: Examples:

        >>> manager = SEGYPlotLayerManager()
        >>> manager.add('foobar','posfills',active=False)
        >>> print manager.exists('posfills')
        True
        >>> print manager.exists('does not exist')
        False
        """
        if plot_item in self.ACTIVE_PLOT_ITEMS:
            return True
        elif plot_item in self.INACTIVE_PLOT_ITEMS:
            return True
        else:
            return False

    def _is_active(self,plot_item):
        """
        Checks if a plot item is active.
        """
        if plot_item in self.ACTIVE_PLOT_ITEMS:
            return True
        else:
            return False

    def _is_inactive(self,plot_item):
        """
        Checks if a plot item is inactive.
        """
        if plot_item in self.INACTIVE_PLOT_ITEMS:
            return True
        else:
            return False

    def add(self,artists,plot_item,active=True):
        """
        Add new plot items to the dictionary.
        """
        if active:
            PLOT_ITEMS = self.ACTIVE_PLOT_ITEMS
        else:
            PLOT_ITEMS = self.INACTIVE_PLOT_ITEMS

        if PLOT_ITEMS.has_key(plot_item):
            PLOT_ITEMS[plot_item].extend([artists])
        else:
            PLOT_ITEMS[plot_item] = [artists]

    def remove(self,plot_item,axes=None):
        """
        Removes plot items.

        Purges plot items from the dictionary and optionally removes them from
        an existing plot axes.
        """
        if self.status(plot_item) == 'active':
            self._deactivate(plot_item,axes=axes)
            return self.INACTIVE_PLOT_ITEMS.pop(plot_item)
        elif self.status(plot_item) == 'inactive':
            return self.INACTIVE_PLOT_ITEMS.pop(plot_item)

    def remove_all(self,axes):
        """
        Removes all plot items from the dictionaries.
        """
        items = [k for k in self.ACTIVE_PLOT_ITEMS]
        items.extend([k for k in self.INACTIVE_PLOT_ITEMS])
        for plot_item in items:
            self.remove(plot_item,axes)

    def toggle(self,plot_item,axes=None):
        """
        Toggles the status of an existing plot item.
        """
        if self.status(plot_item) == 'active':
            self._deactivate(plot_item,axes=axes)
        elif self.status(plot_item) == 'inactive':
            self._activate(plot_item,axes=axes)

    def _activate(self,plot_item,axes=None):
        """
        Activate plot items.

        Moves plot items from the inactive dictionary to the 
        active dictionary and optionally re-adds them from an existing axes.
        """
        if plot_item in self.PLOT_ITEM_TYPES['patches']:
            for patches in self.INACTIVE_PLOT_ITEMS.pop(plot_item):
                if axes:
                    axes.patches.append(patches)
                self.add(patches,plot_item,active=True)
        elif plot_item in self.PLOT_ITEM_TYPES['lines']:
            for lines in self.INACTIVE_PLOT_ITEMS.pop(plot_item):
                if axes:
                    axes.patches.append(lines)
                self.add(artists,plot_item,active=True)
        else:
            msg = "No plot item type found for '%s'" % plot_item
            raise KeyError(msg)

    def _deactivate(self,plot_item,axes=None):
        """
        Deactive plot items.
        
        Moves plot items from the active dictionary to the 
        inactive dictionary and optionally removes them from an existing axes.
        """
        if plot_item in self.PLOT_ITEM_TYPES['patches']:
            for patches in self.ACTIVE_PLOT_ITEMS.pop(plot_item):
                if axes:
                    axes.patches.remove(patches)
                self.add(patches,plot_item,active=False)
        elif plot_item in self.PLOT_ITEM_TYPES['lines']:
            for lines in self.ACTIVE_PLOT_ITEMS.pop(plot_item):
                if axes:
                    axes.lines.remove(lines)
                self.add(lines,plot_item,active=False)
        else:
            msg = "No plot item type found for '%s'" % plot_item
            raise KeyError(msg)

class SEGYPlotManager(SEGYPlotLayerManager):
    """
    Layer and parameter manager for SEGY Plotter.
    """

    def __init__(self):

        self.ACTIVE_PLOT_ITEMS = {}
        self.INACTIVE_PLOT_ITEMS = {}



if __name__ == "__main__":
    import doctest
    doctest.testmod()

