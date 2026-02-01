
import unittest
from unittest import TestCase

from wholemail import TemplateStyles


class TestTemplateStylesClass(TestCase):

	def test_ShowAvailableStyles(self):
		print(TemplateStyles())