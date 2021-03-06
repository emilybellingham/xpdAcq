.. _usb_running:

Running scans
-------------

The hard work of the experimental setup is now done.  It involved creating all the
rich metadata container and ScanPlan objects, but with this in the past it makes
it easy and low overhead to run the scans, allowing the experimenter to concentrate
on the science and not the experimental process.

To run scans there are just a few xpdAcq
run engines(functions) that you need.  To run a scan you simply pick the run engine you want
and give it a predefined Sample object and
a predefined ScanPlan object, then hit return and sit back, your scan will be carried out.

The allowed scan types are:

.. code-block:: python

  >>> xrun(sample, scanplan)

.. autofunction:: xpdacq.xpdacq.xrun

``xrun`` stands for "XPD run" which is a our main run engine.

Here are some examples of a workflow.  Assume a Ni_calibrant sample is loaded on the diffractometer
and the ``Ni_calibrant`` Sample object is created as well as all the ``ScanPlan`` we need.
We will start by doing a scan with ``Sample`` object ``Setup`` on our ``ct_1`` ScanPlan.

Remember, always start with ``bt.list()``

.. code-block:: python

  >>> bt.list()

  ScanPlans:
  0: 'ct_5'
  1: 'ct_0.1'
  2: 'ct_1'
  3: 'ct_10'
  4: 'ct_30'
  5: 'ct_60'
  7: 'ct_1.5'
  8: 'ct_100.5'

  Samples:
  0: Setup
  1: Ni_calibrant
  2: bkgd_kapton_0.9mmOD
  3: bkgd_kapton_1mmOD
  4: bkgd_kapton_0.5mmOD
  5: activated_carbon_1
  6: activated_carbon_2
  7: activated_carbon_3
...

The Sample object I want has list index 0 and the ScanPlan has list index 2.
Let's try to make sure everything is ok.

.. code-block:: python

  >>> xrun(0, 2)
  INFO: requested exposure time = 1 - > computed exposure time= 1.0
  INFO: No calibration file found in config_base. Scan will still keep going on
  INFO: no mask has been associated with current glbl
  +-----------+------------+------------+
  |   seq_num |       time |  pe1_image |
  +-----------+------------+------------+
  |         1 | 15:58:47.4 |       5.00 |
  +-----------+------------+------------+
  generator count ['73dc71'] (scan num: 3)

OK, it seems to work, lets do some testing to see how much intensity we need.
We will do three setup scans with 1.5 seconds and 100.5 seconds exposure
and then compare them.

.. code-block:: python

  >>> xrun(0, 7)  #1.5 seconds
  INFO: requested exposure time = 1.5 - > computed exposure time= 1.5
  INFO: No calibration file found in config_base. Scan will still keep going on
  INFO: no mask has been associated with current glbl
  +-----------+------------+------------+
  |   seq_num |       time |  pe1_image |
  +-----------+------------+------------+
  |         1 | 16:01:37.3 |       5.00 |
  +-----------+------------+------------+
  generator count ['728f2f'] (scan num: 5)

  >>> setupscan(0, 8)  #100.5 seconds
  INFO: requested exposure time = 100.5 - > computed exposure time= 100.5
  INFO: No calibration file found in config_base. Scan will still keep going on
  INFO: no mask has been associated with current glbl
  +-----------+------------+------------+
  |   seq_num |       time |  pe1_image |
  +-----------+------------+------------+
  |         1 | 16:02:57.0 |       5.00 |
  +-----------+------------+------------+
  generator count ['981e70'] (scan num: 6)


It seems that the 2 second scans are the best, so let's do with desired ``Sample``
to get the first data-set.

