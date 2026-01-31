
def fn(data):
    import numpy as n

    
    matrix = n.zeros((8,8), dtype=int)

    #data = get_object_or_404(AtlasDiffSubcells, obs=expname).order_by('region')

    for cell in data:
        x = cell.region % 8
        y = int (cell.region / 8)
        matrix[[x][y]] = cell.ndet

    print(matrix)


import random

class EmptyClass:
    pass

data = EmptyClass()

ndet = []
region = []

for i in range(64):
    region
    data.region = 
    n = random.randint(0,2000)
    randomlist.append(n)

fn(randomlist)
