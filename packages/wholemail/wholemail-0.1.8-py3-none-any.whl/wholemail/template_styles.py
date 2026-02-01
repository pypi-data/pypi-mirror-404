class TemplateStyles:
	basic =1
	japanese_indigo = 2
	def __init__(self):
		self.basic = 1
		self.japanese_indigo = 2
	def __str__(self):
		to_display = "".join("{} - {} , ".format(v,k) for v,k in self.__dict__.items()  )
		return to_display

	def __repr__(self):
		return self.__str__

TEMPLATE_STYLES_AVAILABLE = list( TemplateStyles().__dict__.values())