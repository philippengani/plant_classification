#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Axel Angel, copyright 2015, license GPLv3.

import sys
import caffe
import numpy as np
import lmdb
from StringIO import StringIO
import argparse
from collections import defaultdict
import PIL.Image

def flat_shape(x):
    "Returns x without singleton dimension, eg: (1,28,28) -> (28,28)"
    return x.reshape(filter(lambda s: s > 1, x.shape))

def getImage(datum):
    if datum.encoded:
        s = StringIO(datum.data)
        image = np.array(PIL.Image.open(s))
    else:
        image = caffe.io.datum_to_array(datum).astype(np.uint8)
    return image

def lmdb_reader(fpath):
    import lmdb
    lmdb_env = lmdb.open(fpath)
    lmdb_txn = lmdb_env.begin()
    lmdb_cursor = lmdb_txn.cursor()

    for key, value in lmdb_cursor:
        datum = caffe.proto.caffe_pb2.Datum()
        datum.ParseFromString(value)
        label = int(datum.label)
        image = getImage(datum)
        #image = image.reshape(datum.channels, datum.height, datum.width)
        yield (key, flat_shape(image), label)

    '''
    for key, value in lmdb_cursor:
        datum = caffe.proto.caffe_pb2.Datum()
        datum.ParseFromString(value)
        label = int(datum.label)
        print(label)
        #Getting data
        #print(datum.shape)
        #flat_x = np.fromstring(datum.data, dtype=np.uint8)
        #print(flat_x.shape)
        #image = caffe.io.datum_to_array(datum)
        #print(image)
        #x = flat_x.reshape(datum.channels, datum.height, datum.width)
        s = StringIO()
        s.write(datum.data)
        s.seek(0)
        image = np.array(PIL.Image.open(s)).reshape(datum.channels, datum.height, datum.width)
        print(image)
        yield (key, flat_shape(image), label)
    '''
def leveldb_reader(fpath):
    import leveldb
    db = leveldb.LevelDB(fpath)

    for key, value in db.RangeIter():
        datum = caffe.proto.caffe_pb2.Datum()
        datum.ParseFromString(value)
        label = int(datum.label)
        image = caffe.io.datum_to_array(datum).astype(np.uint8)
        yield (key, flat_shape(image), label)

def npz_reader(fpath):
    npz = np.load(fpath)

    xs = npz['arr_0']
    ls = npz['arr_1']

    for i, (x, l) in enumerate(np.array([ xs, ls ]).T):
        yield (i, x, l)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--proto', type=str, required=True)
    parser.add_argument('--model', type=str, required=True)
    parser.add_argument('--mean', type=str, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--lmdb', type=str, default=None)
    group.add_argument('--leveldb', type=str, default=None)
    group.add_argument('--npz', type=str, default=None)
    args = parser.parse_args()

    # Extract mean from the mean image file
    mean_blobproto_new = caffe.proto.caffe_pb2.BlobProto()
    f = open(args.mean, 'rb')
    mean_blobproto_new.ParseFromString(f.read())
    mean_image = caffe.io.blobproto_to_array(mean_blobproto_new)
    f.close()

    count = 0
    correct = 0
    matrix = defaultdict(int)  # (real,pred) -> int
    labels_set = set()

    # CNN reconstruction and loading the trained weights
    net = caffe.Net(args.proto, args.model, caffe.TEST)
    caffe.set_mode_gpu()
    print "args", vars(args)
    if args.lmdb != None:
        reader = lmdb_reader(args.lmdb)
    if args.leveldb != None:
        reader = leveldb_reader(args.leveldb)
    if args.npz != None:
        reader = npz_reader(args.npz)

    for i, image, label in reader:
        print(image.shape)
        input_dims = net.blobs['data'].shape
        #compute the mean
        image = image.transpose(2,0,1)
        print(image)
        print(mean_image)
        image = image - mean_image
        print(image.shape)
        print("DIMS")
        print(mean_image.shape)
        batch_size, num_channels, input_height, input_width = input_dims

        caffe_in = np.zeros(input_dims, dtype=np.float32)
        #print(image[:,:,0:227,0:227].reshape(3,227,227))

        caffe_in[0] = image[:,:,0:227,0:227].reshape(3,227,227)
        image = image[:,:,0:227,0:227].reshape(3,227,227)
        print(image.shape)
        print(caffe_in[0])

        out = net.forward_all(data=image)
        prob = out['prob'][0]
        plabel = int(out['prob'][0].argmax(axis=0))

        count += 1
        iscorrect = label == plabel
        correct += (1 if iscorrect else 0)
        matrix[(label, plabel)] += 1
        labels_set.update([label, plabel])

        if not iscorrect:
            print("\rError: i=%s, expected %i but predicted %i" \
                    % (i, label, plabel))

        sys.stdout.write("\rAccuracy: %.1f%%" % (100.*correct/count))
        sys.stdout.flush()

    print(", %i/%i corrects" % (correct, count))

    print ""
    print "Confusion matrix:"
    print "(r , p) | count"
    for l in labels_set:
        for pl in labels_set:
            print "(%i , %i) | %i" % (l, pl, matrix[(l,pl)])