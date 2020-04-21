import numpy as np

####
# Global function and object definitions for common array manipulation tasks

# Rotate clockwise 90 deg
rotateCW90matrix = np.array([[0.0, -1.0], [1.0, 0.0]])
def rotCW90(a):
    return np.dot(a, rotateCW90matrix)

# Rotate clockwise 180 deg
rotateCW180matrix = np.array([[-1.0,0.0],[0.0,-1.0]])
def rotCW180(a):
    return np.dot(a, rotateCW180matrix)

# Rotate clockwise 270 deg
rotateCW270matrix = np.array([[0.0,1.0],[-1.0,0.0]])
def rotCW270(a):
    return np.dot(a, rotateCW270matrix)

# Returns the length of the vector
def eDist(a):
    # See this link for theory behind this https://stackoverflow.com/questions/1401712/how-can-the-euclidean-distance-be-calculated-with-numpy
    return np.linalg.norm(a)

# Returns a vector with Euclidean distance of 1 but the same direction as the input (provided the vector actually has direction, i.e. is not zero distance)
def unity(a):
    initLength = eDist(a)
    if initLength > 0:
        return a / initLength
    else:
        return a
