import logging
import calendar
from time import gmtime, localtime, mktime
from datetime import datetime

import mongoengine
import numpy as np
from formencode import validators as fev
from formencode import schema as fes
import formencode as fe

from ..realtime import ChannelManager
from SimpleSeer.util import utf8convert

from SimpleSeer import validators as V
from .base import SimpleDoc
from .Inspection import Inspection
from .Result import Result

log = logging.getLogger(__name__)


class OLAPSchema(fes.Schema):
    name = fev.UnicodeString(not_empty=True)
    queryInfo = V.JSON(not_empty=True)
    descInfo = V.JSON(if_empty=None, if_missing=None)
    chartInfo = V.JSON(not_empty=True)
  
class QueryInfoSchema(fes.Schema):
    name = fev.UnicodeString(not_empty = True)
    since = V.DateTime(if_empty=0, if_missing=None)
    
class DescInfoSchema(fes.Schema):
    formula = fev.OneOf(['moving', 'mean', 'median', 'mode', 'var', 'std', 'max', 'min', 'first', 'last', 'uq', 'lq'], if_missing=None)
    window = fev.Int(if_missing=None)

class ChartInfoSchema(fes.Schema):
    chartType = fev.OneOf(['line', 'bar', 'pie', 'spline', 'area', 'areaspline','column','scatter'])
    chartColor = fev.UnicodeString(if_empty="")
    #TODO, this should maybe be validated to a hex string or web color

class RealtimeOLAP:

    def realtime(self, res):
        olaps = OLAP.objects
        for o in olaps:
            
            log.info('checking ' + o.name)
            # First, check for entries that just want the raw data
            if (o.descInfo is None) or (not o.descInfo.has_key('formula')):
                log.info('Send raw data for OLAP ' + o.name)
                r = ResultSet()
                rset = r.resultToResultSet(res)
                log.info(rset['data'])
                self.sendMessage(o, rset['data'])

            elif o.descInfo['formula'] == 'moving':
                # Special case for the moving average
                # TODO: This goes through the unnecessary step of putting together chart params.  
                # Could optimize by just doing data steps
                log.info('Send moving average for OLAP ' + o.name)
                
                o.queryInfo['limit'] = o.descInfo['window']
                rset = o.execute()
                log.info(rset['data'])
                self.sendMessage(o, rset['data'])
                
            else:
                # Trigger a descriptive if the previous record was on the other side of a group by window/interval
                
                window = o.descInfo['window']
                thisTime = calendar.timegm(res.capturetime.timetuple())
                previousTime = self.lastResult()
                border = thisTime - (thisTime % window)
                
                if (previousTime < border):
                    # This does the unnecessary step of creating chart info.  Could optimize this.
                    log.info('Sending descriptive for ' + o.name)
                    o.descInfo['trim'] = 0
                    rset = o.execute(sincetime = border - window)
                    log.info(rset['data'])
                    self.sendMessage(o, rset['data'])
                else:
                    log.info(o.name + ' declined update')
                    
                
    def lastResult(self):
        # Show the timestamp of the last entry in the result table
        rs = Result.objects.order_by('-capturetime')
        return calendar.timegm(rs[0].capturetime.timetuple())

    def sendMessage(self, o, data):
        log.info(len(data))
        msgdata = [dict(
            id = str(o.id),
            data = d[0:2],
            inspection_id =  str(d[2]),
            frame_id = str(d[3]),
            measurement_id= str(d[4]),
            result_id= str(d[5])
        ) for d in data]
        
        # Channel naming: OLAP/olap_name
        olapName = 'OLAP/' + utf8convert(o.name) + '/'
        ChannelManager().publish(olapName, dict(u='data', m=msgdata))
        

