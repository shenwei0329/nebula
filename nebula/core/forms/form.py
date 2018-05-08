#-*- coding: utf-8  -*-
import flask_wtf
from flask import g

from nebula.core.common.encodingutils import safe_encoding

from .mixins import I18nMixin


class NebulaForm(I18nMixin, flask_wtf.Form):

    @property
    def request_args(self):
        return g.request_args

    @property
    def request_kwargs(self):
        return g.request_kwargs

    # TODO(xuwenbao): delete this shit
    def validate(self):
        """
        this method is a shit! 验证字段的中文名称应该由前端来获取.
        """
        success = super(NebulaForm, self).validate()
        if success is not None and not success and self.errors:
            _errors = {}
            for field_name, error in self.errors.items():
                field = self._fields.get(field_name)
                error = isinstance(error, list) and [safe_encoding(e) for e in error] or safe_encoding(error)
                _errors[field and field.label.text.encode('utf-8') or field_name] = error
            self._errors = _errors
        return success

