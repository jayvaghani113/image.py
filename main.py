import http.server
import socketserver
from urllib.parse import parse_qs, urlparse, unquote
import os
import mysql.connector
from jinja2 import Environment, FileSystemLoader
#mysql-connector-python 8.3.0
#pip install mysql-connector-python
# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'jay@#123',
    'database': 'student',
}
port = 8000

# Initialize a MySQL connection
try:
    # Attempt to establish a MySQL connection
    db_connection = mysql.connector.connect(**db_config)
    db_cursor = db_connection.cursor()

    # Check if the connection is successful
    if db_connection.is_connected():
        print("Connected to MySQL database")

except mysql.connector.Error as err:
    print(f"Error: {err}")
    exit(1)  # Exit the program if there's an error in database connection

# Create a table to store user data if not exists
create_table_query = """
CREATE TABLE IF NOT EXISTS user_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(15) NOT NULL
);
"""
db_cursor.execute(create_table_query)

# Define the template environment
template_env = Environment(loader=FileSystemLoader(os.path.abspath('.')))

# Define the request handler class
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = 'index.html'
        elif self.path == '/list':
            self.path = 'go.html'
            select_query = "SELECT name, phone FROM user_data"
            db_cursor.execute(select_query)
            user_data = [{'name': name, 'phone': phone} for name, phone in db_cursor.fetchall()]
            print(user_data)
            self.send_response(200)
            self.end_headers()
            template = template_env.get_template('go.html')
            rendered_template = template.render(user_data=user_data)
            self.wfile.write(rendered_template.encode('utf-8'))
            return
        elif self.path == '/del':
            # Redirect to the list page
            self.send_response(303)
            self.send_header('Location', '/list')
            self.end_headers()
            return
        elif self.path.startswith('/edit'):
            # Parse the URL query parameters
            query_params = parse_qs(urlparse(self.path).query)
            name = unquote(query_params.get('name', [''])[0])
            phone = unquote(query_params.get('phone', [''])[0])
            self.send_response(200)
            self.end_headers()
            template = template_env.get_template('edit.html')
            rendered_template = template.render(name=name, phone=phone)
            self.wfile.write(rendered_template.encode('utf-8'))
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data_dict = parse_qs(post_data)

            name = data_dict['name'][0]
            phone = data_dict['phone'][0]

            try:
                # Store the data in MySQL
                insert_query = "INSERT INTO user_data (name, phone) VALUES (%s, %s)"
                db_cursor.execute(insert_query, (name, phone))
                db_connection.commit()

                print(f"Data inserted into the database: Name={name}, Phone={phone}")

                # Redirect to the list page
                self.send_response(303)
                self.send_header('Location', '/list')
                self.end_headers()

            except mysql.connector.Error as err:
                print(f"Error inserting data into the database: {err}")
                # Handle the error as needed

        elif self.path.startswith('/edit_submit'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data_dict = parse_qs(post_data)

            old_name = data_dict['old_name'][0]
            old_phone = data_dict['old_phone'][0]
            new_name = data_dict['new_name'][0]
            new_phone = data_dict['new_phone'][0]

            try:
                # Update the data in MySQL
                update_query = "UPDATE user_data SET name=%s, phone=%s WHERE name=%s AND phone=%s"
                db_cursor.execute(update_query, (new_name, new_phone, old_name, old_phone))
                db_connection.commit()

                print(f"Data updated in the database: Old Name={old_name}, Old Phone={old_phone}, New Name={new_name}, New Phone={new_phone}")

                # Redirect to the list page
                self.send_response(303)
                self.send_header('Location', '/list')
                self.end_headers()

            except mysql.connector.Error as err:
                print(f"Error updating data in the database: {err}")
                # Handle the error as needed

        elif self.path == '/delete':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data_dict = parse_qs(post_data)

            name = data_dict['name'][0]
            phone = data_dict['phone'][0]

            try:
                # Delete the data from MySQL
                delete_query = "DELETE FROM user_data WHERE name=%s AND phone=%s"
                db_cursor.execute(delete_query, (name, phone))
                db_connection.commit()
                print("Data deleted from the database: Name={}, Phone={}".format(name, phone))

                # Redirect to the list page
                self.send_response(303)
                self.send_header('Location', '/list')
                self.end_headers()

            except mysql.connector.Error as err:
                print(f"Error deleting data from the database: {err}")
                # Handle the error as needed

                # Redirect to the list page
                self.send_response(303)
                self.send_header('Location', '/list')
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

# Create the server
with socketserver.TCPServer(("", port), MyHandler) as httpd:
    print(f"Serving on port {port}")

    # Start the server
    httpd.serve_forever()


