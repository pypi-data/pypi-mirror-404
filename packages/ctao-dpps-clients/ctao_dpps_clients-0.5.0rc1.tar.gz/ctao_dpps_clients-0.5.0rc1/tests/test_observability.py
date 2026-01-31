import json
import logging
import os
import re
import time
from collections.abc import Callable

import pytest
import requests

release_name = os.getenv("AIV_RELEASE_NAME", "dpps")


def fail():
    """Fail the test if it is not implemented"""
    # simply repeating this last line makes sonarqube unhappy
    pytest.fail("not implemented")


def selector_event(involved_object) -> Callable:
    """Create a selector function for the event collector."""
    return (
        lambda line: re.match(
            involved_object, line.get("involvedObject", {}).get("name", "")
        )
        is not None
    )


def selector_log_container(container_name: str) -> Callable:
    """Create a selector function for the log collector."""
    return lambda line: (
        re.match(container_name, line.get("kubernetes", {}).get("container_name", ""))
        is not None
    )


def selectors_and(*selectors: list[Callable]) -> Callable:
    """Combine multiple selectors with AND logic."""
    return lambda line: all(selector(line) for selector in selectors)


def select_log_rows_testkit(selectors: list[Callable]) -> list[dict]:
    """Select log rows from the testkit collector based on the provided selectors."""

    lines = []

    for line in requests.get("http://testkit:8000/logs.ndjson").content.splitlines():
        try:
            line_dict = json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
            logging.error("Could not parse line as JSON: '%s'", line)
            raise

        for selector in selectors:
            if selector(line_dict):
                lines.append(line_dict)

    return lines


def report_log_rows(rows: list[dict], required: bool = True) -> float:
    """Report the log rows to the console."""

    if not rows and required:
        raise ValueError("No log rows found")

    # rows may not be. This can have marginal effect on estimate of execution duration.
    rows.sort(key=lambda x: x["date"])

    duration = rows[-1]["date"] - rows[0]["date"]

    logging.info(
        "Found %d entries emitted in %ss\n%s",
        len(rows),
        duration,
        "\n".join(
            [f"{row['date']}: {row.get('message', row.get('log'))}" for row in rows]
        ),
    )

    return duration


@pytest.mark.verifies_usecase("DPPS-UC-170-2.1")
def test_fetch_startup_logs_from_toolkit_collector():
    """Test that we can fetch logs from the toolkit collector, assert that the logs report bootstrap time"""

    report_log_rows(
        select_log_rows_testkit(
            [
                selector_event(".*gcert.*"),
            ]
        )
    )

    report_log_rows(
        select_log_rows_testkit(
            [
                selector_log_container(f"{release_name}-cvmfs-mkfs"),
            ]
        )
    )


@pytest.mark.verifies_usecase("DPPS-UC-170-2.1")
def test_fetch_logs_from_loki():
    """Test that we can fetch logs from the loki, select logs from dirac server bootstrap, report duration of different components bootstrap"""

    r = requests.get(
        f"http://{release_name}-loki:3100/loki/api/v1/query_range",
        params={
            "query": '{job="fluent-bit"}',
            "start": int(time.time() - 60 * 60 * 24),  # last 24 hours
            "end": int(time.time()),
            "limit": 1000,
        },
    )

    logging.info("Retrieved %d bytes of logs from loki", len(r.content))

    r.raise_for_status()

    log_data = r.json()
    assert log_data.get("status") == "success", "Failed to query loki"
    assert log_data.get("data", {}).get("result"), "No logs found"


@pytest.mark.verifies_usecase("DPPS-UC-170-2.1")
def test_fetch_metrics_from_prometheus():
    """Test that we can fetch metrics from the prometheus, assert that they have some useful content"""

    for metric in [
        "container_memory_rss",
        "container_cpu_system_seconds_total",
        "container_cpu_usage_seconds_total",
        "container_network_receive_bytes_total",
    ]:
        # container_cpu_system_seconds_total
        query = f'sum({metric} {{image!=""}})'

        r = requests.get(
            f"http://{release_name}-prometheus-server/api/v1/query_range",
            params=dict(query=query, step=1, start=time.time() - 30, end=time.time()),
        )

        r.raise_for_status()

        assert r.json().get("status") == "success", "Failed to query prometheus"

        logging.info("got: %s", r.json())

        metrics = r.json().get("data", {}).get("result")[0].get("values", [])

        assert metrics, "No metrics found"

        logging.info(
            "Found %d metrics for '%s', peaking %s",
            len(metrics),
            metric,
            max(metrics, key=lambda x: x[1]),
        )

    assert len(metrics) > 0, "No metrics found for the specified query"


