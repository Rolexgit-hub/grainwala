from flask_mysqldb import MySQL
import os

mysql = MySQL()

def init_db(app):

    app.config['MYSQL_HOST'] = os.getenv("MYSQLHOST")
    app.config['MYSQL_USER'] = os.getenv("MYSQLUSER")
    app.config['MYSQL_PASSWORD'] = os.getenv("MYSQLPASSWORD")
    app.config['MYSQL_DB'] = os.getenv("MYSQLDATABASE")
    app.config['MYSQL_PORT'] = int(os.getenv("MYSQLPORT", "3306"))

    mysql.init_app(app)