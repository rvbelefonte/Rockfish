''' Collection of tools to manipulate SQLite databases '''

def assign_sql_types_to_dict(dictionary):
    ''' 
    Add SQLite data types to each entry in dictionary.

    >>> dict1={'myrealfield':1.00, 'mystringfield':'foobar', 'myintegerfield':9, 'mytuplefield':('foo',1.3)}
    >>> dict2=assign_sql_types_to_dict(dict1)
    >>> print dict2
    {'myrealfield': (1.0, 'real'), 'mystringfield': ('foobar', 'text'), 'mytuplefield': (('foo', 1.3), 'text'), 'myintegerfield': (9, 'integer')}

    '''
    
    python2sqlite={'str':'text','int':'integer','float':'real'}

    for key in list(dictionary):
        python_type = type(dictionary[key]).__name__
        try :
            sql_type = python2sqlite[python_type]
        except KeyError:            # store unknown python types as text field
            sql_type = 'text'
            pass

        dictionary[key]=(dictionary[key],sql_type)

    return dictionary


def create_table_from_dict(table,dictionary):
    ''' 
    Generate SQLite command to create table with a field
    for each entry in dictionary.

    >>> table='mynewtable'
    >>> dict={'myrealfield':1.00, 'mystringfield':'foobar', 'myintegerfield':9, 'mytuplefield':('foo',1.3)}
    >>> sql=create_table_from_dict(table,dict)
    >>> print sql
    CREATE TABLE 'mynewtable' (myrealfield real, mystringfield text, mytuplefield text, myintegerfield integer);

    '''

    # Map python data types to sql data types
    d=assign_sql_types_to_dict(dictionary)

    # Get field names and data types
    field_types=[]
    for key in list(d):
       (value,sql_type)=d[key]
       field_types.append(key + ' ' + sql_type)
       
    # Create sql code for creating a new table
    sql =  "CREATE TABLE '" + table + "'"
    sql += ' ('
    sql += ', '.join(field_types)
    sql += ');'

    return sql

def add_fields_from_dict(table,dictionary):

    sql = 'ALTER TABLE ' + table + ' ADD '
    for key in list(dictionary):
        sql += str(key) + " " + str(dictionary[key])
    sql += ";"

    return sql


def insert_dict_as_row(table,dictionary):
    ''' Generate SQLite command to insert values from dictionary into table

    >>> table_name='mynewtable'
    >>> dict={'myrealfield':1.00, 'mystringfield':'foobar', 'myintegerfield':9, 'mytuplefield':('foo',1.3)}
    >>> sql=insert_dict_as_row(table_name,dict)
    >>> print sql
    INSERT INTO mynewtable (myrealfield, mystringfield, mytuplefield, myintegerfield)  VALUES ( " 1.0 " ,  " foobar " ,  " ('foo', 1.3) " ,  " 9 " );
    
    '''

    values=[]
    for key in list(dictionary):
	    values.append(pad_value(dictionary[key]))

    sql =  'INSERT INTO ' + table
    sql += ' ('
    sql += ', '.join(list(dictionary))
    sql += ')  VALUES (' + ', '.join(values)
    sql += ');'

    return sql


def pad_value(value):
    '''
    >>> print pad_value(1)
     " 1 " 
    >>> print pad_value((1,'one'))
     " (1, 'one') " 
    >>> print pad_value('foobar')
     " foobar " 

    '''

    return '"' + str(value) + '"'

def field_types_from_table(conn,table_name):
    ''' Create a dictionary of field_types={field_name:field_type} from the existing
        table table_name.
    '''

    field_list = conn.execute("PRAGMA table_info('" + table_name + "')").fetchall()
    nfields=len(field_list)
    field_types = {}
    for i in range(0,nfields):
        entries = field_list[i]
        name = str(entries[1])
        sql_type = str(entries[2])
        field_types[name] = sql_type


    return field_types

import datetime
import sqlite3



def convert2str(record):
    """
    Convert data to strings for using in sql insert statements.
    """

    type_str = type('str')
    type_datetime = type(datetime.datetime.now())
    type_int = type(1)
    type_float = type(1.0)
    type_None = type(None)

    res = []
    for item in record:
        if type(item)==type_None:
            res.append('NULL')
        elif type(item)==type_str:
            res.append('"'+item+'"')
        elif type(item)==type_datetime:
            res.append('"'+str(item)+'"')
        else:  # for numeric values
            res.append(str(item))
    return ','.join(res)

def copy_table(tab_name, src_cursor, dst_cursor):
    """
    Copy one table into another database.
    """

    sql = 'select * from %s'%tab_name
    res = src_cursor.execute(sql).fetchall()
    cnt = 0
    for record in res:
        val_str = ', '.join(["'" + str(r) + "'" for r in record])
        sql = 'insert into %s values(%s)'%(tab_name, val_str)
        print sql
        dst_cursor.execute(sql)




if __name__ == "__main__":
    import doctest
    doctest.testmod()
