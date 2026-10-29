from phase0.metrics import cer, normalize, wer
from phase0.prepare import assign_clips, find_prompt_id
from phase0.prompts import load_prompts


def test_normalize_folds_hyphens_accents_and_punctuation():
    assert normalize("Ngicela u-set-e i-alarm ye-six o'clock!") == "ngicela usete ialarm yesix oclock"
    assert normalize("tse dintšhwa, Mmê") == "tse dintshwa mme"


def test_wer_and_cer():
    assert wer("Sawubona Malume", "sawubona malume.") == 0.0
    assert wer("a b c d", "a x c") == 0.5
    assert cer("abcd", "abce") == 0.25
    assert wer("", "anything") == 0.0


def test_find_prompt_id():
    assert find_prompt_id("zu05.m4a") == "zu05"
    assert find_prompt_id("New Recording TN12.m4a") == "tn12"
    assert find_prompt_id("zu123.m4a") is None
    assert find_prompt_id("Recording 3.m4a") is None


def test_prompts_are_well_formed():
    prompts = load_prompts()
    assert len(prompts) > 50
    for pid, p in prompts.items():
        assert pid.startswith(p.lang)
        assert p.type in {"pure", "cs", "free"}


def test_assign_clips_by_name_and_by_order(tmp_path):
    prompts = load_prompts()
    (tmp_path / "zu05.m4a").touch()
    (tmp_path / "random.m4a").touch()
    ts_dir = tmp_path / "ts"
    ts_dir.mkdir()
    n_ts = sum(p.lang == "ts" for p in prompts.values())
    for i in range(n_ts):
        (ts_dir / f"PTT-{i:03d}.opus").touch()

    pairs, problems = assign_clips(tmp_path, prompts)
    by_file = {path.name: pid for path, pid in pairs}
    assert by_file.pop("zu05.m4a") == "zu05"
    assert list(by_file.values()) == [pid for pid, p in prompts.items() if p.lang == "ts"]
    assert len(problems) == 1 and "random.m4a" in problems[0]


def test_assign_clips_rejects_count_mismatch(tmp_path):
    (tmp_path / "zu").mkdir()
    (tmp_path / "zu" / "a.ogg").touch()
    pairs, problems = assign_clips(tmp_path, load_prompts())
    assert pairs == [] and len(problems) == 1
