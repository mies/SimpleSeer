
from celery import Celery
from celery import task
from celery.exceptions import RetryTaskError
from celery.contrib import rdb
from celery.result import ResultSet

from bson import ObjectId
from gridfs import GridFS

from .util import ensure_plugins, jsonencode

from .realtime import ChannelManager
from . import models as M
from .Session import Session

from celery.utils import log
log = log.get_task_logger(__name__)
import logging

from . import celeryconfig
celery = Celery()
celery.config_from_object(celeryconfig)
            
from collections import defaultdict
            
ensure_plugins()

class InspectionLogHandler(logging.Handler):

    def __init__(self):
        super(InspectionLogHandler, self).__init__()
        
    def emit(self, msg):
        import ipdb;ipdb.set_trace()
        from .realtime import ChannelManager
        
        insp = self._getInspectionId(msg.msg)
        if insp:
            fra = self._getFrame(msg.msg)
            if fra:
                # This should be doing an update of the feature history log
                pass
                
    def _getInspectionId(self, msg):
        # Assume the first 24 digits is inspection id
        potentialId = msg[:24]
        if ObjectId.is_valid(potentialId):
            insp = M.Inspection.objects(id=potentialId)
            if insp:
                return insp[0].id
        
        return None
        
    def _getFrame(self, msg):
        # Assume the first 24 digits is inspection id
        potentialId = msg[25:49]
        if ObjectId.is_valid(potentialId):
            fra = M.Frame.objects(id=potentialId)
            if fra:
                return fra[0].id
        
        return None
        
            

class Foreman():
# Manages a lot of worker-related tasks
# This is a borg (speed worker status, plugin checks)

    _useWorkers = False
    _initialized = False
    _inspectionLog = None
    
    __sharedState = {}
    
    def __init__(self):
        from .realtime import PubSubHandler
            
        self.__dict__ = self.__sharedState
            
        if not self._initialized:
            self._useWorkers = self.workerRunning()
            self._initialized = True
            ensure_plugins()
            
            log.addHandler(PubSubHandler())
            log.addHandler(InspectionLogHandler())
            log.setLevel(20) # INFO 

    def workerRunning(self):
        i = celery.control.inspect()
        if i.active_queues() is not None:
            return True
        else:
            return False

    def process_inspections(self, frame, inspections=None):
        inspKwargs = {'camera': frame.camera, 'parent__exists': False}
        if inspections:
            inspKwargs['id__in'] = inspections
        
        filteredInsps = M.Inspection.objects(inspKwargs)
        
        if self._useWorkers:
            return self.worker_inspection_iterator(frame, filteredInsps)    
        else:
            return self.serial_inspection_iterator(frame, filteredInsps)

    def process_measurements(self, frame, measurements=None):
        measKwargs = {}
        
        if frame.features:        
            # only measurements for which there is a matching feature...
            # exact format of feature object depends on whether it came from worker or serial
            if '_data' in frame.features[0]:
                insps = [ feat.inspection for feat in frame.features ]
            else:
                insps = [ feat.__dict__['inspection'] for feat in frame.features ]
            measKwargs['inspection__in'] = insps
        else:
            # No features, but limit measurements to those associated with features on this camera
            measKwargs['inspection__in'] = [ insp.id for insp in M.Inspection.objects(camera=frame.camera) ]
            
        if measurements:
            measKwargs['id__in'] = measurements
        
        filteredMeass = M.Measurement.objects(**measKwargs)
        
        if self._useWorkers:
            return self.worker_measurement_iterator(frame, filteredMeass)
        else:
            return self.serial_measurement_iterator(frame, filteredMeass)

    def worker_inspection_iterator(self, frame, insps):
        sched = self.worker_x_schedule(frame, insps, self.inspection_execute)
        return self.worker_x_iterator(sched)
        
    def worker_measurement_iterator(self, frame, meass):
        sched = self.worker_x_schedule(frame, meass, self.measurement_execute)
        return self.worker_x_iterator(sched)
            
    def worker_x_schedule(self, frame, objs, fn):
        scheduled = ResultSet([])
        for o in objs:
            scheduled.add(fn.delay(frame.id, o.id))
        return scheduled
            
    def worker_x_iterator(self, scheduled):
        for output in scheduled:
            for out in output:
                yield out
        
    def serial_inspection_iterator(self, frame, insps):
        for i in insps:
            features = i.execute(frame)
            for feat in features:
                yield feat
                
    def serial_measurement_iterator(self, frame, meass):
        for m in meass:
            results = m.execute(frame)
            for res in results:
                yield res

    @task
    def inspection_execute(fid, iid):
        try:
            log.warn('{} {} Inspecting'.format(iid, fid))
            frame = M.Frame.objects.get(id=fid)
            inspection = M.Inspection.objects.get(id=iid)
            features = inspection.execute(frame)
            return features        
        except Exception as e:
            log.error(e)
            print e
            return []

    @task
    def measurement_execute(fid, mid):
        try:
            log.warn('Measuring {}'.format(mid))
            frame = M.Frame.objects.get(id=fid)
            measurement = M.Measurement.objects.get(id=mid)
            results = measurement.execute(frame)
            return results        
        except Exception as e:
            log.error(e)
            return []
