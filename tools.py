"""
tools.py  (server side)

The same GPA/CGPA tools from Assignment 2, but as PLAIN Python functions -
no LangChain @tool decorator. server.py hands each one to FastMCP, which
reads the type hints + docstring and publishes them over MCP (tools/list),
exactly the way @tool used to describe them to the model.

Return types are `float | str` because every tool returns an
"Error: ..." string on bad input instead of raising, and MCP validates the
result against the declared output type.
"""

from __future__ import annotations

# Ordered highest-to-lowest; each entry is (minimum_marks, grade_label, points)
_GRADE_BANDS = [
    (85, "A", 4.0),
    (80, "A-", 3.7),
    (75, "B+", 3.3),
    (70, "B", 3.0),
    (65, "B-", 2.7),
    (61, "C+", 2.3),
    (58, "C", 2.0),
    (55, "C-", 1.7),
    (50, "D", 1.0),
    (0, "F", 0.0),
]

# ---------------------------------------------------------------------------
# 5.2 Scheme of studies - BS Computer Science
# ---------------------------------------------------------------------------
# Each entry: (course_code, course_name, credit_hours)
# MD-001 / MD-002 (Math Deficiency) are deliberately absent: they are
# non-credit pass/fail and never count towards GPA.
COURSES: dict[int, list[tuple[str, str, float]]] = {
    1: [
        ("MS-251", "Probability & Statistics", 3.0),
        ("GE-160", "Applications of ICT", 3.0),
        ("GE-169", "Applied Physics", 3.0),
        ("GE-167", "Discrete Structures", 3.0),
        ("HQ-001", "Quran Translation - I", 0.5),
        ("GE-190", "Functional English", 3.0),
    ],
    2: [
        ("CC-112", "Programming Fundamentals", 3.0),
        ("CC-112-L", "Programming Fundamentals Lab", 1.0),
        ("CC-110", "Digital Logic Design", 2.0),
        ("CC-110-L", "Digital Logic Design Lab", 1.0),
        ("MS-252", "Linear Algebra", 3.0),
        ("GE-191", "Expository Writing", 3.0),
        ("GE-163", "Islamic Studies", 2.0),
        ("HQ-002", "Quran Translation - II", 0.5),
    ],
    3: [
        ("CC-211", "Object Oriented Programming", 3.0),
        ("CC-211-L", "Object Oriented Programming Lab", 1.0),
        ("CC-215", "Database Systems", 3.0),
        ("CC-215-L", "Database Systems Lab", 1.0),
        ("CC-210", "Computer Organization & Assembly Language", 3.0),
        ("GE-162", "Calculus & Analytical Geometry", 3.0),
        ("GE-192", "Introduction to Management", 2.0),
        ("HQ-003", "Quran Translation - III", 0.5),
    ],
    4: [
        ("CC-213", "Data Structures", 3.0),
        ("CC-213-L", "Data Structures Lab", 1.0),
        ("CC-312", "Information Security", 3.0),
        ("CC-214", "Computer Networks", 3.0),
        ("CC-212", "Software Engineering", 3.0),
        ("DC-220", "Advanced Database Management Systems", 3.0),
        ("HQ-004", "Quran Translation - IV", 0.5),
    ],
    5: [
        ("CC-313", "Analysis of Algorithms", 3.0),
        ("CC-310", "Artificial Intelligence", 3.0),
        ("DC-320", "Theory of Automata and Formal Languages", 3.0),
        ("DC-321", "Human Computer Interaction", 3.0),
        ("DC-322", "Computer Architecture", 3.0),
        ("EC-330", "Web Technologies / Elective", 3.0),
        ("HQ-005", "Quran Translation - V", 0.5),
    ],
    6: [
        ("CC-311", "Operating Systems", 3.0),
        ("EC-333", "Mobile Application Development / Elective", 3.0),
        ("EC-324", "Software Construction & Development / Elective", 3.0),
        ("EC-335", "Machine Learning / Elective", 3.0),
        ("EC-334", "Game Design and Development / Elective", 3.0),
        ("MS-253", "Multivariable Calculus", 3.0),
        ("HQ-006", "Quran Translation - VI", 0.5),
    ],
    7: [
        ("CC-411", "Final Year Project - I", 2.0),
        ("DC-328", "Parallel & Distributed Computing", 3.0),
        ("EC-345", "Computer Vision / Elective", 3.0),
        ("EC-425", "Software Quality Engineering / Elective", 3.0),
        ("MS-254", "Technical and Business Writing", 3.0),
        ("GE-263", "Entrepreneurship", 2.0),
        ("GE-262", "Professional Practices", 2.0),
        ("HQ-007", "Quran Translation - VII", 0.5),
    ],
    8: [
        ("CC-412", "Final Year Project - II", 4.0),
        ("DC-421", "Compiler Construction", 3.0),
        ("UE-272", "Introduction to Marketing", 3.0),
        ("GE-168", "Ideology and Constitution of Pakistan", 2.0),
        ("GE-363", "Civics and Community Engagement", 2.0),
        ("HQ-008", "Quran Translation - VIII", 0.5),
    ],
}