.. code-block:: python

  >>>In [13]: xrun(0, 8)
  INFO: requested exposure time = 100.5 - > computed exposure time= 100.5
  INFO: closing shutter...
  INFO: taking dark frame....
  INFO: No calibration file found in config_base. Scan will still keep going on
  INFO: no mask has been associated with current glbl
  +-----------+------------+------------+
  |   seq_num |       time |  pe1_image |
  +-----------+------------+------------+
  |         1 | 16:04:31.4 |       5.00 |
  +-----------+------------+------------+
  generator count ['d770c7'] (scan num: 7)
  opening shutter...
  INFO: No calibration file found in config_base. Scan will still keep going on
  INFO: no mask has been associated with current glbl
  +-----------+------------+------------+
  |   seq_num |       time |  pe1_image |
  +-----------+------------+------------+
  |         1 | 16:04:31.5 |       5.00 |
  +-----------+------------+------------+
  generator count ['0beaaf'] (scan num: 8)


  .. _auto_dark:

Automated dark collection
"""""""""""""""""""""""""

you might have found something weird when you running a ``xrun`` command:

*I only requested one ``xrun`` but program runs two scans*

So what happen?

That is actually a feature called auto-dark subtraction of ``xpdAcq``.
When you are running your experiment, ``xpdAcq`` actually checks if you have
collected a **fresh and appropriate** dark frame every time it collects a scan.
The definition of **fresh and appropriate** is:

**Nice and fresh**
^^^^^^^^^^^^^^^^^^

  .. code-block:: none

    Given a certain period T (``dark window``), there exists a dark frame
    with the same **total exposure time** and exactly the same **acquisition time**
    as the light frame we are about collect.

  .. note::

    At **XPD**, area detector is running in the ``continuous acquisition`` mode,
    which means detector keeps **reading** but only **saves** image when ``xpdAcq``
    tells it to save, with desired exposure time.

    In short,

    * acquisition time defines how fast is the detector reading time,
      ranged from 0.1s to 5s.

    * exposure time means total exposure time, which is user defined.

  Automated dark collection is enabled by default and it can be turned off by:

  .. code-block:: python

    glbl.auto_dark = False
    glbl.shutter_control = False

  And period of dark window can be modified by:

  .. code-block:: python

    glbl.dk_window = 200 # in minutes. default is 3000 minutes

  Having ``auto_dark`` set to ``True`` is strongly recommended as this enables
  ``xpdAcq`` to do automated dark frame subtraction when you pull out data from
  centralized **NSLSL-II** server.

.. _auto_calib:

Automated calibration capture
"""""""""""""""""""""""""""""

Often times, keeping track with which calibration file is associated with
certain scan is very tiring. ``xpdAcq`` makes this easier for you. Before every
scan is being collected, program goes to grab the most recent calibration
parameters in ``/home/xf28id1/xpdUser/config_base`` and load them as part of
metadata so that you can reference them whenever you want and make in-situ data
reduction possible!

.. _calib_manual:

Quick guide of calibration steps with pyFAI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. First you will see an image window like this:

  .. image:: ./img/calib_05.png
    :width: 400px
    :align: center
    :height: 300px

  That is the image we want to perform azimuthal calibration with. Use **magnify
  tool** at the tool bar to zoom in and **right click** on rings. Starting from
  the inner ring and to the outer rings. Usually a few rings (~5) should be
  enough.

  .. image:: ./img/calib_07.png
    :width: 400px
    :align: center
    :height: 300px


  .. note::

    * For a better calibration, we suggest you to select rings that are
      **well separated** from its neighbors.
    * Also, we suggest you to zoom in more for better accuracy when selecting rings.

2. After selecting rings, click on the *original* terminal and hit ``<enter>``.
  Then you will be requested to supply indices of rings you just selected.
  Remember index **starts from 0** as we are using ``python``.
  After supplying all indices, you should have a window to show your calibration:

  .. image:: ./img/calib_08.png
    :width: 400px
    :align: center
    :height: 300px

  Program will ask you if you want to modify parameters. In most of cases, you
  don't have to change the parameters, so just type ``done`` in the terminal and
  calibration process will be done.

3. Finally 1D integration and 2D regrouping results will pop out:

  .. image:: ./img/calib_09.png
    :width: 400px
    :align: center
    :height: 300px

  You can qualitatively interrogate your calibration by looking if lines in
  2D regrouping are straight or not.

  After this step, a calibration file with name ``pyFAI_calib.yml`` will be
  saved under ``/home/xf28id1/xpdUser/config_base``

Alright, you are done then! With ```automated calibration capture`` feature, ``xpdAcq``
will load calibration parameters from the most recent config file.

.. _import_sample:

Sample metadata imported from spreadsheet
"""""""""""""""""""""""""""""""""""""""""

