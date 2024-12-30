import socket
import time

SERVER_NAME = "localhost"
SERVER_PORT = 12345


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
    config["message"] = input("Enter your message: ").strip()
    config["window_size"] = input("Enter window size: ").strip()
    config["timeout"] = input("Enter timeout: ").strip()
    return config


def parse_ack(data: str) -> list[int]:
    try:
        ack_parts = data.split("ACK")
        ack_numbers = []
        for part in ack_parts:
            if part.strip().isdigit():
                ack_numbers.append(int(part.strip()))
        if not ack_numbers:
            raise ValueError(f"Invalid ACK format: {data}")
        return ack_numbers
    except Exception as e:
        print(f"Error parsing ACK:{e} ")
        raise ValueError("Invalid message format")


def split_message(message, max_size):
    message_bytes = message.encode("utf-8")
    message_size = len(message_bytes)
    print(f"The original message is {message}")
    print(f"original message size {message_size}")
    if message_size <= max_size:
        return [f"M0: {message}"]
    num_chunks = (message_size + max_size - 1) // max_size
    print(f"The message will be split into {num_chunks} chunks.")
    labeled_chunks = []
    for i in range(num_chunks):
        start = i * max_size
        end = min(start + max_size, message_size)
        label = f"M{i}: "
        chunk = message_bytes[start:end].decode("utf-8", errors="ignore")
        labeled_chunks.append(label + chunk)
    return labeled_chunks


def send_data(client_socket, message, max_size, window_size, timeout):
    chunks = split_message(message, max_size)
    total_chunks = len(chunks)
    base = 0
    next_seq = 0
    timer_start = None
    print(f"The window size is {window_size}")

    while base < total_chunks:
        # שליחת מקטעים בתוך החלון הזז
        while next_seq < base + window_size and next_seq < total_chunks:
            chunk = chunks[next_seq] + "\n"
            print(f"Sending chunk {next_seq}: {chunk.strip()}")
            client_socket.sendall(chunk.encode("utf-8"))
            if timer_start is None:  # התחלת טיימר רק בהודעה הראשונה
                timer_start = time.time()
            next_seq += 1

        # קבלת אישורים (ACK)
        try:
            while base < next_seq:
                client_socket.settimeout(timeout)
                ack = client_socket.recv(1024).decode("utf-8")
                ack_nums = parse_ack(ack)  # פירוק האישור למספרים
                print(f"[ACK RECEIVED] ACK: {ack_nums}")
                if ack_nums:
                    base = max(ack_nums) + 1  # עדכון הבסיס לחלון
                    timer_start = None  # איפוס הטיימר אם התקבלו כל האישורים

        except socket.timeout:
            print("Timeout occurred. Resending unacknowledged messages...")
            for i in range(base, next_seq):  # שליחה מחדש של מקטעים לא מאושרים
                chunk = chunks[i] + "\n"
                print(f"Resending chunk {i}: {chunk.strip()}")
                client_socket.sendall(chunk.encode("utf-8"))
            timer_start = time.time()  # עדכון זמן התחלה לאחר שליחה מחדש

    print("All chunks sent, all ACKs received. Closing connection.")
    client_socket.close()




def client(server_address, server_port, config):
    message = config["message"]
    sliding_window_size = int(config["window_size"])
    timeout = int(config["timeout"])

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_address, server_port))

    print(f"Connected to server at {server_address}:{server_port}")
    max_size_message = client_socket.recv(1024).decode("utf-8")
    print(f"Server says: {max_size_message}")

    if max_size_message.startswith("Maximum message size allowed: "):
        max_size = int(max_size_message.split(": ")[1].split()[0])
    else:
        raise ValueError("Invalid message format from server.")
    send_data(client_socket, message, max_size, sliding_window_size, timeout)
    client_socket.close()
    print("Disconnected from the server.")



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
    client(SERVER_NAME, SERVER_PORT, config)

