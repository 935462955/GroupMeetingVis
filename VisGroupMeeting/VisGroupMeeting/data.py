import json,os
from VisGroupMeeting import app

path = os.path.join(app.config['DATA_PATH'],'merged/ES2002a.json')
dialogs = None
reply_relation = None
sessions = None
with open(path,'r',encoding='utf-8') as f:
    dialogs = json.load(f)
path = os.path.join(app.config['DATA_PATH'],'reply_relation/reply_ES2002a.json')
with open(path,'r',encoding='utf-8') as f:
    reply_relation = json.load(f)
path = os.path.join(app.config['DATA_PATH'],'edge_bunding/edgeBunding_ES2002a.json')
with open(path,'r',encoding='utf-8') as f:
    sessions = json.load(f)

for index,item in enumerate(reply_relation):
    dialogs[index]['id'] = index
    dialogs[index]['reply_to_id'] = item['reply_to_id']
