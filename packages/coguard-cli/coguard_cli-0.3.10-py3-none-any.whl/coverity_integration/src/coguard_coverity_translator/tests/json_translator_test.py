"""
Unit tests for the Json translator module.
"""

import unittest
import unittest.mock
from pathlib import Path

from coguard_coverity_translator import json_translator

class TestCommonFunctions(unittest.TestCase):
    """
    The class to test the functions in coguard_cli.__init__
    """

    def test_translate_result_json(self):
        """
        Basic test for `translate_result_json` where we mock all the
        other functions.
        """
        with unittest.mock.patch(
                'coguard_coverity_translator.json_translator._get_sources_from_manifest',
                new_callable=lambda: lambda x, y: []), \
                unittest.mock.patch(
                    'coguard_coverity_translator.json_translator._extract_issues_from_result',
                    new_callable=lambda: lambda x, y, z: []
                ):
            path_to_files = Path("/")
            manifest = {}
            coguard_result = {}
            result = json_translator.translate_result_json(
                path_to_files,
                manifest,
                coguard_result
            )
            expected = {
                "header": {
                    "version" : 1,
                    "format" : "cov-import-results input"
                },
                "sources": [],
                "issues": []
            }
            self.assertDictEqual(result, expected)

    def test_get_sources_from_manifest_nothing_present(self):
        """
        Simple test Where the manifest is empty
        """
        path_to_files = Path("/tmp/bar")
        manifest = {}
        result = json_translator._get_sources_from_manifest(
            path_to_files,
            manifest
        )
        self.assertListEqual(result, [])

    def test_get_sources_from_manifest_machine_only(self):
        """
        Simple test Where the manifest is not empty
        """
        path_to_files = Path("/tmp/bar")
        manifest = {
            "machines": {
                "us-jfk-001": {
                    "services": {
                        "Kerberos": {
                            "configFileList": [
                                {
                                    "fileName": "krb5.conf",
                                    "defaultFileName": "krb5.conf",
                                    "subPath": ".",
                                    "configFileType": "krb"
                                },
                                {
                                    "fileName": "kdc.conf",
                                    "defaultFileName": "kdc.conf",
                                    "subPath": ".",
                                    "configFileType": "krb"
                                }
                            ]
                        }
                    }
                }
            }
        }
        result = json_translator._get_sources_from_manifest(
            path_to_files,
            manifest
        )
        self.assertListEqual(result, [
            {
                "file": "/tmp/bar/us-jfk-001/Kerberos/krb5.conf",
                "language": "krb"
            },
            {
                "file": "/tmp/bar/us-jfk-001/Kerberos/kdc.conf",
                "language": "krb"
            }
        ])

    def test_get_sources_from_manifest_with_cluster_services(self):
        """
        Simple test Where the manifest is not empty
        """
        path_to_files = Path("/tmp/bar")
        manifest = {
            "clusterServices": {
                "terraform": {
                    "version": "1.0",
                    "serviceName": "terraform",
                    "configFileList": [
                        {
                            "fileName": "versions.tf",
                            "defaultFileName": "main.tf",
                            "subPath": "./",
                            "configFileType": "hcl2"
                        }
                    ],
                    "complimentaryFileList": []
                }
            },
            "machines": {
                "us-jfk-001": {
                    "services": {
                        "Kerberos": {
                            "configFileList": [
                                {
                                    "fileName": "krb5.conf",
                                    "defaultFileName": "krb5.conf",
                                    "subPath": ".",
                                    "configFileType": "krb"
                                },
                                {
                                    "fileName": "kdc.conf",
                                    "defaultFileName": "kdc.conf",
                                    "subPath": ".",
                                    "configFileType": "krb"
                                }
                            ]
                        }
                    }
                }
            }
        }
        result = json_translator._get_sources_from_manifest(
            path_to_files,
            manifest
        )
        self.assertListEqual(result, [
            {
                "file": "/tmp/bar/us-jfk-001/Kerberos/krb5.conf",
                "language": "krb"
            },
            {
                "file": "/tmp/bar/us-jfk-001/Kerberos/kdc.conf",
                "language": "krb"
            },
            {
                "file": "/tmp/bar/clusterServices/terraform/versions.tf",
                "language": "hcl2"
            }
        ])

    def test_extract_issues_from_result_empty(self):
        """
        Simple test with empty result list
        """
        coguard_result = {"failed": []}
        path_to_files = "/tmp"
        manifest = {}
        result = json_translator._extract_issues_from_result(
            path_to_files,
            manifest,
            coguard_result
        )
        self.assertListEqual(result, [])


    def test_extract_issues_from_result_machines(self):
        """
        Simple test with machines in the result.
        """
        self.maxDiff = None
        coguard_result = {"failed": [
            {
                "rule": {
                    "name": "kerberos_default_tgs_enctypes",
                    "severity": 3,
                    "documentation": {
                        "documentation": "One should avoid the legacy TGS enctypes setting...",
                        "remediation": "`libdefaults` has a key called \"default_tgs_enctypes\"...",
                        "sources": [
                            "https://web.mit.edu/kerberos/krb5-1.12/doc/admin/"
                        ]
                    }
                },
                "config_file": {
                    "fileName": "krb5.conf",
                    "subPath": ".",
                    "configFileType": "krb"
                },
                "machine": "us-jfk-001",
                "service": "Kerberos"
            }
        ]}
        path_to_files = "/tmp"
        manifest = {
            "machines": {
                "us-jfk-001": {
                    "services": {
                        "Kerberos": {
                            "serviceName": "kerberos",
                            "configFileList": [
                                {
                                    "fileName": "krb5.conf",
                                    "defaultFileName": "krb5.conf",
                                    "subPath": ".",
                                    "configFileType": "krb"
                                },
                                {
                                    "fileName": "kdc.conf",
                                    "defaultFileName": "kdc.conf",
                                    "subPath": ".",
                                    "configFileType": "krb"
                                }
                            ]
                        }
                    }
                }
            }
        }
        expected_result = {
            'checker': 'CG.KERBEROS_DEFAULT_TGS_ENCTYPES',
            'extra': 'kerberos_default_tgs_enctypes',
            'file': '/tmp/us-jfk-001/Kerberos/krb5.conf',
            'subcategory': 'none',
            'properties': {
                'category': 'misconfiguration',
                'type': 'Kerberos misconfiguration',
                'localEffect': 'One should avoid the legacy TGS enctypes setting...',
                'longDescription': (
                    'One should avoid the legacy TGS enctypes setting...\n\nRemediation: '
                    '`libdefaults` has a key called "default_tgs_enctypes"...\n\nSources:'
                    '\nhttps://web.mit.edu/kerberos/krb5-1.12/doc/admin/'
                ),
                'impact': 'Medium',
                'issueKind': 'QUALITY,SECURITY'
            },
            'events': [
                {
                    'tag': 'Kerberos misconfiguration',
                    'description': 'One should avoid the legacy TGS enctypes setting...',
                    'line': 1
                }
            ]
        }
        result = json_translator._extract_issues_from_result(
            path_to_files,
            manifest,
            coguard_result
        )
        self.assertListEqual(result, [expected_result])
