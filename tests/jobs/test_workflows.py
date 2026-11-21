from meritum_core.jobs.contracts import CONTRACT_VERSION, PING, WORKFLOWS, PingInput


def test_workflow_names_are_unique() -> None:
    names = [spec.name for spec in WORKFLOWS]
    assert len(names) == len(set(names))


def test_ping_payload_is_plain_json_with_contract_version() -> None:
    payload = PING.input(message="hej").model_dump(mode="json")
    assert payload == {"contract_version": CONTRACT_VERSION, "message": "hej"}
    assert PingInput.model_validate(payload).message == "hej"
