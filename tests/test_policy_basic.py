from runtime.policy import PolicyConfig, pick_next_assignment


def test_policy_prefers_drills():
    catalog = [
        {"content_id":"lesson_caged_1","kind":"lesson","title":"CAGED 1"},
        {"content_id":"drill_alt_1","kind":"drill","title":"Alt 1"},
        {"content_id":"drill_alt_2","kind":"drill","title":"Alt 2"},
    ]
    items = pick_next_assignment(catalog, recent_sessions=[], cfg=PolicyConfig(max_items=2))
    assert items[0]["kind"] == "drill"
