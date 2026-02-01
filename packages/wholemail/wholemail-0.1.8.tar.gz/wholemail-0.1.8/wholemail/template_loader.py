import os

from .email_template import EmailTemplate , FileEmailTemplate
from .exceptions import EmailTemplateLoadingError




def LoadTemplate( html_text = "" , html_file = ""  , context ={}  , name = EmailTemplate.name ):
	'''
	This function creates an EmailTemlate opbject based on the information provided

	NOTE : 	Provide only either html_text or html_file parameters , 
			if both are provided , the html_file will be used, if it has issues, the html text will be used,
			if both html_file and html_text have issues, an exception will be raised
	
	Parameters
	----------
	html_text:str
		HTML content you want to send , it should contain the {{value}} blocks for context rendering
	html_file:str , optional
		The path of a html file you wish to create a template from
	context:dict , optional
		A dict containing the values you want inserted into the html content . 
	name:str , optional
		The name you want to give to the template

	Returns
	-------
	EmailTemplate


	'''

	# chec the html file
	html_content = ""
	html_file_content = ""
	if html_file:
		if not os.path.isfile(html_file):
			try:
				folder , file = os.path.split(html_file)
				if not os.path.isdir(folder):
					# make the folder since its not there
					os.makedirs(folder)
					# make the html file
				with open(html_file , "w" , encoding ='utf-8') as f:
					f.write("")

			except FileNotFoundError:
				raise EmailTemplateLoadingError("The file could not be found or created")
			except Exception as e:
				raise EmailTemplateLoadingError("Could not load the template html content because of {}".format(e))
		else:
			try:
				with open(html_file , "r" , encoding ="utf-8") as f:
					html_file_content = f.read()
			except (FileNotFoundError , PermissionError ) as e:
				print(f"Error reading file {html_file} , skipping file read")
	if not html_text and not html_file:
		# raise an error	
		raise EmailTemplateLoadingError("Please specify a file or text content for the email template")
	# select which content to use
	if html_file_content and html_text:
		html_content = html_file_content
	elif html_file_content and not html_text:
		html_content = html_file_content
	elif html_text and not html_file_content:
		html_content = html_text
	elif not html_file_content and not html_text:
		html_content = ""
	template = EmailTemplate(html_content , context =context , name = name  )
	return template