from sim.protocol import Message, MessageBus


def test_to_dict_renames_from():
    d = Message("umbra", "veridia", "dm", "hi").to_dict()
    assert d == {"from": "umbra", "to": "veridia", "channel": "dm",
                 "text": "hi", "verdict": None}


def test_visibility_rules():
    bus = MessageBus()
    bus.post(Message("veridia", "umbra", "public", "I will share", verdict="truthful"))
    bus.post(Message("umbra", "veridia", "dm", "secret plan"))
    # public visible to a third observer; dm not
    assert len(bus.visible_to("observer")) == 1
    # dm visible to its participants
    assert len(bus.visible_to("veridia")) == 2
    assert len(bus.visible_to("umbra")) == 2
