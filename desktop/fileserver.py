from flask import Flask, Response

from json import loads, dumps
from thread import start_new_thread
from time import sleep
from urllib import urlencode
from urllib2 import urlopen
from hashlib import md5
import pycurl


from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('fileserver', '.'))

from file_listing import FileList
from config import Config

app = Flask(__name__)

BUFFER_SIZE = 5000000
PING_TIME = 10  # 10 seconds (for testing)
FILE_SCAN_TIME = 300  # 5 minutes for now
#SERVER_HOST = "severe-fog-6187.herokuapp.com"
#SERVER_PORT = 80
PING_PATH = "/ping/%s"
REGISTER_PATH = "/app/register"
NEW_USER_PATH = "/user/new"
LOGIN_PATH = "/user/login"
GET_UPLOAD_URL_PATH = "/transfer/%s/start_upload"
UPLOAD_COMPLETE_PATH = "/transfer/%s/done"
FILE_LIST_PATH = "/install/%s/files"
CONFIG_FILE = "./config.ini"
FILE_CACHE_NAME = './files.cache'

fs = None

test_files_template = env.get_template('test_files_template.html')
install_id = None



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

@app.route("/test/files")
def test_files_page():
    print fs
    resp = urlopen(fs.get_url(FILE_LIST_PATH % fs.config.get('install_id')))
    res = loads(resp.read())
    install_id = fs.config.get('install_id')

    return test_files_template.render(files=res['files'],
                                      user_token=fs.config.get('user_token'),
                                      new_transfer_url=fs.get_url('/transfer/new'),
                                      install_id=install_id)

class FileServer:

  def get_url(self, path):
    print self.config.config
    ret = "http://%s:%s%s" % (self.config.get('server_host'),
                              self.config.get('server_port'),
                              path)
    print ret
    return ret
    
  def request(self, path, data=None):
    response = urlopen(self.get_url(path), data)
    return loads(response.read())

  def get(self, path, extra_path_components=[]):
    path = path % extra_path_components
    return self.request(path)

  def post(self, path, extra_path_components=[], data={}):
    path = path % extra_path_components
    return self.request(path, urlencode(data))
    
  def ping_server(self):
    data = self.post(PING_PATH, self.config.get('install_id'),
                     data={'user_token': self.config.get('user_token')})
    command = data.get("command")
    if command == "get_file":
      for transfer in data['transfers']:
        self.send_file(transfer['file_hash'], transfer['transfer_id'])
    elif command == 'test':
      print "Test command received!!!!!"


  def send_file(self, file_hash, transfer_id):
    resp = urlopen(self.get_url(GET_UPLOAD_URL_PATH % transfer_id),
             urlencode({'user_token': self.config.get('user_token')}))
    res = loads(resp.read())
    
    url = res['url']
    
    file = self.file_list.get_file_info(file_hash)
    if not file:
      print "File not found for hash: " + file_hash
      # TODO: Let the server know the file wasn't found
    print file
    start_new_thread(self._send_file, (file, url, transfer_id))


  # TODO: Have this thread somehow communicate its status
  def _send_file(self, file, url, transfer_id):
    print "Executing transfer (%s) with %s" % (file['name'], url)

    with open(file['full_path']) as fp:
      c = pycurl.Curl()
      c.setopt(c.UPLOAD, 1)
      c.setopt(c.READFUNCTION, fp.read)
      c.setopt(c.CUSTOMREQUEST, 'PUT')
      c.setopt(c.URL, str(url))
      c.setopt(c.INFILESIZE_LARGE, file['size'])
      if file['mime_type']:
         c.setopt(pycurl.HTTPHEADER, ['Content-Type: %s' % (file['mime_type']),
                                     'Content-Disposition: attachment; filename=%s' %
                                      file['name']])
      c.perform()
      c.close()
    self._done_uploading(transfer_id)
      
  def _done_uploading(self, transfer_id):
    # TODO: Update the client-side list of pending transfers
    self.post(UPLOAD_COMPLETE_PATH, transfer_id)

  def hashed_password(self):
    # TODO: should hash with something random
    d = md5()
    d.update(self.config.get("password") + "ABC432")
    return d.hexdigest()


  def new_user(self, username, password):
    #TODO: Ask user for credentials
    self.config.set('username', username)
    self.config.set('password', password)
    resp = urlopen(self.get_url(NEW_USER_PATH),
            urlencode({'username': self.config.get('username'),
                       'password': self.hashed_password()}))
    resp_dict = loads(resp.read())
    token = resp_dict.get('user_token')
    if token:
      self.config.set('user_token', token)
    else:
      # TODO: Real exceptions
      print ("Create user failed, got back: %s" % resp_dict)
      return False
    return True


  def login(self):
    if self.config.get('user_token'):
      return
    resp = urlopen(self.get_url(LOGIN_PATH),
            urlencode({'username': self.config['username'],
                       'password': self.hashed_password()}))
    resp_dict = loads(resp.read())
    token = resp_dict.get('user_token')
    if token:
      self.config.set('user_token', token)
      print "user token: " + token
    else:
      # this should throw a specific exception
      raise Exception("Tried to login, got back %s as token" % resp_dict)


  def register_with_server(self):
    self.login()
    resp = urlopen(self.get_url(REGISTER_PATH),
                   urlencode({'user_token': self.config.get('user_token'),
                              'port': self.config.get('public_port')}))
    new_conf = loads(resp.read())
    print new_conf
    for k, v in new_conf:
     self.config.set(k, v)

  def upload_listing(self, listing):
    #print "Upload listing: " + str(listing)
    resp = urlopen(self.get_url(FILE_LIST_PATH % self.config.get('install_id')),
                   urlencode({'user_token': self.config.get('user_token'),
                              'file_list': dumps({'files': listing})}))
    resp = loads(resp.read())
    if resp.get('status') != 'OK':
        print "Failed to upload listing."
    # TODO: Error handling here?
    
    
  def get_install_id(self):
    if not self.config.get('install_id'):
      self.register_with_server()
    return self.config.get('install_id')

  def ping_thread(self, args):
    while True:
      try:
        self.ping_server()
      except Exception as e:
        # TODO: log something
        print "Exception in ping thread"
        print e
      sleep(PING_TIME)

  def file_scan_thread(self, unused_args):
    while True:
      try:
        self.file_list.update_listing()
        listing = self.file_list.get_listing()
        self.upload_listing(listing)
      except Exception as e:
        # TODO: log something!
        print "Exception in file thread"
        print e
      sleep(FILE_SCAN_TIME)

  def verify_config(self):
    return self.config.get('install_id')


  def first_time_registration(self):
    # TODO: This needs to get the user's info somehow
    self.new_user('wan', 'pass')
    self.config.set('username', 'wan')
    self.config.set('install_id', self.get_install_id())
    self.config.save()


  def setup_config(self):
    self.config = Config(CONFIG_FILE)
    self.file_list = FileList(FILE_CACHE_NAME)
    self.file_list.set_directories(self.config.get('shared_dirs'))
    

if __name__ == '__main__':
  fs = FileServer()
  fs.setup_config()
  start_new_thread(fs.ping_thread, (None,))
  start_new_thread(fs.file_scan_thread, (None,))
  app.run(host='0.0.0.0', port=int(fs.config.get('local_port')))
