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
        c = 0.0
        for a in ans: 
            c += float(a['answer'])
        if val != 0: c = c/val
        f = (c+1) / 2
        col = '#%02x%02x%02x' % ((1-f)*255, f*255, 0.)

        # if value is 0, increase it to 1 so that the dot shows up
        if val == 0: val = 1

        return {'value':val,'color':col,'score':c}


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
        'facets':request.values.get('facets','').split(','),    
        'answers': request.values.get('answers',False),
        'selectedtags': request.values.get('selectedtags',False),
        'oneoftags': request.values.get('oneoftags',False),
        'selectedkeywords': request.values.get('selectedkeywords',False),
        'selectedgroups': request.values.get('selectedgroups',False),
        'query': request.values.get('query',False),
        'question': request.values.get('question',False)
    }

    # the starting query
    qs = {
        'query':{
            'match_all':{
            }
        },
        'size':10000,
        'fields':[
            'question.exact',
            'groups.exact',
            'tags.exact',
            'author.exact',
            'id.exact'
        ],
        'facets':{
        }
    }

    for fct in params['facets']:
        if len(fct) > 0:
            qs['facets'][fct] = {
                'terms':{
                    'field':fct + '.exact',
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

    if params['oneoftags']:
        if 'bool' not in qs['query'].keys():
            qs['query'] = {
                'bool':{
                    'must':[]
                }
            }
        if 'should' not in qs['query']['bool'].keys():
            qs['query']['bool']['should'] = []
        for s in params['oneoftags'].split(','):
            qs['query']['bool']['should'].append({'term':{'tags.exact':s}})

    if params['selectedkeywords']:
        if 'bool' not in qs['query'].keys():
            qs['query'] = {
                'bool':{
                    'must':[]
                }
            }
        for s in params['selectedkeywords'].split(','):
            qs['query']['bool']['must'].append({'term':{'keywords.exact':s}})

    if params['selectedgroups']:
        if 'bool' not in qs['query'].keys():
            qs['query'] = {
                'bool':{
                    'must':[]
                }
            }
        for s in params['selectedgroups'].split(','):
            qs['query']['bool']['must'].append({'term':{'groups.exact':s}})

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

    # get all the questions that match the query
    res = models.Question.query(q=qs)
    questions = [i['fields'] for i in res.get('hits',{}).get('hits',[])]
    if 'tags' in params['facets']:
        tags = [i for i in res.get('facets',{}).get('tags',{}).get('terms',[])]
    else:
        tags = []
    if 'usernames' in params['facets']:
        usernames = [i for i in res.get('facets',{}).get('usernames',{}).get('terms',[])]
    else:
        usernames = []
    if 'groups' in params['facets']:
        groups = [i for i in res.get('facets',{}).get('groups',{}).get('terms',[])]
    else:
        groups = []
        

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
            'label': '#' + t['term'],
            'hoverlabel': t['term'] + " (" + str(t['count']) + ')',
            'value':t['count'],
            'color':'white'
        })
        positions[t['term']] = len(nodes) - 1

    # put all usernames into the nodes
    for u in usernames:    
        nodes.append({
            'type':'username',
            'id':u['term'],
            'className':u['term'],
            'label': '@' + u['term'],
            'hoverlabel': u['term'] + " (" + str(u['count']) + ')',
            'value':u['count'],
            'color':'orange'
        })
        positions[u['term']] = len(nodes) - 1

    # put all groups into the nodes
    for g in groups:
        nodes.append({
            'type':'group',
            'id':g['term'],
            'className':g['term'],
            'label': '@' + g['term'],
            'hoverlabel': g['term'] + " (" + str(g['count']) + ')',
            'value':g['count'],
            'color':'#ffeeaa'
        })
        positions[g['term']] = len(nodes) - 1

    for q in questions:
        # add every question to the nodes
        qv = qvals(q['id.exact'])
        nodes.append({
            'type':'question',
            'id':q['id.exact'],
            'className':q.get('question.exact',""),
            'label': q.get('shortquestion.exact',q.get('question.exact',"")),
            'hoverlabel': q.get('question.exact',"") + " - averaged " + str(qv['score']) + " over " + str(qv['value']) + " votes",
            'score':qv['score'],
            'value':qv['value'],
            'color':qv['color']
        })
        positions[q['id.exact']] = len(nodes) - 1
        # for every question write a link to the author
        if 'usernames' in params['facets']:
            links.append({
                'source':positions[q['id.exact']],
                'target':positions[q['author.exact']]
            })
            linksindex[str(positions[q['id.exact']]) + "," + str(positions[q['author.exact']])] = 1
        # for every question write a link to all of its tags
        if 'tags' in params['facets']:
            tgs = q.get('tags.exact',[])
            if not isinstance(tgs,list): tgs = [tgs]
            for tag in tgs:
                links.append({
                    'source':positions[q['id.exact']],
                    'target':positions[tag]
                })
                linksindex[str(positions[q['id.exact']]) + "," + str(positions[tag])] = 1    
        # for every question write a link to all of its tags
        if 'groups' in params['facets']:
            gps = q.get('groups.exact',[])
            if not isinstance(gps,list): gps = [gps]
            for gp in gps:
                links.append({
                    'source':positions[q['id.exact']],
                    'target':positions[gp]
                })
                linksindex[str(positions[q['id.exact']]) + "," + str(positions[gp])] = 1

        
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
                'label': "",
                'hoverlabel': a['author.exact'] + " voted " + str(a['answer']),
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
            # TODO: put links to faceted things that are relevant to answers, like groups or usernames
            '''if params['usernames']:
                links.append({
                    'source':positions[a['id.exact']],
                    'target':positions[a['author.exact']]
                })
                linksindex[str(positions[a['id.exact']]) + "," + str(positions[a['author.exact']])] = 1'''


    # send back the answer
    resp = make_response( json.dumps( {'nodes':nodes,'links':links, 'linksindex':linksindex} ) )
    resp.mimetype = "application/json"
    return resp





