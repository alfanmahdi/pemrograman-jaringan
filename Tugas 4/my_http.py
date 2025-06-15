import os.path
from glob import glob
from datetime import datetime
import json

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        self.files_directory = './files/'

    def response(self, kode=404, message='Not Found', messagebody='', headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = [
            f"HTTP/1.1 {kode} {message}\r\n",
            f"Date: {tanggal}\r\n",
            "Connection: close\r\n",
            "Server: myserver/1.0\r\n",
            f"Content-Length: {len(messagebody)}\r\n"
        ]
        for kk, vv in headers.items():
            resp.append(f"{kk}: {vv}\r\n")
        resp.append("\r\n")

        response_headers = "".join(resp)
        
        if isinstance(messagebody, str):
            messagebody = messagebody.encode()

        return response_headers.encode() + messagebody

    def proses(self, data):
        header_bytes, body_bytes = data.split(b'\r\n\r\n', 1)
        header_text = header_bytes.decode('utf-8')

        requests = header_text.split("\r\n")
        baris = requests[0]
        all_headers = [n for n in requests[1:] if n]

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()

            if method == 'GET':
                return self.http_get(object_address)
            elif method == 'POST':
                return self.http_post(object_address, all_headers, body_bytes)
            elif method == 'DELETE':
                return self.http_delete(object_address)
            elif method == 'LIST':
                return self.http_list(object_address)
            else:
                return self.response(405, 'Method Not Allowed', 'Method Not Allowed')

        except IndexError:
            return self.response(400, 'Bad Request', 'Bad Request')
        except Exception as e:
            return self.response(500, 'Internal Server Error', f'Error: {e}')

    def http_get(self, object_address):
        if object_address == "/":
            return self.http_list('.')
            
        file_path = os.path.join(self.files_directory, object_address.strip('/'))

        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as fp:
                isi = fp.read()
            
            fext = os.path.splitext(file_path)[1]
            content_type = self.types.get(fext, 'application/octet-stream')
            
            headers = {'Content-type': content_type}
            return self.response(200, 'OK', isi, headers)
        else:
            return self.response(404, 'Not Found', 'Not Found')

    def http_post(self, object_address, headers, body_bytes):
        file_path = os.path.join(self.files_directory, object_address.strip('/'))

        try:
            with open(file_path, 'wb') as f:
                f.write(body_bytes)
            
            return self.response(201, 'Created', 'File Created')
        except Exception as e:
            return self.response(500, 'Internal Server Error', f'Error: {e}')
    
    def http_delete(self, object_address):
        file_path = os.path.join(self.files_directory, object_address.strip('/'))

        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                os.remove(file_path)
                return self.response(200, 'OK', 'File Deleted')
            except Exception as e:
                return self.response(500, 'Internal Server Error', f'Error: {e}')
        else:
            return self.response(404, 'Not Found', 'Not Found')

    def http_list(self, directory):
        safe_directory_part = directory.lstrip('/')
        safe_path = os.path.abspath(os.path.join(self.files_directory, safe_directory_part))

        if not safe_path.startswith(os.path.abspath(self.files_directory)):
            return self.response(403, "Forbidden", "Access denied.")

        if os.path.exists(safe_path) and os.path.isdir(safe_path):
            try:
                file_list = os.listdir(safe_path)
                files_json = json.dumps(file_list)
                
                headers = {'Content-Type': 'application/json'}
                return self.response(200, 'OK', files_json, headers)
            except Exception as e:
                return self.response(500, 'Internal Server Error', f'{{"error": "{e}"}}')
        else:
            return self.response(404, 'Not Found', '{"error": "Directory not found"}')


if __name__ == "__main__":
    httpserver = HttpServer()
    