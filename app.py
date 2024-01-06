# Import all the necessary libraries
import numpy as np
from numpy.core.numeric import NaN
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json
import re
import time
import cv2
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from flask import Flask , render_template , request , url_for , jsonify , Response, session
from werkzeug.utils import redirect, secure_filename
from pyresparser import ResumeParser
from fer import Video
from fer import FER
from flask_mail import Mail , Message
from flask_mysqldb import MySQL
from video_analysis import extract_text
from decouple import config
from predict import Predictor
from model import Model
import os
import random

# Access the environment variables stored in .env file
MYSQL_USER = config('mysql_user')
MYSQL_PASSWORD = config('mysql_password')

# To send mail (By interviewer)
MAIL_USERNAME = config('mail_username')
MAIL_PWD = config('mail_pwd')

# For logging into the interview portal
COMPANY_MAIL = config('company_mail')
COMPANY_PSWD = config('company_pswd')

# Create a Flask app
app = Flask(__name__)

# App configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = MYSQL_USER
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = 'databasename' 
user_db = MySQL(app)

#Creating static file for images
static = os.path.join('/Users/avikawadgave/Downloads/Project-Video/static/')
app.config['STATIC_FOLDER'] = static
app.secret_key = 'Secret key to session in Flask'
UPLOAD_FOLDER = os.path.join('/Users/avikawadgave/Downloads/Project-Video/static/')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Mail configurations
mail = Mail(app)              
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PWD
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_ASCII_ATTACHMENTS'] = True
mail = Mail(app)

#Function calling predictor
P = Predictor()


# Initial sliding page
@app.route('/')
def home():
    return render_template('index.html')


# Interviewee signup 
@app.route('/signup' , methods=['POST' , 'GET'])
def interviewee():
    if request.method == 'POST' and 'username' in request.form and 'usermail' in request.form and 'userpassword' in request.form:
        username = request.form['username']
        usermail = request.form['usermail']
        userpassword = request.form['userpassword']
    
        cursor = user_db.connection.cursor()

        cursor.execute("SELECT * FROM candidates WHERE email = %s", (usermail,))
        account = cursor.fetchone()
    
        if account:
            err = "Email Already Exists"
            return render_template('index.html' , err = err)
        else:
            cursor.execute("SELECT * FROM candidates WHERE candidatename = %s", (username,))
            account = cursor.fetchone()
            if account:
                err = "Username Already Exists"
                return render_template('index.html' , err = err)
  
        if not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', usermail):
            err = "Invalid Email Address !!"
            return render_template('index.html' , err = err)
        elif not re.fullmatch(r'[A-Za-z0-9\s]+', username):
            err = "Username must contain only characters and numbers !!"
            return render_template('index.html' , err = err)
        elif not username or not userpassword or not usermail:
            err = "Please fill out all the fields"
            return render_template('index.html' , err = err)
        else:
            cursor.execute("INSERT INTO candidates VALUES (NULL, % s, % s, % s)" , (username, usermail, userpassword,))
            user_db.connection.commit()
            reg = "You have successfully registered !!"
        return render_template('trial.html' , reg = reg)
    else:
        return render_template('index.html')


# Interviewer signin 
@app.route('/signin' , methods=['POST' , 'GET'])
def interviewer():
    if request.method == 'POST' and 'company_mail' in request.form and 'password' in request.form:
        company_mail = request.form['company_mail']
        password = request.form['password']

        if company_mail == COMPANY_MAIL and password == COMPANY_PSWD:
            cursor = user_db.connection.cursor()
            cursor.execute("SELECT candidatename FROM candidates")
            username = [row[0] for row in cursor.fetchall()]  
            return render_template('usernames.html', usernames=username)
        else:
            return render_template("index.html" , err = "Incorrect Credentials")
    else:
        return render_template("index.html")



