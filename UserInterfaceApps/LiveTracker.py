class LiveTracker:
    def __init__(self):
        raise NotImplementedError('You must implement your own live tracker.')
    
    def initialize(self, frame):
        raise NotImplementedError('You must implement your own live tracker.')
    
    def get_keypoints(self, frame):
        raise NotImplementedError('You must implement your own live tracker.')
    
    def terminate(self):
        raise NotImplementedError('You must implement your own live tracker.')