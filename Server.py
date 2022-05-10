from multiprocessing.dummy import Pool as ThreadPool
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from pythonping import ping
import mysql.connector, threading, logging, socket, logging, time
import logging, asyncio
from aiogram import Bot, Dispatcher
from aiogram.utils import exceptions, executor
from datetime import datetime

API_TOKEN = open("telegram-key.txt", "r").read()
pool = ThreadPool(3)
all_data = [[], [1920, 1080], [], [{}]]
# [all devices] - [settings] - [towers] - [models]
ips = []
ping_data = []
dellay = 4
move_data = []
add_temp = []
users = {}
username = ""
all_devices = 0
timeout_list = []
log_data = []
user_list = []
timeout_list = []

log = logging.getLogger('broadcast')
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

try:
    conn = mysql.connector.connect(host='localhost', database='roshan', user='root', password='123456')
    if conn.is_connected():
        db_Info = conn.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = conn.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)
except:
    print("Error while connecting to MySQL")

# Update sql structure
class update:
    def __init__(self, table_name, table_set, new_variable, table_variable_where, target_variable):
        self.table_name = table_name
        self.table_set = table_set
        self.new_variable = new_variable
        self.table_variable_where = table_variable_where
        self.target_variable = target_variable
    
    def update_sql(self, conn):
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {self.table_name} SET {self.table_set} = '{self.new_variable}' WHERE {self.table_variable_where} = ('{self.target_variable}')")
        conn.commit()

# Delete sql structure
class delete:
    def __init__(self, from_table, where_field, target_name):
        self.from_table = from_table
        self.where_field = where_field
        self.target_field = target_name
    
    def delete_sql(self, conn):
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.from_table} WHERE {self.where_field} = '{self.target_field}'")
        conn.commit()

# Read and make a dic from sql
def read_from_sql():
    cursor.execute('SELECT * FROM devices')
    for row in cursor:
        all_data[0].append({'id': row[0], 'tower_name': row[1], 'device_name': row[2], 'ip': row[3], 'ping': "", 'mode': row[4], 'models': row[5], 'os': row[6], 'status': row[7], 'time_active' : row[8], 'area': row[9], 'delta_time': "", 'notification': row[10]})
        if row[7] == "enable":
            ips.insert(0, row[3])
        
    # make dictionary from towers name
    cursor.execute('SELECT * FROM towers')
    for row in cursor:
        all_data[2].append({'id': row[0], 'tower_name': row[1], 'top': row[2], 'left': row[3], 'address': row[4]})

    # make list from users
    cursor.execute('SELECT * FROM users')
    for row in cursor:
        users[row[2]] = {'id': row[0], 'rank': row[1], 'username': row[2], 'password': row[3], 'firstname': row[4], 'lastname': row[5]}
        user_list.append({'username': row[2]})

    # log
    cursor.execute('SELECT * FROM log')
    for row in cursor:
        log_data.append({'id': row[0], 'date': row[1], 'event': row[2], 'operatore': row[3]})

    # make a list from models
    cursor.execute('SELECT * FROM models')
    for row in cursor:
        all_data[3][0][row[1]] = row[2]
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

read_from_sql()

def log_page(event):
    log_date_and_time = time.localtime()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO log (date, event, operatore) VALUES (%s, %s, %s)", (log_date_and_time, event, "admin"))
    log_data.clear()
    cursor.execute('SELECT * FROM log')
    for row in cursor:
        log_data.append({'id': row[0], 'date': row[1], 'event': row[2], 'operatore': row[3]})
    conn.commit()

# Update towers list
def update_towers():
    towers_temp = []
    cursor.execute('SELECT * FROM towers')
    for row in cursor:
        towers_temp.append({'id': row[0], 'tower_name': row[1], 'top': row[2], 'left': row[3], 'address': row[4]})
    all_data[2] = []
    all_data[2] = towers_temp

# sort towers by id
def sort_towers_id():
    list_old = []
    for data in all_data[2]:
        list_old.append(data['id'])
    counter = 1
    for qw in list_old:
        update_command = update("towers", "id", counter, "id", qw)
        update_command.update_sql(conn)
        counter = counter + 1

