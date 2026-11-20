import subprocess

def run_scripts(commands):
    input_data = "\n".join(commands)+ "\n"
    result = subprocess.run(
        ["./DataBase"],
        input = input_data.encode("utf-8"),
        #text = True,
        capture_output = True,
        check=True,
    )
    return result.stdout.decode("utf-8", errors="replace").split("\n")
"""
#1st test
def test_inserts_and_retrieves_a_row():
    result = run_scripts([
        "insert 1 user1 person1@example.com",
        "select",
        ".exit",
    ])
    print("ACTUAL RESULT:", repr(result))
    assert result == [
        "db > Executed.",
        "db > (1, user1, person1@example.com)",
        "Executed.",
        "db > ",
    ]

#2nd Test
def test_inserts_and_retrieves_a_row():
    scripts = run_scripts(f"insert {i} user{i} person{i}@example.com" for i in range(1, 1402))
    scripts.append(".exit")
    result = run_scripts(scripts)
    assert result[-2] != "db > Error: Table full."
"""

def test_allows_inserting_strings_that_are_the_more_than_maximum_length():
    long_username = "a" * 33 #32
    long_email = "a" * 256 #255
    script = [
        f"insert 1 {long_username} {long_email}",
        "select",
        ".exit",
    ]
    result = run_scripts(script)
    print("ACTUAL:", result)
    assert result == [
        "db > String is too long.",
        "db > Executed.",
        "db > ",
    ]


def test_allows_inserting_negative_id():
    scripts = [
        "insert -1 cstack foo@bar.com",
        "select",
        ".exit",
    ]
    result = run_scripts(scripts)
    print("ACTUAL:", result)
    assert result == [
        "db > ID must be positive.",
        "db > Executed.",
        "db > ",
    ]
if __name__ == "__main__":
    #test_inserts_and_retrieves_a_row()
    #test_allows_inserting_strings_that_are_the_more_than_maximum_length()
    test_allows_inserting_negative_id()
    print("Test passed!")