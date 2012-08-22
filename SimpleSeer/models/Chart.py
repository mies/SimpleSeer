import logging

import mongoengine
from .base import SimpleDoc

from formencode import validators as fev
from formencode import schema as fes
from SimpleSeer import validators as V

from calendar import timegm
from datetime import datetime

from .OLAP import OLAP

log = logging.getLogger(__name__)


#################################
# name: the chart's name
# olap: the name of the olap to query to get data
# chartid: if overlaying multiple charts, provide the ID of the parent chart
# style: the type of chart (line, pie, area, etc.), selected from the list in the schema
# color: If chart has just one color, use the color parameter (this is just passed through: we need to more tightly define this)
# colormap: If chart has multipe colors, map x-series labels to their appropriate colors.  e.g., {'average': 'blue', 'max': 'red'}
# valuemap: If need to change the labels from the fieldnames to something more human friendly.  e.g., {'avgnumeric': 'average'}
# minval: the smallest value on the y-axis
# maxval: the largest value on the y-axis
# xtype: type of values on the x-axis, such as date/time or a linear scale of numers
# accumulate: boolean defining whether it accumulates/redraws existing values (helpful for histograms)
# renderorder: integeter specifying location on screen.  Smaller values to the top, larger to the bottom
# halfsize: if true, will draw at half the normal width.  Also causes subsequent graph to be drawn halfsize.
# realtime: boolean where True means do realtime updating
# datamap: a list of which fields are considered the raw data
# metamap: a list of the fields that are considered metadata
#################################

class ChartSchema(fes.Schema):
    name = fev.UnicodeString()
    description = fev.UnicodeString()
    olap = fev.UnicodeString()
    chartid = fev.UnicodeString()
    style = fev.UnicodeString()            
    color = fev.UnicodeString(if_missing='blue')                  
    colormap = V.JSON(if_empty=None, if_missing=None)
    labelmap = V.JSON(if_empty=None, if_missing=None)
    xTitle = fev.UnicodeString(if_empty='', if_missing='')
    yTitle = fev.UnicodeString(if_empty='', if_missing='')
    #stupid hack because i cant get labelmap to default to None
    useLabels = fev.Bool(if_missing=False)
    minval = fev.Int(if_missing=0)
    maxval = fev.Int(if_missing=100)
    xtype = fev.OneOf(['linear', 'logarithmic', 'datetime'], if_missing='datetime')
    accumulate = fev.Bool(if_missing=False)
    renderorder = fev.Int(if_missing=1)
    halfsize = fev.Bool(if_missing=False)
    realtime = fev.Bool(if_missing=True)
    dataMap = V.JSON(if_missing=[])
    metaMap = V.JSON(if_missing=[])


class Chart(SimpleDoc, mongoengine.Document):

    name = mongoengine.StringField()
    description = mongoengine.StringField()
    olap = mongoengine.StringField()
    style = mongoengine.StringField()
    chartid = mongoengine.ObjectIdField()
    color = mongoengine.StringField()
    colormap = mongoengine.DictField()
    labelmap = mongoengine.DictField()
    xTitle = mongoengine.StringField()
    yTitle = mongoengine.StringField()
    useLabels = mongoengine.BooleanField()
    minval = mongoengine.IntField()
    maxval = mongoengine.IntField()
    xtype = mongoengine.StringField()
    accumulate = mongoengine.BooleanField()
    renderorder = mongoengine.IntField()
    halfsize = mongoengine.BooleanField()
    realtime = mongoengine.BooleanField()
    dataMap = mongoengine.ListField()
    metaMap = mongoengine.ListField()

    meta = {
        'indexes': ['name']
    }

    def __repr__(self):
        return "<Chart %s>" % self.name
    
    def mapData(self, results):
        data = []
        
        for r in results:
            if 'capturetime' in r:
                if type(r['capturetime']) == datetime:
                    r['capturetime'] = timegm(r['capturetime'].timetuple()) * 1000
            thisData = [r.get(d, 0) for d in self.dataMap]
            thisMeta = [r.get(m, 0) for m in self.metaMap]
            
            data.append({'d': thisData, 'm': thisMeta})
            
        return data
    
    def createChart(self, **kwargs):
        
        # Get the OLAP and its data
        o = OLAP.objects(name=self.olap)
        o = o[0]
        if ('sincetime' in kwargs):
            o.since = int(kwargs['sincetime'] / 1000)
    
        if 'beforetime' in kwargs:
            o.before = int(kwargs['beforetime'] / 1000)

        data = o.execute()
                
        chartData = {'name': self.name,
                     'olap': self.olap,
                     'chartid': self.chartid,
                     'style': self.style,
                     'color': self.color,
                     'colormap': self.colormap,
                     'labelmap': self.labelmap,
                     'minval': self.minval,
                     'maxval': self.maxval,
                     'xTitle': self.xTitle,
                     'yTitle': self.yTitle,
                     'xtype': self.xtype,
                     'accumulate': self.accumulate,
                     'renderorder': self.renderorder,
                     'halfsize': self.halfsize,
                     'realtime': self.realtime,
                     'dataMap': self.dataMap,
                     'metaMap': self.metaMap,
                     'data': self.mapData(data)}

        
        return chartData


    def chartMeta(self):
        meta = {'name': self.name,
                'olap': self.olap,
                'chartid': self.chartid,
                'style': self.style,
                'color': self.color,
                'colormap': self.colormap,
                'labelmap': self.labelmap,
                'minval': self.minval,
                'maxval': self.maxval,
                'xTitle': self.xTitle,
                'yTitle': self.yTitle,
                'xtype': self.xtype,
                'accumulate': self.accumulate,
                'renderorder': self.renderorder,
                'halfsize': self.halfsize,
                'realtime': self.realtime,
                'dataMap': self.dataMap,
                'metaMap': self.metaMap}

        return meta

    def chartData(self, allParams = []):
        from SimpleSeer.OLAPUtils import OLAPFactory
        
        # Get the OLAP and its data
        if self.realtime and 'query' in allParams:
            of = OLAPFactory()
            cname, o = of.createTransient(allParams['query'], self)
        else:
            o = OLAP.objects(name=self.olap)[0]
            cname = self.name
            
        if 'limit' in allParams:
            o.limit = allParams['limit']
        if 'skip' in allParams:
            o.skip = allParams['skip']

        if 'sortinfo' in allParams:
            o.sortInfo = allParams['sortinfo']
        else:
            o.sortInfo = {}
        
        if 'query' in allParams:    
            query = allParams['query']
        else:
            query = []
            
        data = self.mapData(o.execute(query))
        res = dict(chart = str(cname), data = data)

        return res
