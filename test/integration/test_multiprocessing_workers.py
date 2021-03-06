import time
import unittest


from botoflow import (
    MultiprocessingActivityExecutor, MultiprocessingWorkflowExecutor, workflow_starter,
    WorkflowWorker, ActivityWorker)
from multiprocessing_workflows import (
    NoActivitiesWorkflow, NoActivitiesFailureWorkflow, OneActivityWorkflow)
from various_activities import BunchOfActivities
from utils import SWFMixIn


class TestMultiprocessingWorkers(SWFMixIn, unittest.TestCase):

    def test_no_activities(self):

        worker = MultiprocessingWorkflowExecutor(WorkflowWorker(
            self.session, self.region, self.domain, self.task_list, NoActivitiesWorkflow))
        with workflow_starter(self.session, self.region, self.domain, self.task_list):
            instance = NoActivitiesWorkflow.execute(arg1="TestExecution")
            self.workflow_execution = instance.workflow_execution

        # start + stop should run the worker's Decider once
        worker.start()
        worker.stop()
        worker.join()
        time.sleep(2)

        hist = self.get_workflow_execution_history()
        self.assertEqual(len(hist), 5)
        self.assertEqual(hist[-1]['eventType'], 'WorkflowExecutionCompleted')
        self.assertEqual(self.serializer.loads(
            hist[-1]['workflowExecutionCompletedEventAttributes']['result']), 'TestExecution')

    def test_no_activities_failure(self):

        worker = MultiprocessingWorkflowExecutor(WorkflowWorker(
            self.session, self.region, self.domain, self.task_list, NoActivitiesFailureWorkflow))
        with workflow_starter(self.session, self.region, self.domain, self.task_list):
            instance = NoActivitiesFailureWorkflow.execute(arg1="TestExecution")
            self.workflow_execution = instance.workflow_execution

        worker.start()
        worker.stop()
        worker.join()
        time.sleep(1)

        hist = self.get_workflow_execution_history()
        self.assertEqual(len(hist), 5)
        self.assertEqual(hist[-1]['eventType'], 'WorkflowExecutionFailed')
        self.assertEqual(str(self.serializer.loads(
            hist[-1]['workflowExecutionFailedEventAttributes']['details'])[0]),
                         "ExecutionFailed")

    def test_one_activity(self):
        wf_worker = MultiprocessingWorkflowExecutor(WorkflowWorker(
            self.session, self.region, self.domain, self.task_list, OneActivityWorkflow))

        act_worker = MultiprocessingActivityExecutor(ActivityWorker(
            self.session, self.region, self.domain, self.task_list, BunchOfActivities()))

        with workflow_starter(self.session, self.region, self.domain, self.task_list):
            instance = OneActivityWorkflow.execute(arg1=1, arg2=2)
            self.workflow_execution = instance.workflow_execution

        wf_worker.start()
        act_worker.start()
        time.sleep(20)
        act_worker.stop()
        wf_worker.stop()
        act_worker.join()
        wf_worker.join()
        time.sleep(1)

        hist = self.get_workflow_execution_history()
        self.assertEqual(len(hist), 11)
        self.assertEqual(hist[-1]['eventType'], 'WorkflowExecutionCompleted')
        self.assertEqual(self.serializer.loads(
            hist[-1]['workflowExecutionCompletedEventAttributes']['result']), 3)

if __name__ == '__main__':
    unittest.main()
