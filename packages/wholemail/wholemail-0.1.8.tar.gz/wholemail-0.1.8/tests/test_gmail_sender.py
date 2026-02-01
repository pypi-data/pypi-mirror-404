
'''

Before running this test , make sure a file called [my_email_auth] exists in the root directory 
in the file incluse the following variables

		- GMAIL_EMAIL - An email address you own that will send the email
		- GMAIL_APP_PASSWORD - Gmail app password (NOT THE NORMAL PASSWORD)
		- TEST_RECEIVER_EMAIL - A different  email address you own that will receive the test emauk

  '''


import unittest
from unittest import TestCase


from wholemail import EmailWorker ,GmailEmailWorker , EmailTemplate , GmailSender
from my_email_auth import GMAIL_EMAIL , GMAIL_APP_PASSWORD , TEST_RECIPIENT

from tests.data_for_tests import *


test_sender = GmailSender(GMAIL_EMAIL , GMAIL_APP_PASSWORD )

class Test_send_Email_using_GmailSender(TestCase):
	'''
	Test functionalities of the GmailEmailWOrker class. ie test sending emails via gmail
	'''
	def test_SendHTMLEmail(self):
		'''
		test sending a html email using gmail
		'''
		sender = test_sender
		html  = test_email_template.content
		plain_message = test_email_template.plain_text_content
		subject = "Testing wholemail gmail mail sending"
		result = sender.SendHTMLEmail( TEST_RECIPIENT , subject , html , plain_message  )
		self.assertTrue(result)


	def test_SendTextEmail(self):
		'''
		test sending a text based email using gmail
		'''

		sender = test_sender
		message = "Just testing"
		subject = "Testing wholemail gmail mail sending"
		result = sender.SendTextEmail( TEST_RECIPIENT , subject ,message  )
		self.assertTrue(result)