class OLAP(SimpleDoc, mongoengine.Document):
    # General flow designed for:
    # - One or more Queries to retrieve data from database
    # - Zero or more DescriptiveStatistics, computed from Queries
    # - One or more Chart, with the resuls from Cube or InferentialStats
    #
    # This class will handle most of the processing rather than 
    # Stepping through these manually.  Put a query string in one
    # end and the configuration and data for a chart will pop out 
    # the other end.

    name = mongoengine.StringField()
    queryInfo = mongoengine.DictField()
    descInfo = mongoengine.DictField()
    chartInfo = mongoengine.DictField()
        
    def __repr__(self):
        return "<OLAP %s>" % self.name
        
    def execute(self, sincetime = 0, limitresults = None):
        r = ResultSet()
        
        
        # Process configuration parameters
        queryinfo = self.queryInfo.copy()
        queryinfo['since'] = sincetime
        queryinfo['limit'] = self.limitResults(limitresults)
        
        # Get the resultset
        resultSet = r.execute(queryinfo)
        
        # Check if any descriptive processing (and any data to process)
        if (self.descInfo) and (len(resultSet['data']) > 0):
            d = DescriptiveStatistic()
            resultSet = d.execute(resultSet, self.descInfo)
        
        # Create and return the chart
        c = Chart()
        chartSpec = c.createChart(resultSet, self.chartInfo)
        return chartSpec
        
        
    def limitResults(self, thelimit):
        # If provided a limit, always use that limit
        # Else, if not defined in OLAP, use 500
        # Otherwise, use the one defined in OLAP
        if thelimit:
			return thelimit
        elif not self.queryInfo.has_key('limit'):
			return 500
        
        return self.queryInfo['limit']
		
        
			
        
        
class Chart:
    # Takes the data and puts it in a format for charting
    
    def dataRange(self, dataSet):
	# compute the min and max values suggested for the chart drawing
		ranges = dict()
	
		yvals = np.hsplit(np.array(dataSet),[1,2])[1]
		if (len(yvals) > 0):
			std = np.std(yvals)
			mean = np.mean(yvals)
			
			minFound = np.min(yvals)
			
			ranges['max'] = int(mean + 3*std)
			ranges['min'] = int(mean - 3*std)
			
			if (minFound > 0) and (ranges['min'] < 0): ranges['min'] = 0
		else:
			ranges['max'] = 0
			ranges['min'] = 0
		
		return ranges
    
    def createChart(self, resultSet, chartInfo):
        # This function will change to handle the different formats
        # required for different charts.  For now, just assume nice
        # graphs of (x,y) coordiantes
        
        chartRange = self.dataRange(resultSet['data'])
        
        chartData = { 'chartType': chartInfo['name'],
                      'chartColor': chartInfo['color'],
                      'labels': resultSet['labels'],
                      'range': chartRange,
                      'data': resultSet['data'] }
        
        return chartData


