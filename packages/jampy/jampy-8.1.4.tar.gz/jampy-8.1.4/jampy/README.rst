The JamPy Package
=================

**Jeans Anisotropic Modelling for Galactic Dynamics**

.. image:: https://users.physics.ox.ac.uk/~cappellari/images/jam-logo.svg
    :target: https://users.physics.ox.ac.uk/~cappellari/software
    :width: 100
.. image:: https://img.shields.io/pypi/v/jampy.svg
    :target: https://pypi.org/project/jampy/
.. image:: https://img.shields.io/badge/arXiv-0806.0042-orange.svg
    :target: https://arxiv.org/abs/0806.0042
.. image:: https://img.shields.io/badge/DOI-10.1111/...-green.svg
    :target: https://doi.org/10.1111/j.1365-2966.2008.13754.x

``JamPy`` is a Python implementation of the Jeans Anisotropic Modelling (JAM)
formalism for the dynamical modelling of galaxies. 

This software can be used e.g. to measure the mass of supermassive black holes 
in galaxies, to infer their dark-matter content or to measure galaxy masses and
density profiles.

The method calculates all the first and second velocity moments, for both the
intrinsic and the projected kinematics, in spherical and axisymmetric geometry.

The JAM solution assuming a cylindrically-oriented velocity ellipsoid was introduced in 
`Cappellari (2008) <https://ui.adsabs.harvard.edu/abs/2008MNRAS.390...71C>`_,
while the solution assuming a spherically-oriented velocity ellipsoid was introduced in 
`Cappellari (2020) <https://ui.adsabs.harvard.edu/abs/2020MNRAS.494.4819C>`_

.. contents:: :depth: 2

Attribution
-----------

If you use this software for your research, please cite `Cappellari (2008)`_
for the cylindrically-aligned JAM solution and `Cappellari (2020)`_
for the spherically-aligned JAM solution.

The BibTeX entry for the two main JAM papers are respectively::

    @ARTICLE{Cappellari2008,
        author = {Cappellari, Michele},
        title = "{Measuring the inclination and mass-to-light ratio of axisymmetric 
            galaxies via anisotropic Jeans models of stellar kinematics}",
        journal = {MNRAS},
        eprint = {0806.0042},
        year = 2008,
        volume = 390,
        pages = {71-86},
        doi = {10.1111/j.1365-2966.2008.13754.x}
    }

    @ARTICLE{Cappellari2020,
        author = {{Cappellari}, Michele},
        title = "{Efficient solution of the anisotropic spherically-aligned axisymmetric
            Jeans equations of stellar hydrodynamics for galactic dynamics}",
        journal = {MNRAS},
        eprint = {1907.09894},
        year = 2020,
        volume = 494,
        pages = {4819-4837},
        doi = {10.1093/mnras/staa959}
    }

Installation
------------

install with::

    pip install jampy

Without writing access to the global ``site-packages`` directory, use::

    pip install --user jampy

To upgrade ``JamPy`` to the latest version use::

    pip install --upgrade jampy

Documentation
-------------

Full documentation is contained in the individual files docstrings.

Usage examples are contained in the directory ``jampy/examples`` 
which is copied by ``pip`` within the global folder
`site-packages <https://stackoverflow.com/a/46071447>`_.

What follows is the documentation of the two main procedures of the ``JamPy``
package, extracted from their Python docstrings. The other procedures are 
documented in their respective docstrings.

###########################################################################
