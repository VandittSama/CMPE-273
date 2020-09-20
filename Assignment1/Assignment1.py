from flask import Flask, jsonify, abort, request, send_file
from sqlitedict import SqliteDict
import hashlib
import qrcode
import io

app = Flask(__name__)

bookmarksDB = SqliteDict('.my_db.sqlite', autocommit=True)

@app.route('/')
def root():
    return 'Assignment 1 root address'

@app.route('/api')
def home():
    return 'Please enter complete address'

@app.route('/api/bookmarks', methods=['POST'])
def newBookmark():
    if not request.json:
        abort(400)
    id = hashlib.sha256(request.json['url'].encode('utf-8')).hexdigest()
    if id in bookmarksDB:
        return jsonify({'reason':"The given URL already existed in the system."}), 400
    newBookmark = {
        'id' : id,
        'name' : request.json['name'],
        'url' : request.json['url'],
        'description' : request.json['description']
    }
    bookmarksDB[id] = newBookmark
    return jsonify({'ID' : id}), 201 

@app.route('/api/bookmarks/<id>', methods=['GET', 'DELETE'])
def getOrDelete(id):
    if not id in bookmarksDB:
            abort(404)
    if request.method == 'GET':
        return jsonify(bookmarksDB[id])
    elif request.method == 'DELETE':
        del bookmarksDB[id]
        return '', 204

@app.route('/api/bookmarks/<id>/qrcode')
def qrCode(id):
    if not id in bookmarksDB:
            abort(404)
    bookmark = bookmarksDB[id]
    img = qrcode.make(bookmark['url'])
    return serve_pil_image(img)

@app.route('/api/bookmarks/<id>/stats')
def stats(id):
    if not id in bookmarksDB:
            abort(404)
    return '<HTML>Should support conditional get</HTML>'

def serve_pil_image(pil_img):
    img_io = io.BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run()