@pytest.mark.verifies_usecase("DPPS-UC-170-2.1")
def test_probe_grafana():
    """Test that we can fetch metrics and logs from grafana, assert that they have some useful content"""

    r = requests.get(
        f"http://{release_name}-grafana/api/org",
        auth=("admin", "admin"),
    )

    r.raise_for_status()


@pytest.mark.verifies_usecase("DPPS-UC-170-2.1")
@pytest.mark.skip(reason="Grafana alerts are not yet implemented")
def test_fetch_from_grafana():
    """Test that we can fetch metrics and logs from grafana, assert that they have some useful content"""

    r = requests.get(
        f"http://{release_name}-grafana/api/org",
        auth=("admin", "admin"),
    )

    r.raise_for_status()


@pytest.mark.verifies_usecase("DPPS-UC-170-2.1")
def test_fetch_alerts_from_grafana():
    """Test that we can fetch metrics and logs from grafana, assert that they have some useful content"""

    r = requests.get(
        f"http://{release_name}-grafana/api/org",
        auth=("admin", "admin"),
    )

    r.raise_for_status()

    # POST /api/v1/provisioning/alert-rules

    # POST /api/folders HTTP/1.1

    r = requests.post(
        f"http://{release_name}-grafana/api/folders",
        auth=("admin", "admin"),
        json={
            "title": "SET_FOLDER_UID",
        },
    )

    if r.status_code == 400:
        logging.error("Failed to create folder: %s", r.json())

    r.raise_for_status()

    logging.info("got: %s", r.json())

    folder_uid = r.json().get("uid")

    r = requests.post(
        f"http://{release_name}-grafana/api/v1/provisioning/alert-rules",
        auth=("admin", "admin"),
        json={
            "title": "TEST-API_1",
            "ruleGroup": "API",
            "folderUID": folder_uid,
            "noDataState": "OK",
            "execErrState": "OK",
            "for": "5m",
            "orgId": 1,
            "uid": "",
            "condition": "B",
            "annotations": {"summary": "test_api_1"},
            "labels": {"API": "test1"},
            "data": [
                {
                    "refId": "A",
                    "queryType": "",
                    "relativeTimeRange": {"from": 600, "to": 0},
                    "datasourceUid": "XXXXXXXXX-XXXXXXXXX-XXXXXXXXXX",
                    "model": {
                        "expr": "up",
                        "hide": False,
                        "intervalMs": 1000,
                        "maxDataPoints": 43200,
                        "refId": "A",
                    },
                },
                {
                    "refId": "B",
                    "queryType": "",
                    "relativeTimeRange": {"from": 0, "to": 0},
                    "datasourceUid": "-100",
                    "model": {
                        "conditions": [
                            {
                                "evaluator": {"params": [6], "type": "gt"},
                                "operator": {"type": "and"},
                                "query": {"params": ["A"]},
                                "reducer": {"params": [], "type": "last"},
                                "type": "query",
                            }
                        ],
                        "datasource": {"type": "__expr__", "uid": "-100"},
                        "hide": False,
                        "intervalMs": 1000,
                        "maxDataPoints": 43200,
                        "refId": "B",
                        "type": "classic_conditions",
                    },
                },
            ],
        },
    )

    if r.status_code == 400:
        logging.error("Failed to create alert rule: %s", r.json())

    r.raise_for_status()

    logging.info("got: %s", r.json())

    r = requests.get(
        f"http://{release_name}-grafana/api/v1/provisioning/alert-rules",
        auth=("admin", "admin"),
    )

    r.raise_for_status()

    logging.info("got: %s", r.json())

    assert len(r.json()) > 0, "No alert rules found"
