from flask import Flask, Response

from threading import Thread
from time import sleep

app = Flask(__name__)

BUFFER_SIZE = 5000000
PING_TIMER = 10  # 10 seconds (for testing)
SERVER_HOST = "severe-fog-6187.herokuapp.com"
SERVER_PORT = 80
PING_PATH = "/ping"
REGISTER_PATH = "/app/register"

paths = []
install_id = None

@app.route('/status')
def get_status():
    status = ""
    status += "OK!\r\n"
    status += "Ping Interval: %s\r\n" % PING_TIMER
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
    paths.append('/Users/juan/Desktop/IMG_0343.JPG')
    paths.append('/Users/juan/Desktop/LivingSocial Voucher.pdf')

def get_ping_url():
    # Check if we have an install ID
    # if not, register
    # otherwise return url
    pass

def ping_server():
    urlopen(get_ping_url())

def get_install_id():
	if not config['install_id']:
		resp = urlopen(SERVERHOST+REGISTER_PATH,
		               urlencode({'username': config['username']})
		new_conf = loads(resp)
	return config['install_id']
		

def ping_thread():
    while True:
        ping_server()
def load_config(filename):
    with open(filename, 'r') as f:
        return json.loads(f.read())

def write_config(filename, config):
    with open(filename, 'w') as f:
        f.write(dumps(config))

def verify_config():
    return config.get('install_id'):


def first_time_registration():
    # TODO: This needs to get the user's info somehow                           
    config['username'] = 'wan'
    config['install_id'] = get_install_id()
    write_config(CONFIG_FILE, config)


def setup_config():
    try:
        config = load_config(CONFIG_FILE)
        if not verify_config():
            first_time_registration()
    except:
        print "Unable to load config file."

if __name__ == '__main__':
    setup_config()
    start_new_thread(ping_thread)
    # TODO: File scanning thread
    app.run(host='0.0.0.0', port=config['port'])
