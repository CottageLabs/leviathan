'''
A question system

'''

import json, requests, markdown

from flask import Blueprint, request, abort, make_response, render_template, flash, redirect, url_for
from flask.ext.login import current_user

from HTMLParser import HTMLParser

from portality.core import app

import portality.models as models

from portality.view.mine import mine

blueprint = Blueprint('question', __name__)




# deliver or receive particular questions
@blueprint.route('/', methods=['GET','POST'])
@blueprint.route('/<identifier>', methods=['GET','POST'])
def question(identifier=None):
    if request.method == 'GET':

        params = {
            'tags': request.values.get('tags',False),
            'keywords': request.values.get('keywords',False)
        }

        res = None
        
        if identifier is None:
            # TODO: this query should be filtered so as not to include questions 
            # the currently logged in user has already answered (if the user is logged in)
            
            # TODO: it is necessary for the UI to be able to pass query params into this
            # so that people can filter questions by tags
            
            qry = {
                "query" : { "match_all" : {} },
                "sort" : {
                    "_script" : { 
                        "script" : "Math.random()",
                        "type" : "string",
                        "params" : {},
                        "order" : "asc"
                    }
                }
            }

            if params['tags']:
                if 'bool' not in qry['query'].keys():
                    qry['query'] = {'bool':{'must':[]}}
                for v in params['tags'].split(','):
                    qry['query']['bool']['must'].append({'term':{'tags.exact':v}})
            if params['keywords']:
                if 'bool' not in qry['query'].keys():
                    qry['query'] = {'bool':{'must':[]}}
                for v in params['keywords'].split(','):
                    qry['query']['bool']['must'].append({'term':{'keywords.exact':v}})

            f = models.Question().query(q=qry)
            try:
                res = json.dumps(f['hits']['hits'][0]['_source'])
            except:
                pass
        else:
            f = models.Question().pull(identifier)
            if f is not None: res = f.json

            
        if res is not None:
            resp = make_response( res )
            resp.mimetype = "application/json"
            return resp
        else:
            abort(404)

    else:
        if identifier is not None:
            f = models.Question().pull(identifier)
        else:
            f = models.Question()

        if request.json:
            for k in request.json.keys():
                if k == 'tags':
                    f.data[k] = [i.strip(" ") for i in request.json[k].split(',')]
                else:
                    f.data[k] = request.json[k]
        else:
            for k, v in request.values.items():
                if k == 'tags':
                    f.data[k] = [i.strip(" ") for i in v.split(',')]
                elif k not in ['submit']:
                    f.data[k] = v

        if len(f.data.get('question','')) > 2:        
            f.data['question'] = strip_tags(f.data['question'])

        if len(f.data.get('question','')) > 2:
            f.data['formattedquestion'] = markdown.markdown(f.data['question'])
            f.data['shortquestion'] = ''
        
            tt = []
            for val in f.data['tags']:
                val = val.replace('#','').replace('@','')
                if len(val) > 1:
                    tt.append(val)
            f.data['tags'] = tt
            
            f.data['keywords'] = mine(blurb=f.data['question'],omitscores=True,raw=True)
            tk = []
            for val in f.data['keywords']:
                val = val.replace('#','').replace('@','')
                if len(val) > 2:
                    tk.append(val)
            f.data['keywords'] = tk
            
            f.data = metadata(request,f.data)
            
            f.save()
            flash("Thanks, your question has been added.","success")

        else:
            flash("Sorry, your question was not sufficiently verbose. Please try again.","danger")

        return redirect("/")
        


# get metadata about the question or answer submitted
def metadata(request,data):
    if 'request' not in data:
        try:
            src = requests.get('http://api.hostip.info/get_json.php?position=true&ip=' + request.remote_addr)
            try:
                data['request'] = {
                    'country_name': src.json()['country_name'],
                    'country_code': src.json()['country_code'],
                    'city': src.json()['city'],
                    'ip': src.json()['ip'],
                    'geo':{
                        'lat': src.json()['lat'],
                        'lng': src.json()['lng']
                    }
                }
            except:
                pass
        except:
            pass

    if 'groups' not in data:
        data['groups'] = []

    if current_user.is_anonymous() and 'anonymous' not in data['groups']:
        data['groups'].append('anonymous')
    elif current_user.id not in data['groups']:
        data['groups'].append(current_user.id)

    if data['request'].get('city',''):
        if data['request']['city'] not in data['groups']:
            data['groups'].append(data['request']['city'])
    if data['request'].get('ip',''):
        if data['request']['ip'] not in data['groups']:
            data['groups'].append(data['request']['ip'])
    if data['request'].get('geo',{}).get('lat',False) and data['request'].get('geo',{}).get('lng',False):
        latlng = str(data['request']['geo']['lat']) + ',' + str(data['request']['geo']['lng'])
        if latlng not in data['groups']:
            data['groups'].append(latlng)

    return data


# strip html from the input question
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
