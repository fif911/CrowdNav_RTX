# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from sklearn import linear_model
import math

DEFAULT = r"C:\Users\ozakotianskyi\PycharmProjects\RTX\rtxlib\trafficprovider\trafficDBs\traffic_hourly.csv"


class Deintegrator():
    def __init__(self, data, linear_structure=True):
        ldata = np.log(data)
        if linear_structure:
            regr = linear_model.LinearRegression()
            result = regr.fit(np.array(range(len(ldata))).reshape(-1, 1), np.array(ldata).reshape(-1, 1))
            a, b = result.intercept_[0], result.coef_[0][0]
            self.intercept = a
            self.slope = b
        else:
            a = self.intercept = np.mean(data)
            b = self.slope = 0
        regressor = pd.core.series.Series([a + b * i for i in range(len(data))], data.index)
        self.data = ldata - regressor
        self.dilation = 1.0

    def deintegratedData(self):
        return self.data

    def rescale(self, time, value):
        ttime = time * self.dilation
        tlimit = len(self.data)
        if ttime > tlimit:
            texcess = ttime - tlimit
            transfer = tlimit / 100
            a = min(1, texcess / transfer)
            ttime = a * (texcess ** (9 / 10)) + (1 - a) * texcess + tlimit
        return np.exp(self.intercept + self.slope * ttime + value)


class TrafficGenerator():
    def __init__(self, reference_mean = 1000, dataset = None, minute_in_step = 15, rescale_time = None, extend = "Loop",
                 model = "Fourier", interpolate = "linear", interpolate_order = 2, noiseScale = 0, stream = False,
                 remove_growth = False):
        """inputs:
            reference_mean: Intended mean of population at the start of simulation
            dataset: Traffic Dataset to pass to the simulation
            minute_in_step: Minutes in a Subdivisions for interpolation
            rescale_time: Scale Factor for the minute_in_step.
                            If its 30 tic per second and 5 minute_in_step then rescale should be 1/(5*30)
            extend: Algorithm to handle time points after end of dataset ("Error","Extrapolate","Hold","Loop")
            model: Model for Extrapolation, only option is "Fourier"
            interpolate: Pandas Interpolation Argument, defaults to 'linear'
            noiseScale: Scale of Additive noise added during extrapolation
            stream: Whether it's a batched dataset or it's a stream (only False is supported)
            remove_growth = Treat traffic as non-integrated
        """
        self.integral = not remove_growth
        self.rescale_time = rescale_time
        self.minutesTic = minute_in_step
        self.interpolate = interpolate
        self.order = interpolate_order
        if dataset is None and not stream:
            self.load(DEFAULT)
        elif not stream:
            self.load(dataset)
        else:
            raise NotImplementedError("Data Streaming Not Implemented")
        modelEnum = {"Fourier": self.fourierModel}
        modelF = modelEnum[model] if model in modelEnum else self.fourierModel
        extendEnum = {"Error": self.raiseOutOfData, "Extrapolate": modelF,
                      "Hold": self.hold, "Loop": self.loop}
        if extend in extendEnum:
            extendEnum[extend]()
        else:
            self.loop()
        self.noiseSigma = self.evalNoise(noiseScale)
        self.sourceMean = self.evalMean()
        self.simulationMean = reference_mean
        self.currentIndex = 0
        self.noiseIndex = 0
        self.removeIntegration = remove_growth

    def load(self, filepath):
        mxt = self.minutesTic
        raw_data = pd.read_csv(filepath, parse_dates=True, date_parser=pd.to_datetime)
        raw_data["timestamp"] = pd.to_datetime(raw_data["timestamp"])
        time = raw_data["timestamp"]
        data = raw_data.set_index("timestamp")["volume"]
        self.raw_data = raw_data
        self.integrationModel = Deintegrator(data, self.integral)
        data = self.integrationModel.deintegratedData()
        idx = data.index
        secFreq = int(mxt * 60)
        nidx = pd.date_range(time.min(), time.max(), freq='%ds' % secFreq)
        res = data.reindex(idx.union(nidx)).interpolate(self.interpolate, order=self.order).reindex(nidx)
        self.integrationModel.dilation = len(idx) / len(nidx)
        self.data = res
        self.start_date = time.min()
        self.dilation = self.minutesTic * self.rescale_time if self.rescale_time is not None else 1

    def date(self,tic):
        return self.start_date + pd.Timedelta(self.dilation * tic,"min")

    def rescale(self, tic, val):
        tic = 0 if self.removeIntegration else tic
        volume = self.integrationModel.rescale(tic, val)
        scale_factor = self.simulationMean / self.integrationModel.rescale(0, self.sourceMean)
        return scale_factor * volume

    def _scaled_tic_(self, tic):
        if len(self.data) > tic:
            return self.rescale(tic, self.data.iloc[tic])
        else:
            return self.rescale(tic, self.extrapolate(tic))

    def __call__(self, tic=None):
        if tic is None:
            tic = self.currentIndex
        if self.rescale_time is not None:
            ntic = tic * self.rescale_time
            l = math.floor(ntic)
            r = math.ceil(ntic)
            lval = self._scaled_tic_(l)
            rval = self._scaled_tic_(r)
            a = ntic - l
            return (1 - a) * lval + (a) * rval
        else:
            return self._scaled_tic_(tic)

    def next(self):
        ix = self.currentIndex
        if self.currentIndex < len(self.data):
            vol = self.rescale(ix, self.data.iloc[ix])
        else:
            vol = self.rescale(ix, self.extrapolate(ix))
        self.currentIndex += 1
        return vol

    def evalMean(self):
        return np.mean(self.data)

    def evalNoise(self, noiseScale):
        return np.std(self.data) * noiseScale

    def raiseOutOfData(self):
        raise IndexError("Time Series index out of range")

    def hold(self, *args, **kwargs):
        self.extrapolate = lambda t: self.data.iloc[-1] + self.noise()

    def fourierModel(self, harmonic_depth=None):
        data = self.data
        if harmonic_depth is None:
            harmonic_depth = len(data) // 10
        n = len(data)
        t = np.arange(0, n)
        x_freqdom = np.fft.fft(data)
        f = np.fft.fftfreq(n)
        indexes = range(n)
        indexes = sorted(indexes, key=lambda i: np.absolute(f[i]))

        t = np.arange(0, n)
        restored_sig = np.zeros(t.size)
        for i in indexes[:1 + harmonic_depth * 2]:
            ampli = np.absolute(x_freqdom[i]) / n  # amplitude
            phase = np.angle(x_freqdom[i])  # phase
            restored_sig += ampli * np.cos(2 * np.pi * f[i] * t + phase)
        restored_sig = restored_sig * np.std(data) / np.std(restored_sig)

        def extrapolate(tic):
            noise = self.noise()
            return restored_sig[tic % n] + noise

        self.extrapolate = extrapolate

    def noise(self):
        return np.random.normal(0, self.noiseIndex)

    def loop(self):
        self.extrapolate = lambda t: self.data.iloc[t % len(self.data)]
