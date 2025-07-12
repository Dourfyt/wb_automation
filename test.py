import win32print
import win32ui
from PIL import Image, ImageWin

printer_name = win32print.GetDefaultPrinter()
hprinter = win32print.OpenPrinter(printer_name)
printer_info = win32print.GetPrinter(hprinter, 2)
pdc = win32ui.CreateDC()
pdc.CreatePrinterDC(printer_name)
pdc.StartDoc("Image Print Job")
pdc.StartPage()

# Открываем и вставляем изображение
img = Image.open("for_print/test-article-001/ПЕЧАТЬ.png")
bmp = img.convert("RGB")  # JPEG может быть CMYK

# Масштабирование под A4 (например)
width, height = bmp.size
dib = ImageWin.Dib(bmp)
dib.draw(pdc.GetHandleOutput(), (0, 0, width, height))

pdc.EndPage()
pdc.EndDoc()
pdc.DeleteDC()