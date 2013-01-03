
import sqlite3

conn = sqlite3.Connection(':memory:')
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE stocks
             (date text, trans text, symbol text, qty real, price real)''')

c.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")

c.execute("INSERT INTO stocks (?, ?) VALUES (?, ?)", 
          ('date', 'symbol', '2012-01-04', 'RHAT'))

t = ('RHAT',)
c.execute('SELECT * FROM stocks WHERE symbol=?', t)

print c.fetchall()