class DescriptiveStatistic:

    _descInfo = {}
    
    def execute(self, resultSet, descInfo):
        self._descInfo = descInfo
      
        # Moving Average
        if (descInfo['formula'] == 'moving'):
            resultSet['data'] = self.movingAverage(resultSet['data'], descInfo['window'])
            resultSet['labels']['dim1'] = str(descInfo['window']) + ' Measurement Moving Average'
        # Mean
        elif (descInfo['formula'] == 'mean'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], np.mean)
            resultSet['labels']['dim1'] = 'Mean, group by ' + self.epochToText(descInfo['window'])
        # Median
        elif (descInfo['formula'] == 'median'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], np.median)
            resultSet['labels']['dim1'] = 'Median, group by ' + self.epochToText(descInfo['window'])
        # Mode
        elif (descInfo['formula'] == 'mode'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], self.mode)
            resultSet['labels']['dim1'] = 'Mode, group by ' + self.epochToText(descInfo['window'])
        # Variance
        elif (descInfo['formula'] == 'var'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], np.var)
            resultSet['labels']['dim1'] = 'Variance, group by ' + self.epochToText(descInfo['window'])
        # Standard Deviation
        elif (descInfo['formula'] == 'std'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], np.std)
            resultSet['labels']['dim1'] = 'Standard Deviation, group by ' + self.epochToText(descInfo['window'])
        # Max
        elif (descInfo['formula'] == 'max'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], np.max)
            resultSet['labels']['dim1'] = 'Maximum, group by ' + self.epochToText(descInfo['window'])
        # Min
        elif (descInfo['formula'] == 'min'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], np.min)
            resultSet['labels']['dim1'] = 'Minimum, group by ' + self.epochToText(descInfo['window'])
        # First
        elif (descInfo['formula'] == 'first'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], self.first)
            resultSet['labels']['dim1'] = 'First, group by ' + self.epochToText(descInfo['window'])
        # Last
        elif (descInfo['formula'] == 'last'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], self.last)
            resultSet['labels']['dim1'] = 'Last, group by ' + self.epochToText(descInfo['window'])
        # Lower Quartile
        elif (descInfo['formula'] == 'lq'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], self.lq)
            resultSet['labels']['dim1'] = 'Lower Quartile, group by ' + self.epochToText(descInfo['window'])
        # Upper Quartile
        elif (descInfo['formula'] == 'uq'):
            resultSet['data'] = self.binStatistic(resultSet['data'], descInfo['window'], self.uq)
            resultSet['labels']['dim1'] = 'Upper Quartile, group by ' + self.epochToText(descInfo['window'])
        else:
            # If no matching function, just return the original result set    
            log.warn('Descriptive statistic got unknown formula: ' + descInfo['formula'])
        
        return resultSet

    def movingAverage(self, dataSet, window):
        # Just return the raw data if window too big
        if (len(dataSet) < window):
            return dataSet
            
        # Right now, hard code to do the average on the second dimension (y vals)
        xvals, yvals, ids = np.hsplit(np.array(dataSet), [1,2])
        weights = np.repeat(1.0, window) / window
        yvals = np.convolve(yvals.flatten(), weights)[window-1:-(window-1)]
        xvals = xvals[window-1:]
        ids = ids[window-1:]

        dataSet = np.hstack((xvals, yvals.reshape(len(xvals),1), ids)).tolist()
        return dataSet

    def mode(self, x):
        # A little hack since the related SciPy function returns unnecessary data
        from scipy import stats
        return stats.mode(x)[0][0][0]
        
    def first(self, x):
        return x[0][0]
        
    def last(self, x):
        return x[-1][0]
    
    def lq(self, x):
        # The lower quartile/25th percentile
        from scipy import stats
        return stats.scoreatpercentile(x, 25)[0]
        
    def uq(self, x):
        # The upper quartile/75th percentile
        from scipy import stats
        return stats.scoreatpercentile(x, 75)[0]
    
    def binStatistic(self, dataSet, groupBy, func):
        # Computed the indicated statistic (func) on each bin of data set
        
        # First trim the partial times on each end (unless told not to)
        if (not self._descInfo.has_key('trim')) or (self._descInfo['trim'] == 1):
            dataSet = self.trimData(dataSet, groupBy)
            
        # Group the data into bins
        [binSet, bins] = self.binData(dataSet, groupBy)
        
        numBins = len(bins)
        
        means = []
        objectids = []
        
        # Compute the means for each set of bins
        for b in binSet:
            xvals, yvals, ids = np.hsplit(np.array(b), [1,2])
            if (len(yvals) > 0):
                means.append(func(yvals)) 
                objectids.append(ids[-1].flatten())
            else:
                means.append(0)
                objectids.append([])

        log.info(objectids)
        # Tweak since numpy gets confused by sizes
        if numBins == 1:
            objs = np.array(objectids).reshape(numBins, 4)
        else:
            objs = np.array(objectids).reshape(numBins, 1)
        
        # Replace the old time (x) values with the bin value    
        dataSet = np.hstack((np.array(bins).reshape(numBins, 1), np.array(means).reshape(numBins, 1), objs)).tolist()
        return dataSet
    
    def binData(self, dataSet, groupBy):
        # Note: bins are defined by the maximum value of an item allowed in the bin
        
        minBinVal = int(dataSet[0][0] + groupBy)
        maxBinVal = int(dataSet[-1][0] + groupBy)
        
        # Round the time to the nearest groupBy interval
        minBinVal -= minBinVal % groupBy
        maxBinVal -= maxBinVal % groupBy
        
        # Find the number of bins and size per bin
        numBins = (maxBinVal - minBinVal) / groupBy + 1
        bins = range(minBinVal, maxBinVal + 1, groupBy)
        
        # Identify which x values should appear in each bin
        xvals, rest = np.hsplit(np.array(dataSet), [1])
        # Hack to change xvals from type object to int
        xvals = np.array(xvals.flatten().tolist())
        inds = np.digitize(xvals, bins)

        # Put each data element i nits appropriate bin
        binified = [ [] for x in bins ]        
        for binNum, val in zip(inds, dataSet):
            binified[binNum].append(val)
        
        # Return the bin-ified original data and the bin labels (values)    
        return [binified, bins]
        
    def trimData(self, dataSet, groupBy):
        # Remove the fractional (minute, hour, day) from the beginning and end of the dataset
        
        startTime = dataSet[0][0] + groupBy
        endTime = dataSet[-1][0]
        
        # Round the time to the nearest groupBy interval
        startTime -= (startTime % groupBy)
        endTime -= (endTime % groupBy)
        
        # Filter out the beginning
        dataArr = np.array(dataSet)
        dataArr = dataArr[dataArr[0:len(dataArr),0:1].flatten() > startTime]
        # If anything left, filter out the end
        if len(dataArr) > 0: dataArr = dataArr[dataArr[0:len(dataArr),0:1].flatten() < endTime]
        
        return dataArr.tolist()
        
        
    def epochToText(self, groupBy):
        if groupBy < 60: return str(groupBy) + ' Second(s)'
        elif groupBy < 3600: return str(groupBy / 60) + ' Minute(s)'
        elif groupBy < 86400: return str(groupBy / 3600) + ' Hour(s)'
        elif groupBy < 604800: return str(groupBy / 86400) + ' Day(s)'
        else: return str(groupBy / 604800) + ' Week(s)'

        
