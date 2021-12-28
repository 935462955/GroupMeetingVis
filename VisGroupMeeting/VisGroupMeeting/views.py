from flask import Flask, render_template,jsonify,request
import json, os
from VisGroupMeeting import app,data

@app.route('/')
def index():
    print(data.personal_ability) # TODO
    return render_template('index.html',dialogs=json.dumps(data.dialogs),sessions=json.dumps(data.sessions)
                           ,personal_ability = json.dumps(data.personal_ability),headPos=json.dumps(data.headPos)
                           ,keywordsOfPersonal = json.dumps(data.keywordsOfPersonal)
                           ,agendas = json.dumps(data.agendas))