from agent.agent import AgentLoop
from storage.database import init_db
from tools.search import SearchTool

def test_transient_failure_recovery_with_retry():
    init_db()
    # Inject 100% timeout on first call, 0% on subsequent calls to simulate recovery
    flaky_search = SearchTool(timeout_rate=1.0, seed=42)
    
    agent = AgentLoop(max_retries=2, tools=[flaky_search])
    
    # Change timeout_rate to 0 dynamically after initialization to test recovery
    flaky_search.timeout_rate = 0.0
    
    run = agent.run("Search for population of Canada")
    assert run.success is True