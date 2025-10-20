
import sqlite3
import os
from datetime import datetime
import glob
import argparse

def get_file_path(manifest_path, domain, relative_path):
    conn = sqlite3.connect(manifest_path)
    cursor = conn.cursor()
    cursor.execute(f"
        SELECT fileID FROM Files WHERE domain = '{domain}' AND relativePath = '{relative_path}'
    ")
    result = cursor.fetchone()
    conn.close()
    if result:
        file_id = result[0]
        return os.path.join(os.path.dirname(manifest_path), file_id[:2], file_id)
    return None

def main():
    parser = argparse.ArgumentParser(description='Extracts SMS and iMessage data from an iPhone backup.')
    parser.add_argument('backup_path', type=str, help='The path to the iPhone backup directory.')
    args = parser.parse_args()

    backup_dir = args.backup_path
    manifest_paths = glob.glob(os.path.join(backup_dir, '*/Manifest.db'))
    if not manifest_paths:
        print(f"Error: Manifest.db not found in subdirectories of {backup_dir}")
        return
    manifest_path = manifest_paths[0]

    output_dir = os.path.join(os.path.dirname(__file__), 'text_messages')
    os.makedirs(output_dir, exist_ok=True)

    sms_db_path = get_file_path(manifest_path, 'HomeDomain', 'Library/SMS/sms.db')
    address_book_path = get_file_path(manifest_path, 'HomeDomain', 'Library/AddressBook/AddressBook.sqlitedb')

    if not sms_db_path or not address_book_path:
        print("Could not find database paths. Exiting.")
        exit()

    # 1. Read Address Book
    contacts = {}
    try:
        conn = sqlite3.connect(address_book_path)
        cursor = conn.cursor()
        cursor.execute(""
            SELECT
                p.ROWID,
                p.First,
                p.Last,
                mv.value
            FROM
                ABPerson as p
            JOIN
                ABMultiValue as mv ON mv.record_id = p.ROWID
            WHERE
                mv.property = 3
        ")
        for row in cursor.fetchall():
            person_id, first, last, phone = row
            if phone:
                name = " ".join(filter(None, [first, last]))
                if name:
                    normalized_phone = ''.join(filter(str.isdigit, phone))
                    contacts[normalized_phone] = name
        conn.close()
    except sqlite3.Error as e:
        print(f"Error reading address book: {e}")

    # 2. Read SMS database
    messages_by_thread = {}
    try:
        conn = sqlite3.connect(sms_db_path)
        cursor = conn.cursor()
        cursor.execute(""
            SELECT
                chat.chat_identifier,
                handle.id,
                message.text,
                message.is_from_me,
                message.date
            FROM
                message
            LEFT JOIN
                chat_message_join ON chat_message_join.message_id = message.ROWID
            LEFT JOIN
                chat ON chat.ROWID = chat_message_join.chat_id
            LEFT JOIN
                handle ON handle.ROWID = message.handle_id
            ORDER BY
                chat.chat_identifier, message.date
        ")

        for row in cursor.fetchall():
            chat_identifier, handle_id, text, is_from_me, date = row
            if not chat_identifier:
                continue

            if chat_identifier not in messages_by_thread:
                messages_by_thread[chat_identifier] = []

            if date:
                try:
                    date_in_seconds = date / 1_000_000_000
                    timestamp = datetime.fromtimestamp(date_in_seconds + 978307200)
                except (OSError, OverflowError) as e:
                    print(f"Error converting date: {date}. Error: {e}")
                    timestamp = None
            else:
                timestamp = None

            normalized_handle_id = ''.join(filter(str.isdigit, handle_id)) if handle_id else ''
            
            sender = "Me" if is_from_me else contacts.get(normalized_handle_id, handle_id)
            receiver = chat_identifier if is_from_me else "Me"

            messages_by_thread[chat_identifier].append({
                'timestamp': timestamp,
                'sender': sender,
                'receiver': receiver,
                'text': text
            })
        conn.close()
    except sqlite3.Error as e:
        print(f"Error reading SMS database: {e}")

    # 3. Format and write output
    full_output = ""
    sorted_chat_identifiers = sorted(messages_by_thread.keys())

    for chat_identifier in sorted_chat_identifiers:
        messages = messages_by_thread[chat_identifier]
        
        normalized_chat_identifier = ''.join(filter(str.isdigit, chat_identifier))
        chat_name = contacts.get(normalized_chat_identifier, chat_identifier)
        full_output += f"--- Conversation with {chat_name} ---

"

        for msg in messages:
            if msg['timestamp'] and msg['text']:
                formatted_message = f"[{msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] {msg['sender']}: {msg['text']}\n"
                full_output += formatted_message
        full_output += "\n"

    combined_output_path = os.path.join(output_dir, "all_messages_combined.txt")
    with open(combined_output_path, 'w', encoding='utf-8') as f:
        f.write(full_output)

    max_chars = 3500000
    output_file_count = 1
    start_index = 0
    while start_index < len(full_output):
        end_index = start_index + max_chars
        chunk = full_output[start_index:end_index]
        
        output_path = os.path.join(output_dir, f"pt {output_file_count}.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chunk)
            
        output_file_count += 1
        start_index = end_index

    print(f"Successfully extracted and formatted messages into a combined file and {output_file_count - 1} chunked file(s).")

if __name__ == '__main__':
    main()
