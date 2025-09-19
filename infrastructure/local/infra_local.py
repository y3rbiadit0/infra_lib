import os
from infra_lib import Environment, AWSInfraBuilder, AWSQueueConfig, AWSLambdaParameters

class LocalInfra(AWSInfraBuilder):
    def build(self):
        """
        Build the infrastructure for local environment and net8 stack.
        """
        # Create secrets first
        self.secrets_util.create_secrets()
        
        ## Add more infra