_TOTAL_PROGRAM_CREDIT_HOURS = sum(
    ch for courses in COURSES.values() for (_, _, ch) in courses
)  # 134.0


def _semester_total(semester: int) -> float:
    return sum(ch for (_, _, ch) in COURSES[semester])


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def marks_to_grade_points(marks: int) -> float | str:
    """
    Convert a single course's numeric marks (0-100) into PUCIT grade points
    using the official grade band table (85+ = A = 4.0, down to below 50 = F
    = 0.0).

    Use this whenever the student gives you raw marks (e.g. "I got 78 in
    AI") and you need the grade points for a GPA calculation. Call it once
    per course/mark. Do not estimate grade points yourself.

    Returns the grade points as a float, or an error string such as
    "Error: marks must be between 0 and 100" if the input is out of range.
    """
    if not isinstance(marks, (int, float)) or isinstance(marks, bool):
        return "Error: marks must be a number"
    if marks < 0 or marks > 100:
        return "Error: marks must be between 0 and 100"

    for minimum, _label, points in _GRADE_BANDS:
        if marks >= minimum:
            return points
    return 0.0  # unreachable, kept for safety


def calculate_semester_gpa(
    grade_points: list[float], credit_hours: list[float]
) -> float | str:
    """
    Calculate one semester's credit-weighted GPA from a list of grade
    points and the matching list of credit hours, using
    GPA = sum(grade_point * credit_hours) / sum(credit_hours).

    Use this once you have grade points (from marks_to_grade_points or
    given directly by the student) and credit hours for every course in
    the semester. The two lists must be the same length and in the same
    order (grade_points[i] goes with credit_hours[i]). Exclude MD-001 /
    MD-002 (Math Deficiency) entirely - they are non-credit pass/fail and
    never enter a GPA calculation.

    Returns the semester GPA as a float, or an error string if the input
    is invalid (mismatched list lengths, empty lists, or non-positive
    total credit hours).
    """
    if not grade_points or not credit_hours:
        return "Error: grade_points and credit_hours must not be empty"
    if len(grade_points) != len(credit_hours):
        return "Error: grade_points and credit_hours must be the same length"
    if any(ch <= 0 for ch in credit_hours):
        return "Error: credit_hours must all be greater than 0"
    if any(gp < 0 or gp > 4.0 for gp in grade_points):
        return "Error: grade_points must each be between 0.0 and 4.0"

    total_credit_hours = sum(credit_hours)
    if total_credit_hours <= 0:
        return "Error: total credit hours must be greater than 0"

    weighted_sum = sum(gp * ch for gp, ch in zip(grade_points, credit_hours))
    return round(weighted_sum / total_credit_hours, 4)


