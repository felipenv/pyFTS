import numpy as np
from pyFTS.common import FuzzySet,FLR
from pyFTS import fts

class ExponentialyWeightedFLRG(object):
    def __init__(self, LHS, c):
        self.LHS = LHS
        self.RHS = []
        self.count = 0.0
        self.c = c

    def append(self, c):
        self.RHS.append(c)
        self.count = self.count + 1.0

    def weights(self):
        wei = [self.c ** k for k in np.arange(0.0, self.count, 1.0)]
        tot = sum(wei)
        return np.array([k / tot for k in wei])

    def __str__(self):
        tmp = self.LHS.name + " -> "
        tmp2 = ""
        cc = 0
        wei = [self.c ** k for k in np.arange(0.0, self.count, 1.0)]
        tot = sum(wei)
        for c in sorted(self.RHS, key=lambda s: s.name):
            if len(tmp2) > 0:
                tmp2 = tmp2 + ","
            tmp2 = tmp2 + c.name + "(" + str(wei[cc] / tot) + ")"
            cc = cc + 1
        return tmp + tmp2

    def __len__(self):
        return len(self.RHS)


class ExponentialyWeightedFTS(fts.FTS):
    def __init__(self, order, **kwargs):
        super(ExponentialyWeightedFTS, self).__init__(1, "EWFTS")
        self.name = "Exponentialy Weighted FTS"
        self.detail = "Sadaei"
        self.c = 1

    def generateFLRG(self, flrs, c):
        flrgs = {}
        for flr in flrs:
            if flr.LHS.name in flrgs:
                flrgs[flr.LHS.name].append(flr.RHS)
            else:
                flrgs[flr.LHS.name] = ExponentialyWeightedFLRG(flr.LHS, c);
                flrgs[flr.LHS.name].append(flr.RHS)
        return (flrgs)

    def train(self, data, sets,order=1,parameters=2):
        self.c = parameters
        self.sets = sets
        ndata = self.doTransformations(data)
        tmpdata = FuzzySet.fuzzySeries(ndata, sets)
        flrs = FLR.generateRecurrentFLRs(tmpdata)
        self.flrgs = self.generateFLRG(flrs, self.c)

    def forecast(self, data, **kwargs):
        l = 1

        data = np.array(data)

        ndata = self.doTransformations(data)

        l = len(ndata)

        ret = []

        for k in np.arange(0, l):

            mv = FuzzySet.fuzzyInstance(ndata[k], self.sets)

            actual = self.sets[np.argwhere(mv == max(mv))[0, 0]]

            if actual.name not in self.flrgs:
                ret.append(actual.centroid)
            else:
                flrg = self.flrgs[actual.name]
                mp = self.getMidpoints(flrg)

                ret.append(mp.dot(flrg.weights()))

        ret = self.doInverseTransformations(ret, params=[data[self.order - 1:]])

        return ret
