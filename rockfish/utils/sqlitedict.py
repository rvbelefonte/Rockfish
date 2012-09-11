"""
A persistent (sqlite3) python dictionary

Based on:
http://erezsh.wordpress.com/2009/05/31/filedict-bug-fixes-and-updates/
Author: Erez Shinan
Date: 31-May-2009

Copyright 2010 Matteo Bertini <matteo@naufraghi.net>
Python Software Foundation License (PSFL)
"""

import UserDict
import cPickle as pickle
import sqlite3


class SqliteDict(UserDict.DictMixin):
    "A dictionary that stores its data persistently in a database"

    def __init__(self, filename, flag='c', protocol=-1, writeback=False):
        self.filename = filename
        self.flag = flag
        self.protocol = protocol
        self.writeback = writeback
        # flag as in http://docs.python.org/library/anydbm.html#anydbm.open
        if flag in ('r', 'w'):
            if not os.path.exists(filename):
                raise IOError("File {0!r} missing!".format(filename))
            
        sqlite3.register_converter("PICKLE", self._loads)
        self._conn = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)
        if flag == 'n':
            self._dbdrop()
        if flag in ('n', 'c'):
            self._dbcreate()

    def _dbdrop(self):
        self._conn.execute("DROP TABLE IF EXISTS dict;")
        self._conn.commit()

    def _dbcreate(self):
        self._conn.execute("""CREATE TABLE IF NOT EXISTS dict (idx INTEGER PRIMARY KEY,
                                                               key STRING UNIQUE,
                                                               value PICKLE);""")
        self._conn.execute("CREATE INDEX IF NOT EXISTS dict_index ON dict(key);")
        self._conn.commit()

    def _commit(self):
        if self.writeback: 
            self._conn.commit()

    def _dumps(self, value):
        return buffer(pickle.dumps(value, self.protocol))
    def _loads(self, blob):
        return pickle.loads(blob)

    def __getitem__(self, key):
        cursor = self._conn.execute("SELECT value FROM dict WHERE key=?;", (key,))
        for (value,) in cursor:
            return value
        raise KeyError(key)

    def _setitems(self, items):
        parameters = ((key, self._dumps(value)) for key, value in items)
        self._conn.executemany("INSERT OR REPLACE INTO dict (key, value) values (?, ?);",
                               parameters)
        self._commit()

    def __setitem__(self, key, value):
        self._setitems([(key, value)])

    def __delitem__(self, key):
        cursor = self._conn.execute("DELETE FROM dict WHERE key=?;", (key,))
        if cursor.rowcount <= 0:
            raise KeyError(key)
        self._commit()

    def update(self, d):
        self._setitems(d.iteritems())

    def iterkeys(self):
        return self._conn.execute("SELECT key FROM dict;")
    def itervalues(self):
        return self._conn.execute("SELECT value FROM dict;")
    def iteritems(self):
        return self._conn.execute("SELECT key, value FROM dict;")

    def __iter__(self):
        return self.iterkeys()
    def keys(self):
        return list(self.iterkeys())
    def values(self):
        return list(self.itervalues())
    def items(self):
        return list(self.iteritems())

    def __contains__(self, key):
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False

    def __len__(self):
        return self._conn.execute("SELECT COUNT(*) FROM dict;").fetchone()[0]

    def close(self):
        self.sync()
        self._conn.close()
    
    def sync(self):
        self._conn.commit()
        
    def __del__(self):
        self.close()

def open(filename, flag='c', protocol=-1, writeback=False):
    return SqliteDict(filename, flag, protocol, writeback)
