# PRT582-Software-Engineering-Assessment-2---Mini-Control-System---Jordan-Then-Ryan-S405349

This is the mini version control system

## Features:
- "__init__": to create new repository
- "commit": snapshooting the tracked files with a message
- "checkout": restoring a barch or commit
- "branching": it creaters, switch, list, and delete branches
- "merge": it have fast-forward and three-way merge, with file conflict detection
- "log": it will commit history reversal

## The project layout
```
MiniControlSystem/
    repository.py
    branch.py
    merge.py
    history.py
    exceptions.py
Testing/                # pytest (46 Test with 98% coverage)
demo.py                 # scripted demo testing
'''

## Setup
''' bash
pip install -r requirements.txt
'''

## Full test suite run
'''bash
python -m pytest Testing/ -v
'''

## Running test with coverage
'''bash
python -m coverage run --source=MiniControlSystem -m pytest Testing/
python -m coverage report -m
python -m coverage html -d htmlcov
'''

## Running demo testing
'''bash 
python demo_testing.py
'''