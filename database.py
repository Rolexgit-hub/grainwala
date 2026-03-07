from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'flaskuser'
    app.config['MYSQL_PASSWORD'] = 'Kalki'
    app.config['MYSQL_DB'] = 'grainwala_db'

    mysql.init_app(app)
