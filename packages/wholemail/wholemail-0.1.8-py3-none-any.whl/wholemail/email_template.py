import os 
import jinja2
from bs4 import BeautifulSoup

from .pre_set_email_templates import EMAIL_VERIFICATION_TEMPLATES , VERIFICATION_CODE_TEMPLATES , INFORMATIVE_MESSAGE_TEMPLATES , RESET_PASSWORD_LINK_TEMPLATES , OFFICE_LETTER_TEMPLATES
from .template_styles import TEMPLATE_STYLES_AVAILABLE , TemplateStyles


def strip_html_tags(html:str)-> str:
	'''
	Removes the tags from html content and return the plain text in between the tags .
	'''
	soup = BeautifulSoup(html , "html.parser")
	text  = soup.get_text()
	return text



class EmailTemplate:
	"""
	This class represents the HTML email you wish to send 
	"""

	name = "template"
	def __init__(self , html, context = {} , name = "template"):
		'''
		Parameters
		----------
		html:str
			The html code to send in the email 
		context:dict 
			Context information to be inserted into the html code eg. { 'name' : 'John' }
		name:str
			The name you wish to give to the template

		Methods
		-------
		Edit(key:str , value:str)
			Edit a variable in the context and update the html_content

			Parameters
			----------
			key:str
				The name of the value to be updated in the html code
			value:str
				The value you wish to insert into the html code
		UpdateContent()
			Update the data in the content attribute 
			Use this when editing/updating the context 
		'''
		self.name = name 
		self.context = context		 
		self.html = html # will not change ever
		self.content = ""
		self.plain_text_content = ""
		self.jinja_environment = jinja2.Environment()
		self.UpdateContent()

	def UpdateContent(self) -> None:
		'''
		Update the data in the content attribute 
		Use this when editing/updating the context 
		'''
		template = self.jinja_environment.from_string(self.html)
		content =  template.render(**self.context)
		self.content =content
		self.plain_text_content = strip_html_tags(content)

	def Edit(self, key:str , value:str):
		'''
		Edit a variable in the context and update the html_content

		Parameters
		----------
		key:str
			The name of the value to be updated in the html code
		value:str
			The value you wish to insert into the html code
	
		'''
		if not key in self.context:
			raise KeyError("The key provided is not in the context : {}".format(self.context))
		self.context[key] = value
		self.UpdateContent()

 

class FileEmailTemplate(EmailTemplate) :
	'''
	An Emailtemplate class where html content is loaded from a file 

	Parameters
	----------
	file:str
		The path to the file with the html code  
	context:dict 
		Context information to be inserted into the html code eg. { 'name' : 'John' }
	name:str
		The name you wish to give to the template
	'''
	def __init__(self ,file:str , context:dict , name = "file-email-template" ):
		self.context = context
		self.file  =file
		if not os.path.isfile(file):
			raise FileNotFoundError("Please provide the file path ",file)
		with open(file , "r", encoding  ="utf-8") as f:
			html = f.read()

		EmailTemplate.__init__(self , html , context , name = name)


def insert_context_into_preset_class_during_init(  template:EmailTemplate , context:dict):
	'''
	This function is used to load context data in a PresetEmailtemplate , 
	the context is loaded using the locals() function but it still has unwanted data , this function removes 
	that unwanted data . 

	Parameters
	----------
	template:Emailtemplate
		The template class to load the context for
	context:dict
		The context that neeeds cleaning before being inserted into the Emailtemplate's attribute 

	Returns
	-------
	None

	'''
	context  = context
	# print("CONTEXT ",context)
	context.pop("self")
	context.pop("template_style")
	context.pop("name")
	template.context = context
	template.UpdateContent()

