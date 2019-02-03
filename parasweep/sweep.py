# -*- coding: utf-8 -*-
"""Main sweep functionality."""
from parasweep.namers import SequentialNamer
from parasweep.dispatchers import PythonSubprocessDispatcher
from parasweep.templates import PythonFormatTemplate

import time
import datetime
import os


def run_sweep(command, configs, templates, sweep, sweep_id=None,
              naming=SequentialNamer(),
              dispatcher=PythonSubprocessDispatcher(),
              template_engine=PythonFormatTemplate, delay=0.0, serial=False,
              wait=False, cleanup=False, verbose=True, overwrite=True,
              save_mapping=True):
    r"""
    Run parameter sweeps.

    This function runs the program with the Cartesian product of the parameter
    ranges.

    Parameters
    ----------
    command : str
        The command to run. Must include '{sim_id}' indicating where the
        simulation ID is to be inserted.
    configs : list
        List of paths indicating where the configuration files should be saved
        after substitution of the parameters into the templates. Must be in the
        same order as `templates`.
    templates : list
        List of paths of templates to substitute parameters into. Must be in
        the same order as `configs`.
    sweep : sweepers.Sweep instance
        A :class:`parasweep.sweepers.Sweep` object
    sweep_id : str, optional
        A name for the sweep. By default, the name is generated automatically
        from the date and time.
    naming : namers.Namer instance, optional
        A :class:`parasweep.namers.Namer` object that specifies how to assign
        simulation IDs. By default, assigns simulation IDs sequentially.
    dispatcher : dispatchers.Dispatcher instance, optional
        A :class:`parasweep.dispatchers.Dispatcher` object that specifies how
        to run the jobs. By default, uses Python's `subprocess` module.
    template_engine : templates.Template class, optional
        A :class:`parasweep.templates.Template` class that specifies the
        template engine to use. By default, uses Python format strings.
    delay : float, optional
        How many seconds to delay between dispatching successive simulations.
        0.0 by default.
    serial : bool, optional
        Whether to run simulations serially, i.e., to wait for each simulation
        to complete before executing the next one. Enabling this turns off
        parallelism. False by default.
    wait : bool, optional
        Whether to wait for all simulations to complete before returning.
        False by default.
    cleanup : bool, optional
        Whether to delete configuration files after all the simulations are
        done. This will cause the command to wait on all processes before
        returning (as with the `wait` argument). False by default.
    verbose : bool, optional
        Whether to print some information about each simulation as it is
        launched. True by default.
    overwrite : bool, optional
        Whether to overwrite existing files when creating configuration files.
        If False, a `FileExistsError` will be raised when a configuration
        filename coincides with an existing one in the same directory. True by
        default.
    save_mapping : bool, optional
        Whether to return a mapping between the parameters to the simulation
        IDs. If the sweep is a grid sweep, an N-dimensional labelled array
        (using `xarray`) which maps the parameters to the simulation IDs will
        be returned. The array coordinates correspond to each sweep parameter,
        while the values contain the simulation IDs. This array will also be
        saved as a netCDF file with the name 'sim_ids_{sweep_id}.nc'. If
        instead specific parameter sets are provided (using the
        `parameter_sets` argument) then a dictionary mapping the simulation IDs
        to the parameter sets will be returned. True by default.

    Examples
    --------
    An example of the basic formatting that can be done with the Python
    formatting templates:

        >>> from parasweep import run_sweep, CartesianSweep
        >>> with open('template.txt', 'w') as template:
        ...     template.write('Hello {x:.2f}\n')
        >>> mapping = run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
        ...                     templates=['template.txt'],
        ...                     sweep=CartesianSweep({'x': [1/3, 2/3, 3/3]}),
        ...                     verbose=False)
        Hello 0.33
        Hello 0.67
        Hello 1.00

    Mako templates provide functionality that is not available with Python
    formatting templates, being able to insert code within the template:

        >>> from parasweep.templates import MakoTemplate
        >>> with open('template.txt', 'w') as template:
        ...     template.write('Hello ${x*10}\n')
        >>> run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
        ...           templates=['template.txt'],
        ...           sweep=CartesianSweep({'x': [1, 2, 3]}), verbose=False,
        ...           template_engine=MakoTemplate, mapping=False)
        Hello 10
        Hello 20
        Hello 30

    Multiple configuration files and their corresponding templates can be used:

    >>> run_sweep(command='cat {sim_id}_1.txt {sim_id}_2.txt',
    ...           configs=['{sim_id}_1.txt', '{sim_id}_2.txt'],
    ...           template_texts=['Hello {x:.2f}\n',
    ...                           'Hello again {y}\n'],
    ...           sweep_parameters={'x': [1/3, 2/3, 3/3], 'y': [4]},
    ...           verbose=False, mapping=False)
    Hello 0.33
    Hello again 4
    Hello 0.67
    Hello again 4
    Hello 1.00
    Hello again 4

    By default (if `mapping` is True), a mapping will be returned between
    the parameters and the simulation IDs, which facilitates postprocessing::

        >>> run_sweep('cat {sim_id}.txt >> out', ['{sim_id}.txt'],
        ...           template_texts=['Hello {x} {y} {z}\n'],
        ...           sweep_parameters={'x': [1, 2], 'y': [3, 4, 5],
        ...                             'z': [6, 7, 8, 9]})
        <xarray.DataArray 'sim_id' (x: 2, y: 3, z: 4)>
        array([[['0', '1', '2', '3'],
                ['4', '5', '6', '7'],
                ['8', '9', '10', '11']],

               [['12', '13', '14', '15'],
                ['16', '17', '18', '19'],
                ['20', '21', '22', '23']]], dtype='<U2')
        Coordinates:
          * x        (x) int64 1 2
          * y        (y) int64 3 4 5
          * z        (z) int64 6 7 8 9


    The default sweep is a Cartesian sweep, meaning that all the combinations
    of all the parameters are used (every member in the Cartesian product of
    the parameter values). Alternatively, specific parameter sets can be used:

    >>> mapping = run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
    ...                     template_texts=['Hello {x}, {y}, {z}\n'],
    ...                     parameter_sets=[{'x': 2, 'y': 8, 'z': 5},
    ...                                     {'x': 1, 'y': -4, 'z': 9}],
    ...                     verbose=False)
    Hello 2, 8, 5
    Hello 1, -4, 9

    In the case that parameter sets are used, the parameter mapping is a
    dictionary like the following:

    >>> mapping
    {'0': {'x': 2, 'y': 8, 'z': 5}, '1': {'x': 1, 'y': -4, 'z': 9}}

    """
    if isinstance(configs, str) or isinstance(templates, str):
        raise TypeError('`configs` and `templates` must be a list.')

    if not sweep_id:
        current_time = datetime.datetime.now()
        sweep_id = current_time.strftime('%Y-%m-%dT%H:%M:%S')

    config = template_engine(paths=templates)

    naming.start(length=sweep.sweep_length)

    sim_ids = []
    config_filenames = []

    dispatcher.initialize_session()

    for sweep_params in sweep.elements():
        sim_id = naming.next(sweep.keys, sweep_params.values())
        sim_ids.append(sim_id)

        rendered = config.render(sweep_params)
        for config_rendered, config_path in zip(rendered, configs):
            config_filename = config_path.format(sim_id=sim_id)
            config_filenames.append(config_filename)
            if not overwrite:
                if os.path.isfile(config_filename):
                    raise FileExistsError('{} exists, set `overwrite` '
                                          'to True to '
                                          'overwrite.'.format(config_filename))
            with open(config_filename, 'wb') as config_file:
                config_file.write(config_rendered.encode('utf-8', 'replace'))

        if verbose:
            print('Running simulation {} with parameters:'.format(sim_id))
            print('\n'.join('{}: {}'.format(key, param) for key, param
                            in sweep_params.items()))
        dispatcher.dispatch(command.format(sim_id=sim_id), serial)
        if delay:
            time.sleep(delay)

    if wait:
        dispatcher.wait_all()

    if cleanup:
        dispatcher.wait_all()
        for config_filename in config_filenames:
            os.remove(config_filename)

    return sweep.mapping(sim_ids, sweep_id, save_mapping)