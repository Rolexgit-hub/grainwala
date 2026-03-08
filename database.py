from flask_mysqldb import MySQL
import os

mysql = MySQL()

def init_db(app):
    app.config['MYSQL_HOST'] = os.getenv("MYSQLHOST") or os.getenv("MYSQL_PUBLIC_URL")
    app.config['MYSQL_USER'] = os.getenv("MYSQLUSER") or "root"
    app.config['MYSQL_PASSWORD'] = os.getenv("MYSQLPASSWORD") or os.getenv("MYSQL_ROOT_PASSWORD")
    app.config['MYSQL_DB'] = os.getenv("MYSQLDATABASE") or os.getenv("MYSQL_DATABASE")
    app.config['MYSQL_PORT'] = int(os.getenv("MYSQLPORT", "3306"))

    mysql.init_app(app)