class PresetEmailTemplate(FileEmailTemplate):
	'''
	A parent class for creating custom FileEmailtemplate objects

	Parameters
	----------
	html_file:str
		A path to the file containing the HTML code
	recipient_name:str  , optional
		The name of the person to receive this email
	company_name:str , optional 
		The name of the company sending the email 
	company_address:str , optional 
		The address of the company sending the email 
	customer_support_link:str , optional 
		The link the user will click for technical support 
	company_phone_number:str , optional 
		The telephone number of the company
	company_logo_link:str , optional
		A url directing to the logo image of the company 
	company_website_link:str , optional 
		A url directing to the company's website 
	name:str , optional
		The name of the template 

	'''
	def __init__(self ,html_file:str ,
				recipient_name:str = "",
				company_name:str = "", 
				company_address:str = "",
				customer_support_link:str = "" ,
				company_phone_number:str = "",
				company_logo_link:str = "",
				company_website_link:str = "" , 
				name:str = "PresetEmailtemplate"):
		FileEmailTemplate.__init__(self,  html_file,   {}  ,   name)


class CodeVerificationEmailTemplate(PresetEmailTemplate):
	'''
	A pre-set template for sending authentication code type emails 

	
	Parameters
	----------
	code:str
		The authentication code you wish to send to the user
	recipient_name:str  , optional
		The name of the person to receive this email
	company_name:str , optional 
		The name of the company sending the email 
	company_address:str , optional 
		The address of the company sending the email 
	customer_support_link:str , optional 
		The link the user will click for technical support 
	company_phone_number:str , optional 
		The telephone number of the company
	company_logo_link:str , optional
		A url directing to the logo image of the company 
	company_website_link:str , optional 
		A url directing to the company's website 
	name:str , optional
		The name of the template 
	template_style:int
		The style of temlate to use  , check templateStyles class  for more 

	'''

	def __init__(self ,
		code:str ,
		recipient_name:str = "",
		company_name:str  = "", 
		company_address:str  = "",
		customer_support_link:str  = "" ,
		company_phone_number:str  = "",
		company_logo_link:str  = "",
		company_website_link:str  = "",
		template_style:int = TemplateStyles.basic,
		name = 'code-verification-email-template'):
		html_file = VERIFICATION_CODE_TEMPLATES[template_style]
		PresetEmailTemplate.__init__(self, html_file , name = "Preset-code-verification-template")
		insert_context_into_preset_class_during_init(self , locals())
		

class EmailVerificationEmailTemplate(PresetEmailTemplate):
	'''
	A pre-set template for sending  email authentication emails (confusing , read it again lol)
	
	Parameters
	----------
	email_verification_link:str , optional
		A url which the user will click to verif their email address
	recipient_name:str  , optional
		The name of the person to receive this email
	company_name:str , optional 
		The name of the company sending the email 
	company_address:str , optional 
		The address of the company sending the email 
	customer_support_link:str , optional 
		The link the user will click for technical support 
	company_phone_number:str , optional 
		The telephone number of the company
	company_logo_link:str , optional
		A url directing to the logo image of the company 
	company_website_link:str , optional 
		A url directing to the company's website 
	name:str , optional
		The name of the template 
	template_style:int
		The style of temlate to use  , check templateStyles class  for more 

	'''


	def __init__(self ,
					recipient_name:str  = "", 
					company_name:str =  "", 
					email_verification_link:str  = "", 
					company_address:str  = "",
					customer_support_link:str  = "" ,
					company_phone_number:str  = "",
					company_logo_link:str  = "",
					company_website_link:str  = "",
					template_style:int = TemplateStyles.basic,
					name = "Simple-email-verification-template",
					 ):
		html_file =  EMAIL_VERIFICATION_TEMPLATES[template_style]
		PresetEmailTemplate.__init__(self, html_file , name = name)
		insert_context_into_preset_class_during_init(self , locals())
 


class ResetPasswordLinkEmailTemplate(PresetEmailTemplate):
	'''
	A pre-set template for password reset emails ie. Emails that have a link for resetting the password to an account


	Parameters
	----------
	reset_password_link:str , optional
		A url which the user will click to verif their email address
	recipient_name:str  , optional
		The name of the person to receive this email
	company_name:str , optional 
		The name of the company sending the email 
	company_address:str , optional 
		The address of the company sending the email 
	customer_support_link:str , optional 
		The link the user will click for technical support 
	company_phone_number:str , optional 
		The telephone number of the company
	company_logo_link:str , optional
		A url directing to the logo image of the company 
	company_website_link:str , optional 
		A url directing to the company's website 
	name:str , optional
		The name of the template 
	template_style:int
		The style of temlate to use  , check templateStyles class  for more 

	'''

	def __init__(self ,
					recipient_name:str = "", 
					reset_password_link:str = "", 
					company_name:str=  "", 
					company_address:str = "",
					customer_support_link:str = "" ,
					company_phone_number:str = "",
					company_logo_link:str = "",
					company_website_link:str = "",
					template_style:int = 1,
					name:str= "Reset password template",
					 ):
		html_file = RESET_PASSWORD_LINK_TEMPLATES[template_style]
		PresetEmailTemplate.__init__(self, html_file , name = name)
		insert_context_into_preset_class_during_init(self , locals())
		 
 
 
