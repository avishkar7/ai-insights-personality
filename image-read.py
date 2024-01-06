import os
import json    
from predict import Predictor
from model import Model

P = Predictor()

def trial():
    directory = './static'
    filename = 'result_avi7.json'
    filepath = os.path.join(directory, filename)
    filenameans = 'answers_avi7.json'
    fileanswer = os.path.join(directory, filenameans)   
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
    print(answer)

    prediction = P.predict([answer])
    print(prediction)
    
if __name__ == '__main__':
    trial()