
'''

Before running this test , make sure a file called `my_email_auth.py` exists in the root directory 
in the file incluse the following variables

		- GMAIL_EMAIL - An email address you own that will send the email
		- GMAIL_APP_PASSWORD - Gmail app password (NOT THE NORMAL PASSWORD)
		- TEST_RECEIVER_EMAIL - A different  email address you own that will receive the test emauk

The tests here send you an email for you to check if everything works alright 
It also tests that those templates have been sent

  '''


import unittest
from unittest import TestCase

from tests.data_for_tests import *

from wholemail import CodeVerificationEmailTemplate , GmailSender , TemplateStyles
from wholemail import ResetPasswordLinkEmailTemplate , OfficeLetterEmailTemplate , InformativeMessageEmailTemplate , EmailVerificationEmailTemplate
from my_email_auth import GMAIL_EMAIL , GMAIL_APP_PASSWORD , TEST_RECIPIENT

test_sender = GmailSender(GMAIL_EMAIL , GMAIL_APP_PASSWORD ,raise_exceptions = True )
template_style = TemplateStyles.japanese_indigo
test_company_logo_link = 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Kermit_puppet.jpg/330px-Kermit_puppet.jpg' 
"https://i.ibb.co/q3tdgSsM/wholemail-new-logo.png"
test_link = "https://google.com"

class Test_EmailVerificationEmailTemplate(TestCase):
	def test_Template(self):
		'''
		Just sending an email to see if everything works and looks as ot should
		'''

		sender = test_sender
		test_email_template = EmailVerificationEmailTemplate(

					recipient_name = "JohnDoe" , 
					company_name = "WholemailApp",
					email_verification_link = test_link,
					company_address = "Mars",
					customer_support_link = "support",
					company_phone_number = "+123456",
					company_website_link = "wholemailwebsite",
					company_logo_link = test_company_logo_link,
					template_style = template_style,
					 )
		html  = test_email_template.content
		plain_message = test_email_template.plain_text_content
		subject = "Testing EmailVerificationEmailTemplate"
		result = sender.SendHTMLEmail( TEST_RECIPIENT , subject , html , plain_message  )
		self.assertTrue(result)
		print("Email sent to {} for testing purposes".format(TEST_RECIPIENT))

class Test_CodeVerificationEmailTemplate(TestCase):
	def test_Template(self):
		'''
		Just sending an email to see if everything works and looks as ot should ,
		check your address to see the result
		'''

		sender = test_sender
		test_email_template = CodeVerificationEmailTemplate(
					code = "12345",
					recipient_name = "JohnDoe" , 
					company_name = "WholemailApp",
					company_address = "Mars",
					customer_support_link = "support",
					company_phone_number = "+123456",
					company_website_link = "wholemailwebsite",
					company_logo_link = test_company_logo_link,
					template_style = template_style,
					)
		html  = test_email_template.content
		plain_message = test_email_template.plain_text_content
		subject = "Testing CodeVerificationEmailTemplate"
		result = sender.SendHTMLEmail( TEST_RECIPIENT , subject , html , plain_message  )
		self.assertTrue(result)
		print("Email sent to {} for testing purposes".format(TEST_RECIPIENT))


class Test_ResetPasswordLinkEmailTemplate(TestCase):
	def test_Template(self):
		'''
 
		'''

		sender = test_sender
		test_email_template = ResetPasswordLinkEmailTemplate(
					reset_password_link = test_link,
					recipient_name = "JohnDoe" , 
					company_name = "WholemailApp",
					company_address = "Mars",
					customer_support_link = "support",
					company_phone_number = "+123456",
					company_website_link = "wholemailwebsite",
					company_logo_link = test_company_logo_link,
					template_style = template_style,
					)
		html  = test_email_template.content
		plain_message = test_email_template.plain_text_content
		subject = "Testing ResetPasswordLinkEmailTemplate"
		result = sender.SendHTMLEmail( TEST_RECIPIENT , subject , html , plain_message  )
		self.assertTrue(result)
		print("Email sent to {} for testing purposes".format(TEST_RECIPIENT))


class Test_OfficeLetterEmailTemplate(TestCase):
	def test_Template(self):
		'''
 
		'''

		sender = test_sender
		test_email_template = OfficeLetterEmailTemplate(
					message = test_message,
					senders_position = "CEO",
					senders_name = "MarkZucks",
					recipient_name = "JohnDoe" , 
					company_name = "WholemailApp",
					company_address = "Mars",
					customer_support_link = "support",
					company_phone_number = "+123456",
					company_website_link = "wholemailwebsite",
					company_logo_link = test_company_logo_link,
					template_style = template_style,
					)
		html  = test_email_template.content
		plain_message = test_email_template.plain_text_content
		subject = "Testing OfficeLetterEmailTemplate"  
		result = sender.SendHTMLEmail( TEST_RECIPIENT , subject , html , plain_message  )
		self.assertTrue(result)
		print("Email sent to {} for testing purposes".format(TEST_RECIPIENT))



class Test_InformativeMessageEmailTemplate(TestCase):
	def test_Template(self):
		'''
 
		'''

		sender = test_sender
		test_email_template = InformativeMessageEmailTemplate(
					message = test_message,
					title = "title:",
					recipient_name = "JohnDoe" , 
					image_links = test_image_links,
					company_name = "WholemailApp",
					company_address = "Mars",
					customer_support_link = "support",
					company_phone_number = "+123456",
					company_website_link = "wholemailwebsite",
					company_logo_link = test_company_logo_link,
					template_style = template_style,
					)
		html  = test_email_template.content
		plain_message = test_email_template.plain_text_content
		subject = "Testing Inform"
		result = sender.SendHTMLEmail( TEST_RECIPIENT , subject , html , plain_message  )
		self.assertTrue(result)
		print("Email sent to {} for testing purposes".format(TEST_RECIPIENT))




