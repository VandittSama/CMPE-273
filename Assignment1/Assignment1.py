from flask import Flask, jsonify, abort, request, send_file
from etag_cache import etag_cache
from sqlitedict import SqliteDict
import hashlib
import qrcode
import io
import flask_monitoringdashboard as dahsboard

app = Flask(__name__)
dahsboard.bind(app)

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
    
    etag = str(hashlib.md5(request.json['url'].encode('utf-8')).hexdigest())
    newBookmark = {
        'id' : id,
        'name' : request.json['name'],
        'url' : request.json['url'],
        'description' : request.json['description'],
        'latest_etag' : str(etag)
    }
    bookmarksDB[id] = newBookmark
    bookmarksDB[str(etag)] = int(0)
    bookmarksDB.commit
    return jsonify({'ID' : id}), 201 

@app.route('/api/bookmarks/<id>', methods=['GET', 'DELETE'])
def getOrDelete(id):
    if not id in bookmarksDB:
            abort(404)
    if request.method == 'GET':
        bookmark = bookmarksDB[id]
        latestEtag = str(bookmark['latest_etag'])
        count = int(bookmarksDB[latestEtag])
        count = count + 1
        del bookmarksDB[bookmark['latest_etag']]
        temp = str(bookmark['url']) + str(count)
        etag = hashlib.md5(temp.encode('utf-8')).hexdigest()
        bookmarksDB[etag] = count
        bookmark['latest_etag'] = etag
        bookmarksDB[id] = bookmark
        bookmarksDB.commit
        del bookmark['latest_etag']
        return jsonify(bookmark)
    elif request.method == 'DELETE':
        bookmark = bookmarksDB[id]
        latestEtag = str(bookmark['latest_etag'])
        del bookmarksDB[latestEtag]
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
    reqEtag = request.headers.get(key='If-None-Match')
    bookmark = bookmarksDB[id]
    latestEtag = bookmark['latest_etag']
    if reqEtag == latestEtag:
        return '', 304
    checkCache = etag_cache(my_view)
    res = checkCache(latestEtag)
    return res

def my_view(latestEtag):
    yield {
                'ETag': latestEtag,
                'Cache-Control': 'max-age=60'
            }
    # Make the response
    yield str(bookmarksDB[latestEtag])

def serve_pil_image(pil_img):
    img_io = io.BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run()