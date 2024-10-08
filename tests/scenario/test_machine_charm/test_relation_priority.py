# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from cosl import GrafanaDashboard
from scenario import Context, PeerRelation, State, SubordinateRelation

import charm
from tests.scenario.test_machine_charm.helpers import set_run_out


def trigger(evt: str, state: State, vroot: Path = None, **kwargs):
    context = Context(
        charm_type=charm.GrafanaAgentMachineCharm,
        charm_root=vroot,
    )
    return context.run(event=evt, state=state, **kwargs)


@pytest.fixture
def mock_cfg_path(tmp_path):
    return tmp_path / "foo.yaml"


@pytest.fixture(autouse=True)
def patch_all(placeholder_cfg_path):
    with patch("grafana_agent.CONFIG_PATH", placeholder_cfg_path):
        yield


@patch("charm.subprocess.run")
def test_no_relations(mock_run, vroot, charm_config):
    def post_event(charm: charm.GrafanaAgentMachineCharm):
        assert not charm._cos.dashboards
        assert not charm._cos.logs_alerts
        assert not charm._cos.metrics_alerts
        assert not charm._cos.metrics_jobs
        assert not charm._cos.snap_log_endpoints

    set_run_out(mock_run, 0)
    trigger("start", State(config=charm_config), post_event=post_event, vroot=vroot)


@patch("charm.subprocess.run")
def test_juju_info_relation(mock_run, vroot, charm_config):
    def post_event(charm: charm.GrafanaAgentMachineCharm):
        assert not charm._cos.dashboards
        assert not charm._cos.logs_alerts
        assert not charm._cos.metrics_alerts
        assert not charm._cos.metrics_jobs
        assert not charm._cos.snap_log_endpoints

    set_run_out(mock_run, 0)
    trigger(
        "start",
        State(
            relations=[
                SubordinateRelation(
                    "juju-info", remote_unit_data={"config": json.dumps({"subordinate": True})}
                )
            ],
            config=charm_config,
        ),
        post_event=post_event,
        vroot=vroot,
    )


@patch("charm.subprocess.run")
def test_cos_machine_relation(mock_run, vroot, charm_config):
    def post_event(charm: charm.GrafanaAgentMachineCharm):
        assert charm._cos.dashboards
        assert charm._cos.snap_log_endpoints
        assert not charm._cos.logs_alerts
        assert not charm._cos.metrics_alerts
        assert charm._cos.metrics_jobs

    set_run_out(mock_run, 0)

    cos_agent_data = {
        "config": json.dumps(
            {
                "metrics_alert_rules": {},
                "log_alert_rules": {},
                "dashboards": [
                    "/Td6WFoAAATm1rRGAgAhARYAAAB0L+WjAQAmCnsKICAidGl0bGUiOiAi"
                    "Zm9vIiwKICAiYmFyIiA6ICJiYXoiCn0KAACkcc0YFt15xAABPyd8KlLdH7bzfQEAAAAABFla"
                ],
                "metrics_scrape_jobs": [
                    {"job_name": "mock-principal_0", "path": "/metrics", "port": "8080"}
                ],
                "log_slots": ["charmed-kafka:logs"],
            }
        )
    }

    peer_data = {
        "config": json.dumps(
            {
                "unit_name": "foo",
                "relation_id": "2",
                "relation_name": "peers",
                "metrics_alert_rules": {},
                "log_alert_rules": {},
                "dashboards": [GrafanaDashboard._serialize('{"very long": "dashboard"}')],
            }
        )
    }
    trigger(
        "start",
        State(
            relations=[
                SubordinateRelation(
                    "cos-agent",
                    remote_app_name="mock-principal",
                    remote_unit_data=cos_agent_data,
                ),
                PeerRelation("peers", peers_data={1: peer_data}),
            ],
            config=charm_config,
        ),
        post_event=post_event,
        vroot=vroot,
    )


@patch("charm.subprocess.run")
def test_both_relations(mock_run, vroot, charm_config):
    def post_event(charm: charm.GrafanaAgentMachineCharm):
        assert charm._cos.dashboards
        assert charm._cos.snap_log_endpoints
        assert not charm._cos.logs_alerts
        assert not charm._cos.metrics_alerts
        assert charm._cos.metrics_jobs

    set_run_out(mock_run, 0)

    cos_agent_data = {
        "config": json.dumps(
            {
                "metrics_alert_rules": {},
                "log_alert_rules": {},
                "dashboards": [
                    "/Td6WFoAAATm1rRGAgAhARYAAAB0L+WjAQAmCnsKICAidGl0bGUiOiAi"
                    "Zm9vIiwKICAiYmFyIiA6ICJiYXoiCn0KAACkcc0YFt15xAABPyd8KlLdH7bzfQEAAAAABFla"
                ],
                "metrics_scrape_jobs": [
                    {"job_name": "mock-principal_0", "path": "/metrics", "port": "8080"}
                ],
                "log_slots": ["charmed-kafka:logs"],
            }
        )
    }

    peer_data = {
        "config": json.dumps(
            {
                "unit_name": "foo",
                "relation_id": "2",
                "relation_name": "peers",
                "metrics_alert_rules": {},
                "log_alert_rules": {},
                "dashboards": [GrafanaDashboard._serialize('{"very long": "dashboard"}')],
            }
        )
    }

    context = Context(
        charm_type=charm.GrafanaAgentMachineCharm,
        charm_root=vroot,
    )
    state = State(
        relations=[
            SubordinateRelation(
                "cos-agent",
                remote_app_name="remote-cos-agent",
                remote_unit_data=cos_agent_data,
            ),
            SubordinateRelation("juju-info", remote_app_name="remote-juju-info"),
            PeerRelation("peers", peers_data={1: peer_data}),
        ],
        config=charm_config,
    )
    context.run(event="start", state=state, post_event=post_event)
