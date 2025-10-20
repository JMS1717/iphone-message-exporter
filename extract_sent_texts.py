
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
    parser = argparse.ArgumentParser(description='Extracts sent SMS and iMessage data from an iPhone backup.')
    parser.add_argument('backup_path', type=str, help='The path to the iPhone backup directory.')
    args = parser.parse_args()

    backup_dir = args.backup_path
    manifest_paths = glob.glob(os.path.join(backup_dir, '*/Manifest.db'))
    if not manifest_paths:
        print(f"Error: Manifest.db not found in subdirectories of {backup_dir}")
        return
    manifest_path = manifest_paths[0]

    output_dir = os.path.join(os.path.dirname(__file__), 'sent_texts')
    os.makedirs(output_dir, exist_ok=True)

    sms_db_path = get_file_path(manifest_path, 'HomeDomain', 'Library/SMS/sms.db')

    if not sms_db_path:
        print("Could not find database paths. Exiting.")
        exit()

    common_phrases = ["yes", "no", "ok", "lol", "thanks"]

    sent_messages = []
    try:
        conn = sqlite3.connect(sms_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                message.text,
                message.date
            FROM
                message
            WHERE
                message.is_from_me = 1
            ORDER BY
                message.date
        """)

        for row in cursor.fetchall():
            text, date = row

            if not text:
                continue

            if text.lower().strip() in common_phrases:
                continue

            if date:
                try:
                    date_in_seconds = date / 1_000_000_000
                    timestamp = datetime.fromtimestamp(date_in_seconds + 978307200)
                except (OSError, OverflowError) as e:
                    print(f"Error converting date: {date}. Error: {e}")
                    timestamp = None
            else:
                timestamp = None
            
            if timestamp:
                sent_messages.append({
                    'timestamp': timestamp,
                    'text': text
                })

        conn.close()
    except sqlite3.Error as e:
        print(f"Error reading SMS database: {e}")

    full_output = ""
    for msg in sent_messages:
        formatted_message = f"[{msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] {msg['text']}\n"
        full_output += formatted_message

    combined_output_path = os.path.join(output_dir, "sent_texts_combined.txt")
    with open(combined_output_path, 'w', encoding='utf-8') as f:
        f.write(full_output)

    max_chars = 750000
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

    print(f"Successfully extracted and formatted sent messages into a combined file and {output_file_count - 1} chunked file(s).")

if __name__ == '__main__':
    main()
