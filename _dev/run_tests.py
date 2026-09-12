"""Full bug test suite for Developer Job Application Tracker PRO v2.0"""
import sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
results = []

def test(name, fn):
    try:
        fn()
        results.append(('OK', name, ''))
    except Exception as e:
        results.append(('ERR', name, traceback.format_exc()))

# ── interview_prep ────────────────────────────────────────────────────────────
def t_interview():
    import interview_prep as ip
    cats = ip.get_categories()
    assert len(cats) == 4, f'Expected 4 cats, got {len(cats)}'
    for cat in cats:
        qs = ip.get_questions(cat)
        assert len(qs) > 0, f'No questions for {cat}'
        tip = ip.get_tip(cat)
        assert isinstance(tip, str)
        r = ip.analyze_answer(
            qs[0],
            'I led a team of 5 engineers at my previous company. The situation required us to '
            'deliver a critical feature in 3 weeks. I organized daily standups and we shipped '
            'on time, reducing bugs by 40%.',
            cat, 95.0
        )
        assert 1 <= r['score'] <= 5, f'Score out of range: {r["score"]}'
        assert 'feedback' in r and len(r['feedback']) > 0
        assert 'reaction' in r
        assert 'follow_up' in r
        assert 'word_count' in r
        assert 'summary' in r
    s = ip.get_summary()
    ip.save_score({'question':'q','category':cats[0],'score':4,'elapsed_s':90,
                   'session_id':'test_suite','date':'2026-01-01','word_count':100})
    s2 = ip.get_summary()
    assert s2['total_answers'] >= 1
    assert 0 < s2['overall_avg'] <= 5

test('interview_prep — all cats + scoring + save', t_interview)

# ── linkedin_message_generator ────────────────────────────────────────────────
def t_linkedin():
    import linkedin_message_generator as lmg
    types = lmg.get_message_types()
    assert len(types) == 5, f'Expected 5 types, got {len(types)}'
    for mt in types:
        msg = lmg.generate(
            message_type=mt,
            your_name='Alex Johnson',
            your_role='Senior Developer',
            your_field='backend development',
            years='5',
            first_name='Sarah',
            company='Google',
            target_role='Staff Engineer',
            their_field='backend development',
            highlight='building distributed systems',
            reason="Google's innovative work",
            shared_context='building distributed systems',
        )
        unfilled = [w for w in msg.split() if w.startswith('{') and w.endswith('}')]
        assert not unfilled, f'Unfilled placeholders in [{mt}]: {unfilled}'
        assert len(msg) > 20, f'Message too short for {mt}'
        assert lmg.get_char_limit(mt) > 0
        assert len(lmg.get_description(mt)) > 5

test('linkedin — all 5 templates, no placeholders', t_linkedin)

# ── salary_calculator ─────────────────────────────────────────────────────────
def t_salary():
    import salary_calculator as sc

    # Page 1: breakdown + takehome merge
    comp = sc.calculate_total_comp(120000, 10, 20000, 10000, 12000)
    assert comp['total_comp'] > 0
    th = sc.calculate_takehome(comp['total_cash'], 0.24)
    assert 'net_annual' in th and 'net_monthly' in th
    assert 'net_annual' not in comp, 'net_annual should NOT be in comp dict'
    merged = {**comp, **th}
    for k in ['base','bonus','equity_annual','signing_annual','benefits',
              'total_cash','total_comp','net_annual','net_monthly']:
        assert k in merged, f'Missing key after merge: {k}'

    # Page 2: negotiation strategy
    strat = sc.negotiation_strategy(100000, 120000, 90000,
                                    sc.get_levels()[1], sc.get_locations()[3])
    assert 'verdict' in strat
    assert 'counter_offer' in strat
    assert strat['counter_offer'] > 0

    # Page 3: compare offers with 3 companies (medals IndexError test)
    offers = sc.compare_offers([
        {'company':'A','base':90000,'bonus_pct':10,'equity_annual':5000,
         'signing_bonus':0,'benefits':12000,'tax_rate':0.24},
        {'company':'B','base':130000,'bonus_pct':15,'equity_annual':30000,
         'signing_bonus':0,'benefits':12000,'tax_rate':0.24},
        {'company':'C','base':110000,'bonus_pct':12,'equity_annual':15000,
         'signing_bonus':0,'benefits':12000,'tax_rate':0.24},
    ])
    assert offers[0]['rank'] == 1
    assert offers[0]['total_comp'] >= offers[1]['total_comp'] >= offers[2]['total_comp']
    medals = ['🥇','🥈','🥉']
    for r in offers:
        m = medals[r['rank']-1] if r['rank'] <= len(medals) else f"#{r['rank']}"
        assert m  # no IndexError

    # Edge: single offer
    single = sc.compare_offers([
        {'company':'Solo','base':100000,'bonus_pct':0,'equity_annual':0,
         'signing_bonus':0,'benefits':12000,'tax_rate':0.24}
    ])
    assert single[0]['rank'] == 1

test('salary_calculator — all 3 pages + edge cases', t_salary)

