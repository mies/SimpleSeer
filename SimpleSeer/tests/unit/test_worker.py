import unittest
import sys
from SeerCloud.testdata import TestData
from SimpleSeer.worker import Foreman
from SimpleSeer.Session import Session
from SimpleSeer.states import Core

import logging
log = logging.getLogger(__name__)

class Test(unittest.TestCase):
    
    testData = None
    fm = None
    core = Core(Session('.'))
    
    def setUp(self):
        self.testData = TestData()
        self.testData.makeMeasurements(1)
        self.testData.makeFrames(5)
        self.fm = Foreman()
        
    def tearDown(self):
        self.testData.remove()
        
        del self.testData    
        del self.fm

    def testWorker(self):
        
        self.fm._useWorkers = self.fm.workerRunning()
        self.assertTrue(self.fm._useWorkers, 'Worker is not detected.  Is it running?')
        
        if self.fm._useWorkers:
            # Construct features/results using worker
            log.info('Running worker tests')
            for idx, f in enumerate(M.Frame.objects(id__in=self.testData.addedFrames)):
                log.info('Processing frame {} of {}'.format(idx + 1, len(self.testData.addedFrames)))
                f.results = []
                self.core.process(f)
                f.save()
            
            # Each frame should have one feature
            # That feature should have a featuredata point named testdata
            for f in M.Frame.objects(id__in=self.testData.addedFrames):
                print "("* 10
                print len(f.features)
                self.assertEqual(len(f.features), 1, 'Expected exactly one feature')
                if len(f.features):
                    self.assertIn('testdata', f.features[0].featuredata, 'Expected feature data not found on frame')

            # Each frame should have one result
            # And that result should have a non-None numeric value
            for f in M.Frame.objects(id__in=self.testData.addedFrames):
                self.assertEqual(len(f.results), 1, 'Expected exactly one result')
                if len(f.results):
                    self.assertIsNot(f.results[0].numeric, None, 'Result should not be None')
                    self.assertEqual(f.features[0].featuredata['testdata'], f.results[0].numeric, 'Result does not match corresponding feature data')
        else:
             log.warn('Worker is not running.  Tests skipped.')

    def testSerial(self):
        
        # Construct features/results using serial
        self.fm._useWorkers = False
        co = Core(Session('.'))
        log.info('Running serial tests')
        for idx, f in enumerate(M.Frame.objects(id__in=self.testData.addedFrames)):
            log.info('Processing frame {} of {}'.format(idx + 1, len(self.testData.addedFrames)))
            f.results = []
            self.core.process(f)
            f.save()
        
        # Each frame should have one feature
        # That feature should have a featuredata point named testdata
        for f in M.Frame.objects(id__in=self.testData.addedFrames):
            self.assertEqual(len(f.features), 1, 'Expected exactly one feature')
            if len(f.features):
                self.assertIn('testdata', f.features[0].featuredata, 'Expected feature data not found on frame')

        # Each frame should have one result
        # And that result should have a non-None numeric value
        for f in M.Frame.objects(id__in=self.testData.addedFrames):
            self.assertEqual(len(f.results), 1, 'Expected exactly one result')
            if len(f.results):
                self.assertIsNot(f.results[0].numeric, None, 'Result should not be None')
                self.assertEqual(f.features[0].featuredata['testdata'], f.results[0].numeric, 'Result does not match corresponding feature data')