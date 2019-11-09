from flask import Flask, request, session, after_this_request, jsonify, url_for
import random
import os
import json
import yaml

class Config:
    def __init__(self, APP_SECRET_KEY, SERVER_URL, AUTH_KEY_LENGTH, AUTH_EMAILS):
        self.APP_SECRET_KEY = APP_SECRET_KEY
        self.SERVER_URL = SERVER_URL
        self.AUTH_KEY_LENGTH = int(AUTH_KEY_LENGTH)
        self.AUTH_EMAILS = AUTH_EMAILS
        self.AUTH_KEY_COUNT = len(AUTH_EMAILS)

    def __repr__(self):
        return f"Config(APP_SECRET_KEY={self.APP_SECRET_KEY}, SERVER_URL={self.SERVER_URL}, "+\
           f"AUTH_KEY_COUNT={self.AUTH_KEY_COUNT}, AUTH_KEY_LENGTH={self.AUTH_KEY_LENGTH})"

with open('config.yaml', 'r') as f:
    config = Config(**yaml.load(f))
print("loaded config: "+str(config).replace('(', '(\n  ').replace(', ', ',\n  '))
app = Flask(__name__)
app.secret_key = config.APP_SECRET_KEY
SERVER_URL = config.SERVER_URL
# AUTH_TOKENS = config.AUTH_KEYS

def gen_b64():
    table = [ chr(ord('A')+i) for i in range(26) ] + [
        chr(ord('a')+i) for i in range(26) ] + [
        chr(ord('0')+i) for i in range(10) ] + [ '+', '_' ]
    # print(table)
    # print(len(table))
    def gen_b64(n):
        def gen_b64():
            return ''.join([ table[random.randint(0, 63)] for i in range(n) ])
        return gen_b64
    return gen_b64
gen_b64 = gen_b64()

def gen_unique(generator, unique_ids):
    def gen_unique():
        id = generator()
        while id in unique_ids:
            id = generator()
        unique_ids.add(id)
        return id
    return gen_unique

event_ids = set()
pitch_ids = set()
voter_ids = set()
auth_keys = set()

gen_event_id = gen_unique(gen_b64(6), event_ids)
gen_pitch_id = gen_unique(gen_b64(12), pitch_ids)
gen_voter_id = gen_unique(gen_b64(16), voter_ids)
gen_auth_key = gen_unique(gen_b64(config.AUTH_KEY_LENGTH), auth_keys)
gen_id = gen_b64(16)

AUTH_TOKENS = {
    k: v for k, v in [ 
        (gen_auth_key(), gen_auth_key())
        for i in range(config.AUTH_KEY_COUNT)
    ]
}

def load_events(dir='events'):
    for file in os.listdir(dir):
        path = os.path.join(dir, file)
        if path.endswith('.yaml'):
            print(f"loading event: {path}")
            with open(path, 'r') as f:
                yield file.strip('.yaml'), yaml.load(f)



class Event:
    def __init__(self, name, pitches, voting_rounds):
        self.id = gen_event_id()
        self.name = name
        self.pitches = {
            pitch.id: pitch
            for pitch in [ 
                Pitch(**(pitchinfo or {})) 
                for pitchinfo in pitches
            ]
        }
        self.pitches_dict = [
            pitch.dict for pitch in self.pitches.values()
        ]
        self.pitches_json = json.dumps(self.pitches_dict)
        self.voting_rounds = [
            VotingRound(f'{self.name}/{i+1}', self, **(round or {}))
            for i, round in enumerate(voting_rounds)
        ]

    def __repr__(self):
        return f"Event(pitches={self.pitches}, voting_rounds={self.voting_rounds})"


class Pitch:
    def __init__(self, name, url=None):
        self.name = name
        self.url = url
        self.id = gen_pitch_id()
        self.dict = { 'name': name, 'url': url, 'id': self.id }

    def __repr__(self):
        return f"Pitch(id='{self.id}', name='{self.name}', url='{self.url}')"

class VotingRound:
    def __init__(self, id, event, method=None, votes=None, slots=None):
        self.id = id
        self.event = event
        self.method = method or 'single'
        self.votes = int(votes or 1)
        self.slots = int(slots or 2)
        self.dict = { 'pitches': self.event.pitches_dict, 'method': self.method, 'votes': self.votes, 'slots': self.slots }
        self.json = json.dumps(self.dict)

    def __repr__(self):
        return f"VotingRound(id='{self.id}', method='{self.method}', votes={self.votes}, slots={self.slots})"

events = {
    event: Event(event, **info)
    for event, info in load_events()
}
print(f"{len(events)} event(s):")
for name, event in events.items():
    print(f"  {name}:")
    print(f"    id: {event.id}")
    print(f"    url: {SERVER_URL}/event/{name}")
    print(f"    pitches:")
    for pitch in event.pitches.values():
        print(f"      {pitch}")
    print(f"    rounds:")
    for round in event.voting_rounds:
        print(f"      {round} url:")
        print(f"        info url: {SERVER_URL}/info/{round.id}")
        print(f"        vote url: {SERVER_URL}/vote/{round.id}")
        print(f"        view url: {SERVER_URL}/view/{round.id}")

