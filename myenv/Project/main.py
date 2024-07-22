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
from multiprocessing import Process


uri = "mongodb://Projectdb:27018"
# uri = os.getenv('MONGO_URI')


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
            self.send_static('index.html', 'text/html')
        elif self.path == '/style.css':
            self.send_static('style.css', 'text/css')
        elif self.path == '/logo.png':
            self.send_static('logo.png', 'image/png')
        elif self.path == '/message.html':
            self.send_static('message.html', 'text/html')
        else:
            self.send_static('error.html', 'text/html')


    def send_file(self, filename,status=200):
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

    def send_static(self, filename, content_type='text/plain'):
        base_path = '/Users/HP/Desktop/4_Computer_systems_Tier2/goit-cs-hw-06/myenv/Project'
        full_path = os.path.join(base_path, filename)
    
        try:
            with open(full_path, 'rb') as file:
                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.send_header("Content-Length", str(os.path.getsize(full_path)))
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, 'File not found')

def run_http_server():
    server_address = ('', HTTPServer_Port)
    http = HTTPServer(server_address, HttpHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def save_data(data):
    client = MongoClient(uri, server_api=ServerApi("1"))
    # db = client.DB_Client
    db = client.Projectdb
    # Вибір колекції для вставки документів
    collection = db['client']
    
    result_one = collection.insert_one(
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
    http_process = Process(target=run_http_server)
    http_process.start()

    # Start the Socket server
    socket_process = Process(target=run_socket_server, args=(UDP_IP, UDP_PORT))
    socket_process.start()

    # Wait for the processes to complete
    http_process.join()
    socket_process.join()
