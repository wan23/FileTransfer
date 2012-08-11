from configobj import ConfigObj

class Config:
	
	def __init__(self, filename):
		self.config = ConfigObj(filename)
		

	def get(self, key):
		return self.config[key]
		
	def set(self, key, value):
		self.config[key] = value
		
	def save(self):
		self.config.write()



if __name__ == '__main__':
	config = Config('config.ini')
	print config.get('shared_dirs')