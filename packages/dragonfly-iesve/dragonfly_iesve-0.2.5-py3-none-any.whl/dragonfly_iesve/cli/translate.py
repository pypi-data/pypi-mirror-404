"""honeybee iesve translation commands."""
import click
import sys
import logging

from ladybug.commandutil import process_content_to_output
from dragonfly.model import Model

from dragonfly_iesve.writer import model_to_gem as writer_model_to_gem

_logger = logging.getLogger(__name__)


@click.group(help='Commands for translating Dragonfly JSON files to IES files.')
def translate():
    pass


@translate.command('model-to-gem')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--multiplier/--full-geometry', ' /-fg', help='Flag to note if the '
    'multipliers on each Building story will be passed along to the '
    'generated Room objects or if full geometry objects should be '
    'written for each story in the building.', default=True, show_default=True)
@click.option(
    '--plenum/--no-plenum', '-p/-np', help='Flag to indicate whether '
    'ceiling/floor plenum depths assigned to Room2Ds should generate '
    'distinct 3D Rooms in the translation.', default=True, show_default=True)
@click.option(
    '--merge-method', '-m', help='Text to describe how the Room2Ds should '
    'be merged into individual Rooms during the translation. Specifying a '
    'value here can be an effective way to reduce the number of Room '
    'volumes in the resulting Model and, ultimately, yield a faster simulation '
    'time with less results to manage. Choose from: None, Zones, PlenumZones, '
    'Stories, PlenumStories.', type=str, default='None', show_default=True)
@click.option(
    '--output-file', '-o', help='Optional GEM file path to output the GEM string '
    'of the translation. By default this will be printed out to stdout.',
    type=click.File('w'), default='-', show_default=True)
def model_to_gem_cli(model_file, multiplier, plenum, merge_method, output_file):
    """Translate a Dragonfly Model JSON file to an IES-VE GEM file.

    \b
    Args:
        model_json: Full path to a Model JSON file (DFJSON) or a Model pkl (DFpkl) file.
    """
    try:
        full_geometry = not multiplier
        no_plenum = not plenum
        model_to_gem(model_file, full_geometry, no_plenum, merge_method, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_gem(
    model_file, full_geometry=False, no_plenum=False, merge_method='None',
    output_file=None, multiplier=True, plenum=True
):
    """Translate a Model file to an IES-VE GEM string.

    Args:
        model_file: Full path to a Model JSON file (DFJSON) or a Model pkl (DFpkl) file.
        full_geometry: Boolean to note if the multipliers on each Building story
            will be passed along to the generated Honeybee Room objects or if
            full geometry objects should be written for each story in the
            building. (Default: False).
        no_plenum: Boolean to indicate whether ceiling/floor plenum depths
            assigned to Room2Ds should generate distinct 3D Rooms in the
            translation. (Default: False).
        merge_method: An optional text string to describe how the Room2Ds should
            be merged into individual Rooms during the translation. Specifying a
            value here can be an effective way to reduce the number of Room
            volumes in the resulting Model and, ultimately, yield a faster simulation
            time with less results to manage. Note that Room2Ds will only be merged if
            they form a contiguous volume. Otherwise, there will be multiple Rooms per
            zone or story, each with an integer added at the end of their
            identifiers. Choose from the following options:

            * None - No merging will occur
            * Zones - Room2Ds in the same zone will be merged
            * PlenumZones - Only plenums in the same zone will be merged
            * Stories - Rooms in the same story will be merged
            * PlenumStories - Only plenums in the same story will be merged

        output_file: Optional GEM file to output the GEM string of the translation.
            If None, the string will be returned from this method. (Default: None).
    """
    # re-serialize the Dragonfly Model
    model = Model.from_file(model_file)
    # create the strings for the model
    multiplier = not full_geometry
    gem_str = writer_model_to_gem(model, multiplier, no_plenum)
    # write out the GEM file
    return process_content_to_output(gem_str, output_file)
