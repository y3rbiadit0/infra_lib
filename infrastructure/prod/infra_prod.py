import os
from infra_lib import Environment, AWSInfraBuilder, AWSQueueConfig, AWSLambdaParameters

class ProdInfra(AWSInfraBuilder):
    def build(self):
        """
        Build the infrastructure for prod environment and net8 stack.
        """
        # Create secrets first
        self.secrets_util.create_secrets()
        
        ## Add more infra