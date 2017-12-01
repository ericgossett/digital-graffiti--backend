import requests
import os
"""
 This script will upload all the models present in the dummy-data directory. 

 To use install requests:
    pip install requests
"""

labels = [
    'tabby, tabby cat',
    'Labrador retriever',
    'jay',
    'jellyfish',
    'bee',
    'monarch, monarch butterfly, milkweed butterfly, Danaus plexippus'
]

upload_data = [
    {
        'username': name,
        'tag': './tags/' + name + '_tag.jpg',
        'model': './models/' + name + '_model.obj',
        'texture': './textures/' + name + '_texture.jpg'

    } for name in labels
]

url = 'http://127.0.0.1/upload'

for d in upload_data:
    files = {
        'tag': open(d['tag'], 'rb'),
        'model': open(d['model'], 'rb'),
        'texture': open(d['texture'], 'rb')
    }
    values = {
        'username': d['username'],
        'password': 'TeamNoahsFTW'
    }
    _ = requests.post(url, files=files, data=values)
