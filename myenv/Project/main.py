import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import socket
import logging
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import os


uri = "mongodb://localhost:27017"  

HTTPServer_Port = 3000
UDP_IP = "127.0.0.1"
UDP_PORT = 5000

def send_data_to_socket(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = (UDP_IP, UDP_PORT)
    sock.sendto(data.encode(), server)
    sock.close()

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        
        # Send data to socket server
        send_data_to_socket(data_parse)
        
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

  

    def do_GET(self):
        if self.path == '/':
            self.send_file('index.html')
        elif self.path == '/style.css':
            self.send_file('style.css', 'text/css')
        elif self.path == '/logo.png':
            self.send_file('logo.png', 'image/png')
        elif self.path == '/message.html':
            self.send_file('message.html')
        else:
            self.send_file('error.html', 404) 

   
    def send_file(self, filename, status=200):
        base_path = '/Users/HP/Desktop/4_Computer_systems_Tier2/goit-cs-hw-06/myenv/Project'
        full_path = os.path.join(base_path, filename)
        try:
            with open(full_path, 'rb') as fd:
                self.send_response(status)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(fd.read())
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(os.path.join(base_path, 'error.html'), 'rb') as fd:
                self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', HTTPServer_Port)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def save_data(data):
    client = MongoClient(uri, server_api=ServerApi("1"))
    db = client.DB_Client
    
    result_one = db.client.insert_one(
        {
            "date": datetime.now(),
            "username": data.get("username"),
            "message": data.get("message"),
        }
    )

def run_socket_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = (ip, port)
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            print(f"Received data: {data.decode()} from: {address}")
            
            # Convert data to dictionary
            data_parse = urllib.parse.unquote_plus(data.decode())
            data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            
            # Save data to MongoDB
            save_data(data_dict)
            
            sock.sendto(data, address)
            print(f"Sent data: {data.decode()} to: {address}")

    except KeyboardInterrupt:
        print("Destroying server")
    finally:
        sock.close()

if __name__ == '__main__':
    # Start the HTTP server
    from threading import Thread
    http_thread = Thread(target=run)
    http_thread.start()

    # Start the Socket server
    socket_thread = Thread(target=run_socket_server, args=(UDP_IP, UDP_PORT))
    socket_thread.start()