class ResultSet:    
    # Class to retrieve data from the database and add basic metadata
    
    
    def execute(self, queryInfo):
        # Execute the querystring, returning the results of the
        # query as a list
        #
        # Entering 'Motion' will do a predefined query to return
        # inspection objects
        #
        # Other query handling deferred for another day.

        insp = Inspection.objects.get(name=queryInfo['name'])
        query = dict(inspection = insp.id)
        
        if queryInfo.has_key('since'):
            query['capturetime__gt']= datetime.utcfromtimestamp(queryInfo['since'])
            
        rs = list(Result.objects(**query).order_by('-capturetime')[:queryInfo['limit']])
        
        # When performing some computations, require additional data
        if (len(rs) > 0) and (queryInfo.has_key('required')) and (len(rs) < queryInfo['required']):
        
            # If not, relax the capture time but only take the num records required
            del(query['capturetime__gt'])
            rs = list(Result.objects(**query).order_by('-capturetime')[:queryInfo['required']])
        
        outputVals = [[calendar.timegm(r.capturetime.timetuple()) + r.capturetime.time().microsecond / 1000000.0, r.numeric, r.inspection, r.frame, r.measurement, r.id] for r in rs[::-1]]
        
        
        if (len(outputVals) > 0):
            startTime = outputVals[0][0]
            endTime = outputVals[-1][0]
        else:
            startTime = 0
            endTime = 0
        
        #our timestamps are already in UTC, so we need to use a localtime conversion
        dataset = { 'startTime': startTime,
                    'endTime': endTime,
                    'timestamp': gmtime(),
                    'labels': {'dim0': 'Time', 'dim1': 'Motion', 'dim2': 'InspectionID', 'dim3': 'FrameID', 'dim4':'MeasurementID', 'dim5': 'ResultID'},
                    'data': outputVals}
                    
        return dataset
    
    
    def resultToResultSet(self, res):
        # Given a Result, format the Result like a one record ResultSet
        outputVals = [[calendar.timegm(res.capturetime.timetuple()), res.numeric, res.inspection, res.frame, res.measurement, res.id]]
        dataset = { 'startTime': outputVals[0][0],
                    'endTime': outputVals[0][0],
                    'timestamp': gmtime(),
                    'labels': {'dim0': 'Time', 'dim1': 'Motion', 'dim2': 'InspectionID', 'dim3': 'FrameID', 'dim4':'MeasurementID', 'dim5': 'ResultID'},
                    'data': outputVals}
        
        return dataset 
