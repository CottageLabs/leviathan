'''

a completely customised graph endpoint for leviathan

receives a query with which to filter the questions, e.g. 
by tags or by user or by specific question.

then gets all the relevant questions
and all their tags
and all their answers

and get all the users - that created questions and submitted answers
connect users to the questions and answers they created

connect tags to questions they are about
connect answers to questions they are for
where a positive answer, shade green
where negative, shade red

pass the question text so it can be displayed too, and usernames and tags text

get hierarchies once they are enabled, and set a depth controller
so that for result set can get next level in all three directions
parents, siblings, children
then can recurse to depth setting

'''

import json, urllib2, requests

from flask import Blueprint, request, make_response

from portality.core import app
import portality.models as models
import portality.util as util


blueprint = Blueprint('graph', __name__)


@blueprint.route('/', methods=['GET','POST'])
@util.jsonp
def graph():

    def qvals(qid):
        # get the answers for this question and work out value as number of answers
        ans = [x for x in answers if x['qid.exact'] == qid]
        val = len(ans)

        # then get the color as avg of answers
        c = 0
        for a in ans: 
            c += float(a['answer'])
        if val != 0: c = c/val
        f = float(c+1) / 2
        col = '#%02x%02x%02x' % ((1-f)*255, f*255, 0.)

        # if value is 0, increase it to 1 so that the dot shows up
        if val == 0: val = 1

        return {'value':val*10,'color':col}


    def fuzzify(val):
        if '*' not in val and '~' not in val and ':' not in val:
            valparts = val.split(',')
            nval = ""
            for vp in valparts:
                if len(vp):
                    nval += '*' + vp + '* '
            val = nval

        return val.strip(" ")

    # get any query parameters
    params = {
        'tags': request.values.get('tags',False),
        'usernames': request.values.get('usernames',False),
        'answers': request.values.get('answers',False),
        'hierarchy':False, # TODO: implement question hierarchy
        'selectedtags': request.values.get('selectedtags',False),
        'selectedkeywords': request.values.get('selectedkeywords',False),
        'query': request.values.get('query',False),
        'question': request.values.get('question',False)
    }

    # the starting query
    qs = {
        'query':{
            'match_all':{
            }
        },
        'size':1000,
        'fields':[
            'question.exact',
            'tags.exact',
            'author.exact',
            'id.exact'
        ],
        'facets':{
        }
    }

    # add to the query depending on parameters
    if params['tags']:
        qs['facets']['tags'] = {
            'terms':{
                'field':'tags.exact',
                'size':10000
            }
        }

    if params['usernames']:
        qs['facets']['usernames'] = {
            'terms':{
                'field':'author.exact',
                'size':10000
            }
        }

    if params['selectedtags']:
        if 'bool' not in qs['query'].keys():
            qs['query'] = {
                'bool':{
                    'must':[]
                }
            }
        for s in params['selectedtags'].split(','):
            qs['query']['bool']['must'].append({'term':{'tags.exact':s}})

    if params['selectedkeywords']:
        if 'bool' not in qs['query'].keys():
            qs['query'] = {
                'bool':{
                    'must':[]
                }
            }
        for s in params['selectedkeywords'].split(','):
            qs['query']['bool']['must'].append({'term':{'keywords.exact':s}})

    if params['query']:
        if 'bool' not in qs['query'].keys():
            qs['query'] = {
                'bool':{
                    'must':[]
                }
            }
        qs['query']['bool']['must'].append({'query_string':{'query':fuzzify(params['query'])}})

    if params['question']:
        if 'bool' not in qs['query']:
            qs['query'] = {
                'bool':{
                    'must':[]
                }
            }
        qs['query']['bool']['must'] = {'term':{'id.exact':params['question']}}

    print json.dumps(qs,indent=4)

    # get all the questions that match the query
    res = models.Question.query(q=qs)
    questions = [i['fields'] for i in res.get('hits',{}).get('hits',[])]
    if params['tags']:
        tags = [i for i in res.get('facets',{}).get('tags',{}).get('terms',[])]
    else:
        tags = []
    if params['usernames']:
        usernames = [i for i in res.get('facets',{}).get('usernames',{}).get('terms',[])]
    else:
        usernames = []
    
    
    # get all the answers to those questions
    aq = {
        'query':{
            'filtered':{
                'query':{
                    'match_all':{}
                },
                'filter':{
                    'terms':{
                        'qid.exact':[i['id.exact'] for i in questions]
                    }
                }
            }
        },
        'size':100000,
        'fields':[
            'answer',
            'author.exact',
            'qid.exact',
            'id.exact'
        ]
    }
    ares = models.Answer.query(q=aq)
    answers = [i['fields'] for i in ares.get('hits',{}).get('hits',[])]
    


    # put everything into the nodes and work out the links
    positions = {}
    nodes = []
    links = []
    linksindex = {}

    # put all tags into the nodes
    for t in tags:    
        nodes.append({
            'type':'tag',
            'id':t['term'],
            'className':t['term'],
            'value':t['count'],
            'color':'#ccc'
        })
        positions[t['term']] = len(nodes) - 1

    # put all usernames into the nodes
    for u in usernames:    
        nodes.append({
            'type':'username',
            'id':u['term'],
            'className':u['term'],
            'value':u['count'],
            'color':'orange'
        })
        positions[u['term']] = len(nodes) - 1

    for q in questions:
        # add every question to the nodes    
        nodes.append({
            'type':'question',
            'id':q['id.exact'],
            'className':q.get('question.exact',""),
            'value':qvals(q['id.exact'])['value'],
            'color':qvals(q['id.exact'])['color']
        })
        positions[q['id.exact']] = len(nodes) - 1
        # for every question write a link to the author
        if params['usernames']:
            links.append({
                'source':positions[q['id.exact']],
                'target':positions[q['author.exact']]
            })
            linksindex[str(positions[q['id.exact']]) + "," + str(positions[q['author.exact']])] = 1
        # for every question write a link to all of its tags
        if params['tags']:
            for tg in q.get('tags.exact',[]):
                links.append({
                    'source':positions[q['id.exact']],
                    'target':positions[tg]
                })
                linksindex[str(positions[q['id.exact']]) + "," + str(positions[tag])] = 1    

        
    if params['answers']:
        for a in answers:
            # add every answer to the nodes
            if a['answer'] > 0:
                col = '#33CC00'
            elif a['answer'] == 0:
                col = '#666'
            elif a['answer'] < 0:
                col = 'red'
            nodes.append({
                'type':'answer',
                'id':a['id.exact'],
                'value':1,
                'color':col
            })
            positions[a['id.exact']] = len(nodes) - 1
            # for every answer write a link to the question
            links.append({
                'source':positions[a['id.exact']],
                'target':positions[a['qid.exact']]
            })
            linksindex[str(positions[a['id.exact']]) + "," + str(positions[a['qid.exact']])] = 1
            # for every answer write a link to the author
            if params['usernames']:
                links.append({
                    'source':positions[a['id.exact']],
                    'target':positions[a['author.exact']]
                })
                linksindex[str(positions[a['id.exact']]) + "," + str(positions[a['author.exact']])] = 1


    # send back the answer
    resp = make_response( json.dumps( {'nodes':nodes,'links':links, 'linksindex':linksindex} ) )
    resp.mimetype = "application/json"
    return resp





