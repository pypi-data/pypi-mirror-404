# Honeybee: A Plugin for Environmental Analysis (GPL)
# This file is part of Honeybee.
#
# Copyright (c) 2025, Ladybug Tools.
# You should have received a copy of the GNU Affero General Public License
# along with Honeybee; If not, see <http://www.gnu.org/licenses/>.
# 
# @license AGPL-3.0-or-later <https://spdx.org/licenses/AGPL-3.0-or-later>

"""
Identify problematic areas in Fairyfly models that make them un-simulate-able.
_
These inclue "problem regions," which identify cases where there are two or
more groups of shapes that are disconnected from one another.
_
It also includes "problem holes," which identify cases of gaps or holes within
a larger connected region of shapes.
-

    Args:
        _model: A Fairyfly Model for which problem regions are to be visualized.

    Returns:
        regions - Polylines for regions of shapes that are disconnected from one
            another and are therefore un-simulate-able.
        holes - Polylines for holes in the model that make it un-simulate-able.
"""

ghenv.Component.Name = 'FF Visualize Problem Areas'
ghenv.Component.NickName = 'Problems'
ghenv.Component.Message = '1.9.0'
ghenv.Component.Category = 'Fairyfly'
ghenv.Component.SubCategory = '0 :: Create'
ghenv.Component.AdditionalHelpFromDocStrings = '0'

try:  # import the fairyfly dependencies
    from fairyfly.model import Model
except ImportError as e:
    raise ImportError('\nFailed to import fairyfly:\n\t{}'.format(e))

try:  # import the ladybug_rhino dependencies
    from ladybug_rhino.fromgeometry import from_polyline3d
    from ladybug_rhino.grasshopper import all_required_inputs, give_warning
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_rhino:\n\t{}'.format(e))


if all_required_inputs(ghenv.Component):
    # extract the regions and holes
    assert isinstance(_model, Model), \
        'Expected Fairyfly Model. Got {}.'.format(type(_model))
    regions, holes = _model.properties.therm.problem_areas
    regions = [from_polyline3d(pl) for pl in regions]
    holes = [from_polyline3d(pl) for pl in holes]

    # give warnings about problems
    if len(regions) != 0:
        msg = '{} disconnected regions in the model were found.'.format(len(regions))
        give_warning(ghenv.Component, msg)
    if len(holes) != 0:
        msg = '{} holes in the model were found.'.format(len(holes))
        give_warning(ghenv.Component, msg)
