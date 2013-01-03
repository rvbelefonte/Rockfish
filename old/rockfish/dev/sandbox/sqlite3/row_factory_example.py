
import sqlite3

conn = sqlite3.connect(":memory:")
c = conn.cursor()
c.execute('''create table stocks
(date text, trans text, symbol text,
 qty real, price real)''')
c.execute("""insert into stocks
          values ('2006-01-05','BUY','RHAT',100,35.14)""")
conn.commit()
c.close()

conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('select * from stocks')
#<sqlite3.Cursor object at 0x7f4e7dd8fa80>
r = c.fetchone()
type(r)
#<type 'sqlite3.Row'>
r
#(u'2006-01-05', u'BUY', u'RHAT', 100.0, 35.14)
len(r)
#5
r[2]
#u'RHAT'
r.keys()
#['date', 'trans', 'symbol', 'qty', 'price']
r['qty']
#100.0
for member in r:
    print member

