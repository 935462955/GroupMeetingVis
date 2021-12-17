from flask import Flask, render_template,jsonify,request
import json, os
from VisGroupMeeting import app,data

@app.route('/')
def index():
    return render_template('index.html',dialogs=json.dumps(data.dialogs),sessions=json.dumps(data.sessions))