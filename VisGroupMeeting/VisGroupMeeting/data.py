import base64
import json, os, time
from VisGroupMeeting import app
import cv2


class Node():
    def __init__(self, id, parent, children, speaker, session_id=None):
        self.id = id
        self.speaker = speaker
        self.parent = parent
        self.children = children
        self.session_id = session_id


def get_key_frame(desire_frames, file):  # file 从会议名称开始
    path = os.path.join(app.config['DATA_PATH'], 'video/' + file)
    vidcap = cv2.VideoCapture(path)
    if not vidcap.isOpened():
        print("open video failed")
        return []
    start = time.time()
    result = []
    for i in desire_frames:
        vidcap.set(1, i - 1)
        success, image = vidcap.read()
        if success:
            # RBG矩阵转 base64图片
            res_b = cv2.imencode('.jpg', image)[1].tostring()
            res_bs64 = base64.b64encode(res_b)
            result.append({'frame': i, 'img': "data:image/jpg;base64,{}".format(res_bs64.decode())})
        else:
            result.append({'frame': i, 'img': "data:image/jpg;base64,{}".format("")})
    #  cv2.imwrite("frame%d.jpg" % count, image)     # save frame as JPEG file
    vidcap.release()
    print(time.time() - start)
    return result


def getVideoFPS(file):
    video = cv2.VideoCapture(os.path.join(app.config['DATA_PATH'], 'video/' + file))
    # Find OpenCV version
    (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

    if int(major_ver) < 3:
        fps = video.get(cv2.cv.CV_CAP_PROP_FPS)
        print("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
    else:
        fps = video.get(cv2.CAP_PROP_FPS)
        print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))
    video.release()
    return fps

def class2json(root):
    session_id = root.session_id
    idx2treenode = {}
    nodelist = []
    def traver(pynode):
        result = get_key_frame(
            [int((float(dialogs[pynode.id]['startTime']) + float(dialogs[pynode.id]['endTime'])) / 2) * fps],
            meetingName + '/' + dialogs[pynode.id]['role'] + '.mp4')
        nodelist.append({
            "id": pynode.id,
            "parent": pynode.parent.id if pynode.parent else -1,
            "children": [node.id for node in pynode.children],
            "session_id": session_id,
            "img": result[0]['img']
        })
        idx2treenode[pynode.id] = len(nodelist) - 1
        for node in pynode.children:
            traver(node)

    traver(root)
    return {"nodelist": nodelist, "idx2treenode": idx2treenode}


def getReplyTree(session_id):
    for root in roots:
        if root.session_id == session_id:
            return class2json(root)


meetingName = "ES2002a"
path = os.path.join(app.config['DATA_PATH'], 'merged/' + meetingName + '.json')
dialogs = None
reply_relation = None
sessions = None
with open(path, 'r', encoding='utf-8') as f:
    dialogs = json.load(f)
roles = list(set([dialog['role'] for dialog in dialogs]))
path = os.path.join(app.config['DATA_PATH'], 'reply_relation/reply_' + meetingName + '.json')
with open(path, 'r', encoding='utf-8') as f:
    reply_relation = json.load(f)
path = os.path.join(app.config['DATA_PATH'], 'edge_bunding/edgeBunding_' + meetingName + '.json')
with open(path, 'r', encoding='utf-8') as f:
    sessions = json.load(f)
path = os.path.join(app.config['DATA_PATH'], 'agendas/' + meetingName + '.json')
with open(path, 'r', encoding='utf-8') as f:
    agendas = json.load(f)
headPos = {}
key_frames = {}
fps = getVideoFPS(meetingName + '/' + roles[0] + '.mp4')
for role in roles:
    path = os.path.join(app.config['DATA_PATH'], 'headPose/{}/{}.json'.format(meetingName, role))
    with open(path, 'r', encoding='utf-8') as f:
        headPos[role] = json.load(f)
        # 以下为读取关键帧图像
        require_frame = []
        left = headPos[role][0]
        right = left
        for i, pos in enumerate(headPos[role]):
            if pos['facePos'] == left['facePos']:
                right = pos
            else:
                if left['facePos'] != 'up':
                    j = (int(left['time']) + int(headPos[role][i]['time'])) // 2
                    require_frame.append(j * fps)
                left = pos
                right = left
        key_frames[role] = require_frame
# print(key_frames)
temp = {}
for role in roles:
    temp[role] = get_key_frame(key_frames[role], meetingName + '/' + role + '.mp4')
key_frames = temp
# print(headPos)
trees = []  # 下标索引树节点
roots = []  # 所有子会话的根
session_id = 0
for index, item in enumerate(reply_relation):
    if item['reply_to_id'] != '-':
        try:
            node = Node(index, trees[int(item['reply_to_id'])], [], item['speaker'])
        except:
            print(int(item['reply_to_id']))
        trees[int(item['reply_to_id'])].children.append(node)
    else:
        node = Node(index, None, [], item['speaker'], session_id)
        session_id += 1
        roots.append(node)
    trees.append(node)
for index, item in enumerate(reply_relation):
    dialogs[index]['id'] = index
    dialogs[index]['reply_to_id'] = item['reply_to_id']

# region personalData
with open(os.path.join(app.config['DATA_PATH'], 'backchannel.txt'), 'r') as f:  # 附和词
    bc = set([word.lower() for word in f.read().split(",")])
with open(os.path.join(app.config['DATA_PATH'], 'agreeWords.txt'), 'r') as f:  # 赞同词
    agreeWords = set([word.lower() for word in f.read().split(",")])
with open(os.path.join(app.config['DATA_PATH'], 'stopwords.txt'), 'r', encoding='utf-8') as f:  # 附和词
    stopwords = set([word.lower() for word in f.read().split("\n")])
