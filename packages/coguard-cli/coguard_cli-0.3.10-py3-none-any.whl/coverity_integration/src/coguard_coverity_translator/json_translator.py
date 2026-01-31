"""
This is the main module where we are translating our report-json format into
Coveritie's expected format.
"""

import logging
from typing import List, Dict
from pathlib import Path

def _translate_file_to_coverity(
        path_to_files: Path,
        machine_folder_name: str,
        service_folder_name: str,
        file_manifest: Dict
) -> Dict[str, str]:
    """
    Helper function for `_get_sources_from_manifest`.
    This is simply to translate the extracted information when iterating
    through the manifest file into the format that the coverity third party
    exporter is expecting.
    """
    path_of_file = path_to_files.joinpath(
        machine_folder_name
    ).joinpath(
        service_folder_name
    ).joinpath(
        file_manifest.get('subPath', '.')
    ).joinpath(
        file_manifest.get('fileName', '.')
    )
    file_type = file_manifest.get("configFileType")
    return {
        "file": str(path_of_file.absolute()),
        "language": file_type
    }

def _get_sources_from_manifest(
        path_to_files: Path,
        manifest: dict
) -> List[Dict]:
    """
    The helper function for `translate_result_json`, where we take the path_to_files
    variable, and the manifest, and extract all the relevant file-paths there.
    """
    #For now
    result = []
    machines = manifest.get("machines", {})
    for machine_name, machine_manifest in machines.items():
        services = machine_manifest.get("services", {})
        for service_name, service_manifest in services.items():
            config_file_list = service_manifest.get("configFileList", [])
            complimentary_file_list = service_manifest.get("complimentaryFileList", [])
            config_file_list.extend(complimentary_file_list)
            for file_manifest in config_file_list:
                result.append(_translate_file_to_coverity(
                    path_to_files,
                    machine_name,
                    service_name,
                    file_manifest
                ))
    for service_name, service_manifest in manifest.get("clusterServices", {}).items():
        config_file_list = service_manifest.get("configFileList", [])
        complimentary_file_list = service_manifest.get("complimentaryFileList", [])
        config_file_list.extend(complimentary_file_list)
        for file_manifest in config_file_list:
            result.append(_translate_file_to_coverity(
                path_to_files,
                "clusterServices",
                service_name,
                file_manifest
            ))
    return result

def _extract_issues_from_result(
        path_to_files: Path,
        manifest: Dict,
        coguard_result: Dict
) -> List[Dict]:
    """
    The helper function of `translate_result_json` to create a list of `issue` objects
    according to the documentation of Coverity, given the same inputs as
    translate_result_json
    """
    result = []
    for failed_entry in coguard_result.get("failed", []):
        if not failed_entry.get("config_file", ""):
            logging.warning("Could not deduce file from %s.",
                            str(failed_entry))
            continue
        machine_id = failed_entry.get("machine", "")
        service_id = failed_entry.get("service")
        service_name = manifest.get(
            "machines", {}
        ).get(
            machine_id, {}
        ).get(
            "services", {}
        ).get(
            service_id, {}
        ).get("serviceName") if machine_id else manifest.get(
            "clusterServices", {}
        ).get(
            service_id, {}
        ).get("serviceName")
        if not service_name:
            logging.warning("Could not extract service for entry %s",
                            failed_entry)
            continue
        rule_identifier = failed_entry.get("rule", {}).get("name")
        rule_documentation = failed_entry.get(
            "rule", {}
        ).get(
            "documentation", {}
        ).get("documentation")
        rule_remediation = failed_entry.get("rule", {}).get("documentation", {}).get("remediation")
        rule_sources = "\n".join(
            failed_entry.get("rule", {}).get("documentation", {}).get("sources")
        )
        severity = failed_entry.get("rule", {}).get("severity")
        checker = f"CG.{rule_identifier.upper()}"
        extra = rule_identifier
        sub_category = "none"
        properties = {}
        properties["category"] = "misconfiguration"
        properties["type"] = f"{service_name.title()} misconfiguration"
        properties["localEffect"] = rule_documentation
        properties["longDescription"] = (
            f"{rule_documentation}\n\nRemediation: {rule_remediation}\n\nSources:\n{rule_sources}"
        )
        properties["impact"] = "Low" if severity < 3 else "Medium" if severity == 3 else "High"
        properties["issueKind"] = "QUALITY,SECURITY"
        event = {}
        event["tag"] = f"{service_name.title()} misconfiguration"
        event["description"] = rule_documentation
        event["line"] = failed_entry.get('fromLine', 0) + 1
        result.append({
            "checker": checker,
            "extra": extra,
            "file": str(
                Path(
                    path_to_files
                ).joinpath(
                    failed_entry.get("machine", "clusterServices")
                ).joinpath(
                    failed_entry.get("service")
                ).joinpath(
                    failed_entry.get("config_file", {}).get("subPath", ".")
                ).joinpath(
                    failed_entry.get("config_file", {}).get("fileName")
                )
            ),
            "subcategory": sub_category,
            "properties": properties,
            "events": [event]
        })
    return result

def translate_result_json(
        path_to_files: Path,
        manifest: Dict,
        coguard_result: Dict
) -> Dict:
    """
    The main translation function. It consumes a parsed CoGuard result-json,
    and translates it into the format as described on the Coverity third party
    integration toolkit documentation page.

    The input parameters are:
     - The path to the files. We need to make sure it is an absolute path according to the
       documentation (see sources).
     - The manifest file as produced by CoGuard
     - The result JSON file as produced by CoGuard
    """
    # The header is a constant
    header = {
        "version" : 1,
        "format" : "cov-import-results input"
    }
    # Sources need to be a direct translation between the manifest file and
    sources = _get_sources_from_manifest(path_to_files, manifest)
    issues = _extract_issues_from_result(
        path_to_files,
        manifest,
        coguard_result
    )
    return {
        "header": header,
        "sources" : sources,
        "issues": issues
    }
