import socket
import logging

def main():
  server_address = ('172.16.16.101', 45000)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect(server_address)

  try:
    while True:
      user_input = input("TIME/QUIT: ").strip().upper()

      sock.sendall(user_input.encode())

      if user_input == "QUIT":
        logging.info("Connection closed")
        break

      # accept response from server
      response = sock.recv(1024).decode()
      print(response)

  finally:
    sock.close()

if __name__ == "__main__":
  main()