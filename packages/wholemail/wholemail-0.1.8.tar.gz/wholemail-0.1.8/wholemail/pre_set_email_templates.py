'''


This file contains file path information for preset email templates



'''

import os
from os.path import join 

current_file = __file__
base_dir ,file_name = os.path.split(current_file)
boilerplates_dir = join(base_dir , "html_boilerplates") # where all bolerplates are stored

email_verification_templates_base_dir = join(boilerplates_dir , "email_verification")
verification_code_templates_base_dir = join(boilerplates_dir , "verification_code")
reset_password_link_templates_base_dir = join(boilerplates_dir , "reset_password")
office_letter_templates_base_dir = join(boilerplates_dir , "office_letter")
informative_message_templates_base_dir = join(boilerplates_dir , "informative_message")




EMAIL_VERIFICATION_TEMPLATES = {
		1:join( email_verification_templates_base_dir , "basic.html" ),
		2:join( email_verification_templates_base_dir , "japanese_indigo.html" ),

}

VERIFICATION_CODE_TEMPLATES = {
		1:join( verification_code_templates_base_dir, "basic.html" ),
		2:join( verification_code_templates_base_dir, "japanese_indigo.html" ),

	
}


OFFICE_LETTER_TEMPLATES =  {
	1:join(office_letter_templates_base_dir  , "basic.html"),
	2:join( office_letter_templates_base_dir, "japanese_indigo.html" ),

	
}


INFORMATIVE_MESSAGE_TEMPLATES = {
	1:join(informative_message_templates_base_dir , "basic.html"),
		2:join( informative_message_templates_base_dir, "japanese_indigo.html" ),

	
}


RESET_PASSWORD_LINK_TEMPLATES = {
	
	1:join(reset_password_link_templates_base_dir  , "basic.html"),
		2:join(reset_password_link_templates_base_dir, "japanese_indigo.html" ),

	
}

 