# ── streak_tracker ────────────────────────────────────────────────────────────
def t_streak():
    import streak_tracker as st

    data = st.get_data()
    assert 'daily_goal' in data
    assert 'weekly_goal' in data
    assert 'entries' in data

    res = st.log_applications(3, 'test note')
    assert 'today_count' in res
    assert 'streak' in res
    assert 'best_streak' in res
    assert 'message' in res
    assert 'total_apps' in res
    assert isinstance(res['today_count'], int)

    summary = st.get_weekly_summary()
    assert 'week_total' in summary
    assert 'weekly_goal' in summary
    assert 'daily_goal' in summary
    assert 'pct' in summary
    assert 'days_active' in summary
    assert 'days_hit_goal' in summary
    assert 'entries' in summary
    assert 'week_days' in summary
    assert 'streak' in summary
    assert 'best_streak' in summary
    assert 'total_apps' in summary
    assert 'tip' in summary
    assert len(summary['week_days']) == 7

    stats = st.get_all_time_stats()
    assert 'total_apps' in stats
    assert 'active_days' in stats
    assert 'best_day' in stats

    st.set_goals(7, 25)
    d2 = st.get_data()
    assert d2['daily_goal'] == 7
    assert d2['weekly_goal'] == 25
    st.set_goals(5, 20)  # restore

    # forward ref test: simulate save_goals calling refresh before it's defined
    _refresh_ref = [None]
    def save_goals_sim():
        if _refresh_ref[0]:
            _refresh_ref[0]()
    save_goals_sim()  # should not raise even when ref is None
    _refresh_ref[0] = lambda: None
    save_goals_sim()  # should not raise with ref set

test('streak_tracker — all functions + forward ref pattern', t_streak)

# ── cover_letter_generator ────────────────────────────────────────────────────
def t_cover():
    import cover_letter_generator as clg
    for tone in ['professional', 'enthusiastic', 'concise']:
        letter = clg.generate(
            company='Google', role='Senior Python Developer',
            jd_text='We need a Python developer with REST API, Docker, and team leadership skills.',
            your_name='Alex Johnson', years='5', field='backend development',
            tone=tone, extra_notes='I have AWS experience.', api_key=''
        )
        assert len(letter) > 100, f'Letter too short for tone={tone}'
        assert 'Google' in letter
        assert 'Alex Johnson' in letter
        unfilled = [w for w in letter.split() if w.startswith('{') and w.endswith('}')]
        assert not unfilled, f'Unfilled placeholders (tone={tone}): {unfilled}'

test('cover_letter_generator — all 3 tones, no placeholders', t_cover)

# ── ats_resume_checker ────────────────────────────────────────────────────────
def t_ats():
    import ats_resume_checker as ats
    import inspect
    src = inspect.getsource(ats)
    assert 'def ' in src  # has functions

test('ats_resume_checker — importable', t_ats)

# ── job_description_analyzer ─────────────────────────────────────────────────
def t_jda():
    import job_description_analyzer as jda
    import inspect
    src = inspect.getsource(jda)
    assert 'def ' in src

test('job_description_analyzer — importable', t_jda)

def t_sync_notion():
    import sync_notion as sn
    assert hasattr(sn, 'NotionSync')
    assert hasattr(sn, 'sync_to_notion')

test('sync_notion — importable and exposes expected API', t_sync_notion)

def t_package_builder():
    pkg_path = os.path.join(os.path.dirname(__file__), 'package_builder.py')
    src = open(pkg_path, encoding='utf-8').read()
    for required in ['settings.py', 'i18n.py', "os.path.join('_dev', 'sync_notion.py')", "os.path.join('_dev', 'test_formulas.py')"]:
        assert required in src, f'Missing package source mapping: {required}'

test('package_builder — includes required runtime/package files', t_package_builder)

# ── launcher.py ───────────────────────────────────────────────────────────────
def t_launcher():
    import ast
    code = open(os.path.join(os.path.dirname(__file__), '..', 'launcher.py'),
                encoding='utf-8').read()
    ast.parse(code)

    required_fns = [
        'build_home_tab', 'build_ats_tab', 'build_jd_tab', 'build_tools_tab',
        'build_email_tab', 'build_notion_tab', 'build_cover_letter_tab',
        'build_interview_tab', 'build_linkedin_tab', 'build_salary_tab',
        'build_streak_tab',
    ]
    for fn in required_fns:
        assert f'def {fn}(' in code, f'Missing: {fn}'

    # check no bare .get() on Text widgets (height>1 field helpers)
    # find all field() calls with height>=2
    import re
    text_vars = re.findall(r'(\w+)\s*=\s*field\([^)]*height\s*=\s*[2-9][^)]*\)', code)
    for var in text_vars:
        # check they use .get("1.0","end") not .get()
        bare = re.findall(rf'\b{var}\.get\(\)', code)
        assert not bare, f'Text widget "{var}" called with bare .get() — should be .get("1.0","end")'

    # check SIDEBAR_BG is defined
    assert 'SIDEBAR_BG' in code
    # check scrolledtext is imported
    assert 'scrolledtext' in code
    # check datetime is imported
    assert 'from datetime import datetime' in code

test('launcher.py — syntax, all builders, no widget .get() mismatches', t_launcher)

# ── Print results ─────────────────────────────────────────────────────────────
print()
ok  = [r for r in results if r[0] == 'OK']
err = [r for r in results if r[0] == 'ERR']

for r in ok:
    print(f'  PASS  {r[1]}')
if err:
    print()
for r in err:
    print(f'  FAIL  {r[1]}')
    print('         ' + r[2].replace('\n', '\n         '))

print()
print(f'Result: {len(ok)}/{len(results)} passed', '✓' if not err else '✗')