print("AUTH_TOKEN URLS:")
for email, (k, v) in zip(config.AUTH_EMAILS, AUTH_TOKENS.items()):
    print(f"  {email}: {SERVER_URL}/authorize/{k}/{v}")



# print(events)
voter_info = {}
voting_data = {}

# AUTH_KEYS = """
#     FOO: BAR
# """
# AUTH_KEYS = AUTH_KEYS.strip().split('\n')
# AUTH_KEYS = [ line.strip() for line in AUTH_KEYS ]
# AUTH_KEYS = [ line for line in AUTH_KEYS if line != "" ]
# AUTH_KEYS = [ line.split(':') for line in AUTH_KEYS ]
# AUTH_KEYS = [ (k.strip(), v.strip()) for k, v in AUTH_KEYS ]
# AUTH_TOKENS = dict(AUTH_KEYS)
# SERVER_URL = 'http://127.0.0.1:5000'


class VoterInfo:
    def __init__(self, id, authkey, privkey):
        print(f"loading voter w/ id {id}")
        self.id = id
        self.authkey = authkey
        self.privkey = privkey
        if self.id not in voter_info or self.authkey != voter_info[self.id].authkey:
             self.id = gen_voter_id()
             self.authkey = gen_id()
             self.privkey = gen_id()
             self.authorized = False
             print(f"Registered new voter: {self.id} auth: {self.authkey} priv: {self.privkey} (not yet authorized)")
             voter_info[self.id] = self
        else:
            self.authorized = voter_info[self.id].authorized
            self.privkey = voter_info[self.id].privkey

    @staticmethod
    def get(session):
        voter = VoterInfo(
            id=session.get("voter_id"),
            authkey=session.get("voter_authkey"),
            privkey=session.get("voter_privkey"))
        voter.update(session)
        return voter

    def update(self, session):
        session['voter_id'] = self.id
        session['voter_authkey'] = self.authkey
        session['voter_privkey'] = self.privkey
        # print(f"updated session: {session}")


def has_authorization_priveleges(session):
    authid = session.get('authid')
    authtoken = session.get('authtoken')
    return authid in AUTH_TOKENS and authtoken == AUTH_TOKENS[authid]


def get_auth_url(voter):
    return SERVER_URL + url_for('setauth', user=voter.id, authkey=voter.authkey)

def get_auth_link_html(voter):
    auth_url = get_auth_url(voter)
    return f'<a href="{auth_url}">{auth_url}</a>'

@app.route('/register')
def register():
    voter = VoterInfo.get(session)
    if not voter.authorized:
        voter.update(session)
        return json.dumps({ 'authorized': False, 'id': voter.id, 'key': voter.authkey, 
            'auth_url': get_auth_url(voter) })
            #os.path.join(SERVER_URL, url_for('setauth', user=voter.id, authkey=voter.authkey)) })
    return json.dumps({ 'authorized': True })


@app.route('/info/<string:event>/<int:round>', methods=['GET'])
def info(event=None,round=None):
    return events[event].voting_rounds[round-1].json


@app.route('/vote/<string:event>/<int:round>', methods=['GET','POST'])
def vote(event=None, round=None):
    # print(session)
    voter = VoterInfo.get(session)
    if not voter.authorized:
        return get_auth_link_html(voter)
        # return json.dumps({ 'error': 'user not authorized!' })

    if event not in events:
        return json.dumps({ 'error': f'no such event {event}' })

    eventid = events[event].id

    if eventid not in voting_data:
        voting_data[eventid] = {}
    if voter.id not in voting_data[eventid]:
        voting_data[eventid][voter.id] = {}

    if request.method == 'GET':
        return json.dumps(voting_data[eventid][voter.id])
    elif request.method == 'POST':
        # try:
            vote = get_verified_voting_data(request.form)
            voting_data[eventid][voter.id] = vote 
            process_vote(voter.id, vote)
            return "OK"
        # except InvalidVotingDataException as e:
        #     return str(e)
    else:
        return json.dumps({ 'error': f'invalid http method {request.method}'})
    return 'OK'

@app.route('/authorize/<string:authid>/<string:authtoken>')
def authorize(authid, authtoken):
    session['authid'] = authid
    session['authtoken'] = authtoken
    if has_authorization_priveleges(session):
        return "OK"
    return "invalid auth token(s)"

@app.route('/setauth/<string:user>/<string:authkey>/')
def setauth(user, authkey):
    if not has_authorization_priveleges(session):
        return json.dumps({ 'error': 'you do not have auth priveleges' })
    if user not in voter_info:
        return json.dumps({ 'error': 'invalid voter id' })
    if authkey != voter_info[user].authkey:
        return json.dumps({ 'error': 'invalid auth key' })
    if voter_info[user].authorized:
        return 'voter already authorized'
    print(f"authorized voter: {user}, authkey: {authkey}; authorized by: {session['authid']}, {session['authtoken']}")
    voter_info[user].authorized = True
    return 'OK'


