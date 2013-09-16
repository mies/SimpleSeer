import mongoengine
from formencode import schema as fes
from .base import SimpleDoc, SONScrub


class RenderLayerSchema(fes.Schema):
    allow_extra_fields=True
    filter_extra_fields=True
    basesvg = fev.UnicodeString(if_missing=None)
    _svg = fev.UnicodeString(if_missing=None)


class RenderLayer(SimpleDoc, mongoengine.Document):
    basesvg = mongoengine.StringField(default=None)
    _svg = mongoengine.StringField(default=None)

    meta = {
        'allow_inheritance': True
    }

    def generateSVG(self):
        return ""

    @property
    def svg(self):
        if self._svg == None:
            self._svg = self.generateSVG()
            self.save()
        return self._svg

    @svg.setter
    def svg(self, value):
        return
