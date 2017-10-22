import requests
import os

tag_files = ['tags/' + f for f in os.listdir('tags') if f.endswith('.jpg')]
users = ['Banksy', 'Daim', 'Revok', 'Seak', 'Reyes', 'Invader', 'Saber']

upload_data = [{'username': name, 'tag': tag} for name, tag in zip(users, tag_files)]

url = 'http://127.0.0.1/upload'

for d in upload_data:
    files = {
        'tag': open(d['tag'], 'rb'),
        'model': open('x-wing.obj', 'rb'),
        'texture': open('x-wing_texture.jpg', 'rb')
    }
    values = {
        'username': d['username']
    }
    _ = requests.post(url, files=files, data=values)