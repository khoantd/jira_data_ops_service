import sqlite3


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # print("SQLite connection is established!")
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        # print("The table was created successfully!")
    except sqlite3.Error as e:
        print(e)


def query_exec(conn, query_stmt):
    """
    Execute query statement
    :param conn: the Connection object
    :return:
    """
    # print(query_stmt)
    rows = conn.execute(query_stmt)
    return rows


def tuple_convert(obj):
    if isinstance(obj, list):
        return tuple(obj)
    else:
        return tuple(
            obj.values()
        )


def update_stmt_convert(tuple_obj, key_pos):
    obj_list = []
    counter = 0
    t_key = ""
    for i in tuple_obj:
        if counter != key_pos:
            obj_list.append(i)
        else:
            t_key = i
        counter += 1
    obj_list.append(t_key)
    return tuple(obj_list)


def update_exec(conn, update_stmt, key_pos, obj_list):
    """
    Update a record to a desired table
    :param conn: the Connection object
    :param update_stmt: the Update statement
    :param obj_list: the list of objects
    :return:
    """
    flag = "NA"
    for obj in obj_list:
        flag = one_rec_update(conn, update_stmt, key_pos, obj)
    return flag


def one_rec_update(conn, update_stmt, key_pos, obj):
    str = ""
    # print(tuple(obj)[1])
    # print(tuple_convert(obj))
    # str += tuple_convert(obj)[1]
    try:
        conn.execute(update_stmt, update_stmt_convert(
            tuple_convert(obj), key_pos))
        conn.commit()
        str += " was updated successfully!"
        flag = "S"
    except sqlite3.IntegrityError as e:
        str += " was not updated!"
        conn.rollback()
        flag = "F"
        pass
    return flag


def insert_exec(conn, insert_stmt, obj_list):
    """
    Insert new record to a desired table
    :param conn: the Connection object
    :param insert_stmt: the Insert statement
    :param obj_list: the list of objects
    :return:
    """
    flag = "NA"
    for obj in obj_list:
        flag = one_rec_insert(conn, insert_stmt, obj)
    return flag


def one_rec_insert(conn, insert_stmt, obj):
    str = ""
    # print("insert_stmt:", insert_stmt)
    # print("obj:", obj)
    # print(tuple(obj.values())[1])
    # str += tuple(obj.values())[1]
    try:
        if isinstance(obj, tuple) == True:
            # print(obj)
            conn.execute(insert_stmt, obj)
            str = ""
            str += " inserted successfully!"
            flag = "S"
            conn.commit()
        elif isinstance(obj, list) == True:
            # print(obj)
            conn.execute(insert_stmt, tuple(obj))
            str = ""
            str += " inserted successfully!"
            flag = "S"
            conn.commit()
        else:
            # print(obj)
            str += tuple(obj.values())[1]
            conn.execute(insert_stmt, tuple(obj.values()))
            str = ""
            str += " inserted successfully!"
            flag = "S"
            conn.commit()
        # print(str)
        # print("inserted successfully!")
    except sqlite3.IntegrityError as e:
        # print("Oops!", e, "occurred.")
        str += " is already existing!"
        # print(str)
        flag = "E"
        pass
    return flag
# Function to convert


def listToString(s):
    """
        This function is used for concating items of a list with comma (,)
        input: list
        output: string
    """
    str1 = ","
    return (str1.join(s))


def query_stmt_convert(table_name, columns):
    """
        This function is used for converting query statement from table name and columns
        input: table name, list of column names
        output: string
    """
    str = listToString(columns)
    query_stmt = f"Select {str} from {table_name}"
    return query_stmt


def all_table_data_get(table_name, db_name):
    conn = create_connection(db_name)
    check_log = f'''
    SELECT * FROM {table_name}"
    '''
    data = []
    with conn as conn:
        items_count = query_exec(conn, check_log)
        for i in items_count:
            data.append(i)
    return data


if __name__ == "__main__":
    print()
