import os
from json import dumps, loads

class FileList:
    directories = []
    filters = []
    files = []

    def __init__(self, cache_filename):
        self.cache_file = cache_filename
        self.load_from_cache()

    def add_directory(self, dir):
        self.directories.append(dir)

    def add_filter(self, filter):
        self.filters.append(filter)

    def _file_record(self, dirpath, name, is_dir):
        return {'full_path': os.path.join(dirpath, name),
                'name': name,
                'is_dir': is_dir}

    def get_listing(self):
        if not self.files:
            self.update_listing()
        return list(self.files)

    def update_listing(self):
        self.files = []
        for dir in self.directories:
            for (dirpath, dirnames, filenames) in os.walk(dir):
                for name in filenames:
                    file = self._file_record(dirpath, name, False)
                    self.files.append(file)
                for name in dirnames:
                    file = self._file_record(dirpath, name, True)
                    self.files.append(file)
                    
                    
    def save_to_cache(self):
		with open(self.cache_file, 'w') as f:
			data = dumps({'files': self.files})
			f.write(data)
			
    def load_from_cache(self):
    	self.files = []
    	try:
    		with open(self.cache_file) as f:
    			data = loads(f.read())
    			self.files = data.get('files')
    	except:
    		pass
    			

			
	