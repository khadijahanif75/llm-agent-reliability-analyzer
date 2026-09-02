from agent.agent import AgentLoop
from storage.database import init_db

def test_agent_loop_calculator_flow():
    init_db()
    agent = AgentLoop()
    run = agent.run("What is 345 multiplied by 72?", expected_tool="calculator")
    
    assert run.success is True
    assert "24840" in run.final_response
    assert run.total_steps >= 1

def test_agent_loop_max_steps_exceeded():
    init_db()
    # Set max_steps=0 to trigger trajectory overflow
    agent = AgentLoop(max_steps=0)
    run = agent.run("Search for population of Canada")
    
    assert run.success is False
    assert run.primary_failure_type.value == "MAX_STEPS_EXCEEDED"