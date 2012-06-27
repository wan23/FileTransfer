import os

class FileList:
    directories = []
    filters = []
    files = []

    def __init__(self):
        pass

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
        return self.files

    def update_listing(self):
        files = []
        for dir in self.directories:
            for (dirpath, dirnames, filenames) in os.walk(dir):
                for name in filenames:
                    file = self._file_record(dirpath, name, False)
                    files.append(file)
                for name in dirnames:
                    file = self._file_record(dirpath, name, True)
                    files.append(file)
