import h5py
import glob
import re

for iter_file in glob.glob("/home/ngani/Desktop/SYS866/Plant Classification/Experiment 1/code/alexnet/color-20-80/train_from_scratch/hdf5_dumps/*"):
    print(iter_file)
    snapshot_id = int(re.findall("iter_(\d*).h5", iter_file)[0])
    print snapshot_id

    d = h5py.File(iter_file, 'r')
    print(d)
    print(d.keys())
    # Parse Results in digestible result_map
    result_map = {}
    for _key in d.keys():
        _type = _key.split("__")[0]
        print(_type)
        #_order = int(_key.split("__")[1])
