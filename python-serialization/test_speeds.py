""" This script reports the time to serialize/deserialize a small object
from  a bunch of different python serialization libraries.

The data being serialized represents a single 'Tweet' from twitter, and has
just 4 fields: text, userId, location and timestamp.
"""

import random
import time
import numpy
import gc
import os
import functools

import json

import cPickle
import pickle

import msgpack

from thrift.transport.TTransport import TMemoryBuffer
from thrift.protocol.TBinaryProtocol import TBinaryProtocolAccelerated, TBinaryProtocol
"""
try:
    from thriftobj.Tweet.ttypes import Tweet as ThriftTweet
except ImportError:
    print "generating thrift objects"
    os.system("thrift --gen py Tweet.thrift")
    os.system("mv gen-py thriftobj")
    from thriftobj.Tweet.ttypes import Tweet as ThriftTweet
"""
class Tweet(object):
    def __init__(self, text=None, userId=None, timestamp=None, location=None, children = None):
        self.text = text
        self.userId = userId
        self.timestamp = timestamp
        self.location = location
        self.children = children

    def serialize(self, obj):
       return obj.__dict__ 

    def toJSON(self):
        return json.dumps(self, default=self.serialize)

    @classmethod
    def fromJSON(cls, data):
        return cls(**json.loads(data))

    def toMessagePack(self):
        return msgpack.packb(self, default=self.serialize)

    @classmethod
    def fromMessagePack(cls, data):
        return cls(**msgpack.unpackb(data))

"""
def thriftDumps(tweet, ProtocolClass=TBinaryProtocolAccelerated):
    buf = TMemoryBuffer()
    protocol = ProtocolClass(buf)
    tweet.write(protocol)
    return buf.getvalue()

def thriftLoads(data, ProtocolClass=TBinaryProtocolAccelerated):
    ret = ThriftTweet()
    buf = TMemoryBuffer(data)
    protocol = ProtocolClass(buf)
    ret.read(protocol)
    return ret
"""
alphabet = map(chr, range(ord('a'), ord('z') + 1))
def randomString(length):
    return ''.join(random.choice(alphabet) for _ in xrange(length))

def get_random_tweet(x):
    rec_max = (x/2) + 1
    rec_limit = int(0.6*rec_max)
    i = random.randint(0, rec_max)
    return Tweet(randomString(random.randint(10, 1100)),
                    randomString(random.randint(5, 20)),
                    int(time.time()),
                    randomString(random.randint(10, 30)),
                    get_random_tweet(rec_max) if i > rec_limit else None 
                    )

def get_random_tweet_list():
    data = [Tweet(randomString(random.randint(10, 1100)),
                    randomString(random.randint(5, 20)),
                    int(time.time()),
                    randomString(random.randint(10, 30)),
                    get_random_tweet(x)
                    )
                for x in xrange(100)]
    return data

def runTests():
    print "generating data"
    data = [Tweet(randomString(random.randint(10, 1100000)),
                    randomString(random.randint(5, 20)),
                    int(time.time()),
                    randomString(random.randint(10, 30)),
                    get_random_tweet(x))
                for x in xrange(1000)]

    ## thriftdata = [ThriftTweet(d.text, d.userId, d.timestamp, d.location) for d in data]

    minSize = numpy.average([len(d.text) + len(d.userId) + len(d.location) + 8 for d in data])
    print "generated data, size lower bound = ", minSize

    methods = {
               'Pickle' : (pickle.dumps, pickle.loads, data),
               'cPickle' : (cPickle.dumps, cPickle.loads, data),
               'cPickle' : (cPickle.dumps, cPickle.loads, data),
               'cPickle\n(Highest Protocol)' : (
                    functools.partial(cPickle.dumps, protocol=cPickle.HIGHEST_PROTOCOL),
                    cPickle.loads, data),
               'JSON' : (lambda d: d.toJSON(), Tweet.fromJSON, data),
               'MessagePack' : (lambda d: d.toMessagePack(),
                                Tweet.fromMessagePack, data),
      #         'Thrift' : (thriftDumps, thriftLoads, thriftdata),
               }

    output = []
    for method, (packer, unpacker, inputData) in methods.items():
        gc.collect()

        startPack = time.time()
        packed = [packer(d) for d in inputData]

        startUnpack = time.time()
        unpacked = [unpacker(d) for d in packed]

        unpackTime = time.time() - startUnpack
        packTime = startUnpack - startPack
        averageSize = numpy.average([len(d) for d in packed])

        output.append({'method' : method,
                       'packTime' : packTime,
                       'unpackTime' : unpackTime,
                       'packRate' : len(inputData)/packTime,
                       'unpackRate' : len(inputData)/unpackTime,
                       'averageSize' : averageSize})
        print "-" * 80
        print method
        print "packTime", packTime, "s - ", len(inputData)/packTime, "items/s"
        print "unpackTime", unpackTime, "s - ", len(inputData)/unpackTime, "items/s"
        print "size", averageSize
        print

    output.sort(key=lambda x: x['packRate'])
    open("speed_data.json", "wb").write(json.dumps(output))

if __name__ == "__main__":
    runTests()
