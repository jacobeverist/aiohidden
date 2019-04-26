# Example originally based on Python documentation example of using multiprocessing queues
#
# Developed by Jacob Everist, 2019

from aiohidden import SomeApplication

class Task:

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __call__(self):
        #time.sleep(0.1)  # pretend to take time to do the work
        return '{self.a} * {self.b} = {product}'.format(
            self=self, product=self.a * self.b)

    def __str__(self):
        return '{self.a} * {self.b}'.format(self=self)

if __name__ == '__main__':

    app = SomeApplication()

    # CASE 1:
    # enqueue lots of jobs and wait for them to finish

    # Enqueue jobs
    num_jobs = 10
    for i in range(num_jobs):
        app.addTask(Task(i,i))

    # Wait for all of the tasks to finish
    app.waitUntilAllTasksDone()

    # Start printing results
    while num_jobs:
        print('CASE 1:', app.getResult())
        num_jobs -= 1

    # CASE 2:
    # Run jobs one at a time, waiting for the result back before starting the new one

    # send tasks and receive results one at a time
    count = 1
    while True:
        app.addTask(Task(count,count))
        print('CASE 2:', app.getResult())

        count += 1
        if count > 10:
            break

    app.terminate()