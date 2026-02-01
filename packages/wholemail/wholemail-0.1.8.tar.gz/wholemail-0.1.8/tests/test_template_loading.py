
import unittest 
from unittest import TestCase

from wholemail import EmailTemplateLoadingError
from wholemail import LoadTemplate


test_html_text = "<h3>{{title}}</h3><p>{{message}}</p>"
test_html_file = "test_data/test_html.html"
test_context = {
		"title":"testtitle",
		"message":"themessagefortesting"
}
expected_content_render = "<h3>{}</h3><p>{}</p>".format(test_context['title'] ,test_context['message'])

def PrepareTestFile():
	with open(test_html_file , "w" , encoding="utf-8") as f:
		f.write(test_html_text)


class TestTemplateLoading(TestCase):
	'''
	This TestCase class is for testing the template loading functionality of the wholemail package
	'''

	def test_HTMLContentLoading(self):
		'''Testing if the html content is loaded correctly
		'''

		PrepareTestFile()
		#Test if normal loading happens
		template = LoadTemplate(html_text = test_html_text , html_file = test_html_file, context = test_context )
		self.assertTrue(template.content == expected_content_render)
		self.assertTrue(template.html == test_html_text)

		# test if invalid file exception
		with self.assertRaises(EmailTemplateLoadingError):
			template = LoadTemplate(html_text = "" , html_file = "", context = test_context )

		# html_text is "" and html_file present
		template = LoadTemplate(html_text = "" , html_file = test_html_file, context = test_context )
		self.assertTrue(template.content == expected_content_render)