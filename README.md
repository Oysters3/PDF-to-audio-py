# PDF-to-audio-py
PDF to audio Py 2023.06.18
This was a test to learn about python and its abilities. First time setup Github, VS Code, Python, venv environemtns and loading Packages via pip.

Code intially learnt from TiffinTech off Utube, all credit for original code to her. 
Note: Tiff must be using Unix or MacOs as the commands are different to Windows. 

https://packaging.python.org/en/latest/tutorials/installing-packages/

Also had to change a section for PyPDF2 to line up with instructions. 
  
   number_of_pages = len(reader.pages)
   page = reader.pages[0]
   text = page.extract_text()
   clean_text = text.strip().replace('\n', ' ')
   print(clean_text)

Was good to have the errors and work through them. 

What else are the nights for...
