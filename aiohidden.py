# Example originally based on Python documentation example of using multiprocessing queues
#
# Developed by Jacob Everist, 2019

import asyncio
import multiprocessing

async def run_async_job(sendQueue, recvQueue):
    """
    Asynchronous worker that receives tasks and returns results on queues

    :param sendQueue: Async queue of tasks to async worker
    :param recvQueue: Async queue of results from async worker
    """
    while True:
        # receive task
        next_task = await sendQueue.get()

        # execute task
        answer = next_task()

        # indicate task done
        sendQueue.task_done()

        # send result back
        await recvQueue.put(answer)


async def bridge_queues(taskMPQueue, resultMPQueue, sendQueue, recvQueue):
    """
    Pass through data between synchronous multiprocessing queues and asyncio queues

    :param taskMPQueue: Tasks to be executed, from synchronous main()
    :param resultMPQueue:  Results to be passed back to synchronous main()
    :param sendQueue: Async queue of tasks to async worker
    :param recvQueue: Async queue of results from async worker
    """

    loop = asyncio.get_event_loop()

    while True:

        # get task off of queue
        task_future = loop.run_in_executor(None, taskMPQueue.get)
        await task_future
        next_task = task_future.result()

        # put to async code
        await sendQueue.put(next_task)

        # receive answer from asynchronous code
        answer = await recvQueue.get()
        recvQueue.task_done()

        # indicate work complete on task queue
        done_future = loop.run_in_executor(None, taskMPQueue.task_done)
        await done_future

        # push result on result queue
        result_future = loop.run_in_executor(None, resultMPQueue.put, answer)
        await result_future


class AsyncBrokerProcess(multiprocessing.Process):
    """
    Broker object to hide and use asynchronous code from a standard synchronous Python environment
    Runs and hides asyncio code within new Process
    """

    def __init__(self, taskMPQueue, resultMPQueue):
        """
        Initialize broker with synchronous queues for passing tasks and receiving results

        :param taskMPQueue: Tasks to be executed, from synchronous main()
        :param resultMPQueue:  Results to be passed back to synchronous main()
        """
        multiprocessing.Process.__init__(self)
        self.taskMPQueue = taskMPQueue
        self.resultMPQueue = resultMPQueue

    def run(self):
        """
        Initialize and start asyncio environment in this new process
        """

        try:
            loop = asyncio.get_event_loop()

            sendQueue = asyncio.Queue(loop=loop)
            recvQueue = asyncio.Queue(loop=loop)

            # run synchronous bridging between queues
            fut = asyncio.ensure_future(bridge_queues(self.taskMPQueue, self.resultMPQueue, sendQueue, recvQueue))

            # run asynchronous job worker
            run_fut = asyncio.ensure_future(run_async_job(sendQueue, recvQueue))

            loop.run_until_complete(asyncio.wait([fut,run_fut]))

        except asyncio.CancelledError:
            print("Asynchronous code cancelled")


class SomeApplication():


    def __init__(self):

        # Establish communication queues
        self.taskMPQueue = multiprocessing.JoinableQueue()
        self.resultMPQueue = multiprocessing.Queue()

        # Create and Start Async Broker
        self.process = AsyncBrokerProcess(self.taskMPQueue, self.resultMPQueue)
        self.process.start()

    def __del__(self):
        self.terminate()

    def addTask(self, task):
        self.taskMPQueue.put(task)

    def waitUntilAllTasksDone(self):
        self.taskMPQueue.join()

    def getResult(self):
        return self.resultMPQueue.get()

    def terminate(self):
        self.process.terminate()

