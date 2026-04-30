#!/usr/bin/env python3
import socket
import sys
import threading

HOST = "127.0.0.1"
PORT = 5050

active_client = None
active_socket = None
active_lock = threading.Lock()
quit_flag = False


def console_input():
    global active_socket, quit_flag
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            text = line.rstrip("\n")
        except (KeyboardInterrupt, EOFError):
            break

        if text.strip().lower() == "quit":
            print("Quit command received from console. Closing connection and exiting.")
            with active_lock:
                quit_flag = True
                if active_socket is not None:
                    try:
                        active_socket.close()
                    except OSError:
                        pass
            break

        with active_lock:
            client_socket = active_socket

        if client_socket is None:
            print("No active client to send console message to.")
            continue

        try:
            client_socket.sendall((text + "\n").encode("utf-8"))
            print(f"Sent to client: {text}")
        except OSError as exc:
            print(f"Failed to send console message: {exc}")


def handle_client(client_socket, client_address):
    global active_client, active_socket
    with client_socket:
        print(f"Connected by {client_address}")
        while True:
            data = client_socket.recv(1024)
            if not data:
                print(f"Connection closed by {client_address}")
                break
            message = data.decode("utf-8", errors="replace").rstrip("\n")
            print(f"Received from {client_address}: {message}")
            if message.strip().lower() == "quit":
                print(f"Quit phrase received from {client_address}. Closing connection.")
                break
            client_socket.sendall(data)

    with active_lock:
        active_client = None
        active_socket = None


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.settimeout(1.0)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"TCP echo server listening on {HOST}:{PORT}")

    console_thread = threading.Thread(target=console_input, daemon=True)
    console_thread.start()

    while not quit_flag:
        try:
            client_socket, client_address = server_socket.accept()
        except socket.timeout:
            continue
        except OSError:
            break


        with active_lock:
            if quit_flag:
                break
            if active_client is not None and active_client.is_alive():
                print(f"Rejecting additional connection from {client_address}: server is busy.")
                try:
                    client_socket.sendall(b"Server busy. Only one connection allowed.\n")
                except OSError:
                    pass
                client_socket.close()
                continue

            active_socket = client_socket
            active_client = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True,
            )
            active_client.start()
