
class MiniVCSError(Exception):
    """It will become a base of all errors"""


class NotARepository(MiniVCSError):
    """It will raised an error if the operation
    is attempted outside the repository"""
    

class RepositoryAlredyExist(MiniVCSError):
    """It will raised an error if the repository
    already exist"""
    
    
class EmptyCommit(MiniVCSError):
    """It will raised an error when commit is called
    with nothing staged"""
    
    
class EmptyMessageCommit(MiniVCSError):
    """It will raised when commit is perform without message"""
    
    
class UncommitedChanges(MiniVCSError):
    """It will raised an error if the commit is called
    with a blank massage"""
    

class BranchCommitNotFound(MiniVCSError):
    """It will raised an error when a branch or commit
    cannot be rasolved"""


class BranchAlreadyExist(MiniVCSError):
    """It will raised an error when creating branch is created
    with a name already in use"""
    
    
class DetachedHeadError(MiniVCSError):
    """It will raised an error when a branch only operation
    is attempted in detached HEAD"""
    
    
class MergeConflictError(MiniVCSError):
    """It will raised an error when the merge cannot be perfomed.
    
    it will carries the list of conflicted file path
    so the tests can asser which files is conflicted,
    not just showing something did conflicted."""
    
    def __init__(self, conflict):
        self.conflict = conflict
        super().__init__(f"Merge file conflict in: {", ".join(conflict)}")