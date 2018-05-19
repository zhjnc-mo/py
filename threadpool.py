import Queue

class ThreadPool(object):
    def __init__(self, workerNums=3, timeout=0.1):
        self._workerNums = workerNums
        self._timeout = timeout
        self._workQueue = Queue.Queue()
        self._resultQueue = Queue.Queue()
        self.workers = []
        self.dismissedWorkers = []
        self._createWorkers(self._workerNums)
        
    def _createWorkers(self, workerNums):
        """Add num_workers worker threads to the pool."""
        for i in range(1, workerNums):
            worker = DownloadThread()
            self.workers.append(worker)

    def _dismissWorkers(self, workerNums, _join=False):
        dismissList = []
        for i in range(min(workerNums, len(slef.workers))):
            worker = self.workers.pop()
            worker.dismiss()
            dismissList.append(worker)

        if _join:
            for worker in dismissList:
                worker.join()
        else:
            self.dismissedWorkers.extend(dismissList)

    def _joinAllDismissedWorkers(self):
        for worker in self.dismissedWorkers:
            worker.join()
        self.dismissedWorkers = []

    def addJob(self, callable, *args, **kwds):
        self._workQueue.put((callable, args, kwds))

    def getResult(self, block=False, timeout=0.1):
        try:
            item = self._resultQueue.get(block, timeout)
            return item
        except Queue.Empty, e:
            return None
        except:
            raise

    def waitForComplete(self, timeout=0.1):
        while True:
            workerNums = self._workQueue.qsize()
            runWorkers = len(self.workers)

            if workerNums == 0:
                time.sleep(timeout) # waiting for thread to do job
                