class InformativeMessageEmailTemplate(PresetEmailTemplate):
	'''
	A pre-set template for sending a message with images via email


	Parameters
	----------
	title:str , optional
		The title of the message you want to send
	image_links:list , optional 
		A list coontaining the image links and their names . format -> [  [ image_link , image_name] ]
	message:str
		The message you wish to send to the user
	recipient_name:str  , optional
		The name of the person to receive this email
	company_name:str , optional 
		The name of the company sending the email 
	company_address:str , optional 
		The address of the company sending the email 
	customer_support_link:str , optional 
		The link the user will click for technical support 
	company_phone_number:str , optional 
		The telephone number of the company
	company_logo_link:str , optional
		A url directing to the logo image of the company 
	company_website_link:str , optional 
		A url directing to the company's website 
	name:str , optional
		The name of the template 
	template_style:int
		The style of template to use  , check templateStyles class  for more 
	'''

	def __init__(self ,
					recipient_name:str = "", 
					message:str = "",
					title:str = "",
					image_links:list = [], # [  [image_link,image_name], ]
					company_name:str =  "", 
					company_address:str  = "",
					customer_support_link:str = "" ,
					company_phone_number:str = "",
					company_logo_link:str = "",
					company_website_link:str = "",
					template_style:int = 1,
					name:str = "InformativeMessageEmailtemplate",
					 ):
		html_file =  INFORMATIVE_MESSAGE_TEMPLATES[template_style]
		PresetEmailTemplate.__init__(self, html_file , name = name)
		insert_context_into_preset_class_during_init(self , locals())
 
class OfficeLetterEmailTemplate(PresetEmailTemplate):
	'''
	An Emailtemplate for generic office letters , 
	Such letters start with 'dear user,' , have a body containing the message 
	and probably end in somthing like 'Regards' , 
	if you want to send such an email , use this class

	Parameters
	----------
	senders_position:str , optional
		The position the sender holds in the company 
	senders_name:str , optional
		The name of the sender 
	greetings:str , optional
		The start of the letter , eg "Dear  John, " 
		By default it is 'Greetings John,'
	sign_off_text:
		The closing statement , eg 'Regards' , 'Yours sincerely'
	message:str
		The message you wish to send to the user
	recipient_name:str  , optional
		The name of the person to receive this email
	company_name:str , optional 
		The name of the company sending the email 
	company_address:str , optional 
		The address of the company sending the email 
	customer_support_link:str , optional 
		The link the user will click for technical support 
	company_phone_number:str , optional 
		The telephone number of the company
	company_logo_link:str , optional
		A url directing to the logo image of the company 
	company_website_link:str , optional 
		A url directing to the company's website 
	name:str , optional
		The name of the template 
	template_style:int
		The style of template to use  , check templateStyles class  for more 
	''' 
	def __init__(self ,
					recipient_name:str = "", 
					senders_name:str = "",
					senders_position:str = "" , 
					message:str = "",
					title:str = "",
					company_name:str =  "", 
					company_address:str  = "",
					customer_support_link:str = "" ,
					company_phone_number:str = "",
					company_logo_link:str = "",
					company_website_link:str = "",
					template_style:int = 1,
					greetings:str = "Greetings,",
					sign_off_text:str = "Regards,",
					name:str = "OfficeLetterEmailtemplate",
					 ):
		html_file =  OFFICE_LETTER_TEMPLATES[template_style]
		PresetEmailTemplate.__init__(self, html_file , name = name)
		insert_context_into_preset_class_during_init(self , locals())
		 

