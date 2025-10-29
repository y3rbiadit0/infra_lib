from infra_lib.cli.runner_cli.run_cli import InfraOp


def assert_op_equal(op1: InfraOp, op2: InfraOp):
	assert isinstance(op1, InfraOp)
	assert isinstance(op2, InfraOp)

	assert op1.name == op2.name
	assert op1.description == op2.description
	assert op1.handler == op2.handler
	assert op1.target_envs == op2.target_envs
	assert op1.depends_on == op2.depends_on

	assert op1.target_envs is not op2.target_envs
	assert op1.depends_on is not op2.depends_on
