
from datetime import datetime

from portality.core import app

from portality.dao import DomainObject as DomainObject

'''
Define models in here. They should all inherit from the DomainObject.
Look in the dao.py to learn more about the default methods available to the Domain Object.
When using portality in your own flask app, perhaps better to make your own models file somewhere and copy these examples
'''


# an example account object, which requires the further additional imports
# There is a more complex example below that also requires these imports
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

class Account(DomainObject, UserMixin):
    __type__ = 'account'

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)

    @property
    def is_super(self):
        return not self.is_anonymous() and self.id in app.config['SUPER_USER']
    
    @property
    def questions_created(self):
        # TODO: return all the questions this user created
        return []

    @property
    def questions_modified(self):
        # TODO: return all the questions this user modified
        return []

    @property
    def questions_answered(self):
        # TODO: return all the questions this user answered
        return []

    @property
    def questions_answered_positively(self):
        # TODO: return all the questions this user answered positively
        return []

    @property
    def questions_answered_negatively(self):
        # TODO: return all the questions this user answered negatively
        return []

    @property
    def questions_modified_since_answer(self):
        # TODO: return all the questions that have been modified since this
        # user last answered the question
        return []

    @property
    def answers(self):
        # TODO: return all the answers this user submitted
        return []
    
    
class Question(DomainObject):
    __type__ = 'question'

    @property
    def answers(self):
        # TODO: get all answers about this question and return them
        return []

    @property
    def positive_answers(self):
        # TODO: get all positive answers about this question and return them
        return []

    @property
    def negative_answers(self):
        # TODO: get all negative answers about this question and return them
        return []

    @property
    def history(self):
        # TODO: get all the versions of this question that have existed
        return []


class Answer(DomainObject):
    __type__ = 'answer'
    
    @property
    def question(self):
        # TODO: get the question this answer is about
        return {}


# a special object that allows a search onto all index types - FAILS TO CREATE INSTANCES
class Everything(DomainObject):
    __type__ = 'everything'

    @classmethod
    def target(cls):
        t = 'http://' + str(app.config['ELASTIC_SEARCH_HOST']).lstrip('http://').rstrip('/') + '/'
        t += app.config['ELASTIC_SEARCH_DB'] + '/'
        return t
    

# You could write a record model that stores versions of itself in an archive.
# In which case, here is an example of an Archive model.
class Archive(DomainObject):
    __type__ = 'archive'
    
    @classmethod
    def store(cls, data, action='update'):
        archive = Archive.get(data.get('_id',None))
        if not archive:
            archive = Archive(_id=data.get('_id',None))
        if archive:
            if 'store' not in archive.data: archive.data['store'] = []
            try:
                who = current_user.id
            except:
                who = data.get('_created_by','anonymous')
            archive.data['store'].insert(0, {
                'date':data.get('_last_modified', datetime.now().strftime("%Y-%m-%d %H%M")), 
                'user': who,
                'state': data, 
                'action':action
            })
            archive.save()
        

