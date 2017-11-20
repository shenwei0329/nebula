from .extensions import db, resizer


class Upload(db.Model):
    __tablename__ = 'upload'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)
    url = db.Column(db.Unicode(255), nullable=False)

if resizer:
    for size in resizer.sizes.iterkeys():
        setattr(Upload, size + '_name', db.Column(db.Unicode(255)))
        setattr(Upload, size + '_url', db.Column(db.Unicode(255)))
