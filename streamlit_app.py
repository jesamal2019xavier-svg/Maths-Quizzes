import streamlit as st
import random
import math
import time

# --------------------------------
# Global settings
# --------------------------------

VARS = ["x", "y", "z"]          # variables in order
MIN_SECONDS_PER_QUESTION = 5    # teacher-set minimum


# --------------------------------
# Page config and custom CSS
# --------------------------------

st.set_page_config(page_title="Factorising Quiz", layout="wide")

st.markdown("""
<style>
.big-title {
    font-size: 2rem !important;
    font-weight: 700;
}
.big-question {
    font-size: 1.3rem !important;
    font-weight: 600;
    margin-top: 0.5rem;
}
.big-input-label {
    font-size: 1.05rem !important;
}
.timer-box {
    font-size: 1.3rem !important;
    font-weight: 600;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    background-color: #f0f4ff;
    display: inline-block;
    margin-bottom: 1rem;
}
.result-row-correct {
    background-color: #e6f6e6;
    padding: 0.4rem;
    border-radius: 6px;
}
.result-row-wrong {
    background-color: #fdeaea;
    padding: 0.4rem;
    border-radius: 6px;
}
.certificate-box {
    border: 4px solid gold;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    background: #fff8dc;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------
# Superscript conversion helpers
# --------------------------------

def to_superscript_digits(s: str) -> str:
    superscripts = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    return s.translate(superscripts)

def to_superscript_int(n: int) -> str:
    return to_superscript_digits(str(n))

def convert_carets_to_superscript(expr: str) -> str:
    """Convert ^ followed by digits into superscript digits."""
    if expr is None:
        return ""
    result = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]
        if ch == "^" and i + 1 < n and expr[i + 1].isdigit():
            i += 1
            digits = []
            while i < n and expr[i].isdigit():
                digits.append(expr[i])
                i += 1
            result.append(to_superscript_digits("".join(digits)))
        else:
            result.append(ch)
            i += 1

    return "".join(result)


# --------------------------------
# Monomial / expression formatting
# --------------------------------

def format_monomial(coeff: int, powers: dict, use_vars, use_plus_sign: bool) -> str:
    """Format a monomial like coeff * x^a * y^b * z^c."""
    if coeff == 0:
        return ""

    sign = ""
    abs_coeff = abs(coeff)

    if use_plus_sign:
        sign = " + " if coeff > 0 else " - "
    else:
        if coeff < 0:
            sign = "-"

    var_part = ""
    for v in use_vars:
        p = powers.get(v, 0)
        if p == 0:
            continue
        elif p == 1:
            var_part += v
        else:
            var_part += f"{v}{to_superscript_int(p)}"

    if var_part == "":
        term = f"{abs_coeff}"
    else:
        if abs_coeff == 1:
            coeff_str = ""
        else:
            coeff_str = f"{abs_coeff}"
        term = f"{coeff_str}{var_part}"

    return f"{sign}{term}"

def sorting_key(coeff: int, powers: dict, use_vars):
    """Sorting key for descending lexicographic order by variables."""
    return tuple(-powers.get(v, 0) for v in use_vars)

def format_expression(terms, use_vars):
    """Format an expression given as list of (coeff, powers_dict) pairs."""
    non_zero_terms = [(c, p) for c, p in terms if c != 0]
    if not non_zero_terms:
        return "0"

    non_zero_terms.sort(key=lambda t: sorting_key(t[0], t[1], use_vars))

    pieces = []
    for idx, (c, pows) in enumerate(non_zero_terms):
        pieces.append(format_monomial(c, pows, use_vars, use_plus_sign=(idx != 0)))
    return "".join(pieces)

def format_factorised(outer_coeff: int, outer_powers: dict, inside_terms, use_vars):
    outer = format_monomial(outer_coeff, outer_powers, use_vars, use_plus_sign=False)
    inside = format_expression(inside_terms, use_vars)
    return f"{outer}({inside})"


# --------------------------------
# Generator: inside irreducible
# --------------------------------

def generate_irreducible_inside(num_terms: int, use_vars):
    """
    Generate inside expression with:
      - num_terms = 2 or 3
      - gcd of coefficients = 1
      - for each variable in use_vars, at least one term has power 0
    """
    while True:
        coeffs = []
        powers_list = []

        for _ in range(num_terms):
            c = 0
            while c == 0:
                c = random.randint(-9, 9)
            coeffs.append(c)

            pows = {}
            for v in use_vars:
                pows[v] = random.randint(0, 4)
            powers_list.append(pows)

        # gcd of coefficients must be 1
        g = abs(coeffs[0])
        for c in coeffs[1:]:
            g = math.gcd(g, abs(c))
        if g != 1:
            continue

        # for each variable, at least one term has power 0
        ok_vars = True
        for v in use_vars:
            min_power_v = min(p[v] for p in powers_list)
            if min_power_v != 0:
                ok_vars = False
                break
        if not ok_vars:
            continue

        inside_terms = []
        for c, pows in zip(coeffs, powers_list):
            inside_terms.append((c, pows))

        return inside_terms


def generate_question_answer():
    """
    Generate one question/answer pair, applying the sign rule:

    - If leading expanded term is negative:
      outer factor negative, inside starts positive (signs flipped).
    - If leading term is positive:
      outer factor positive, no flipping.
    """
    num_vars = random.randint(1, 3)
    use_vars = VARS[:num_vars]

    # Start with a positive outer coefficient
    outer_coeff = random.randint(2, 9)

    # Outer powers, ensure at least one positive
    outer_powers = {}
    positive_power_exists = False
    for v in use_vars:
        p = random.randint(0, 3)
        if p > 0:
            positive_power_exists = True
        outer_powers[v] = p

    if not positive_power_exists:
        v_choice = random.choice(use_vars)
        outer_powers[v_choice] = random.randint(1, 3)

    # Generate irreducible inside expression
    num_terms = random.choice([2, 3])
    inside_terms = generate_irreducible_inside(num_terms, use_vars)

    # Expand
    expanded_terms = []
    for c, pows in inside_terms:
        new_coeff = outer_coeff * c
        new_pows = {}
        for v in use_vars:
            new_pows[v] = outer_powers.get(v, 0) + pows.get(v, 0)
        expanded_terms.append((new_coeff, new_pows))

    # Sort expanded terms by descending powers
    expanded_terms.sort(key=lambda t: sorting_key(t[0], t[1], use_vars))

    # Apply Option A sign rule:
    # If leading expanded term is negative:
    # - outer factor negative
    # - inside starts positive (flip all coefficients once)
    if expanded_terms[0][0] < 0:
        # Flip outer factor
        outer_coeff *= -1

        # Flip inside terms
        inside_terms = [(-c, pows) for (c, pows) in inside_terms]

        # Flip expanded terms
        expanded_terms = [(-c, pows) for (c, pows) in expanded_terms]

    # At this point, expanded_terms is consistent with (outer_coeff, outer_powers, inside_terms)
    question_str = format_expression(expanded_terms, use_vars)
    answer_str = format_factorised(outer_coeff, outer_powers, inside_terms, use_vars)

    return question_str, answer_str


# --------------------------------
# Normalisation for marking
# --------------------------------

def normalise(expr: str) -> str:
    if expr is None:
        return ""
    expr = convert_carets_to_superscript(expr)
    expr = expr.replace(" ", "").replace("(", "").replace(")", "")
    return expr


# --------------------------------
# Session state initialisation
# --------------------------------

if "questions" not in st.session_state:
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.finished = False
    st.session_state.quiz_start_time = None
    st.session_state.total_time = None
    st.session_state.time_per_question = None
    st.session_state.timed_out = False

if "score_history" not in st.session_state:
    st.session_state.score_history = []


# --------------------------------
# Utility: capture all answers before timeout/submit
# --------------------------------

def save_all_answers():
    for i in range(10):
        key = f"answer_{i}"
        if key not in st.session_state:
            st.session_state[key] = ""


# --------------------------------
# Title and intro
# --------------------------------

st.markdown("<div class='big-title'>Factorising Practice – Timed 10 Question Quiz</div>", unsafe_allow_html=True)
st.write(
    "Each quiz has 10 questions. You choose a time per question (at least "
    f"{MIN_SECONDS_PER_QUESTION} seconds), and the total time is `10 × time per question`."
)
st.write(
    "You can type powers using `^`, for example `3x^2y^3(2x^3+5xy-2)` will display as `3x²y³(2x³+5xy-2)`."
)


# --------------------------------
# Time per question selector (before quiz starts)
# --------------------------------

if st.session_state.quiz_start_time is None and not st.session_state.finished:
    st.write("### Timing settings")

    tpq = st.number_input(
        f"Time per question (seconds, minimum {MIN_SECONDS_PER_QUESTION}):",
        min_value=MIN_SECONDS_PER_QUESTION,
        max_value=60,
        value=10,
        step=1,
    )

    if st.button("Start quiz"):
        st.session_state.time_per_question = max(tpq, MIN_SECONDS_PER_QUESTION)
        st.session_state.total_time = 10 * st.session_state.time_per_question
        st.session_state.quiz_start_time = time.time()

        st.session_state.questions = []
        st.session_state.answers = []
        st.session_state.finished = False
        st.session_state.timed_out = False

        for _ in range(10):
            q, a = generate_question_answer()
            st.session_state.questions.append(q)
            st.session_state.answers.append(a)

        st.rerun()

    if st.session_state.score_history:
        st.write("### Score history (this session)")
        for idx, entry in enumerate(st.session_state.score_history, start=1):
            st.write(f"Attempt {idx}: {entry['score']}% in {entry['time']} seconds")

    st.stop()


# --------------------------------
# Timing helpers
# --------------------------------

def get_time_info():
    if st.session_state.quiz_start_time is None or st.session_state.total_time is None:
        return None, None, None

    elapsed = time.time() - st.session_state.quiz_start_time
    remaining = st.session_state.total_time - elapsed
    if remaining < 0:
        remaining = 0
    return elapsed, remaining, st.session_state.total_time

elapsed, remaining, total_allowed = get_time_info()

# Handle timeout
if not st.session_state.finished and remaining is not None and remaining <= 0:
    save_all_answers()
    st.session_state.finished = True
    st.session_state.timed_out = True
    st.rerun()


# --------------------------------
# Results screen
# --------------------------------

if st.session_state.finished:
    elapsed, remaining, total_allowed = get_time_info()
    if elapsed is None:
        elapsed = 0
        total_allowed = 0

    st.write("## Quiz complete")

    # Header row for the table
    header_cols = st.columns([3, 2, 2])
    header_cols[0].markdown("**Question**")
    header_cols[1].markdown("**Your answer**")
    header_cols[2].markdown("**Correct answer**")

    score = 0

    for i in range(10):
        user_raw = st.session_state.get(f"answer_{i}", "")
        user = normalise(user_raw)
        correct = normalise(st.session_state.answers[i])

        row_cols = st.columns([3, 2, 2])

        is_correct = (user == correct and user != "")

        css_class = "result-row-correct" if is_correct else "result-row-wrong"
        display_user = user_raw if user_raw else "(no answer)"

        # Question
        row_cols[0].markdown(
            f"<div class='{css_class}'><strong>Q{i+1}:</strong> {st.session_state.questions[i]}</div>",
            unsafe_allow_html=True
        )
        # Your answer
        row_cols[1].markdown(
            f"<div class='{css_class}'>{display_user}</div>",
            unsafe_allow_html=True
        )
        # Correct answer
        row_cols[2].markdown(
            f"<div class='{css_class}'>{st.session_state.answers[i]}</div>",
            unsafe_allow_html=True
        )

        if is_correct:
            score += 1

    percentage = round((score / 10) * 100)
    elapsed_rounded = int(min(elapsed, total_allowed)) if total_allowed else int(elapsed)

    st.write(f"### Score: **{percentage}%**")
    st.write(f"Time allowed: **{int(total_allowed)} seconds**")
    st.write(f"Time used: **{elapsed_rounded} seconds**")

    st.session_state.score_history.append({
        "score": percentage,
        "time": elapsed_rounded
    })

    if percentage == 100:
        st.markdown(
            "<div class='certificate-box'>"
            "<h2>Certificate of Achievement</h2>"
            "<p style='font-size:1.3rem;'>This certifies that</p>"
            "<h1 style='color:#333;'>Student</h1>"
            "<p style='font-size:1.2rem;'>has achieved a perfect score of "
            "<strong>100%</strong></p>"
            "<p style='font-size:1.1rem;'>in the Factorising Quiz</p>"
            "</div>",
            unsafe_allow_html=True
        )

    st.write("### Score history (this session)")
    for idx, entry in enumerate(st.session_state.score_history, start=1):
        st.write(f"- Attempt {idx}: {entry['score']}% in {entry['time']} seconds")

    if st.button("Restart quiz"):
        st.session_state.questions = []
        st.session_state.answers = []
        st.session_state.finished = False
        st.session_state.quiz_start_time = None
        st.session_state.total_time = None
        st.session_state.time_per_question = None
        st.session_state.timed_out = False
        for i in range(10):
            key = f"answer_{i}"
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.stop()


# --------------------------------
# Question screen (timed)
# --------------------------------

if elapsed is not None and total_allowed is not None:
    remaining_int = int(remaining)
    minutes = remaining_int // 60
    seconds = remaining_int % 60
    st.markdown(
        f"<div class='timer-box'>Time left: {minutes} min {seconds} sec</div>",
        unsafe_allow_html=True
    )

st.write("### Answer all questions before the time runs out, then press Submit all.")

for i in range(10):
    st.markdown(
        f"<div class='big-question'>Q{i+1}: {st.session_state.questions[i]}</div>",
        unsafe_allow_html=True
    )

    raw = st.session_state.get(f"answer_{i}", "")
    converted = convert_carets_to_superscript(raw)

    if converted != raw:
        st.session_state[f"answer_{i}"] = converted

    st.text_input(
        f"Your answer for Q{i+1}:",
        key=f"answer_{i}",
    )

if st.button("Submit all"):
    save_all_answers()
    st.session_state.finished = True
    st.rerun()