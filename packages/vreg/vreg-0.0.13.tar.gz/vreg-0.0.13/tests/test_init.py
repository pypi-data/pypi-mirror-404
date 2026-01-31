import numpy as np
import vreg



def test_3d():

    shape = (4,5,2)
    vals = np.zeros(shape)
    affine = np.eye(4)
    vol = vreg.Volume3D(vals, affine)
    assert vol.shape == shape


def test_nd():

    shape = (4,5,2,3)
    vals = np.zeros(shape)
    affine = np.eye(4)
    vol = vreg.Volume3D(vals, affine)
    assert vol.shape == shape


def test_coords():

    shape = (4,5,2,3,9)
    vals = np.zeros(shape)
    affine = np.eye(4)

    # Default coordinates
    vol = vreg.Volume3D(vals, affine)
    assert vol.coords[0][-1,-1] == 2
    assert vol.coords[1][-1,-1] == 8

    # Well-formatted coordinates - same type
    coords = [np.zeros((3,9)), np.ones((3,9))]
    vol = vreg.Volume3D(vals, affine, coords)
    assert vol.coords[0][-1,-1] == 0
    assert vol.coords[1][-1,-1] == 1

    # Well-formatted coordinates - mixed type
    coords = [np.full((3,9), 'A'), np.ones((3,9))]
    vol = vreg.Volume3D(vals, affine, coords)
    assert vol.coords[0][-1,-1] == 'A'
    assert vol.coords[1][-1,-1] == 1

    # Ill-formatted coordinates (single coordinate, needs two)
    coords = [np.zeros((3,9))]
    try:
        vol = vreg.Volume3D(vals, affine, coords)
    except:
        assert True
    else:
        assert False

    # Ill-formatted coordinates (scalar)
    coords = np.zeros((3,9))
    try:
        vol = vreg.Volume3D(vals, affine, coords)
    except:
        assert True
    else:
        assert False

    # Ill-formatted coordinates (one scalar)
    coords = ['A', np.ones((3,9))]
    try:
        vol = vreg.Volume3D(vals, affine, coords)
    except:
        assert True
    else:
        assert False

    # Ill-formatted coordinates (wrong dimensions)
    coords = [np.full((2,9), 'A'), np.ones((3,9))]
    try:
        vol = vreg.Volume3D(vals, affine, coords)
    except:
        assert True
    else:
        assert False


def test_copy():
    shape = (4,5,2,3,9)
    vals = np.zeros(shape)
    affine = np.eye(4)  
    coords = [np.full((3,9), 'A'), np.ones((3,9))]
    dims = ['Name', 'Pos']
    vol = vreg.Volume3D(vals, affine, coords, dims)  
    vol_copy = vol.copy()
    vol_copy.coords[0] = np.full((3,9), 'B')
    assert vol.coords[0][-1,-1] == 'A'
    assert vol_copy.coords[0][-1,-1] == 'B'


def test_separate():

    # Build test volume
    shape = (4,5,2,3,9)
    vals = np.zeros(shape)
    affine = np.eye(4)  
    coords = [np.full((3,9), 'A'), np.ones((3,9))]
    coords[0][1,:] = 'B'
    coords[0][2,:] = 'C'
    dims = ['Name', 'Pos']
    vol = vreg.Volume3D(vals, affine, coords, dims) 

    # Separate along 1 axis
    vols_sep = vol.separate(axis=3)    
    assert vols_sep.shape == (3,)
    assert vols_sep[0].shape == (4,5,2,1,9)
    assert vols_sep[0].coords[0][0,8] == 'A'
    assert vols_sep[1].coords[0][0,8] == 'B'
    assert vols_sep[2].coords[0][0,8] == 'C'

    # Separate along all axes
    vols_sep = vol.separate()  
    assert vols_sep.shape == (3,9)
    assert vols_sep[0,8].shape == (4,5,2,1,1)
    assert vols_sep[0,8].coords[0][0,0] == 'A'
    assert vols_sep[1,8].coords[0][0,0] == 'B'
    assert vols_sep[2,8].coords[0][0,0] == 'C'


if __name__ == '__main__':

    test_3d()
    test_nd()
    test_coords()
    test_copy()
    test_separate()

    print('All init tests passed!!!')