stopwords.remove("\"")  # 传到前端会报错


def mystrip(s, l):
    for i in l:
        s = s.strip(i)
    return s


def myfind(l, target, key='index'):  # list target key  return index of target
    for index, item in enumerate(l):
        if item[key] == target:
            return index
    return -1


def getKeyWords(sentences):
    global s
    total = 30
    agenda_sentence_num = [0] * len(agendas)
    wordsOfAgenda = []
    for _ in agendas:
        wordsOfAgenda.append([])
    if len(sentences) == 0:
        return wordsOfAgenda
    for s in sentences:
        if 'agenda' not in dialogs[s] or dialogs[s]['agenda'] == "-":  # TODO 需要更好的方式处理没有分配议程的句子
            continue
        agenda_id = int(dialogs[s]['agenda'])
        agenda_sentence_num[agenda_id] += 1
        # 分词
        text = dialogs[s]['text'].lower().split(" ")
        for word in text:
            token = mystrip(word, ['.?! ,-'])
            if token not in stopwords:  # 去停用词
                tokIdx = myfind(wordsOfAgenda[agenda_id], token, 'word')
                if tokIdx == -1:
                    wordsOfAgenda[agenda_id].append({'word': token, 'cnt': 1, 'sentences': [s], 'agenda': agenda_id})
                else:
                    wordsOfAgenda[agenda_id][tokIdx]['cnt'] += 1
                    wordsOfAgenda[agenda_id][tokIdx]['sentences'].append(s)
    for index, num in enumerate(agenda_sentence_num):
        agenda_sentence_num[index] = round(num / len(sentences) * total)  # 每个议题可展示关键词席位
    out = []
    for index, _ in enumerate(wordsOfAgenda):  # 选择每个议题下的高频词输出
        wordsOfAgenda[index] = sorted(wordsOfAgenda[index], key=lambda x: x['cnt'], reverse=True)
        if agenda_sentence_num[index] < len(wordsOfAgenda[index]):  #
            out.extend(wordsOfAgenda[index][:agenda_sentence_num[index]])
        else:
            out.extend(wordsOfAgenda[index])
    # print(agenda_sentence_num)
    # print(wordsOfAgenda[0])
    return out


def calActivity(role):
    totalTime = float(dialogs[-1]['endTime'])
    speakTime = 0
    for dialog in dialogs:
        speakTime += float(dialog['endTime']) - float(dialog['startTime']) if dialog['role'] == role else 0
    return round(speakTime / totalTime, 2)


def calPerplexity(role):
    perplexity = 0
    totalUtr = 0
    keySentences = []
    for index, dialog in enumerate(dialogs):
        if dialog['role'] == role:
            totalUtr += 1
            if dialog['text'].find('?') != -1:
                perplexity += 1
                keySentences.append(index)
    keywords = getKeyWords(keySentences)
    return round(perplexity / totalUtr, 2) if totalUtr != 0 else 0, keywords


def calBackchannel(role):
    back = 0
    totalUtr = 0
    for dialog in dialogs:
        if dialog['role'] == role:
            totalUtr += 1
            backchannel_num = 0
            for word in dialog['text'].lower().split(" "):
                if mystrip(word, ['.?! ,-']) in bc:
                    backchannel_num += 1
            rate = backchannel_num / len(dialog['text'].split(" ")) * 100
            if rate >= 50:
                back += 1
                # backchannel graph data
                if dialog['reply_to_id'] == '-' or dialogs[int(dialog['reply_to_id'])]['role'] == role:
                    chordData[role][role] += 1
                else:
                    chordData[role][dialogs[int(dialog['reply_to_id'])]['role']] += 1
    return round(back / totalUtr, 2) if totalUtr != 0 else 0


def calLeadership(role):
    leadship = 0
    keySentences = []
    for root in roots:
        if root.speaker == role:
            leadship += 1
            keySentences.append(root.id)
    keywords = getKeyWords(keySentences)
    return round(leadship / len(roots), 2) if len(roots) != 0 else 0, keywords


def calContribution(role):
    contribute = 0
    totalUtr = 0
    keySentences = []

    def dfs(node):
        if not node:
            return
        if node.speaker == role:
            nonlocal totalUtr
            totalUtr += 1
        if len(node.children) > 0:
            counted = False  # 当前节点是否已经统计为贡献点
            for child in node.children:
                if node.speaker == role and not counted:
                    for word in dialogs[child.id]['text'].lower().split(" "):
                        if mystrip(word, ['.?! ,-']) in agreeWords:
                            nonlocal contribute
                            nonlocal keySentences
                            contribute += 1
                            counted = True
                            keySentences.append(node.id)
                            break
                dfs(child)

    for root in roots:
        dfs(root)
    keywords = getKeyWords(keySentences)
    return round(contribute / totalUtr, 2), keywords


personal_ability = []
keywordsOfPersonal = {}
chordData = {}
for role in roles:
    chordData[role] = {}
    for innerRole in roles:
        chordData[role][innerRole] = 0  # #初始化
for role in roles:
    activity = calActivity(role)
    contribution, keywordsOfContribution = calContribution(role)
    perplexity, keywordsOfPerplexity = calPerplexity(role)
    backchannel = calBackchannel(role)
    leadership, keywordsOfLeadership = calLeadership(role)
    personal_ability.append({
        "role": role,
        "Act": activity,
        "Contri": contribution,
        "Per": perplexity,
        "Bac": backchannel,
        "Lead": leadership,
    })
    keywordsOfPersonal[role] = {"Contribution": keywordsOfContribution, "Perplexity": keywordsOfPerplexity,
                                "Leadership": keywordsOfLeadership}

# endregion
