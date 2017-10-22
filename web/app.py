import os
import json
import settings

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response
from flask import redirect
from flask import flash
from flask import url_for
from flask import render_template
from flask import send_from_directory

from werkzeug.utils import secure_filename

from celery import Celery
from celery import Task

from pymongo import MongoClient
from bson.json_util import dumps

ALLOWED_EXTENSIONS = set(['obj', 'png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config.from_object(settings)

# For docker the mongo url is 'mongodb://<service_name>:<port>'
client = MongoClient('mongodb://mongo:27017')
db = client.test_db
collection = db.test_collection

# Celery Init
def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


celery = make_celery(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def tags():
    context = list(db.pieces.find({}))
    return render_template('index.html', tags=context)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )

@app.route('/upload', methods=['GET', 'POST'])
def upload_piece():
    if request.method == 'POST':
        if 'username' not in request.form:
            return 'username not defined'
        if request.form['username'] == '':
            return 'username is empty'
        username = request.form['username']

        if db.pieces.find_one({'username': username}):
            return 'username taken.'

        document = {
            'username': username,
            'tag': None,
            'model': None,
            'texture': None
        }

        file_keys = ['tag', 'texture', 'model']
        if not all(x in request.files for x in file_keys):
            return 'file missing in request'
        for key, file in request.files.items():
            if file.filename == '':
                return 'the following file is missing: ' + key
            if not allowed_file(file.filename):
                return 'the following file is not in an allowed format ' + key 
            if file and allowed_file(file.filename):
                _, extension = os.path.splitext(file.filename)
                new_filename =  username + '_' + key + extension

                file.save(
                    os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                )

                document[key] = url_for('uploaded_file', filename=new_filename)
                # return(str(os.path.join(app.config['UPLOAD_FOLDER'], new_filename)))
        
        db.pieces.insert_one(document)
    return render_template('upload.html')

###############################################################################
#
#                               API ROUTES
#
###############################################################################

@app.route('/api/v1/pieces')
def pieces():
    return Response(
        dumps(db.pieces.find({})),
        mimetype='application/json',
        headers={
            'Access-Control-Allow-Origin': '*',
        }
    )




###############################################################################
#
#                           CELERY TEST ROUTES
#
###############################################################################


@celery.task(name='task.add')
def add(a, b):
    return a + b


@app.route('/celery')
def test(x=3, y=4):
    try:
        x = int(request.args.get('x', x))
        y = int(request.args.get('y', y))
    except:
        pass
    task = add.apply_async((x, y))
    context = {
        'task': 'x + y',
        'id': task.id,
        'x': x,
        'y': y,
    }
    return jsonify(context)


@app.route('/celery/<task_id>')
def result(task_id):
    result = add.AsyncResult(task_id).get()
    return jsonify(result)


###############################################################################
#
#                             MONGO TEST ROUTES
#
###############################################################################

@app.route('/mongo')
def mongo_get():
    query = collection.find()
    items = list(query)
    return render_template('test.html', items=items)


@app.route('/mongo/post', methods=['POST'])
def mongo_post():
    collection.insert_one({
        'title': request.form['title'],
    })
    return redirect(url_for('mongo_get'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)
  
