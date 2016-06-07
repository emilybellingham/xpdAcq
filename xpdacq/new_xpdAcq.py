import uuid
import time
from mock import MagicMock
from collections import ChainMap
import bluesky.plans as bp
import numpy as np
from bluesky import RunEngine
from bluesky.utils import normalize_subs_input
from bluesky.callbacks import LiveTable
#from bluesky.callbacks.broker import verify_files_saved
from xpdacq.beamtime import ScanPlan
from xpdacq.beamtime import Sample
from xpdacq.glbl import glbl

verify_files_saved = MagicMock()

def _summarize(plan):
    "based on bluesky.utils.print_summary"
    output = []
    read_cache = []
    for msg in plan:
        cmd = msg.command
        if cmd == 'open_run':
            output.append('{:=^80}'.format(' Open Run '))
        elif cmd == 'close_run':
            output.append('{:=^80}'.format(' Close Run '))
        elif cmd == 'set':
            output.append('{motor.name} -> {args[0]}'.format(motor=msg.obj,
                                                             args=msg.args))
        elif cmd == 'create':
            pass
        elif cmd == 'read':
            read_cache.append(msg.obj.name)
        elif cmd == 'save':
            output.append('  Read {}'.format(read_cache))
            read_cache = []
    return '\n'.join(output)


def use_photon_shutter():
    glbl.shutter = 'foo'


def use_fast_shutter():
    glbl.shutter = 'fastfoo'


class CustomizedRunEngine(RunEngine):
    def __call__(self, sample, plan, subs=None, *, raise_if_interrupted=False
            , verify_write=False, auto_dark=True, dk_window=3000,**metadata_kw):
        _subs = normalize_subs_input(subs)
        # For simple usage, allow sample to be a plain dict or a Sample.
        if isinstance(sample, Sample):
            sample_md = sample.md
        else:
            sample_md = sample
        #if livetable:
        #    _subs.update({'all':LiveTable([pe1c, temp_controller])})
        if verify_write:
            _subs.update({'stop':verify_files_saved})
        # No keys in metadata_kw are allows to collide with sample keys.
        if set(sample_md) & set(metadata_kw):
            raise ValueError("These keys in metadata_kw are illegal "
                             "because they are always in sample: "
                             "{}".format(set(sample_md) & set(metadata_kw)))
        metadata_kw.update(sample_md)
        if isinstance(plan, ScanPlan):
            plan = plan.factory()
        sh = glbl.shutter
        # force to open shutter before scan and close it after
        plan = bp.pchain(bp.abs_set(sh, 1), plan, bp.abs_set(sh, 0))
        super().__call__(plan, subs,
                         raise_if_interrupted=raise_if_interrupted,
                         **metadata_kw)


def ct(pe1c, exposure, *, md=None):
    if md is None:
        md = {}
    # setting up detector
    pe1c.number_of_sets.put(1)
    pe1c.cam.acquire_time.put(glbl.frame_acq_time)
    acq_time = pe1c.cam.acquire_time.get()
    # compute number of frames and save metadata
    num_frame = np.ceil(exposure / acq_time)
    if num_frame == 0:
        num_frame = 1
    computed_exposure = num_frame*acq_time
    pe1c.images_per_set.put(num_frame)
    print('INFO: requested exposure time = ',exposure,' -> computed exposure time:',computed_exposure)
    _md = ChainMap(md, {'sp_time_per_frame': acq_time,
                        'sp_num_frames': num_frame,
                        'sp_requested_exposure': exposure,
                        'sp_computed_exposure': computed_exposure,
                        'sp_type': 'ct',
                        # need a name that shows all parameters values
                        # 'sp_name': 'ct_<exposure_time>',
                        'sp_uid': str(uuid.uuid4()),
                        'plan_name': 'ct'})
    plan = bp.count([pe1c], md=_md)
    plan = bp.subs_wrapper(plan, LiveTable([pe1c]))
    yield from plan



class ScanPlan:
    def __init__(self, plan_func, *args, **kwargs):
        self.plan_func = plan_func
        self.plan_name = plan_func.__name__
        self.args = args
        self.kwargs = kwargs

    def factory(self):
        # grab the area detector used in current configuration
        pe1c = glbl.pe1c
        # pass parameter to plan_func
        plan = self.plan_func(pe1c, *self.args, **self.kwargs)
        return plan

    def __str__(self):
        return _summarize(self.factory())