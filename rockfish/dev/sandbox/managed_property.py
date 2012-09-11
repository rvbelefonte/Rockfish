"""
Pythonic way to manage class properties.

"""

class Book(object):

    def get_title(self):
        return self._title

    def set_title(self, title):
        self._title = title

    title = property(get_title, set_title)

print Book.title

Book.title = 'Code Complete'

print Book.title