In order to facilitate retrospective operation on data, we suggest you to enter
as much information as you can and that is the main philosophy behind ``xpdAcq``.

Typing in sample metadata during beamtime is always less efficient and it wastes
your time so a pre-populated excel sheet with all metadata entered beforehand
turns out to be the solution.

In order import sample metadata from spreadsheet, we would need you to have a
pre-filled spreadsheet with name ``<saf_number>_sample.xls`` sit in ``xpdConfig``
directory. Then the import process is simply:

.. code-block:: python

  import_sample(300564, bt) # SAF number is 300564 to current beamtime
                            # beamtime object , bt, with SAF number 300564 has created
                            # file with 300564_sample.xls exists in ``xpdConfig`` directory

.. note::

  Usually ``xpdAcq`` will grab the ``saf_number`` and ``bt`` to current beamtime for you,
  so you can simply run ``import_sample()``. However, if you want to load in different
  spreadsheets, you can also import it by explicitly typing in ``saf_number``.

comma separated fields
^^^^^^^^^^^^^^^^^^^^^^

  Files with information entities are separated by a comma ``,``.

  Each separated by ``,`` will be individually searchable later.

  Fields following this parsing rule are:

  ============= ========================================================
  ``cif name``  pointer of potential structures for your sample, if any.
  ``Tags``      any comment you want to put on for this measurement.
  ============= ========================================================

  Example on ``Tags``:

  .. code-block:: none

    background, standard --> background, standard

  And a search on either ``background`` or``standard`` later on will include
  this header.


name fields
^^^^^^^^^^^

  Fields used to store a person's name in ``first name last name`` format.

  Each person's first and last name will be searchable later on.

  Fields following this parsing rule are:

  ======================    =========================================================
  ``Collaborators``         name of your collaborators
  ``Sample Maker``          name of your sample maker
  ``Lead Experimenters``    a person who is going to lead this experiment at beamline
  ======================    =========================================================

  Example on name fields:

  .. code-block:: none

    Maxwell Terban, Benjamin Frandsen ----> Maxwell, Terban, Benjamin, Frandsen

  A search on either ``Maxwell`` or ``Terban`` or ``Benjamin`` or ``Frandsen``
  later will include this header.


phase string
^^^^^^^^^^^^

  Field used to specify the phase information and chemical composition of your
  sample. It's important to enter this field correctly so that we can have
  accelerated data reduction workflow.

  Fields follows this parsing rule are:

  ==============  ==============================================================
  ``Phase Info``  field to specify phase information and chemical composition of
                  your sample
  ==============  ==============================================================

  phase string will be expect to be enter in a form as
  ``phase_1: amount, phase_2: amount``.

  An example of 0.9% sodium chloride water will be:

  .. code-block:: none

    Nacl: 0.09, H20: 0.91

  This ``Phase Info`` will be parsed as:

  .. code-block:: python

    {'sample_composition': {'Na':0.09, 'Cl':0.09, `H`:1.82, `O`:0.91},
     'sample_phase': {'NaCl':0.09, 'H20':0.91},
     'composition_string': 'Na0.09Cl0.09H1.82O0.91'}

  ``composition_string`` is designed for data reduction software going to be
  used. Under ``xpdAcq`` framework, we will assume
  `pdfgetx3 <http://www.diffpy.org/products/pdfgetx3.html>`_

  As before, a search on ``Na`` or ``Cl`` or ``H`` or ``O`` will include this
  header. Also a search on ``Nacl=0.09`` will include this header as well.

