Installation Guide
==================

BEEhaviourLab is distributed as a Python package.

From PyPI:

.. code-block:: bash

   pip install beehaviourlab

From PyPI with extras:

.. code-block:: bash

   pip install "beehaviourlab[docs]"
   pip install "beehaviourlab[test]"
   pip install "beehaviourlab[dev]"

From source (editable):

.. code-block:: bash

   git clone https://github.com/BEEhaviourLab/BEEhaviourLab.git
   cd BEEhaviourLab
   pip install -e .

Documentation dependencies:

.. code-block:: bash

   pip install -e ".[docs]"

This will install Sphinx and other dependencies required to build the
documentation.

Build the docs locally:

.. code-block:: bash

   sphinx-build -b html docs docs/_build/html

The generated HTML can be found in ``docs/_build/html``.

Test dependencies:

.. code-block:: bash

   pip install -e ".[test]"
