from flask import Flask, render_template
import os
import psycopg2
import random
import string

app = Flask(__name__)

hostname = 'db'  # or '127.0.0.1'
port = 5432
database = 'db'
username = 'postgres'
password = 'postgres'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/data')
def data():
    try:
        conn = psycopg2.connect(
            host=hostname,
            port=port,
            database=database,
            user=username,
            password=password,
            connect_timeout=3
        )
        cur = conn.cursor()
        users = 'users'
        cur.execute('INSERT INTO users (id, name) VALUES (%s, %s);', (random.randint(1,1000), ''.join(random.choices(string.ascii_letters, k=8))))
        conn.commit()
        cur.close()
        return "Connection established"
    except Exception as e:
        return str(e)

    # return "some data2"

if __name__ == "__main__":
    server_port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=server_port)