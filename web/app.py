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

from pymongo import MongoClient
from bson.json_util import dumps

ALLOWED_EXTENSIONS = set(['obj', 'jpg'])

app = Flask(__name__)
app.config.from_object(settings)

# For docker the mongo url is 'mongodb://<service_name>:<port>'
client = MongoClient('mongodb://mongo:27017')
db = client.test_db
collection = db.test_collection


def allowed_file(filename):
    """
    Specifies the allowed file extensions when uploading
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def tags():
    """
    The main view of the web application that list all the tags.
    """
    context = list(db.pieces.find({}))
    return render_template('index.html', tags=context)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Responds with an uploaded asset, given the filename.
    """
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )


@app.route('/upload', methods=['GET', 'POST'])
def upload_piece():
    """
    The upload route. Checks for the password. If vaild will upload 
    the files and save a record in the database.
    """
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
                new_filename = username + '_' + key + extension

                file.save(
                    os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                )

                document[key] = {
                    'name': new_filename,
                    'url': url_for(
                        'uploaded_file',
                        filename=new_filename,
                        _external=True
                    )
                }

        db.pieces.insert_one(document)
        return redirect(url_for('tags'))

    return render_template('upload.html')


@app.route('/piece/<username>')
def piece_viewer(username):
    """
    3D model viewer page for a given username.
    """
    user_piece = db.pieces.find_one({'username': username})
    if user_piece:
        return render_template('piece.html', piece=user_piece)
    else:
        return 'username not found'


###############################################################################
#
#                               API ROUTES
#
###############################################################################

@app.route('/api/v1/pieces')
def pieces():
    """
    Main API endpoint. Returns a JSON array listing every user and their files.
    """
    return Response(
        dumps(db.pieces.find({}, {'_id': False})),
        mimetype='application/json',
        headers={
            'Access-Control-Allow-Origin': '*',
        }
    )


@app.route('/api/v1/delete/<username>', methods=['DELETE'])
def delete_piece(username):
    """
    Deletes an uploaded user.
    """
    if request.method != 'DELETE':
        return Response('nope')
    if db.pieces.find_one({'username': username}):
        db.pieces.remove({'username': username})
        os.remove(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                username + '_tag.jpg'
            )
        )
        os.remove(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                username + '_texture.jpg'
            )
        )
        os.remove(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                username + '_model.obj'
            )
        )
        return Response(username + ' was deleted')
    else:
        return Response('invalid model or password')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)
