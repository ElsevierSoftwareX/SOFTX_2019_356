from abc import ABC, abstractmethod
import itertools
import operator
from functools import reduce
import json


class Sweep(ABC):
    """Sweeps must define an iteration as well as a type of mapping."""

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def elements(self):
        pass

    @abstractmethod
    def mapping(self, sim_ids, sweep_id, save=True):
        pass


class CartesianSweep(Sweep):
    def __init__(self, sweep_parameters, filter=None):
        self.keys = list(sweep_parameters.keys())
        self.values = list(sweep_parameters.values())
        self.filter = filter

        self.lengths = [len(value) for value in self.values]
        self.sweep_length = reduce(operator.mul, self.lengths, 1)

    def elements(self):
        product = itertools.product(*self.values)

        return (dict(zip(self.keys, element)) for element in product)

    def mapping(self, sim_ids, sweep_id, save=True):
        import xarray
        import numpy

        sim_ids_array = xarray.DataArray(numpy.reshape(numpy.array(sim_ids),
                                                       self.lengths),
                                         coords=self.values, dims=self.keys,
                                         name='sim_id')

        if save:
            sim_ids_filename = 'sim_ids_{}.nc'.format(sweep_id)
            sim_ids_array.to_netcdf(sim_ids_filename)

        return sim_ids_array


class SetSweep(Sweep):
    def __init__(self, parameter_sets):
        self.parameter_sets = parameter_sets
        self.keys = parameter_sets[0].keys()
        self.sweep_length = len(parameter_sets)

    def elements(self):
        return self.parameter_sets

    def mapping(self, sim_ids, sweep_id, save=True):
        sim_id_mapping = dict(zip(sim_ids, self.parameter_sets))

        if save:
            sim_ids_filename = 'sim_ids_{}.json'.format(sweep_id)

            with open(sim_ids_filename, 'w') as sim_ids_file:
                json.dump(sim_id_mapping, sim_ids_file)

        return sim_id_mapping