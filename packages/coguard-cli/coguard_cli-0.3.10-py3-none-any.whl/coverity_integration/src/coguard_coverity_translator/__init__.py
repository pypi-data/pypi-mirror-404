"""
The init file for the CoGuard coverity translator script.
It contains the entrypoint and any other related functionality.
"""

import json
from pathlib import Path
from coverity_integration.src.coguard_coverity_translator.json_translator \
    import translate_result_json

def entrypoint(args):
    """
    The main entrypoint where we are doing something with the arguments
    """
    path_to_folder = Path(args.folder_name)
    cluster_snapshot_path = path_to_folder.joinpath('cluster_snapshot')
    with cluster_snapshot_path.joinpath('manifest.json').open(
            encoding='utf-8'
    ) as manifest_json:
        manifest = json.load(manifest_json)
    with path_to_folder.joinpath('result.json').open(encoding='utf-8') as result_json:
        result = json.load(result_json)
    with path_to_folder.joinpath('result_coverity.json').open(mode='w', encoding='utf-8') \
         as cov_result:
        json.dump(
            translate_result_json(
                cluster_snapshot_path.absolute(),
                manifest,
                result
            ),
            cov_result
        )
