import os.path
from flask import Flask, redirect, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.storage import get_default_storage_class
from flask.ext.uploads import delete, init, save, Upload

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['DEFAULT_FILE_STORAGE'] = 'filesystem'
app.config['UPLOADS_FOLDER'] = os.path.realpath('.') + '/static/'
app.config['FILE_SYSTEM_STORAGE_FILE_VIEW'] = 'static'
db = SQLAlchemy(app)
Storage = get_default_storage_class(app)
init(db, Storage)
db.create_all()


@app.route('/')
def index():
    """List the uploads."""
    uploads = Upload.query.all()
    return (
        '<a href="/upload">New Upload</a><br>' +
        u''.join(
            u'<a href="%s">%s</a>'
            u'<form action="/delete/%s" method="POST">'
            u'  <button type="submit">Delete</button>'
            u'</form><br>'
            % (Storage().url(u.name), u.name, u.id)
            for u in uploads
        )
    )


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload a new file."""
    if request.method == 'POST':
        print 'saving'
        save(request.files['upload'])
        return redirect(url_for('index'))
    return (
        u'<form method="POST" enctype="multipart/form-data">'
        u'  <input name="upload" type="file">'
        u'  <button type="submit">Upload</button>'
        u'</form>'
    )


@app.route('/delete/<int:id>', methods=['POST'])
def remove(id):
    """Delete an uploaded file."""
    upload = Upload.query.get_or_404(id)
    delete(upload)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(port=8000)
