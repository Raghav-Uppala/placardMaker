from flask import Flask, request, render_template, send_file
from PIL import Image, ImageFont, ImageDraw
from PyPDF2 import PdfReader, PdfWriter
import numpy as np 
import img2pdf
import csv
import os
import io

def placard_maker(filename):
  def get_dimensions(font_path, font_size, text):
    font = ImageFont.truetype(font_path, font_size)

    left, top, right, bottom = font.getbbox('Hello world')
    width = font.getlength(text)

    return [left, top, right, bottom, width]

  def resize(img, new_width, new_height, scale):
    width = img.width
    height = img.height 

    calc_width = new_width
    calc_height = new_height

    aspect_ratio = width/height
    
    if aspect_ratio > 1:
      calc_width = calc_height * aspect_ratio  
    elif aspect_ratio < 1:
      calc_width = calc_height * aspect_ratio
    
    return img.resize((int(calc_width*scale), int(calc_height*scale)))

  def crop(image, x_shift=0, y_shift=0, width=804, height=803):
      image1 = image.crop((int((image.width - width)/2)+x_shift, y_shift + int((image.height - height)/2), x_shift + width + int((image.width - width)/2), y_shift + height + int((image.height - height)/2)))

      # https://www.codespeedy.com/how-to-crop-an-image-with-rounded-circle-shape-in-python/
      img = image1.convert("RGB") #convert to RGB
      arrImg = np.array(img) #convert to numpy array
      alph = Image.new('L', img.size, 0) #create a new image with alpha channel
      draw = ImageDraw.Draw(alph) #create a draw object
      draw.pieslice([0, 0, img.size[0], img.size[1]], 0, 360, fill = 255) #create a circle
      arAlpha = np.array(alph) #conver to numpy array
      arrImg = np.dstack((arrImg, arAlpha)) #add alpha channel to the image
      return Image.fromarray(arrImg)

  def save_pdf(img, path, img_path):
    pdf_bytes = img2pdf.convert(img_path)
    file = open(path, "wb")
    file.write(pdf_bytes)
    img.close()
    file.close() 

  def wrap_arr(font_path, font_size, text, width):
    dimentions = get_dimensions(font_path, font_size, text)
    text_width = dimentions[4]
    width_of_space = get_dimensions(font_path, font_size, " ")[4]

    if(width > text_width):
      return [text]
      
    else:
      words = text.split(" ")
      len_words = []
      for i in words:
        len_words.append(get_dimensions(font_path, font_size, i)[4])

      lines = []
      line = []
      n = 0
      sum = 0
      for i in len_words:
        sum += i
        if(n < len(len_words)):
          sum += width_of_space
        if (sum < width):
          line.append(n)
          n += 1
          continue
        elif(sum == width):
          line.append(n)
          lines.append(line)
          line = []
        elif(sum > width):
          lines.append(line)
          line = [n]
        sum = 0
        n += 1
      lines.append(line)

      wrapped = []
      counter = 0
      for line in lines:
        wrapped.append("")
        for i in line:
          wrapped[counter] += words[i] + " "
        wrapped[counter] = wrapped[counter].strip()
        counter += 1
    return wrapped

  def place_img(img_path, paste_img, x_shift, y_shift, scale = 1):
    img = Image.open(img_path) 

    img = resize(img, 803, 803, scale)
    img = crop(img, x_shift, y_shift)

    x_corner_coord = int(460 - img.width/2)
    y_corner_coord = int(503 - img.height/2) 

    paste_img.paste(img, (x_corner_coord,y_corner_coord), img) 

  def place_text(x_coord, y_coord, paste_img, text, font_path, font_variation, color, nfont_size=False, box_width=1400, box_height=500, text_width=False):
    
    x_corner_coord = int(x_coord - box_width/2) 
    y_corner_coord = int(y_coord - box_height/2)

    unwrapped_country_name = text # long string

    if(len(unwrapped_country_name) >= 28 and nfont_size == False):
      font_size = 120
    elif(len(unwrapped_country_name) < 28 and nfont_size == False):
      font_size = 150
    else:
      font_size = nfont_size

    font = ImageFont.truetype(font_path, font_size)
    font.set_variation_by_name(font_variation)

    if text_width != False:
      w_text = text_width
    else:
      w_text = box_width + 100

    wrapped_country_name_arr = wrap_arr(font_path, font_size, unwrapped_country_name, w_text)

    box = Image.new("RGBA", (box_width, box_height), (255,255,255,0))

    current_h, pad = 50, 10
    for line in wrapped_country_name_arr:
      draw1 = ImageDraw.Draw(box)
      if(get_dimensions(font_path, font_size, line)[4] > 1900):
        font1 = ImageFont.truetype(font_path, font_size - 10)
        font1.set_variation_by_name(font_variation)
        w = draw1.textlength(line, font=font1)
        h = font_size
        draw1.text(((box_width - w) / 2, current_h), line, color, font=font1)
      else:
        w = draw1.textlength(line, font=font)
        h = font_size
        draw1.text(((box_width - w) / 2, current_h), line, color, font=font)
      current_h += h + pad

    pad1 = 50

    paste_img.paste(box, (x_corner_coord, y_corner_coord - pad1 - len(wrapped_country_name_arr)*font_size - pad*(len(wrapped_country_name_arr)-1)), box)


  with open(filename, mode="r") as matrix_file:
    matrix = csv.reader(matrix_file)
    
    committee_name = filename.rsplit( ".", 1 )[ 0 ] 
    
    # Setting font
    font_path = "fonts/montserrat/Montserrat-VariableFont_wght.ttf"
    font_variation = "Regular"
    color = (0, 50, 85)

    for country in matrix:
      # Reading country details
      countries = csv.reader(open("country.csv", mode = "r"))
      country_details = []

      for line in countries:
        if line[1] == " "+country[0] or line[0] == country[0]:
          country_details = [line[0].strip(), line[1].strip(), line[2].strip(), line[3].strip(), line[4].strip()]
      if country_details == []:
        return "Country flag not available"
      # print(country_details[1])

      # opening  blank placard
      placard = Image.open(r"blank_placard.png") 

      # drawing flag onto placard
      place_img(f"/flags/{country_details[0]}.png", placard, int(country_details[2]),int(country_details[3]), scale=float(country_details[4]))

      # writing country name
      place_text(1925, 730, placard, country_details[1], font_path, font_variation, color, box_width=1900)

      # writing committee name
      place_text(1925, 730+180, placard, committee_name, font_path, "Black", color, nfont_size=120)

      # Saving Placard
      placard.save("out.png")

      save_pdf(placard, f"output/{country_details[1]}.pdf", "out.png")
      print(country_details[1])

  # Save all placards to one pdf
  directory = os.fsencode("output")
  placards = PdfWriter()
  for file in list(reversed(os.listdir(directory))):
      filename = os.fsdecode(file)
      if filename.endswith(".pdf"):
          # print("output/"+filename)
          placard = PdfReader("output/"+filename, "rb")
          placards.add_page(placard.pages[0])
  placardsStream = open(rf"{committee_name}.pdf", "wb")
  placards.write(placardsStream)
  placardsStream.close()

  for file in os.listdir(directory):
    filename = os.fsdecode(file)
    os.remove("output/"+filename)
  return committee_name

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("form.html")

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
    if 'file' in request.files:
      file = request.files['file']
      filename = file.filename
      file.save(os.path.join("./",filename))

      name = placard_maker(filename)

      if name == "Country flag not available":
        return name

      os.remove(os.path.join("./", filename))

      file_path = os.path.join("./", f"{name}.pdf")
    
      return_data = io.BytesIO()
      with open(file_path, 'rb') as fo:
          return_data.write(fo.read())
      # (after writing, cursor will be at last byte, so move it to start)
      return_data.seek(0)

      os.remove(file_path)

      return send_file(return_data, mimetype='application/pdf', as_attachment=True, download_name=f'{name}.pdf')
                       
    return 'No File uploaded'

if __name__ == '__main__':
    app.run(debug=True, port=5000)