.. _background_obj:

Sample Objects
^^^^^^^^^^^^^^

* **Sample**:

  Each row in your spreadsheet will be taken as one valid Sample and metadata
  will be parsed based on the contents you type in with above parsing rule.


Generally, after successfully importing sample from spreadsheet, that is what
you would see:

.. code-block:: python

  In [1]: import_sample(300564, bt)
  *** End of import Sample object ***
  Out[1]: <xpdacq.utils.ExceltoYaml at 0x7fae8ab659b0>

  In [2]: bt.list()

  ScanPlans:


  Samples:
  0: P2S
  1: Ni_calibrant
  2: activated_carbon_1
  3: activated_carbon_2
  4: activated_carbon_3
  5: activated_carbon_4
  6: activated_carbon_5
  7: activated_carbon_6
  8: FeF3(4,4-bipyridyl)
  9: Zn_MOF
  ...

  41: ITO_glass_noFilm
  42: ITO_glass_1hrHeatUpTo250C_1hrhold250C_airdry
  43: ITO_glass_1hrHeatUpTo450C_1hrhold450C_airdry
  44: ITO_glass_30minHeatUpTo150C_1.5hrhold150C_airdry
  45: CeO2_film_calibrant
  46: bkg_1mm_OD_capillary
  47: bkg_0.9mm_OD_capillary
  48: bkg_0.5mm_OD_capillary
  49: bkg_film_on_substrate


.. _auto_mask:

Auto-masking
""""""""""""
Masking can be a tedious process, requireing long hours judging which pixels
are good and which need to be removed. The our automated masking software aims
to alleviate this by applying a set of masks in sequence to return better
quality data.

Masks can be created/used in two ways. The default procedure is a mask is
created for a low scattering sample (usually kapton). Then this mask is reused
for each subsequent image taken with the same detector position. The second
modality is that each image gets is own bespoke mask, potentially derived from
the low scattering mask.


Applied masks
^^^^^^^^^^^^^

0. Any mask passed in to the software:
    If you have any preexisting masks, we will use those as a starting position
    to add upon.

1. Edge mask:
    A default of 30 pixels from the edge of the detector are masked out.
    These pixels are usually faulty as the detector edge has lower than
    expected intensity.

2. Lower threshold mask:
    A lower threshold mask, which removes all pixels who's intensities are
    lower than a certain value is applied. The default theshold is 0.0

3. Upper threshold mask:
    An upper threshold mask, which removes all pixels who's intensities are
    higher than a certain value is applied. This mask is not applied in the
    default settings.

4. Beamstop holder mask:
    A beamstop holder mask, which removes pixels underneath a straight
    beamstop holder is applied. The beamstop holder is masked by finding the
    beamcenter and drawing a pencil like shape from the beamcenter to the edge
    of the detector. All the pixels within this polygon are masked. The default
    settings are to mask out 30 pixels on either side of the line connecting
    the beamcenter and the detector edge

5. Binned outlier mask:
    Lastly a binned outlier mask is applied, removing pixels which are alpha
    standard deviations away from the mean intensity as a function of Q. This
    mask aims to remove many of the dead/hot pixels and streaks. The default
    alpha is 3 standard deviations.

Using the auto-masker
^^^^^^^^^^^^^^^^^^^^^
To use the auto-masker once, creating masks used for subsequent images,
 just run the command:
.. code-block:: python

  run_mask_builder()

This will take a shot and mask it. This mask will then be saved and loaded
into subsequent experiment `run_headers` allowing them to be used for the next
images.


Let's :ref:`take a quick look at our data <usb_quickassess>`
