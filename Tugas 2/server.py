from socket import *
import socket
import threading
import logging
import time

class ProcessTheClient(threading.Thread):
  def __init__(self,connection,address):
    self.connection = connection
    self.address = address
    threading.Thread.__init__(self)

  def run(self):
    while True:
      data = self.connection.recv(32)
      if data:
        # get request
        request = data.decode()
        logging.info(f"Request from client {self.address}: {request}")

        if request == "TIME":
          current_time = time.strftime("%H:%M:%S")
          response = f"JAM {current_time}"
          self.connection.sendall(response.encode())
          logging.info(f"Sent to {self.address}: {response.strip()}")
        elif request == "QUIT":
          self.connection.close()
          break
        else:
          self.connection.sendall(b"Invalid request")
      else:
        break
    self.connection.close()

class Server(threading.Thread):
  def __init__(self):
    self.the_clients = []
    self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    threading.Thread.__init__(self)

  def run(self):
    self.my_socket.bind(('0.0.0.0',45000))
    self.my_socket.listen(1)
    while True:
      self.connection, self.client_address = self.my_socket.accept()
      logging.warning(f"connection from {self.client_address}")

      clt = ProcessTheClient(self.connection, self.client_address)
      clt.start()
      self.the_clients.append(clt)


def main():
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
  svr = Server()
  svr.start()

if __name__=="__main__":
  main()