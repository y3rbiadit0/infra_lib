import os
from infra_lib import Environment, AWSInfraBuilder, AWSQueueConfig, AWSLambdaParameters

class StageInfra(AWSInfraBuilder):
    def build(self):
        """
        Build the infrastructure for stage environment and net8 stack.
        """
        # Create secrets first
        self.secrets_util.create_secrets()
        
        ## Add more infra