# Create towers
def create_tower(add_tower_name, new_tower_address):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO towers (tower_name, top_pos, left_pos, address) VALUES (%s, %s, %s, %s)", (add_tower_name, "200px", "200px", new_tower_address))
    conn.commit()
    update_towers()
    sort_towers_id()
    update_towers()

# Update tower position
def update_tower_position(move_data):
    for tower_position in move_data:
        cursor = conn.cursor()
        cursor.execute(f" UPDATE towers SET top_pos = '{tower_position.get('top')}', left_pos = '{tower_position.get('left')}' WHERE Id = {tower_position.get('id')} ")
        conn.commit()
        update_towers()
        move_data = []

# check tower name if allready exist
def check_tower_name(new_tower_name):
    if len(all_data[2]) == 0:
        return False
    else:
        for i in all_data[2]:
            if i['tower_name'] == new_tower_name:
                return True
            else:
                return False

# Check ip format
def ip_format_check(device_ip):
    try:
        socket.inet_aton(device_ip)
        return True
    except socket.error:
        return False

# Add device
def add_device(new_device_name, new_device_ip, get_tower_name, get_mode, get_model, area):
    os = all_data[3][0].get(f"{get_model}")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO devices (tower_name, device_name, ip, mode, models, os, status, time_active, area) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (get_tower_name, new_device_name, new_device_ip, get_mode, get_model, os, "enable", "", area))
    conn.commit()
    update_devices()

# check device name for allready exist
def check_device_name(new_device_name):
    for i in all_data[0]:
        if i['device_name'] == new_device_name:
            return True
        else:
            return False

# check if ip address exist
def check_ip_exist(new_ip):
    for i in all_data[0]:
        if i['ip'] == new_ip:
            return True
        else:
            return False

# Update device list
def update_devices():
    global ips
    all_data[0] = []
    ips = []
    cursor.execute('SELECT * FROM devices')
    for row in cursor:
        all_data[0].append({'id': row[0], 'tower_name': row[1], 'device_name': row[2], 'ip': row[3], 'ping': "", 'mode': row[4], 'models': row[5], 'os': row[6], 'status': row[7], 'time_active' : row[8], 'area': row[9]})
        if row[7] == "enable":
            ips.insert(0, row[3])

# Add model
def add_model(new_device_model, new_device_os):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO models (models, os) VALUES (%s, %s)", (new_device_model, new_device_os))
    all_data[3][0] = {}
    cursor.execute('SELECT * FROM models')
    for row in cursor:
        all_data[3][0][row[1]] = row[2]
    conn.commit()

# Ping Calc
def ping_system(ip):
    result = ping(ip, size=1, count=1)
    if result.rtt_avg_ms == 2000:
        ping_data.append({'ip': ip, 'ping': "Request timeout"})
    else:
        ping_data.append({'ip': ip, 'ping': result.rtt_avg_ms})

def replace():
    counter = 0
    while counter < len(ping_data):
        finder = next((index for (index, d) in enumerate(all_data[0]) if d["ip"] == ping_data[counter]["ip"]), None)
        if ping_data[counter]["ping"] == "Request timeout":
            time_sructure.insert(counter, finder)
        else:
            all_data[0][finder]['ping'] = ping_data[counter]["ping"]
            time_sructure.remove(counter)
        counter = counter + 1

