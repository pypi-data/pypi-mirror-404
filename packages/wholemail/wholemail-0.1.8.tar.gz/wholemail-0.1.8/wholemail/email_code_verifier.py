
from code_monger import CodeGenerator

class EmailCodeVerifier:
	'''
	This class is used to verify code sent to emails 

	The codes are saved in a file .

	Attributes
	----------
	name:str
		A name you want to call the code verifier, any can do .
	file:str
		A path to a file where you wish to store the codes.
	length:int , optional
		The length of the codes to be generated.
	letters:bool , optional 
		Set to `True` to include alphabet letters  	.	
	punctuation_chars:bool
		Set to `True` to include punctuation charachters.
	casing:bool
		Set to `upper` , `lower` or `all` to set the casing of the code .
		Options are:
			upper - uppercase letters only
			lower - lowercase letters only
			all   - include all cases 

	Methods
	-------
	ValidateCode ( code:str , email:str , delete_if_valid:bool )-> bool
		This method checks if a code is valid ( present in the codes file ),
		along with the email provided . 

		Returns
		--------
		bool
			Whether the code provided was valid or not
	MakeNewCode( email:str) -> str
		Parameters
		----------
		email:str
			The email address asociated with the code to be generated.

		Returns
		-------
		str
			The code generated
	ClearCodes() -> None
		This method clears all the data in the file where the codes are stored.
	
	'''

	def __init__(self ,
						name:str ,
						  file:str , 
						length:int = 6,
						 numbers:bool = True ,
						  letters:bool = False , 
						punctuation_chars:bool = False ,
						 casing:str = "upper" ):
		'''
		Parameters
		----------
		name:str
			A name you want to call the code verifier, any can do .
		file:str
			A path to a file where you wish to store the codes.
		length:int , optional
			The length of the codes to be generated.
		letters:bool , optional 
			Set to `True` to include alphabet letters . 		
		punctuation_chars:bool
			Set to `True` to include punctuation charachters.
		casing:bool
			Set to `upper` , `lower` or `all` to set the casing of the code .
			Options are:
				upper - uppercase letters only
				lower - lowercase letters only
				all   - include all cases 
		'''

		self.file = file
		self.code_generator =CodeGenerator(storage_file = file )
		self.length = length 
		self.numbers = numbers 
		self.letters =  letters 
		self.punctuation_chars = punctuation_chars
		self.casing = casing
		self.name = name

	def ValidateCode(self , code , email , delete_if_valid = True ) -> bool:
		'''
		Used to check whether the code and email provided are present in the file. ie. If they are valid

		Parameters
		----------
		code:str
			A string representing the code that is to be validated .
		email:str
			The email address that was used during code generation .
		delete_if_valid:bool
			Set to `True` to delete the code and email from the file if the code is valid .
		
		Returns
		-------
		bool
			True if the code is valid else False

		'''
		
		return self.code_generator.ValidateCode(code , email , delete_if_valid)

	def MakeNewCode(self , email:str ) ->str:
		'''This method generates and saves a new code in the storage file provided  

		Parameters
		----------
		email:str
			The email address asociated with the code to be generated.

		Returns
		-------
		str
			The code generated
		'''

		code = self.code_generator.NewCode(
				email , length = self.length ,
				 numbers = self.numbers , letters = self.letters ,
				  punctuation_chars = self.punctuation_chars ,
				  casing = self.casing,

				   )
		return code

	def ClearCodes(self) -> None:
		'''
		Deletes all codes from the storage file 
		'''

		print("Removing all codes ...")
		with open(self.file , "w" , encoding='utf-8') as f:
			f.write('')
		print("All codes have been removed")