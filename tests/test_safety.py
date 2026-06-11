from huarun_app.services.safety import classify_question, should_refuse


def test_red_question_is_refused():
    label = classify_question("我胸痛还有呼吸困难，可以把药加量吗？")

    assert label == "red"
    assert should_refuse(label) is True


def test_side_effect_question_is_yellow():
    label = classify_question("吃完以后有点胃疼和头晕，这是副作用吗？")

    assert label == "yellow"
    assert should_refuse(label) is False


def test_packaging_question_is_green():
    label = classify_question("这个药盒上写的一日两次是什么意思？")

    assert label == "green"
    assert should_refuse(label) is False
