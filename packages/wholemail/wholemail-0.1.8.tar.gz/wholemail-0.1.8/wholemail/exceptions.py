

class  EmailTemplateLoadingError(Exception):
	'''
	An exception to be raised when a problem occurs during template loading
	'''
	def __init__(self , message):
		self.message = message
		super().__init__(self.message)



 