def calculate_new_cgpa(
    current_cgpa: float,
    completed_credit_hours: float,
    semester_gpa: float,
    semester_credit_hours: float,
) -> float | str:
    """
    Project the new overall CGPA after adding one semester, using
    new_cgpa = (current_cgpa * completed_ch + semester_gpa * semester_ch)
               / (completed_ch + semester_ch).

    Use this when the student already knows their current CGPA and
    completed credit hours, and either already has (or you have just
    calculated with calculate_semester_gpa) a GPA for a new semester, and
    wants to know where that leaves their overall CGPA.

    Returns the new CGPA as a float, or an error string if the input is
    invalid (negative values, or non-positive credit hours).
    """
    if current_cgpa < 0 or current_cgpa > 4.0:
        return "Error: current_cgpa must be between 0.0 and 4.0"
    if semester_gpa < 0 or semester_gpa > 4.0:
        return "Error: semester_gpa must be between 0.0 and 4.0"
    if completed_credit_hours < 0:
        return "Error: completed_credit_hours cannot be negative"
    if semester_credit_hours <= 0:
        return "Error: semester_credit_hours must be greater than 0"

    total_ch = completed_credit_hours + semester_credit_hours
    new_cgpa = (
        current_cgpa * completed_credit_hours + semester_gpa * semester_credit_hours
    ) / total_ch
    return round(new_cgpa, 4)


def required_gpa_for_target(
    target_cgpa: float,
    current_cgpa: float,
    completed_credit_hours: float,
    remaining_credit_hours: float,
) -> float | str:
    """
    Calculate the GPA needed over the remaining credit hours to reach a
    target CGPA, using
    required_gpa = (target_cgpa * (completed_ch + remaining_ch)
                     - current_cgpa * completed_ch) / remaining_ch.

    Use this whenever the student states or implies a target CGPA (e.g.
    "I want to graduate with a 3.5") and you know their current CGPA,
    completed credit hours, and how many credit hours remain over the
    window you're checking.

    This tool does NOT judge whether the result is achievable - it will
    happily return a number above 4.0. That check, and the strategy of
    widening the window across more semesters when the result is above
    4.0, is the agent's job, not this tool's.

    Returns the required GPA as a float, or an error string if the input
    is invalid (out-of-range CGPAs, negative completed hours, or
    non-positive remaining hours).
    """
    if target_cgpa < 0 or target_cgpa > 4.0:
        return "Error: target_cgpa must be between 0.0 and 4.0"
    if current_cgpa < 0 or current_cgpa > 4.0:
        return "Error: current_cgpa must be between 0.0 and 4.0"
    if completed_credit_hours < 0:
        return "Error: completed_credit_hours cannot be negative"
    if remaining_credit_hours <= 0:
        return "Error: remaining_credit_hours must be greater than 0"

    numerator = target_cgpa * (
        completed_credit_hours + remaining_credit_hours
    ) - current_cgpa * completed_credit_hours
    required_gpa = numerator / remaining_credit_hours
    return round(required_gpa, 4)


def get_semester_courses(semester: int) -> str:
    """
    Return the list of graded courses and their credit hours for a given
    semester (1-8) of the PUCIT BS(CS) scheme of studies, formatted as
    readable text (course code, name, credit hours, and the semester
    total).

    Use this when you need to know what a semester actually contains -
    for example, to check credit hours for a course the student mentioned,
    to help them figure out their semester's total credit hours, or to
    work out the credit hours for one horizon while widening the window
    in the unreachable-target check. Math Deficiency courses (MD-001,
    MD-002) are never included here since they are not part of the graded
    scheme.

    Returns a formatted string, or an error string such as
    "Error: semester must be between 1 and 8" if out of range.
    """
    if not isinstance(semester, int) or isinstance(semester, bool):
        return "Error: semester must be an integer"
    if semester < 1 or semester > 8:
        return "Error: semester must be between 1 and 8"

    lines = [f"Semester {semester}:"]
    for code, name, ch in COURSES[semester]:
        lines.append(f"  {code} - {name} ({ch} ch)")
    lines.append(f"Total: {_semester_total(semester)} credit hours")
    return "\n".join(lines)


