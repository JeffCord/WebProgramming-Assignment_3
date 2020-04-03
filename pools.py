import os
import time

from flask import request
from flask import Flask, render_template
import mysql.connector
from mysql.connector import errorcode
import json

application = Flask(__name__)
app = application


def get_db_creds():
    db = os.environ.get("DB", None) or os.environ.get("database", None)
    username = os.environ.get("USER", None) or os.environ.get("username", None)
    password = os.environ.get("PASSWORD", None) or os.environ.get("password", None)
    hostname = os.environ.get("HOST", None) or os.environ.get("dbhost", None)
    return db, username, password, hostname


def create_table():
    print('Create table called.')
    # Check if table exists or not. Create and populate it only if it does not exist.
    db, username, password, hostname = get_db_creds()
    table_ddl = 'CREATE TABLE pools(pool_name VARCHAR(100) NOT NULL, status VARCHAR(13), phone VARCHAR(12), ' \
                'pool_type VARCHAR(12), PRIMARY KEY (pool_name))'

    cnx = ''
    try:
        # sets up a connection with the mysql server
        cnx = mysql.connector.connect(user=username, password=password, host=hostname, database=db)
    except Exception as exp:
        print(exp)

    # Create an object that can execute operations such as SQL statements.
    # Cursor objects interact with the MySQL server using a MySQLConnection object.
    cur = cnx.cursor()

    try:
        cur.execute(table_ddl)
        cnx.commit()
        populate_data()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        else:
            print(err.msg, '$$$')


def populate_data():

    db, username, password, hostname = get_db_creds()

    print("Inside populate_data")
    print("DB: %s" % db)
    print("Username: %s" % username)
    print("Password: %s" % password)
    print("Hostname: %s" % hostname)

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                       host=hostname,
                                       database=db)
    except Exception as exp:
        print(exp)

    cur = cnx.cursor()
    cur.execute("INSERT INTO message (greeting) values ('Hello, World!')")
    cnx.commit()
    print("Returning from populate_data")


def query_data():

    db, username, password, hostname = get_db_creds()

    print("Inside query_data")
    print("DB: %s" % db)
    print("Username: %s" % username)
    print("Password: %s" % password)
    print("Hostname: %s" % hostname)

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)

    cur = cnx.cursor()

    cur.execute("SELECT greeting FROM message")
    entries = [dict(greeting=row[0]) for row in cur.fetchall()]
    return entries

    try:
        print("---------" + time.strftime('%a %H:%M:%S'))
        print("Before create_table global")
        create_table()
        print("After create_data global")
    except Exception as exp:
        print("Got exception %s" % exp)
        conn = None


@app.route('/pools/<pool_name>', methods=['GET'])
def get_pool():
    return 'get pool method finished\n'


@app.route('/pools/<pool_name>', methods=['PUT'])
def update_pool():
    return 'update pool method finished\n'


@app.route('/pools/<pool_name>', methods=['DELETE'])
def delete_pool(pool_name):
    db, username, password, hostname = get_db_creds()

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)

    check_cur = cnx.cursor()
    check_cur.execute('SELECT * FROM pools_data.pools WHERE pool_name = \'' + pool_name + '\'')
    my_result = check_cur.fetchall()

    if len(my_result) == 0:
        return 'Pool with name ' + pool_name + ' does not exist\n', 404

    delete_query = 'DELETE FROM pools_data.pools WHERE pool_name = \'' + pool_name + '\''
    cur = cnx.cursor()
    cur.execute(delete_query)
    cnx.commit()

    return '', 200


@app.route('/pools', methods=['POST'])
def add_to_db():
    valid_statuses = ['Closed', 'Open', 'In Renovation']
    valid_pool_types = ['Neighborhood', 'University', 'Community']

    msg = request.json  # retrieves a json file from the local repository
    db, username, password, hostname = get_db_creds() # retrieve env vars

    # create a MySQLConnection object
    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)

    # make the python dict into a string separated by commas
    msg_csv = '\'' + msg['pool_name'] + '\', \'' + msg['status'] + '\', \'' + \
              msg['phone'] + '\', \'' + msg['pool_type'] + '\''

    # create a cursor object that interacts with the MySQL server using a MySQLConnection object
    cur = cnx.cursor()

    # check if pool already exists in table
    cur.execute("SELECT * FROM pools_data.pools WHERE pool_name = " + "\'" + msg['pool_name'] + "\'")

    # returns a list of tuples
    # each tuple represents a row in the table that was returned from the most recent sql execution
    my_result = cur.fetchall()
    if len(my_result) != 0:
        return 'Pool with name ' + msg['pool_name'] + ' already exists\n', 400

    # check for valid phone number syntax: 'phone field not in valid format'
    if not valid_phone_syntax(msg['phone']):
        return 'phone field not in valid format\n', 400

    # check for valid pool type: 'pool_type field has invalid value'
    if msg['pool_type'] not in valid_pool_types:
        return 'pool_type field has invalid value\n', 400

    # check for valid status: 'status field has invalid value'
    if msg['status'] not in valid_statuses:
        return 'status field has invalid value\n', 400

    # insert the new record
    cur.execute("INSERT INTO pools_data.pools (`pool_name`, `status`, `phone`, `pool_type`) values (" + msg_csv + ")")

    # make the changes to the database permanent
    cnx.commit()

    return '', 201


# Check if the pool's phone number fits the syntax of 'XXX-XXX-XXXX'
def valid_phone_syntax(phone_num):
    if len(phone_num) != 12:
        return False

    if phone_num[3] != '-' or phone_num[7] != '-':
        return False

    for i in range(3):
        if not phone_num[i].isdigit():
            return False

    for i in range(4, 7):
        if not phone_num[i].isdigit():
            return False

    for i in range(8, 12):
        if not phone_num[i].isdigit():
            return False

    return True


@app.route("/")
def hello():
    return 'Welcome to the Austin pools home page.\n'


if __name__ == "__main__":
    create_table()
    app.debug = True
    app.run()