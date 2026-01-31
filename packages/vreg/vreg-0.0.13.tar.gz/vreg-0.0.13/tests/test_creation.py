import numpy as np
import vreg



def test_coords():

    shape = (4,5,2,3,9)
    vals = np.zeros(shape)
    affine = np.eye(4)

    # Well-formatted coordinates - mixed type
    X = np.full((3,9), 'A')
    Y = np.ones((3,9))
    vol = vreg.volume(vals, affine, [X, Y])
    assert vol.coords[0][-1,-1] == 'A'
    assert vol.coords[1][-1,-1] == 1

    # Well-formatted coordinates - tuple of arrays
    X = np.full(3, 'A')
    Y = np.ones(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][-1,-1] == 'A'
    assert vol.coords[1][-1,-1] == 1

    # Well-formatted coordinates - tuple of lists
    X = ['A'] * 3
    Y = [1] * 9
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][-1,-1] == 'A'
    assert vol.coords[1][-1,-1] == 1

    # Well-formatted coordinates - tuple of lists
    X = ['A', 'B', 'C']
    Y = np.arange(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][-1,-1] == 'C'
    assert vol.coords[1][-1,-1] == 8

    # Well-formatted coordinates - objectarray
    X = np.array(['A', 'B', 'C'], dtype=object)
    Y =  np.arange(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][-1,-1] == 'C'
    assert vol.coords[1][-1,-1] == 8

    # Well-formatted coordinates - object array from mixed type list
    X = np.array(['A', ['A','B'], ['A','B','C']], dtype=object)
    Y = np.arange(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][-1,-1] == ['A', 'B', 'C']
    assert vol.coords[1][-1,-1] == 8

    # Well-formatted coordinates - object array from list of lists
    X = np.array([['A'], ['A','B'], ['A','B','C']], dtype=object)
    Y = np.arange(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][-1,-1] == ['A', 'B', 'C']
    assert vol.coords[1][-1,-1] == 8

    # Well-formatted coordinates - list of lists
    X = [['A'], ['A','B'], ['A','B','C']]
    Y = np.arange(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][-1,-1] == ['A', 'B', 'C']
    assert vol.coords[1][-1,-1] == 8

    # Well-formatted coordinates - list of lists
    X = [['A'], ['A','B'], ['A','B','C']]
    Y = ['X'] * 9
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][-1,-1] == ['A', 'B', 'C']
    assert vol.coords[1][-1,-1] == 'X'

    # Well-formatted coordinates - mixed type list
    X = ['A', ['A','B'], ['A','B','C']]
    Y = np.arange(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][0,-1] == 'A'
    assert vol.coords[0][-1,-1] == ['A', 'B', 'C']
    assert vol.coords[1][-1,-1] == 8

    # Well-formatted coordinates - mixed type list
    X = ['A', ['A','B'], 2]
    Y = np.arange(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][0,-1] == 'A'
    assert vol.coords[0][-1,-1] == 2
    assert vol.coords[1][-1,-1] == 8

    # Well-formatted coordinates - mixed type array
    X = np.array(['A', True, 2], dtype=object)
    Y = np.arange(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][0,-1] == 'A'
    assert vol.coords[0][1,-1] == True
    assert vol.coords[0][2,-1] == 2
    assert vol.coords[1][-1,-1] == 8

    # Well-formatted coordinates - mixed type list
    X = ['A', True, 2]
    Y = np.arange(9)
    vol = vreg.volume(vals, affine, (X, Y))
    assert vol.coords[0][0,-1] == 'A'
    assert vol.coords[0][1,-1] == True
    assert vol.coords[0][2,-1] == 2
    assert vol.coords[1][-1,-1] == 8



if __name__ == '__main__':

    test_coords()

    print('All creation tests passed!!!')