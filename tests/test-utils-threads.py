# -*- coding: utf-8 -*-

from opinel.utils.threads import *

class TestOpinelUtilsThreads:

    def callback(self, q, params):
        while True:
            try:
                i = q.get()
            except:
                pass
            finally:
                q.task_done()


    def test_thread_work(self):
        targets = []
        for i in range(50):
            targets.append(i)
        thread_work(targets, self.callback, {}, 10)
        for i in range(5):
            targets.append(i)
        thread_work(targets, self.callback)


    def test_threaded_per_region(self):
        regions = [ 'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2' ]
        thread_work(regions, threaded_per_region, params = {'method': self.callback})
