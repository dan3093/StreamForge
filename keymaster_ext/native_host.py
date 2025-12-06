#!/usr/bin/env python3
"""
Native Messaging Host for StreamForge Keymaster.
Receives auth headers from the extension and saves them securely.
"""
import sys
import json
import struct
import os

def get_secure_path():
    """Get the secure auth file path in user's home directory."""
    config_dir = os.path.join(os.path.expanduser("~"), ".streamforge")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "browser.json")

def read_message():
    """Read a message from the extension."""
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    message_length = struct.unpack('=I', raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode('utf-8')
    return json.loads(message)

def send_message(message):
    """Send a message back to the extension."""
    encoded = json.dumps(message).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('=I', len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()

def main():
    message = read_message()
    if message and message.get('action') == 'save_auth':
        try:
            headers = message.get('headers', {})
            path = get_secure_path()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(headers, f, indent=2)
            send_message({'success': True, 'path': path})
        except Exception as e:
            send_message({'success': False, 'error': str(e)})
    else:
        send_message({'success': False, 'error': 'Invalid message'})

if __name__ == '__main__':
    main()