class time_sructure:
    def update(id, status_time_out):
        cursor = conn.cursor()
        cursor.execute(f"UPDATE devices SET time_active = '{status_time_out}' WHERE id = ('{id}')")
        conn.commit()

    def delta_time():
        for id, data in enumerate(all_data[0]):
            if data['time_active'] == "":
                pass
            else:
                temp_time = data['time_active'].replace("/", " ").replace(":", " ").split()
                old_time = datetime(int(temp_time[0]), int(temp_time[1]), int(temp_time[2]), int(temp_time[3]), int(temp_time[4]))
                real_time = datetime.now()
                dif = real_time - old_time
                # send telegram msg if device down
                if round(dif.seconds) >= 2:
                    if all_data[0][id]['notification'] == "no":
                        print(all_data[0][id - 1]['notification'])
                        device_name = data['device_name']
                        telegram_msg = f'{device_name} is down'
                        executor.start(dp, telegram.broadcaster(telegram_msg))
                        all_data[0][id]['notification'] = "yes"
                        update_command = update("devices", "notification", "yes", "device_name", all_data[0][id]['device_name'])
                        update_command.update_sql(conn)

                recap = str(dif).replace(":", " ").split()
                if len(recap) == 3:
                    delta_time = f'{recap[0]}:{recap[1]}'
                    all_data[0][id]['delta_time'] = str(delta_time)

    # insert in timeout dict
    def insert(counter, finder):
        if not timeout_list:
            tto = time.localtime()
            tto = f'{tto[3]}{tto[4]}{tto[5]}'
            timeout_list.append({'ip': ping_data[counter]["ip"], 'time': tto})
        else:
            t = 0
            while True:
                if len(timeout_list) == t:
                    tto = time.localtime()
                    tto = f'{tto[3]}{tto[4]}{tto[5]}'
                    timeout_list.append({'ip': ping_data[counter]["ip"], 'time': tto})
                    break
                elif ping_data[counter]['ip'] == timeout_list[t]['ip']:
                    tto = time.localtime()
                    tto = f'{tto[3]}{tto[4]}{tto[5]}'
                    calc_time = int(tto) - (int(timeout_list[t]['time']))
                    if calc_time > 5:
                        all_data[0][finder]['ping'] = "Request timeout"
                        if all_data[0][finder]['time_active'] == "":
                            status_time_out = time.localtime()
                            status_time_out = f'{status_time_out[0]}/{status_time_out[1]}/{status_time_out[2]} {status_time_out[3]}:{status_time_out[4]}'
                            all_data[0][finder]['time_active'] = status_time_out
                            id = all_data[0][finder]['id']
                            time_sructure.update(id, status_time_out)
                    break
                else:
                    t = t + 1

    # remove from timeout_list
    def remove(counter):
        for tol_id, tol in enumerate(timeout_list):
            if ping_data[counter]['ip'] == timeout_list[tol_id]['ip']:
                for v in all_data[0]:
                    if v['ip'] == ping_data[counter]['ip']:
                        id = v['id']
                        empty = ""
                        ip = ping_data[counter]['ip']
                        time_sructure.update(id, empty)
                timeout_list.remove(timeout_list[tol_id])
                # for find time in all_data
                for id, e in enumerate(all_data[0]):
                    if e['ip'] == ip:
                        all_data[0][id]['time_active'] = ""
                        if all_data[0][id]['notification'] == "yes":
                            all_data[0][id]['notification'] = "no"
                            device_name = all_data[0][id]['device_name']
                            telegram_msg = f'{device_name} is up'
                            executor.start(dp, telegram.broadcaster(telegram_msg))
                            update_command = update("devices", "notification", "no", "device_name", all_data[0][id]['device_name'])
                            update_command.update_sql(conn)
                        break
                break

def user_register(new_rank, new_firstname, new_lastname, new_username, new_password, users):
    if new_username in users:
        error = f"{new_username} is allready exist"
        return error
    else:
        cursor.execute("INSERT INTO users (rank_user, username, password, firstname, lastname) VALUES (%s, %s, %s, %s, %s)", (new_rank, new_username, new_password, new_firstname, new_lastname))
        conn.commit()
        error = "user registered successfully"
        return error

def user_list_update():
    global users
    user_temp = {}
    user_list.clear()
    cursor.execute('SELECT * FROM users')
    for row in cursor:
        user_temp[row[2]] = {'id': row[0], 'rank': row[1], 'username': row[2], 'password': row[3], 'firstname': row[4], 'lastname': row[5]}
        user_list.append({'username': row[2]})
    users = {}
    users = user_temp

def user_check_rank(username_ch, users):
    if username_ch in users:
        user = users[username_ch]
        if not "3" == user['rank']:
            return False
        else:
            return True

class telegram:
    async def send_message(user_id: int, text: str, disable_notification: bool = False) -> bool:
        try:
            await bot.send_message(user_id, text, disable_notification=disable_notification)
        except exceptions.BotBlocked:
            log.error(f"Target [ID:{user_id}]: blocked by user")
        except exceptions.ChatNotFound:
            log.error(f"Target [ID:{user_id}]: invalid user ID")
        except exceptions.RetryAfter as e:
            log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            return await telegram.send_message(user_id, text)
        except exceptions.UserDeactivated:
            log.error(f"Target [ID:{user_id}]: user is deactivated")
        except exceptions.TelegramAPIError:
            log.exception(f"Target [ID:{user_id}]: failed")
        else:
            log.info(f"Target [ID:{user_id}]: success")
            return True
        return False

    async def broadcaster(alert):
        user_id = 689643466
        try:
            await telegram.send_message(user_id, alert)
            # await asyncio.sleep(.05)
        except:
            pass

