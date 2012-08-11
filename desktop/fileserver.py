from flask import Flask, Response

from json import loads
from thread import start_new_thread
from time import sleep
from urllib import urlencode
from urllib2 import urlopen
from hashlib import md5

from config import Config

app = Flask(__name__)

BUFFER_SIZE = 5000000
PING_TIME = 10  # 10 seconds (for testing)
#SERVER_HOST = "severe-fog-6187.herokuapp.com"
#SERVER_PORT = 80
PING_PATH = "/ping"
REGISTER_PATH = "/app/register"
NEW_USER_PATH = "/user/new"
LOGIN_PATH = "/user/login"
CONFIG_FILE = "./config.json"

paths = {}
install_id = None

config = None

@app.route('/status')
def get_status():
    status = ""
    status += "OK!\r\n"
    status += "Ping Interval: %s\r\n" % PING_TIME
    return status

@app.route('/files/<path:path>')
def get_file(path):
    # TODO: sanitize paths
    try:
        #print path
        f = open('/' + path, 'r')
    except:
        return "File not found"

    def file_piece():
        data = f.read(BUFFER_SIZE)
        while data:
            yield data
            data = f.read(BUFFER_SIZE)

    return Response(file_piece(), mimetype='application/octet-stream')

@app.route('/list')
def get_listing():
    return '\r\n'.join(paths)

def setup_test():
    paths['file1'] = '/Users/juan/Desktop/IMG_0343.JPG'
    paths['file2'] = '/Users/juan/Desktop/LivingSocial Voucher.pdf'


def get_url(path):
    ret = "http://%s:%s%s" % (config['server_host'],
                               config['server_port'],
                               path)
    print ret
    return ret

def ping_server():
    server_message = urlopen("%s/%s" % (get_url(PING_PATH), config['install_id']))
    data = json.loads(server_message.read())
    command = data.get("command")
    if command == "get_file":
        send_file(data['file_id'], data['transfer_id'])
        
def send_file(file_id, transfer_id):
    path = get_file_path(file_id)
    if path:
        start_new_thread(_send_file, path)

# TODO: Have this thread somehow communicate its status
def _send_file(path, transfer_id):
    print "Executing transfer (%s) with %s" % (transfer_id, path)

def get_file_path(file_id):
    return paths.get(file_id)
    
def hashed_password():
    # TODO: should hash with something random
    d = md5()
    d.update(config["password"] + "ABC432")
    return d.hexdigest()

def new_user(username, password):
    #TODO: Ask user for credentials
    config.set('username', username)
    config.set('password', password)
    resp = urlopen(get_url(NEW_USER_PATH),
            urlencode({'username': config['username'],
                       'password': hashed_password()}))
    resp_dict = loads(resp.read())
    token = resp_dict.get('user_token')
    if token:
        config.set('user_token', token)
    else:
        # TODO: Real exceptions
        print ("Create user failed, got back: %s" % resp_dict)
        return False
    return True

def login():
    if config.get('user_token'):
        return
    resp = urlopen(get_url(LOGIN_PATH),
            urlencode({'username': config['username'],
                       'password': hashed_password()}))
    resp_dict = loads(resp.read())
    token = resp_dict.get('user_token')
    if token:
        config.set('user_token') = token
        print "user token: " + token
    else:
        # this should throw a specific exception
        raise Exception("Tried to login, got back %s as token" % resp_dict)

def register_with_server():
    login()
    resp = urlopen(get_url(REGISTER_PATH),
                   urlencode({'user_token': config['user_token'],
                              'port': config['public_port']}))
    new_conf = loads(resp.read())
    print new_conf
    config.update(new_conf)

def get_install_id():
    if not config.get('install_id'):
        register_with_server()
    return config.get('install_id')

def ping_thread(args):
    while True:
        ping_server()
        sleep(PING_TIME)


def verify_config():
    return config.get('install_id')


def first_time_registration():
    # TODO: This needs to get the user's info somehow
    new_user('wan', 'pass')
    config.set('username'), 'wan')
    config.set('install_id', get_install_id())
    config.save()


def setup_config():
    config = Config(CONFIG_FILE)
    

if __name__ == '__main__':
    setup_config()
    start_new_thread(ping_thread, (None,))
    start_new_thread(file_scan_thread, (None,))
    # TODO: File scanning thread
    app.run(host='0.0.0.0', port=int(config.get('local_port')))
