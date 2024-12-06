import requests
import csv
import threading
import time
import os
import configparser
import argparse
import tkinter as tk
from tkinter import messagebox, filedialog

# Global CSV filename
csv_filename = "data.csv"

# Fetch data from inverter
def fetch_data(user, password, ip_inverter, timeout=30):
    url = f"http://{ip_inverter}/status.html"
    try:
        response = requests.get(url, auth=(user, password), timeout=timeout)
        response.raise_for_status()
        cur_pow = extract_data(response.text, "var webdata_now_p")
        yie_tod = extract_data(response.text, "var webdata_today_e")
        yie_tot = extract_data(response.text, "var webdata_total_e")
        return cur_pow, yie_tod, yie_tot
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {ip_inverter}: {e}")
        return None, None, None

# Helper to extract data from HTML response
def extract_data(html_content, var_name):
    try:
        start = html_content.index(f"{var_name} =") + len(f"{var_name} =")
        end = html_content.index(";", start)
        value = html_content[start:end].strip().strip('"')
        return value
    except ValueError:
        return None

# Polling function with command-line output
def start_polling(settings, poll_interval, live_labels=None, status_label=None):
    while True:
        row = [time.strftime('%Y-%m-%d %H:%M:%S')]
        print(f"\nPolling at {row[0]}:")

        for i, inverter in enumerate(settings['inverters']):
            name = inverter['name'] if inverter['name'] else f"Inverter {i + 1}"
            print(f"- {name} (IP: {inverter['ip_inverter']}):")
            data = fetch_data(inverter['user'], inverter['password'], inverter['ip_inverter'], timeout=settings['timeout'])

            if data:
                cur_pow, yie_tod, yie_tot = data
                if cur_pow and yie_tod and yie_tot:
                    print(f"  Power: {cur_pow} W, Today: {yie_tod} kWh, Total: {yie_tot} kWh")
                    row.extend([cur_pow, yie_tod, yie_tot])
                else:
                    print("  Error: Data incomplete")
                    row.extend([None, None, None])
            else:
                print("  Error: Unable to fetch data")
                row.extend([None, None, None])

            # Update live labels in the GUI
            if live_labels:
                if data and cur_pow and yie_tod and yie_tot:
                    live_labels[i].config(text=f"Power: {cur_pow} W\nToday: {yie_tod} kWh\nTotal: {yie_tot} kWh")
                else:
                    live_labels[i].config(text="Error fetching data")

        # Save row to CSV
        try:
            with open(csv_filename, mode='a', newline='') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(row)
            print("Row written to CSV.")
        except Exception as e:
            print(f"Error writing to CSV file: {e}")

        # Update polling status in GUI
        if status_label:
            status_label.config(text="Polling Active", fg="green")

        # Wait for the next poll
        time.sleep(poll_interval * 60)

# Save settings to INI file
def save_settings(entries, entry_poll_interval, entry_timeout, csv_filename):
    config = configparser.ConfigParser()
    config['Settings'] = {
        'poll_interval': entry_poll_interval.get(),
        'timeout': entry_timeout.get(),
        'csv_filename': csv_filename
    }
    for i, inverter in enumerate(entries):
        config[f"Inverter{i + 1}"] = {
            'name': inverter['name'].get(),
            'user': inverter['user'].get(),
            'password': inverter['password'].get(),
            'ip_inverter': inverter['ip'].get()
        }

    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

    print("Settings saved.")

# Load settings from INI file
def load_settings():
    config = configparser.ConfigParser()
    if os.path.exists('settings.ini'):
        config.read('settings.ini')
        try:
            inverters = []
            for i in range(1, 4):
                section = f"Inverter{i}"
                inverters.append({
                    'name': config[section]['name'],
                    'user': config[section]['user'],
                    'password': config[section]['password'],
                    'ip_inverter': config[section]['ip_inverter']
                })
            return {
                'inverters': inverters,
                'poll_interval': int(config['Settings']['poll_interval']),
                'timeout': int(config['Settings']['timeout']),
                'csv_filename': config['Settings']['csv_filename']
            }
        except KeyError:
            pass
    return None

