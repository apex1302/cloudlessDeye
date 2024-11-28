import requests
import csv
import threading
import time
import os
import configparser
import argparse
import tkinter as tk
from tkinter import messagebox, filedialog

# Globale Variable für CSV-Dateinamen
csv_filename = "data.csv"  # Standardname, der später durch die GUI geändert werden kann

# Funktion, um Daten vom Wechselrichter abzurufen
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
        print(f"Error fetching data: {e}")
        return None

# Hilfsfunktion zum Extrahieren von Daten
def extract_data(html_content, var_name):
    try:
        start = html_content.index(f"{var_name} =") + len(f"{var_name} =")
        end = html_content.index(";", start)
        value = html_content[start:end].strip().strip('"')
        return value
    except ValueError:
        return None

# Funktion, um das Polling im Hintergrund zu starten
def start_polling(user, password, ip_inverter, timeout, poll_interval, label_live_data=None, label_status=None):
    while True:
        data = fetch_data(user, password, ip_inverter, timeout=timeout)
        
        if data:
            cur_pow, yie_tod, yie_tot = data
            try:
                # CSV-Datei schreiben, aber ohne Einheiten
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), cur_pow, yie_tod, yie_tot])
                print(f"Live Data - Power: {cur_pow} W, Today: {yie_tod} kWh, Total: {yie_tot} kWh")
                
                # Textausgabe mit Einheiten
                if label_live_data:
                    label_live_data.config(text=f"Power: {cur_pow} W\nToday: {yie_tod} kWh\nTotal: {yie_tot} kWh")
                
                # Statusanzeige
                if label_status:
                    label_status.config(text="Polling Active", fg="green")
            except Exception as e:
                print(f"Error writing to CSV file: {e}")

        time.sleep(poll_interval * 60)

# Funktion, um die Einstellungen in einer INI-Datei zu speichern
def save_settings(entry_user, entry_password, entry_ip, entry_poll_interval, entry_timeout, csv_filename):
    config = configparser.ConfigParser()
    config['Settings'] = {
        'user': entry_user.get(),
        'password': entry_password.get(),
        'ip_inverter': entry_ip.get(),
        'poll_interval': entry_poll_interval.get(),
        'timeout': entry_timeout.get(),
        'csv_filename': csv_filename
    }
    
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

    print("Settings saved.")

# Funktion, um die Einstellungen aus der INI-Datei zu laden
def load_settings():
    config = configparser.ConfigParser()
    
    if os.path.exists('settings.ini'):
        config.read('settings.ini')
        try:
            return {
                'user': config['Settings']['user'],
                'password': config['Settings']['password'],
                'ip_inverter': config['Settings']['ip_inverter'],
                'poll_interval': int(config['Settings']['poll_interval']),
                'timeout': int(config['Settings']['timeout']),
                'csv_filename': config['Settings']['csv_filename']
            }
        except KeyError:
            pass
    return None

# GUI-Funktion (nur gestartet, wenn --pst nicht angegeben wird)
def start_gui():
    global csv_filename  # Verwenden der globalen csv_filename-Variable

    root = tk.Tk()
    root.title("Deye: No Cloud, Just Power")

    label_user = tk.Label(root, text="Username:")
    label_user.grid(row=0, column=0)
    entry_user = tk.Entry(root)
    entry_user.grid(row=0, column=1)

    label_password = tk.Label(root, text="Password:")
    label_password.grid(row=1, column=0)
    entry_password = tk.Entry(root, show="*")
    entry_password.grid(row=1, column=1)

    label_ip = tk.Label(root, text="Inverter IP Address:")
    label_ip.grid(row=2, column=0)
    entry_ip = tk.Entry(root)
    entry_ip.grid(row=2, column=1)

    label_poll_interval = tk.Label(root, text="Polling Interval (Minutes):")
    label_poll_interval.grid(row=3, column=0)
    entry_poll_interval = tk.Entry(root)
    entry_poll_interval.grid(row=3, column=1)

    label_timeout = tk.Label(root, text="Timeout (Seconds):")
    label_timeout.grid(row=4, column=0)
    entry_timeout = tk.Entry(root)
    entry_timeout.grid(row=4, column=1)

    # Anzeige des Dateinamens
    label_csv = tk.Label(root, text=f"CSV saved as: {csv_filename}")
    label_csv.grid(row=5, column=0, columnspan=2)

    # Anzeige der Live-Daten
    label_live_data = tk.Label(root, text="Live data will appear here.")
    label_live_data.grid(row=6, column=0, columnspan=2)

    # Statusanzeige
    label_status = tk.Label(root, text="Polling Disabled", fg="red")
    label_status.grid(row=7, column=0, columnspan=2)

    # Buttons
    start_button = tk.Button(root, text="Start Polling", command=lambda: start_polling_thread(entry_user.get(), entry_password.get(), entry_ip.get(), int(entry_timeout.get()), int(entry_poll_interval.get()), label_live_data, label_status))
    start_button.grid(row=9, column=0, columnspan=2)

    btn_choose_csv = tk.Button(root, text="Choose CSV Save Location", command=lambda: choose_csv_location(label_csv))
    btn_choose_csv.grid(row=10, column=0, columnspan=2)

    btn_save_settings = tk.Button(root, text="Save Settings", command=lambda: save_settings(entry_user, entry_password, entry_ip, entry_poll_interval, entry_timeout, csv_filename))
    btn_save_settings.grid(row=11, column=0, columnspan=2)

    settings = load_settings()
    if settings:
        entry_user.insert(0, settings['user'])
        entry_password.insert(0, settings['password'])
        entry_ip.insert(0, settings['ip_inverter'])
        entry_poll_interval.insert(0, str(settings['poll_interval']))
        entry_timeout.insert(0, str(settings['timeout']))
        csv_filename = settings['csv_filename']
        label_csv.config(text=f"CSV saved as: {csv_filename}")

    try:
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            if file.tell() == 0:
                writer.writerow(['Timestamp', 'Power (W)', 'Today (kWh)', 'Total (kWh)'])
    except Exception as e:
        messagebox.showerror("Error", f"Error creating the CSV file: {e}")

    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

# Funktion, um das Polling in einem separaten Thread zu starten
def start_polling_thread(user, password, ip_inverter, timeout, poll_interval, label_live_data, label_status):
    polling_thread = threading.Thread(target=start_polling, args=(user, password, ip_inverter, timeout, poll_interval, label_live_data, label_status))
    polling_thread.daemon = True
    polling_thread.start()

# Funktion zum Wählen des Speicherorts für die CSV-Datei
def choose_csv_location(label_csv):
    global csv_filename
    new_filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if new_filename:
        csv_filename = new_filename
        label_csv.config(text=f"CSV saved as: {csv_filename}")

# Hauptfunktion
def main():
    parser = argparse.ArgumentParser(description="Inverter Data Polling Tool")
    parser.add_argument('--pst', action='store_true', help="Start without GUI and begin polling.")
    args = parser.parse_args()

    if args.pst:
        settings = load_settings()
        if settings:
            start_polling(settings['user'], settings['password'], settings['ip_inverter'], settings['timeout'], settings['poll_interval'])
        else:
            print("Settings not found. Please configure first.")
    else:
        start_gui()

if __name__ == '__main__':
    main()

