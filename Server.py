import socket

server_port= 12345
server_IP="localhost"

def load_config_from_file(file_path="input.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            config = {}
            for line in file:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                key, value = line.split(": ", 1)
                config[key.strip()] = value.strip().strip('"')
            print(f"Configuration loaded from file: {file_path}")
            return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file '{file_path}' not found.")
    except Exception as e:
        raise ValueError(f"Error reading configuration file: {e}")

def load_config_from_user():
    config ={}
    config["maximum_msg_size"] = int(input("Enter the maximum message size (bytes): ").strip())
    return config


def process_request(client_socket, max_message_size: int) -> None:
    with client_socket:
        received = {}  # Dictionary to store received messages
        expected_seq = 0  # Tracks the next expected sequence number
        buffer = ""
        adjusted_max_size = max_message_size + 10  # Allow extra space for handling

        try:
            client_address = client_socket.getpeername()
            print(f"[SERVER] Connection established with {client_address}")

            while True:
                # Receive data from the client
                data = client_socket.recv(adjusted_max_size)
                if not data:
                    print(f"[SERVER] Client at {client_address} closed the connection.")
                    break

                # Decode the received data and add it to the buffer
                data = data.decode('utf-8', errors='replace')
                buffer += data
                print(f"[SERVER] Buffer updated: {repr(buffer)}")

                # Process complete messages in the buffer
                while "\n" in buffer:
                    # Split the buffer at the first newline
                    message, buffer = buffer.split("\n", 1)
                    message = message.strip()

                    if not message.startswith("M") or ":" not in message:
                        print(f"[SERVER] Invalid message format: '{message}'")
                        continue

                    try:
                        # Parse the sequence number and content
                        seq_num, content = message.split(":", 1)
                        seq_num = int(seq_num[1:])  # Extract the number after 'M'
                        content = content.strip()
                        print(f"    [Message] M{seq_num}: '{content}'")

                        received[seq_num] = content

                        while expected_seq in received:
                            print(f"    [Processing] M{expected_seq}: '{received[expected_seq]}'")
                            expected_seq += 1

                        ack = f"ACK{expected_seq - 1}\n"
                        client_socket.send(ack.encode('utf-8'))
                        print(f"    [ACK Sent] {ack.strip()}")

                    except (ValueError, IndexError) as e:
                        print(f"[SERVER] Error processing message: '{message}', Error: {e}")
                        continue

        except ConnectionResetError:
            print(f"[SERVER] Connection with {client_address} was reset by the client.")
        except Exception as e:
            print(f"[SERVER] Unexpected error: {e}")



def server(config) -> None:
    max_msg_size=(int(config["maximum_msg_size"]))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((server_IP, server_port))
        server_socket.listen()
        print(f"Server is running on {server_IP}:{server_port} with max message size {max_msg_size} bytes...")
        try:
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    print(f"Connection established with {client_address}")
                    with client_socket:
                        size_message = f"Maximum message size allowed: {max_msg_size} bytes"
                        client_socket.sendall(size_message.encode('utf-8'))
                        process_request(client_socket, max_msg_size)
                except Exception as e:
                    print(f"Error handling client: {e}")
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down...")



if __name__ == "__main__":
    print("Choose configuration option:")
    print("1. Load from file")
    print("2. Enter manually")
    choice = input("Enter your choice (1/2): ").strip()
    if choice == "1":
        config = load_config_from_file("input.txt")
    elif choice == "2":
        config = load_config_from_user()
    else:
        print("Invalid choice. Exiting.")
        exit(1)

    server(config)