# start flask server
def flask():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.secret_key = "hi"
    
    # Data pass through
    @app.route('/_stuff', methods=['GET', 'Post'])
    def stuff():
        if request.method == 'POST':
            move_data = []
            move_data = request.get_json()
            update_tower_position(move_data)
        return jsonify(alldata=all_data)

    # Login
    @app.route("/", methods=['GET', 'POST'])
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if username not in users:
                error = 'You have entered an invalid username or password'
            else:
                user = users[username]
                if not password == user["password"]:
                    error = 'You have entered an invalid username or password'
                else:
                    session["username"] = username
                    log_page(f'user {username} login in')
                    return redirect(url_for('solar'))
        else:
            if "username" in session:
                return redirect(url_for('solar'))
        return render_template('login.html', error=error, alldata=all_data)

   # for naughty users
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('wrong-page.html'), 404
    app.register_error_handler(404, page_not_found)

    # Solar page
    @app.route("/solar")
    def solar():
        global username
        if "username" in session:
            username = session["username"]
            if len(all_data[2]) == 0:
                return render_template('solar_empty.html', alldata=all_data, username=username)
            else:
                return render_template('solar.html', alldata=all_data, username=username)
        else:
            return redirect(url_for('login'))

    # logout page
    @app.route("/logout")
    def logout():
        session.pop("username", None)
        return redirect(url_for('login'))

    # Move
    @app.route("/move", methods=['POST', 'GET'])
    def move():
        global username
        if "username" in session:
            username = session["username"]
            username_ch = session["username"]
            # check username rank for access this page
            if user_check_rank(username_ch, users) == True:
                return render_template('move.html', username=username, all_data=all_data)
            else:
                return render_template('denied.html', username=username)
        else:
            return redirect(url_for('login'))

    # Dashboard
    @app.route("/dashboard", methods=['POST', 'GET'])
    def dashboard():
        global username
        if "username" in session:
            username = session["username"]
            all_devices = len(all_data[0])
            all_towers =  len(all_data[2])
            return render_template('dashboard.html', username=username, all_devices=all_devices, all_towers=all_towers)
        else:
            return redirect(url_for('login'))

    # log
    @app.route("/log")
    def log():
        if "username" in session:
            username = session["username"]
            return render_template("log.html", username=username, log_data=log_data)
        else:
            return redirect(url_for('login'))

    # SSH Section
    @app.route("/ssh", methods=['POST', 'GET'])
    def ssh():
        if "username" in session:
            return render_template("ssh.html")
        else:
            return redirect(url_for('login'))

    # panel
    @app.route("/panel", methods=['POST', 'GET'])
    def panel():
        error = None
        global username
        global user_list

        # Add tower
        if request.method == 'POST':
            if request.form['submit'] == 'Add Tower':
                new_tower_name = request.form['tower_name']
                new_tower_address = request.form['address']
                if new_tower_name == "" or new_tower_address == "":
                    error = 'Empty - Choose a name or address for your tower'
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                else:
                    if check_tower_name(new_tower_name) == False:
                        create_tower(new_tower_name, new_tower_address)
                        error = f'{new_tower_name} added successfully'
                        log_page(error)
                        return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                    else:
                        error = f'{new_tower_name} is all ready exist'
                        return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)

           # Add device
            if request.form['submit'] == 'ADD DEVICE':
                new_device_name = request.form['radio_name']
                new_device_ip = request.form['radio_ip']
                get_tower_name = request.form['tower_name']
                get_mode = request.form['mode']
                get_model = request.form['models']
                area = request.form['area']
                if "" in (new_device_name, new_device_ip, get_tower_name, get_mode, get_model, area):
                    error = 'One of these fields are empty'
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                else:
                    if check_device_name(new_device_name) == True:
                        error = f'{new_device_name} is all ready exist'
                        return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                    else:
                        if ip_format_check(new_device_ip) == True:
                            add_device(new_device_name, new_device_ip, get_tower_name, get_mode, get_model, area)
                            error = f'device name {new_device_name} whit ip {new_device_ip} successfully added'
                            log_page(error)
                            return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                        else:
                            error = f'ip {new_device_ip} is incorect'
                            return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)

            # delete device
            if request.form['submit'] == 'Delete device name':
                delete_devive_name = request.form['target_device_name']
                if "None" in delete_devive_name:
                    error = f"choose a device name"
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                else:
                    delete_command = delete("devices", "device_name", delete_devive_name)
                    delete_command.delete_sql(conn)
                    update_devices()
                    error = f"device {delete_devive_name} deleted Successfully"
                    log_page(error)
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)

            # delete tower name
            if request.form['submit'] == 'Delete Tower':
                delete_tower_name = request.form['delete']
                if "None" in delete_tower_name:
                    error = "Choose a tower"
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                else:
                    error = f"{delete_tower_name} deleted Successfully"
                    delete_command = delete("towers", "tower_name", delete_tower_name)
                    delete_command.delete_sql(conn)
                    update_devices()
                    update_towers()
                    sort_towers_id()
                    update_towers()
                    log_page(error)
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)

            # Edit tower name
            if request.form['submit'] == 'Change tower name':
                target_tower_name = request.form['target_tower_name']
                new_tower_name = request.form['new_tower_name']
                if new_tower_name == "":
                    error = "Choose a new name for your tower"
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                else:
                    if check_tower_name(new_tower_name) == False:
                        update_command = update("towers", "tower_name", new_tower_name, "tower_name", target_tower_name)
                        update_command.update_sql(conn)
                        update_command = update("devices", "tower_name", new_tower_name, "tower_name", target_tower_name)
                        update_command.update_sql(conn)
                        update_towers()
                        update_devices()
                        error = f"Successfully changed from {target_tower_name} to {new_tower_name}"
                        log_page(error)
                        return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                    else:
                        error = f'{new_tower_name} is all ready exist'
                        return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)

            # Rename device name
            if request.form['submit'] == 'Change radio name':
                target_device_name = request.form['target_radio_name']
                new_device_name = request.form['new_radio_name']
                if new_device_name == "" or target_device_name == "None":
                    error = "Choose a new name for your device or select a device"
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                else:
                    if check_device_name(new_device_name) == True:
                            error = f'{new_device_name} is all ready exist'
                            return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                    else:
                        update_command = update("devices", "device_name", new_device_name, "device_name", target_device_name)
                        update_command.update_sql(conn)
                        update_devices()
                        error = f"Successfully changed from {target_device_name} to {new_device_name}"
                        log_page(error)
                        return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)

            # Add device model and os
            if request.form['submit'] == 'add device model':
                new_device_model = request.form['device_model']
                new_device_os = request.form['device_os']
                if new_device_model == "" or new_device_os == "":
                    error = "type device model or OS name"
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                else:
                    error = f"{new_device_model} with os {new_device_os} was added"
                    add_model(new_device_model, new_device_os)
                    log_page(error)
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)

            # Register user
            if request.form['submit'] == 'REGISTER':
                new_rank = request.form['rank']
                new_firstname = request.form['firstname']
                new_lastname = request.form['lastname']
                new_username = request.form['new_username']
                new_password = request.form['new_password']
                if new_firstname == "" or new_lastname == "" or new_username == "" or new_password == "" or new_rank == "None":
                    error = "one of the fields are empty"
                    return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)
                else:
                    error = user_register(new_rank, new_firstname, new_lastname, new_username, new_password, users)
                    user_list_update()
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)

            # Remove user
            if request.form['submit'] == 'Remove user':
                target_user = request.form['target_user']
                if target_user == "None":
                    error = "Select a user to remove"
                    return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)
                else:
                    delete_command = delete("users", "username", {target_user})
                    delete_command.delete_sql(conn)
                    user_list_update()
                    error = f'User {target_user} deleted'
                    log_page(error)
                    return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)
            
            # change rank for user
            if request.form['submit'] == 'Change rank':
                target_user_rank = request.form['target_user_rank']
                new_rank_user = request.form['new_rank_user']
                if target_user_rank == "None" or new_rank_user == "None":
                    error = "select a user or rank"
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)
                else:
                    update_command = update("users", "rank_user", new_rank_user, "username", target_user_rank)
                    update_command.update_sql(conn)
                    user_list_update()
                    error = f'User rank changed from {target_user_rank} to {new_rank_user}'
                    log_page(error)
                    return render_template('panel.html', error=error, all_data=all_data, username=username, user_list=user_list)

            # change device ip
            if request.form['submit'] == 'change ip':
                target_ip = request.form['target_ip']
                new_ip = request.form['new_ip_device']
                if target_ip == "None" or new_ip == "None":
                    error = "select your target ip or input your ip address"
                    return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)
                else:
                    if ip_format_check(new_ip) == True:
                        if check_ip_exist(new_ip) == True:
                            error = f"{new_ip} is allready exist"
                            return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)
                        else:
                            update_command = update("devices", "ip", new_ip, "ip", target_ip)
                            update_command.update_sql(conn)
                            update_devices()
                            error = f"device ip changed from {target_ip} to {new_ip}"
                            log_page(error)
                            return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)

            # change device status
            if request.form['submit'] == 'Apply':
                target_device = request.form['target_device']
                status_mode = request.form['status_mode']
                if target_device == "None" or status_mode == " None":
                    error = "Select a device or status for device"
                    return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)
                else:
                    update_command = update("devices", "status", status_mode, "devies_name", target_device)
                    update_command.update_sql(conn)
                    update_devices()
                    error = f"status changes for device {target_device} to {status_mode}"
                    log_page(error)
                    return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)

            # change device mode
            if request.form['submit'] == 'Change mode':
                ch_target_device_mode = request.form['ch_target_device_mode']
                ch_device_mode = request.form['ch_device_mode']
                if ch_target_device_mode == "None" or ch_device_mode == "None":
                    error = "Select a device or mode for make changes"
                    return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)
                else:
                    update_command = update("devices", "mode", ch_device_mode, "device_name", ch_target_device_mode)
                    update_command.update_sql(conn)
                    update_devices()
                    error = f"{ch_device_mode} mode changed to {ch_device_mode}"
                    log_page(error)
                    return render_template('panel.html', error=error, all_data=all_data, username=username,user_list=user_list)

        else:
            if "username" in session:
                username = session["username"]
                username_ch = session["username"]
                # check username rank for access this page
                if user_check_rank(username_ch, users) == True:
                    return render_template('panel.html', username=username, all_data=all_data, user_list=user_list)
                else:
                    return render_template('denied.html', username=username)
            else:
                return redirect(url_for('login'))

    if __name__ == '__main__':
        from waitress import serve
        serve(app, host="192.168.3.20", port=80)

