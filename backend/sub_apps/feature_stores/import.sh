orchestrate env activate agentic-inc-3-v2

# create tools
orchestrate tools import -k python -f tools/StatsCalculator.py -r tools/requirements.txt 

# create knowledge
# orchestrate knowledge-bases import -f knowledge/sample_datasets.yaml

# create agents
orchestrate agents import -f agents/FeatAgent.yaml