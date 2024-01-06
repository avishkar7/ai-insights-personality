from flask import Flask, render_template, request, session
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)


app.secret_key = 'This is your secret key to utilize session in Flask'
UPLOAD_FOLDER = os.path.join('/Users/avikawadgave/Downloads/Project-Video/static/')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'} 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index_upload_and_show_data.html')
 
@app.route('/',  methods=("POST", "GET"))
def uploadFile():
    if request.method == 'POST':
        # Upload file flask
        uploaded_img = request.files['uploaded-file']
        # Extracting uploaded data file name
        img_filename = secure_filename(uploaded_img.filename)
        # Upload file to database (defined uploaded folder in static path)
        uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        # Storing uploaded file path in flask session
        session['uploaded_img_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
        print(img_filename)

        return render_template('index_upload_and_show_data_page2.html')
 
@app.route('/show_image')
def displayImage():
    # Retrieving uploaded file path from session
    img_file_path = session.get('uploaded_img_file_path', None)
    print(img_file_path)
    img_filename = os.path.basename(img_file_path)
    version = session.get('version', 0) + 1
    session['version'] = version
    # Display image in Flask application web page
    return render_template('show_image.html', user_image = img_file_path, version=version)
 
if __name__=='__main__':
    app.run(debug = True)