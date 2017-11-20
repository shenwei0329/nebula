# -*- coding: utf-8 -*-
from invoke import Collection

from nebula.core import config

from . import db
from . import data
from . import test
from . import doc
from . import server
from . import i18n

config.set_defaults(args=[])
config.setup_logging()

ns = Collection()
ns.add_collection(Collection.from_module(server))
ns.add_collection(Collection.from_module(data))
ns.add_collection(Collection.from_module(db))
