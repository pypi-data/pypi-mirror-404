
import unittest 
from unittest import TestCase

from wholemail import EmailCodeVerifier

from tests.data_for_tests import test_code_verifiers

test_verifier = test_code_verifiers['auth']
test_email = "someemail@dom"
class Test_EmailCodeVerifier(TestCase):
	'''For testing the class EmailCodeVerifier

	'''

	def test_MakeNewCode(self):
		'''Test new code generations
		'''
		verifier = test_verifier
		verifier.ClearCodes()
		expected_code_length = verifier.length
		code = verifier.MakeNewCode(test_email)
		self.assertTrue(len(code) == expected_code_length)



	def test_ValidateCode(self):
		'''
		Test if  codes are validated correctly

		'''
		verifier = test_verifier
		verifier.ClearCodes()
		code = verifier.MakeNewCode(test_email)
		invalid_check_result= verifier.ValidateCode("falsecode123" , test_email)
		valid_check_result = verifier.ValidateCode(code , test_email)
		self.assertTrue(valid_check_result)
		self.assertFalse(invalid_check_result)

		# test when delete_if_valid is set to False
		verifier.ClearCodes()
		code = verifier.MakeNewCode(test_email)
		check_result = verifier.ValidateCode(code , test_email , delete_if_valid = False)
		storage_file_data = ''
		with open(verifier.code_generator.storage_file , "r") as f:
			storage_file_data = f.read()
		self.assertTrue(test_email in storage_file_data)
		self.assertTrue(code in storage_file_data)

		# test when delete_if_valid is set to True
		verifier.ClearCodes()
		code = verifier.MakeNewCode(test_email)
		check_result = verifier.ValidateCode(code , test_email , delete_if_valid = True)
		with open(verifier.code_generator.storage_file , "r") as f:
			storage_file_data = f.read()
		self.assertTrue(test_email not in storage_file_data)
		self.assertTrue(code not in storage_file_data)