# command console
def console():
    help_command = [".register [firstname] [lastname] [username] [passsword] [rank 1-3 (1-User | 2-ban | 3-God)]", ".changerank [user target] [rank 1-3 (1-User | 2-Ban | 3-God)]", ".reload [database]"]
    print("Type .help command name")
    while True:
        command = input("Command me: ")
        try:
            if command == ".help":
                for help in help_command:
                    print(help)
            else:
                if command.split()[0] == ".register":
                    if (len(command.split())) == 6:
                        print(user_register(command.split()[5], command.split()[1], command.split()[2], command.split()[3], command.split()[4], users))
                        user_list_update()
                    else:
                        print(".register [firstname] [lastname] [username] [passsword] [rank 1-3]")
                if command.split()[0] == ".changerank":
                    if (len(command.split())) == 3:
                        if int(command.split()[2]) in range(1, 4, 1):
                            update_command = update("users", "rank_user", command.split()[2], "username", command.split()[1])
                            update_command.update_sql(conn)
                            user_list_update()
                        else:
                            print("rank number is not in range")
                    else:
                        print(".change-rank [user target] [user rank]")
                if command.split()[0] == ".reload":
                    if command.split()[1] == "devices":
                        update_devices()
        except:
            print('Command does not exist')
            
# flask start thread section
flask_thread = threading.Thread(target=flask)
flask_thread.start()

# Console Command thread
console_thread = threading.Thread(target=console)
console_thread.start()

# Loop calc
while True:
    time.sleep(dellay)
    results = pool.map(ping_system, ips)
    replace()
    time_sructure.delta_time()
    ping_data.clear()
