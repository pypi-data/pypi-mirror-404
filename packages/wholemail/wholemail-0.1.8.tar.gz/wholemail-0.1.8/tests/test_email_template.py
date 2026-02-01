'''

Here is what is happening:
	# test update content in EmailTemplate
	# test edit context in EmailTemplate
	# test FileEmailTemplate file loading 


'''
import unittest ,os
from unittest import TestCase

from wholemail import EmailTemplate , FileEmailTemplate

test_html_text = """
{{name}} ( born Albert Chinụalụmọgụ Achebe; {{DOB}} – 21 March 2013)
 was a Nigerian novelist, poet, and critic who is regarded as a central figure of modern African literature.
  His first novel and magnum opus, Things Fall Apart (1958), occupies a pivotal place in African literature and
   remains the most widely studied, translated, and read African novel.

    Along with Things Fall Apart, his No Longer at Ease (1960) and Arrow of God (1964) complete the "African Trilogy".
     Later novels include A Man of the People (1966) and Anthills of the Savannah (1987).
      Achebe is often referred to as the "father of modern African literature",
      although he vigorously rejected the characterization.

     """
test_context = {
	"name":"Chinua Achebe",
	"DOB":"16 November 1930",
}
test_html_file = "test_data/html/chinua_achebe.html"
test_email_template = EmailTemplate(test_html_text,test_context)

# some helper functions
def delete_test_html_file():
	'''
	Delete the html test file . 
	to be used during testing 
	'''
	if os.path.isfile(test_html_file ):
		os.remove(test_html_file)

def restore_test_html_file():
	'''
	Restore the html test file and write the test html text in it  
	to be used during testing 
	'''
	with open(test_html_file , "w" , encoding  ="utf-8") as f:
		f.write(test_html_text)



class TestEmailTemplate(TestCase):

	"""
	test the base class wholemail.EmailTemplate 

	"""

	def test_UpdatingContent(self):
		template = test_email_template
		# the UpdateContent function has alreadybeen run , let's test its results
		# test if the content attriute has changed and includes data from context
		print(template.content)
		self.assertTrue(test_context["name"] in template.content)
		# check if the html attr is intact
		self.assertTrue(template.html == test_html_text)

	def test_EditingContent(self):
		template = test_email_template
		# change the name in the content and see if all is Ok
		new_name = "Groot"
		template.Edit("name" ,new_name)
		self.assertTrue(new_name in template.content) 
		self.assertTrue(template.context["name"] == new_name)


class TestFileEmailTemplate(TestCase):

	"""
	Test the wholemail.FileEmailTemplate class 

	"""
	def test_FileLoading(self):
		# delete the file and see if it is re-created and works alright
		restore_test_html_file()
		template = FileEmailTemplate(test_html_file , test_context)
		# check if the context and content attrs are in order
		self.assertTrue(test_context["name"] in template.content)
		# check if the html attr is intact
		self.assertTrue(template.html == test_html_text)
		# de;ete the file and check stuff
		delete_test_html_file()
		with self.assertRaises(	FileNotFoundError):
			template = FileEmailTemplate(test_html_file , test_context)
