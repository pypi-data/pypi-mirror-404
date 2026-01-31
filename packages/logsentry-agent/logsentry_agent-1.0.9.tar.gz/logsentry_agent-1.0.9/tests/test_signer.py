from logsentry_agent.signer import canonical_string, compute_body_hash, sign_request


def test_signer_hmac_roundtrip():
    body = b"{}"
    body_hash = compute_body_hash(body)
    canonical = canonical_string("agent-id", "123", "nonce", body_hash)
    signature = sign_request("secret", "agent-id", "123", "nonce", body_hash)

    assert "agent-id" in canonical
    assert signature == sign_request("secret", "agent-id", "123", "nonce", body_hash)
