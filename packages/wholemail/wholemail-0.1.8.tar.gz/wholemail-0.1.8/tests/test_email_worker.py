 


import unittest
from unittest import TestCase

from tests.data_for_tests import *

from wholemail import EmailWorker ,GmailEmailWorker , EmailTemplate 


test_templates = {
	"auth":EmailTemplate( "<h1>Authentication</h1>"),
	"hello":EmailTemplate( "<h1>Hello there</h1>"),

}
test_email_worker = EmailWorker("email" ,"password" , storage_folder = "test_data" )
test_email = "testemail@dom"
test_code_verifier = test_code_verifiers['auth']

class Test_EmailWorker(TestCase):


	def test_CodeValidation(self):
		'''
		test if code validation is done correctly 
		'''

		worker = test_email_worker
		verifier = test_code_verifier
		verifier.ClearCodes()
		code = worker.MakeNewCode(verifier , test_email )
		self.assertTrue(len(code) == verifier.length )
		validation = worker.VerifyCode( verifier , code, test_email)
		self.assertTrue(validation)
		
