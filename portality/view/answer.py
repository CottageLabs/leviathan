'''
Answer system

'''

import json

from flask import Blueprint, request, abort, make_response, render_template, flash, redirect, url_for
from flask.ext.login import current_user

from portality.core import app

import portality.models as models


blueprint = Blueprint('answer', __name__)

@blueprint.route('/', methods=['GET','POST'])
@blueprint.route('/<identifier>', methods=['GET','POST'])
def answer(identifier=None):

    if request.method == 'GET':

        if identifier is None:
            abort(404)
        else:
            f = models.Answer().pull(identifier)
            if f:
                resp = make_response( f.json )
                resp.mimetype = "application/json"
                return resp
            else:
                abort(404)

    else:
        if identifier is not None:
            f = models.Answer.pull(identifier)
            if f is None: abort(404)
        else:
            f = models.Answer()

        if request.json:
            for k in request.json.keys():
                f.data[k] = request.json[k]
        else:
            for k, v in request.values.items():
                if k not in ['submit']:
                    f.data[k] = v

        f.save()

        return ""
        



