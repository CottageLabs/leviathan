'''
A contact-form backend mailer endpoint
'''

from flask import Blueprint, request, abort, render_template, flash

from portality.core import app


blueprint = Blueprint('leviathan', __name__)


# the main page
@blueprint.route('/', methods=['GET','POST'])
def index():

    if request.method == 'GET':
        return render_template(
            'index.html'
        )

