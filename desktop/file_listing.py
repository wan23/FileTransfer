import os
from json import dumps, loads
import hashlib
from mimetypes import guess_type

# TODO: This needs to be made thread safe!
class FileList:
    directories = []
    filters = []
    files = {}

    def __init__(self, cache_filename):
        self.cache_file = cache_filename
        self.load_from_cache()

    def add_directory(self, dir):
    	if dir:
	        self.directories.append(dir)
    
    def set_directories(self, dirs):
    	self.directories = dirs or []

    def add_filter(self, filter):
    	if filter:
	        self.filters.append(filter)

    def _file_record(self, dirpath, name, is_dir):
        path = os.path.join(dirpath, name)
        # TODO: Actually use a hash of the file contents
        hash = hashlib.md5(path).hexdigest()
        size = os.path.getsize(path)
        return {'full_path': path,
                'name': name,
                'is_dir': is_dir,
                'hash': hash,
                'size': size,
                'mime_type': guess_type(path)[0] or 'application/octet-stream'}

    def get_listing(self):
        if not self.files:
            self.update_listing()
        return list(self.files.values())

    def update_listing(self):
        print "starting update listing"
        new_files = {}
        print self.directories
        for dir in self.directories:
            if dir == '/':
              	raise Exception('Refusing to index entire filesystem')
            for (dirpath, dirnames, filenames) in os.walk(dir):
                for name in filenames:
                #    print name
                    file = self._file_record(dirpath, name, False)
                    new_files[file['hash']] = file
                for name in dirnames:
                    file = self._file_record(dirpath, name, True)
                    new_files[file['hash']] = file
        self.files = new_files
        print "update listing done"
                    
    def get_file_info(self, file_hash):
    	return self.files.get(file_hash)
    	             
    def save_to_cache(self):
		with open(self.cache_file, 'w') as f:
			data = dumps({'files': self.files})
			f.write(data)
			
    def load_from_cache(self):
    	self.files = {}
    	try:
    		with open(self.cache_file) as f:
    			data = loads(f.read())
    			self.files = data.get('files')
    	except:
    		pass
    			

			
	