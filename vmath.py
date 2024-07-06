import math


def cDist(a,b):
    x1=a.x
    y1=a.y
    
    x2=b.x
    y2=b.y
    
    
    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return dist