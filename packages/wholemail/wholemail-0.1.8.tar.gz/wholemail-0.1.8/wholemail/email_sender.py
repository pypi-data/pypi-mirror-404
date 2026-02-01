import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage

 

class EmailSender:
	'''
	a base class that facilitates sending of emails 

	Attributes
	-----------
	email:str
		Email address to use when sending emails
	password:str
		Password to the email
	raise_exceptions:bool
		Whether or not rasie encountered exceptions 
	'''

	def __init__(
			self ,
			email:str ,
			password:str, 
			raise_exceptions:bool = False 
			):
		'''
		Parameters
		----------
		email:str
			Email address to use when sending emails
		password:str
			Password to the email
		raise_exceptions:bool
		'''

		self.email = email 
		self.password = password
		self.raise_exceptions = raise_exceptions

 
	 

class GmailSender(EmailSender):
	'''
	This class is for sending gmail emails 

	Attributes
	-----------
	email:str
		Email address to use when sending emails
	password:str
		The Gmail app Password to the gmail account

	Methods
	-------
	SendHTMLEmail(email:str , password:str)
		Sends an html email to the provided recipient
		
		Parameters
		----------
		recipients:str
			email address to receive the email .
		subject:str
			The subject of the email to be sent .
		html:
			The html code to send 
		plain_message:str
			Alternative message in text form (To be shown if the HTML doesn't render)


		Returns
		-------
		bool
			True if the email is sent successfully ,else False

	'''

	def __init__(
			self,
			email:str ,
			password:str ,
			raise_exceptions:bool = False):
		'''
		email:str
			Email address to use when sending emails
		password:str
			The Gmail app Password to the gmail account
		'''
		EmailSender.__init__(self , email , password ,raise_exceptions)

	def SendHTMLEmail(self ,recipient:str, subject:str , html:str, plain_message:str = "" ) -> bool:

		'''
		Sends an html email to the provided recipient
		
		Parameters
		----------
		recipients:str
			email address to receive the email .
		subject:str  
			The subject of the email to be sent .
		html:
			The html code to send 
		plain_message:str
			Alternative message in text form (To be shown if the HTML doesn't render)


		Returns
		-------
		bool
			True if the email is sent successfully ,else False

		'''


		# Create the email message
		msg = MIMEMultipart('alternative')
		msg['From'] = self.email
		msg['To'] = recipient
		msg['Subject'] = subject

		# Attach the HTML content
		msg.attach(MIMEText(html, 'html'))

		# Send the email
		try:
		    with smtplib.SMTP('smtp.gmail.com', 587) as server:
		        server.starttls()  # Upgrade the connection to a secure one
		        server.login(self.email , self.password)
		        server.send_message(msg)
		        
		    print(f"Email [{subject}] sent successfully!")
		    return True 
		except Exception as e:
			if self.raise_exceptions:
				raise e  
			print(f"Failed to send email: {e}")
			return False

		return False 
 

	def SendTextEmail(self , recipient:str, subject:str , message:str ) -> bool:
		'''
		Send an text based email to the provided recipients

		Parameters
		----------
		recipient:str
			The email address to receive the email .
		subject:str
			The subject of the email to be sent .
		message:
			The message to send 

		Returns
		-------
		bool
			Whether the email has been sent or not

		'''

		msg = MIMEText(message)
		msg['Subject'] = subject
		msg['From'] =self.email
		msg['To'] = recipient
		print("Preparing to send a text based message to {} from sender {}. [PASSWORD = {} ]".format(recipient, self.email , self.password[:3] + ("*"*(len(self.password)-3))))
		port = 587
		try:
			with smtplib.SMTP('smtp.gmail.com', 587) as server:
				server.starttls()  # Upgrade the connection to a secure one
				server.login(self.email , self.password)
				server.send_message(msg)
				print(f"EMail [{subject}] sent ! ")
				return True
		except Exception as e:
			if self.raise_exceptions:
				print("Could not send email ")
				raise e 
		return False
