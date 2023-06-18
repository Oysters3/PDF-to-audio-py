import pyttsx3, PyPDF2
from PyPDF2 import PdfReader

reader = PdfReader("Irish.pdf")
speaker = pyttsx3.init()

number_of_pages = len(reader.pages)
page = reader.pages[0]
text = page.extract_text()
clean_text = text.strip().replace('\n', ' ')
print(clean_text)

speaker.save_to_file(clean_text, 'Irish.mp3')
speaker.runAndWait()

speaker.stop()