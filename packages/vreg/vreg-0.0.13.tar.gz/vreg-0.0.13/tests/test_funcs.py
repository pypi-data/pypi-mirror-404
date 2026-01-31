import vreg
import numpy as np

def test_flip_chirality():
    arr = np.arange(2 * 3 * 4).reshape((2, 3, 4))
    vol = vreg.volume(arr, orient='coronal')
    assert not vol.is_right_handed
    vol.flip_chirality(2)
    assert vol.is_right_handed
    vol.flip_chirality(1)
    assert not vol.is_right_handed
    vol.flip_chirality(0)
    assert vol.is_right_handed


if __name__=='__main__':
    test_flip_chirality()
    print('funcs tests passed!')