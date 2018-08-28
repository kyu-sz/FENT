import heapq

import numpy as np
from sklearn.mixture.gaussian_mixture import GaussianMixture
from torch import tensor


class SampleManager:
    def __init__(self, batch_size=128, max_sample_num=10000):
        self._mixture = GaussianMixture(batch_size - 1)
        self._max_sample_num = max_sample_num
        self._samples = None
        self._component_sample_idx = None  # sample indices classified to each component
        self._num_init_samples = 0

    def update_gmm(self):
        if len(self._samples) > self._max_sample_num and self._component_sample_idx:
            to_del = {
                t[2] for t in
                heapq.nlargest(
                    len(self._samples) - self._max_sample_num,
                    [(self._samples[i][1], i) for i in range(len(self._samples))])
            }.union(
                set(self._component_sample_idx[np.argmin(self._component_sample_idx)[0]])
            )
            for i in sorted([i for i in to_del if i >= self._num_init_samples], reverse=True):
                del self._samples[i]

        self._mixture.fit(self._samples)
        pred = self._mixture.predict(self._samples)
        self._component_sample_idx = [[]] * self._mixture.n_components
        for idx, p in enumerate(pred):
            self._component_sample_idx[p].append(idx)

    def add_init_samples(self, features: list, rel_bbox: list):
        self._num_init_samples = len(features)
        self._samples = [(f, b, 0) for f, b in zip(features, rel_bbox)]
        self.update_gmm()

    def add_sample(self, features: tensor, rel_bbox: list):
        self._samples.append((features, rel_bbox, 0))
        self._component_sample_idx[self._mixture.predict(features)].append(len(self._samples) - 1)

    def pick_samples(self) -> list:
        """
        Randonly pick a sample within each component.
        :return: a list of samples; each sample is a tuple of features and confidence score.
        """
        if self._component_sample_idx is None:
            self.update_gmm()

        selected_samples = [self._samples[np.random.randint(0, self._num_init_samples)]]
        for c in self._component_sample_idx:
            selected_samples.append(self._samples[c[np.random.randint(0, len(c))]])
        return selected_samples