def get_remaining_credit_hours(current_semester: int) -> float | str:
    """
    Total the graded credit hours remaining in the degree AFTER a given
    semester - i.e. the sum of every semester's credit hours from
    (current_semester + 1) through semester 8. Pass 0 if the student
    hasn't completed any semester yet, to get the full 134.0-hour program.

    Use this to find out how much runway a student has left. It is also
    the building block for the unreachable-target widening check: call it
    once for the student's completed semester and once for a later
    semester, and the difference between the two results is the remaining
    credit hours across exactly that range of semesters (e.g. the
    difference between get_remaining_credit_hours(4) and
    get_remaining_credit_hours(6) is the combined credit hours of
    semesters 5 and 6 only).

    Returns the remaining credit hours as a float, or an error string such
    as "Error: current_semester must be between 0 and 8" if out of range.
    """
    if not isinstance(current_semester, int) or isinstance(current_semester, bool):
        return "Error: current_semester must be an integer"
    if current_semester < 0 or current_semester > 8:
        return "Error: current_semester must be between 0 and 8"

    remaining = sum(
        _semester_total(s) for s in range(current_semester + 1, 9)
    )
    return round(remaining, 4)


def get_credit_hours(semesters: list[int]) -> float | str:
    """
    Return the combined graded credit hours of the given semesters of the
    PUCIT BS(CS) scheme, e.g. [5, 6] -> 37.0 (semester 5 + semester 6).

    Use this to get the remaining credit hours for one horizon while
    widening the window in the unreachable-target check: pass exactly the
    semesters in that horizon (e.g. [5], then [5, 6], then [5, 6, 7]) and
    feed the result to required_gpa_for_target as remaining_credit_hours.
    Math Deficiency courses (MD-001, MD-002) are never counted.

    Returns the total credit hours as a float, or an error string such as
    "Error: every semester must be between 1 and 8".
    """
    if not semesters:
        return "Error: semesters must not be empty"
    if any(not isinstance(s, int) or isinstance(s, bool) for s in semesters):
        return "Error: every semester must be an integer"
    if any(s < 1 or s > 8 for s in semesters):
        return "Error: every semester must be between 1 and 8"
    if len(set(semesters)) != len(semesters):
        return "Error: each semester may only appear once"

    return round(sum(_semester_total(s) for s in semesters), 4)


def save_report(filename: str, content: str) -> str:
    """
    Save a text summary (a semester GPA result, a projected CGPA, or a
    plan for reaching a target CGPA) to a local file, and return a
    confirmation message.

    Only call this when the student has explicitly asked you to save or
    export something, and only after you have already produced a real
    result worth keeping. Never call it after just a clarifying question
    or a single grade lookup, and never call it unprompted.

    Returns a confirmation string naming the saved file, or an error
    string if the filename or content is invalid.
    """
    import os

    if not filename or not filename.strip():
        return "Error: filename must not be empty"
    if not content or not content.strip():
        return "Error: content must not be empty"

    safe_name = os.path.basename(filename.strip())
    if not safe_name:
        return "Error: filename must not be empty"

    # NOTE: this runs on the MCP server, so the file is written on the
    # server's disk (wherever the server is hosted), not the student's PC.
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, safe_name)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        return f"Error: could not save file ({exc})"

    return f"Saved report to {path}"


ALL_TOOLS = [
    marks_to_grade_points,
    calculate_semester_gpa,
    calculate_new_cgpa,
    required_gpa_for_target,
    get_semester_courses,
    get_remaining_credit_hours,
    get_credit_hours,
    save_report,
]
