import pandas as pd

class HumanEvalDataset:

  def __init__(self):
    self.df = pd.read_parquet("hf://datasets/openai/openai_humaneval/openai_humaneval/test-00000-of-00001.parquet")
    self.df['task_id'] = self.df['task_id'].str.split('/').str[1].astype(int)
    self.df = self.df.set_index('task_id')

  def getSingleProblem(self, task_id=0):
    """Get a complete problem by task_id"""
    return self.df.loc[task_id].to_dict()

  def getPrompt(self, task_id):
    """Get the prompt for a specific task"""
    return self.df.loc[task_id, 'prompt']

  def getTest(self, task_id):
    """Get the test cases for a specific task"""
    return self.df.loc[task_id, 'test']

  def getCanonicalSolution(self, task_id):
    """Get the canonical solution for a specific task"""
    return self.df.loc[task_id, 'canonical_solution']

  def getEntryPoint(self, task_id):
    """Get the entry point function name for a specific task"""
    return self.df.loc[task_id, 'entry_point']

  def getAllProblems(self):
    """Get all problems as a list of dictionaries"""
    return self.df.reset_index().to_dict('records')

  def getRandomProblem(self):
    """Get a random problem"""
    return self.df.sample(n=1).iloc[0].to_dict()

  def getTotalCount(self):
    """Get total number of problems"""
    return len(self.df)

  def getProblemsByRange(self, start, end):
    """Get problems in a specific range of task_ids"""
    return self.df.loc[start:end].reset_index().to_dict('records')