# personal details and resume parsing
@app.route('/prediction' , methods = ['GET' , 'POST'])
def predict():
    # get form data
    if request.method == 'POST':
        fname = request.form['firstname'].capitalize()
        lname = request.form['lastname'].capitalize()
        age = int(request.form['age'])
        gender = request.form['gender'].capitalize()
        email = request.form['email']
        college = request.form['college']
        stream = request.form['stream']
        file = request.files['resume']
        photo = request.files['photo']
        
        path = './static/{}'.format(file.filename)
        
        #img_filename = secure_filename(photo.filename)
        #photopath = photo.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        #session['uploaded_img_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
        
        file.save(path)

        # get data from the resume
        data = ResumeParser(path).get_extracted_data()
        
        result = {'Name':fname+' '+lname , 'Age':age , 'Gender':gender, 'Email':email , 'Mobile Number':data.get('mobile_number', None) , 
        'College':college, 
        'Degree':data.get('degree' , None),
        'Specialization':stream,
        'Skills':str(data['skills']).replace("[" , "").replace("]" , "").replace("'" , "")} 
     
        #with open('./static/result.json' , 'w') as file:
        #    json.dump(result , file)
        
        cursor = user_db.connection.cursor()
        cursor.execute("SELECT candidatename FROM candidates ORDER BY id DESC LIMIT 1")
        username = cursor.fetchone()

        # Construct file path
        directory = './static'
        filename = 'result_{}.json'.format(username[0])
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w') as file:
            json.dump(result, file)
        
        img_filename = '{}_photo.jpg'.format(username[0])
        pathphoto = photo.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        session['uploaded_img_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
        
        '''    
        #multiple result records    
        i = 0
        while True:
            filename = './static/result{}.json'.format(i)
            if not os.path.exists(filename):
                with open(filename, 'w') as file:
                    json.dump(result, file)
                break
            i += 1'''
            
    return render_template('questionPage.html')


#interview process
@app.route('/analysis', methods = ['POST'])
def video_analysis():
    
    # recording media recorder js and save
    quest1 = request.files['question1']
    path1 = "./static/{}.{}".format("question1","webm")
    quest1.save(path1)
    
    quest2 = request.files['question2']
    path2 = "./static/{}.{}".format("question2","webm")
    quest2.save(path2)

    quest3 = request.files['question3']
    path3 = "./static/{}.{}".format("question3","webm")
    quest3.save(path3)

    # speech to text response for each question - AWS
    responses = {'Question 1: Tell us something about yourself': [] , 'Question 2: What is the most stressful situation you have encountered at work?': [] , 'Question 3: What is your ideal workspace?': []}
    ques = list(responses.keys())
    
    text1 , data1 = extract_text("question1.webm")
    time.sleep(15)
    responses[ques[0]].append(text1)
    
    text2 , data2 = extract_text("question2.webm")
    time.sleep(15)
    responses[ques[1]].append(text2)

    text3 , data3 = extract_text("question3.webm")
    time.sleep(15)
    responses[ques[2]].append(text3)
    
    # save all responses
    #with open('./static/answers.json' , 'w') as file:
    #        json.dump(responses , file)
    
    '''       
    # saving multiple records of students
    i = 0
    while True:
        filename = './static/answers{}.json'.format(i)
        if not os.path.exists(filename):
            with open(filename, 'w') as file:
                json.dump(responses, file)
            break
        i += 1     
    '''
    cursor = user_db.connection.cursor()
    cursor.execute("SELECT candidatename FROM candidates ORDER BY id DESC LIMIT 1")
    username = cursor.fetchone()

    # Construct file path
    directory = './static'
    filename = 'answers_{}.json'.format(username[0])
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w') as file:
        json.dump(responses, file)
            
    videos = ["question1.webm", "question2.webm", "question3.webm"]
    frame_per_sec = 100
    size = (1280, 720)
    
    video = cv2.VideoWriter(f"./static/combined.webm", cv2.VideoWriter_fourcc(*"VP90"), int(frame_per_sec), size)


    # Write all the frames sequentially to the new video
    for v in videos:
        curr_v = cv2.VideoCapture(f'./static/{v}')
        while curr_v.isOpened():
            r, frame = curr_v.read()    
            if not r:
                break
            video.write(frame)         
    video.release()

    #face emotion recognition
    face_detector = FER(mtcnn=True)
    input_video = Video(r"./static/combined.webm")
    processing_data = input_video.analyze(face_detector, display = False, save_frames = False, save_video = False, annotate_frames = False, zip_images = False)
    vid_df = input_video.to_pandas(processing_data)
    vid_df = input_video.get_first_face(vid_df)
    vid_df = input_video.get_emotions(vid_df)
    
    pltfig = vid_df.plot(figsize=(12, 6), fontsize=12).get_figure()
    plt.ylabel("Emotion Level", fontsize=12)
    plt.xlabel("Time", fontsize=12)
    plt.legend(fontsize = 'large' , loc = 1)
    plt.title('Face Emotion Analysis')
    #pltfig.savefig(f'./static/fer_output.png')

    cursor = user_db.connection.cursor()
    cursor.execute("SELECT candidatename FROM candidates ORDER BY id DESC LIMIT 1")
    username = cursor.fetchone()

    # Construct file path
    directory = './static'
    filename = 'fer_output_{}.png'.format(username[0])
    #session['uploaded_img_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    #pltfig.savefig(uploaded_img_file_path)
    filepath = os.path.join(directory, filename)
    pltfig.savefig(filepath)
    
    return "success"


# Interview completed response message
@app.route('/recorded')
def response():
    return render_template('recorded.html')


# Results corresponding to the candidates
@app.route('/user_data/<username>')
def user_data(username):
    directory = './static'
    filename = 'result_{}.json'.format(username)
    filepath = os.path.join(directory, filename)
    filenameans = 'answers_{}.json'.format(username)
    fileanswer = os.path.join(directory, filenameans)
    filegraph = 'fer_output_{}.png'.format(username)
    filephoto = '{}_photo.jpg'.format(username)
    
    # Load the JSON data from the file
    with open(filepath, 'r') as file:
        output = json.load(file)
    with open(fileanswer, "r") as json_file:
        data = json.load(json_file)
    
    #question = list(data.keys())[0]
    #answer = data[question][0]

    answer_list = []
    for question in data:
        answers = data[question]
        for i in range(len(answers)):
            answer_list.append("".join(answers[i]))
    answer = ". ".join(answer_list)
    prediction = P.predict_personality([answer])
        
    graph = os.path.join(static, filegraph)
    pathphoto = session.get('uploaded_img_file_path')
    return render_template('user_data.html', username=username, responses=data, output=output, predictions=prediction, graph=filegraph, pathphoto=filephoto)



# Send job confirmation mail to selected candidate
@app.route('/accept' , methods=['GET'])
def accept():
    cursor = user_db.connection.cursor()
    cursor.execute("SELECT candidatename FROM candidates ORDER BY id DESC LIMIT 1")
    username = cursor.fetchone()
    directory = './static'
    filename = 'result_{}.json'.format(username[0])
    filepath = os.path.join(directory, filename)
    with open(filepath , 'r') as file:
        output = json.load(file)
    
    name = output['Name']
    email = output['Email']
    position = "Software Development Engineer"

    msg = Message(f'Job Confirmation Letter', sender = MAIL_USERNAME, recipients = [email])
    msg.body = f"Dear {name},\n\n" + f"Thank you for taking the time to interview for the {position} position. We enjoyed getting to know you. We have completed all of our interviews.\n\n"+ f"We are pleased to inform you that we would like to offer you the {position} position. We believe your past experience and strong technical skills will be an asset to our organization. Your starting salary will be $15,000 per year with an anticipated start date of July 1.\n\n"+ f"The next step in the process is to set up meetings with our CEO, Rahul Dravid\n\n."+ f"Please respond to this email by June 23 to let us know if you would like to accept the SDE position.\n\n" + f"I look forward to hearing from you.\n\n"+ f"Sincerely,\n\n"+ f"Harsh Verma\nHuman Resources Director\nPhone: 555-555-1234\nEmail: feedbackmonitor123@gmail.com"
    mail.send(msg)

    return "success"



# Send mail to rejected candidate
@app.route('/reject' , methods=['GET'])
def reject():

    cursor = user_db.connection.cursor()
    cursor.execute("SELECT candidatename FROM candidates ORDER BY id DESC LIMIT 1")
    username = cursor.fetchone()
    directory = './static'
    filename = 'result_{}.json'.format(username[0])
    filepath = os.path.join(directory, filename)
    with open(filepath , 'r') as file:
        output = json.load(file)
    
    name = output['Name']
    email = output['Email']
    position = "Software Development Engineer"

    msg = Message(f'Your application to Smart Hire', sender = MAIL_USERNAME, recipients = [email])
    msg.body = f"Dear {name},\n\n" + f"Thank you for taking the time to consider Smart Hire. We wanted to let you know that we have chosen to move forward with a different candidate for the {position} position.\n\n"+ f"Our team was impressed by your skills and accomplishments. We think you could be a good fit for other future openings and will reach out again if we find a good match.\n\n"+ f"We wish you all the best in your job search and future professional endeavors.\n\n"+ f"Regards,\n\n"+ f"Harsh Verma\nHuman Resources Director\nPhone: 555-555-1234\nEmail: feedbackmonitor123@gmail.com"
    mail.send(msg)

    return "success"

'''
# Display results to interviewee
@app.route('/info')
def info():
    with open('./static/result.json' , 'r') as file:
        output = json.load(file)

    with open('./static/answers.json' , 'r') as file:
        answers = json.load(file)
    
    with open("./static/answers.json", "r") as json_file:
        data = json.load(json_file)
    question = list(data.keys())[0]
    answer = data[question][0]
    prediction = P.predict([answer])
    pathphoto = session.get('uploaded_img_file_path')
    return render_template('tryresult.html' , output = output , responses = answers, predictions=prediction, photo = pathphoto)
'''

if __name__ == '__main__':
    app.run(debug = True)
