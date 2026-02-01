

import os

from .email_template import EmailTemplate 
from .email_sender import GmailSender , EmailSender
from .email_code_verifier import EmailCodeVerifier

class EmailWorker:
	"""
	This is a base class that can send emails and validates email codes.

	storage_folder : where the auth codes files and other files will be stored
	email ,password : Authentication information

	Attributes
	-----------
	email:str
		The email address used to send the email.
	password:str
		The password to the provided email account.
	storage_folder:str , optional
		A directory where files will be stored.

	Methods
	--------
	VerifyCode( code_verifier:EmailCodeVerifier , code:str , email:str , delete_if_valid = False) 
		Parameters
		-----------
		code_verifier:EmailCodeVerifier
			An EmailCodeVerifier object for code verification.
		code:str
			The code to be verified.
		delete_if_valid:bool , optional
			Set to `True` to delete the code if it is valid and vice versa.

		Returns
		-------
		bool
			Whether the code is valid or not
	 MakeNewCode(  code_verifier:EmailCodeVerifier , email:str )
	 	Generate a new code with the email as an identifier in the file .

		Parameters
		-----------
		code_verifier:EmailCodeVerifier
			An EmailCodeVerifier object for code generation.
		email:str
			An email address to be associated with the code .

		Returns
		-------
		str
			The code generated

	"""

	def __init__(self  , email:str , password:str ,storage_folder:str= "./"   ):
		self.storage_folder = storage_folder 
		if not os.path.isdir(storage_folder):
			os.makedirs(storage_folder)
		self.email = email 
		self.password = password 

	def VerifyCode(self , code_verifier:str , code:str , email:str , delete_if_valid = False) -> bool:
		'''Verifies a code that was generated and stored in the storage file

		Parameters
		-----------
		code_verifier:EmailCodeVerifier
			An EmailCodeVerifier object for code verification.
		code:str
			The code to be verified.
		delete_if_valid:bool , optional
			Set to `True` to delete the code if it is valid and vice versa.

		Returns
		-------
		bool
			Whether the code is valid or not
		'''
		# check if the code verifier with the name provided exists 
		return code_verifier.ValidateCode(code ,email , delete_if_valid = delete_if_valid)

	def MakeNewCode(self , code_verifier:EmailCodeVerifier , email:str ):
		'''Generate a new code with the email as an identifier in the file 

		Parameters
		-----------
		code_verifier:EmailCodeVerifier
			An EmailCodeVerifier object for code generation.
		email:str
			An email address associated to be with the code .

		Returns
		-------
		str
			The code generated
		'''

		code = code_verifier.MakeNewCode(email)
		return code 
		 



class GmailEmailWorker(EmailWorker):
	'''
	An EmailWorker child class for sending gmail emails .

	Attributes
	---------
	email:str
		The email address used to send the email
	password:str
		The gmail app password to the provided gsmail account
	storage_folder:str , optional
		A directory where files will be stored

	Methods
	--------
	SendTemplate(  template:EmailTemplate , subject:str  ,    recipient:str ) -> bool
		Parameters
		-----------
		template:EmailTemplate
			The EmailTemplate object you wish to send
		subject:str 
			The subject of the email
		recipient:str
			An email address that will receive the email
		
		Returns
		-------
		bool
			Whether or not the email was sent

	SendTextEmail(  message:str , recipient:list , subject:str) -> bool
		Parameters
		-----------
		message:str
			The message in text form to ve sent
		subject:str 
			The subject of the email
		recipient:str
			An email address that will receive the email
		
		Returns
		-------
		bool
			Whether or not the email was sent
	'''


	def __init__(self ,  email:str , password:str , storage_folder:str = "./" ):
		'''
		Parameters
		---------
		email:str
			The email address used to send the email
		password:str
			The password to the provided email account
		storage_folder:str , optional
			A directory where files will be stored

		'''
		EmailWorker.__init__(self ,   email , password   , storage_folder = storage_folder )

	def SendTemplate(self , template:EmailTemplate , subject:str  ,    recipient:str ) -> bool:
		'''
		Send an email to the provided recipients

		Parameters
		-----------
		template:EmailTemplate
			The EmailTemplate object you wish to send
		subject:str 
			The subject of the email
		recipient:str
			An email address that will receive the email
		
		Returns
		-------
		bool
			Whether or not the email was sent

		'''
		print("Sending  [{}] email to {} ".format(template.name , recipient))
		print("Sending email -----", end = "")
		sender = GmailSender(self.email , self.password)
		content = template.content
		plain_text_content = template.plain_text_content
		send_result =  sender.SendHTMLEmail(recipient , subject , content , plain_text_content)
		print("SENT" if send_result else "FAILED")
		return sendmail

	def SendTextEmail(self , message:str , recipient:list , subject:str) -> bool:
		'''Sends a text based email to the recipient

		Parameters
		-----------
		message:str
			The message in text form to ve sent
		subject:str 
			The subject of the email
		recipient:str
			An email address that will receive the email
		
		Returns
		-------
		bool
			Whether or not the email was sent

		'''
		print("Sending  [{}] email to {} ".format("Text based email" , recipient))
		print("Sending email ..." , end='')
		sender = GmailSender(self.email , self.password)
		send_result = sender.SendTextEmail(recipient , subject , message )
		print("SENT" if send_result else "FAILED")
		return sendmail


 