# GUI
def start_gui():
    global csv_filename

    root = tk.Tk()
    root.title("Inverter Status Tool (3 Inverters)")

    entries = []
    live_labels = []

    for i in range(3):
        tk.Label(root, text=f"Inverter {i + 1}").grid(row=i * 5, column=0, columnspan=2, pady=5, sticky='w')
        tk.Label(root, text="Name:").grid(row=i * 5 + 1, column=0, sticky='e')
        entry_name = tk.Entry(root)
        entry_name.grid(row=i * 5 + 1, column=1)

        tk.Label(root, text="IP Address:").grid(row=i * 5 + 2, column=0, sticky='e')
        entry_ip = tk.Entry(root)
        entry_ip.grid(row=i * 5 + 2, column=1)

        tk.Label(root, text="Username:").grid(row=i * 5 + 3, column=0, sticky='e')
        entry_user = tk.Entry(root)
        entry_user.grid(row=i * 5 + 3, column=1)

        tk.Label(root, text="Password:").grid(row=i * 5 + 4, column=0, sticky='e')
        entry_password = tk.Entry(root, show="*")
        entry_password.grid(row=i * 5 + 4, column=1)

        live_label = tk.Label(root, text="Live data will appear here.")
        live_label.grid(row=i * 5 + 5, column=0, columnspan=2)
        live_labels.append(live_label)

        entries.append({'name': entry_name, 'user': entry_user, 'password': entry_password, 'ip': entry_ip})

    tk.Label(root, text="Polling Interval (Minutes):").grid(row=15, column=0, sticky='e')
    entry_poll_interval = tk.Entry(root)
    entry_poll_interval.grid(row=15, column=1)

    tk.Label(root, text="Timeout (Seconds):").grid(row=16, column=0, sticky='e')
    entry_timeout = tk.Entry(root)
    entry_timeout.grid(row=16, column=1)

    label_csv = tk.Label(root, text=f"CSV saved as: {csv_filename}")
    label_csv.grid(row=17, column=0, columnspan=2)

    label_status = tk.Label(root, text="Polling Disabled", fg="red")
    label_status.grid(row=18, column=0, columnspan=2)

    tk.Button(root, text="Start Polling", command=lambda: start_polling_thread(entries, entry_poll_interval, entry_timeout, live_labels, label_status)).grid(row=19, column=0, columnspan=2)
    tk.Button(root, text="Choose CSV Save Location", command=lambda: choose_csv_location(label_csv)).grid(row=20, column=0, columnspan=2)
    tk.Button(root, text="Save Settings", command=lambda: save_settings(entries, entry_poll_interval, entry_timeout, csv_filename)).grid(row=21, column=0, columnspan=2)

    settings = load_settings()
    if settings:
        for i, inverter in enumerate(settings['inverters']):
            entries[i]['name'].insert(0, inverter['name'])
            entries[i]['user'].insert(0, inverter['user'])
            entries[i]['password'].insert(0, inverter['password'])
            entries[i]['ip'].insert(0, inverter['ip_inverter'])
        entry_poll_interval.insert(0, str(settings['poll_interval']))
        entry_timeout.insert(0, str(settings['timeout']))
        csv_filename = settings['csv_filename']
        label_csv.config(text=f"CSV saved as: {csv_filename}")

    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

def start_polling_thread(entries, entry_poll_interval, entry_timeout, live_labels, status_label):
    settings = {
        'inverters': [{'name': e['name'].get(), 'user': e['user'].get(), 'password': e['password'].get(), 'ip_inverter': e['ip'].get()} for e in entries],
        'poll_interval': int(entry_poll_interval.get()),
        'timeout': int(entry_timeout.get())
    }
    threading.Thread(target=start_polling, args=(settings, settings['poll_interval'], live_labels, status_label), daemon=True).start()

def choose_csv_location(label_csv):
    global csv_filename
    new_filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if new_filename:
        csv_filename = new_filename
        label_csv.config(text=f"CSV saved as: {csv_filename}")

def main():
    parser = argparse.ArgumentParser(description="Polling Tool for 3 Inverters")
    parser.add_argument('--pst', action='store_true', help="Start without GUI using settings from the INI file")
    args = parser.parse_args()

    if args.pst:
        settings = load_settings()
        if settings:
            start_polling(settings, settings['poll_interval'])
        else:
            print("Settings not found. Please configure first.")
    else:
        start_gui()

if __name__ == '__main__':
    main()

