"""CSC402 deterministic stage-6 generators.

Consumes the stage-5 planner contract and produces original mock questions
with answers and marking guidance.  No LLM call and no past-paper text is
copied.  The generator is deterministic for a given seed.

    uv run python -m src.subjects.csc402.generators --seed 1
    uv run python -m src.subjects.csc402.generators --validate
"""
from __future__ import annotations

import argparse
import json
import random
import textwrap
from collections import Counter
from pathlib import Path

from src import config
from src.subjects.csc402.planner import build_plan

SUBJECT = "CSC402"
TRACKING = config.TRACKING_DIR / "csc402"
SAMPLE_PATH = TRACKING / "generator_sample_seed_01.json"
VALIDATION_PATH = TRACKING / "generator_validation.json"

MCQ_BANK = {
    "fundamentals": [
        {"text": "Which term describes a finite sequence of precise steps that solves a problem?",
         "options": ["Algorithm", "Compiler", "Variable", "Array"], "answer": 0,
         "solution": "An algorithm is a finite, ordered set of unambiguous steps."},
        {"text": "Which tool represents an algorithm using standard graphical symbols?",
         "options": ["Flowchart", "Pseudocode", "Compiler", "Debugger"], "answer": 0,
         "solution": "A flowchart uses standard symbols such as terminals, processes and decisions."},
        {"text": "Which phase of the program development life cycle defines what the program must do?",
         "options": ["Analysis", "Coding", "Testing", "Maintenance"], "answer": 0,
         "solution": "Analysis establishes the requirements before design and coding."},
        {"text": "What does a compiler do?",
         "options": ["Translates the whole source program before execution",
                     "Executes one source statement at a time",
                     "Stores only integer values",
                     "Draws flowcharts automatically"], "answer": 0,
         "solution": "A compiler translates the complete source file into object code."},
        {"text": "Which item is NOT a programming paradigm?",
         "options": ["Structured programming", "Object-oriented programming",
                     "Procedural programming", "Debugging"], "answer": 3,
         "solution": "Debugging is an activity, not a programming paradigm."},
        {"text": "What is pseudocode?",
         "options": ["A structured English-like description of an algorithm",
                     "Machine code produced by an assembler",
                     "A C++ header file",
                     "A type of compiler error"], "answer": 0,
         "solution": "Pseudocode expresses algorithm logic without strict language syntax."},
    ],
    "data_types": [
        {"text": "Which identifier is valid in C++?",
         "options": ["total_score", "2total", "total score", "int"], "answer": 0,
         "solution": "An identifier may contain letters, digits and underscores, but cannot start with a digit or be a keyword."},
        {"text": "Which data type stores a whole number?",
         "options": ["int", "float", "char", "string"], "answer": 0,
         "solution": "int stores whole numbers; float stores real values."},
        {"text": "Which keyword prevents a variable's value from being changed after initialisation?",
         "options": ["const", "static", "void", "break"], "answer": 0,
         "solution": "const defines a read-only variable."},
        {"text": "What does the % operator return?",
         "options": ["The remainder of integer division", "The quotient",
                     "The absolute value", "The square root"], "answer": 0,
         "solution": "% is the modulus operator and returns the remainder."},
        {"text": "Which declaration creates a floating-point variable named price?",
         "options": ["float price;", "int price;", "char price;", "bool price;"],
         "answer": 0, "solution": "float is used for real numbers."},
        {"text": "Which values can a bool variable hold?",
         "options": ["true or false", "any integer", "any character", "any decimal"],
         "answer": 0, "solution": "A bool holds true or false."},
    ],
    "control_structures": [
        {"text": "Which loop is guaranteed to execute its body at least once?",
         "options": ["do...while", "while", "for", "if"], "answer": 0,
         "solution": "do...while tests the condition after the body."},
        {"text": "Which statement is most suitable for selecting among several constant cases?",
         "options": ["switch", "for", "while", "do...while"], "answer": 0,
         "solution": "switch selects a case based on a constant expression."},
        {"text": "How many times does a while loop execute when its condition is false initially?",
         "options": ["Zero", "One", "Two", "Until the user stops it"], "answer": 0,
         "solution": "while is a pretest loop; a false condition skips the body."},
        {"text": "Which part of a for loop is executed after each iteration?",
         "options": ["The update expression", "The initialisation",
                     "The condition only", "The loop body twice"], "answer": 0,
         "solution": "The update expression runs after each iteration."},
        {"text": "Which statement immediately exits a loop?",
         "options": ["break", "continue", "return 0", "cin"], "answer": 0,
         "solution": "break terminates the nearest loop or switch."},
        {"text": "Which structure chooses between two alternative paths?",
         "options": ["if...else", "for", "array", "struct"], "answer": 0,
         "solution": "if...else performs two-way selection."},
    ],
    "arrays": [
        {"text": "What is the index of the first element of a C++ array?",
         "options": ["0", "1", "-1", "The array size"], "answer": 0,
         "solution": "C++ arrays are zero-indexed."},
        {"text": "Which declaration creates an integer array of five elements?",
         "options": ["int a[5];", "int a;", "array a[5];", "int a(5);"],
         "answer": 0, "solution": "int a[5]; reserves five integer elements."},
        {"text": "What are parallel arrays?",
         "options": ["Arrays whose elements at the same index are related",
                     "Arrays stored in different programs",
                     "Arrays with no index",
                     "Arrays that hold only characters"], "answer": 0,
         "solution": "Related data is stored at the same index in each array."},
        {"text": "What happens when an array index is outside its valid range?",
         "options": ["Undefined behaviour may occur", "C++ automatically resizes the array",
                     "The compiler always rejects the program", "The array becomes a string"],
         "answer": 0, "solution": "C++ does not perform automatic bounds checking."},
        {"text": "Which loop is commonly used to process every array element?",
         "options": ["for", "switch", "if", "break"], "answer": 0,
         "solution": "A for loop with an index visits each element."},
        {"text": "Which initialisation is valid for an integer array?",
         "options": ["int a[3] = {1, 2, 3};", "int a[3] = (1, 2, 3);",
                     "int a = {1, 2, 3};", "array int a[3];"], "answer": 0,
         "solution": "Array initialisers use braces."},
    ],
    "input_output": [
        {"text": "Which operator sends data to cout?",
         "options": ["<<", ">>", "=", "=="], "answer": 0,
         "solution": "The insertion operator << writes to an output stream."},
        {"text": "Which operator reads data from cin?",
         "options": [">>", "<<", "=", "%"], "answer": 0,
         "solution": "The extraction operator >> reads from an input stream."},
        {"text": "Which header is required for cin and cout?",
         "options": ["<iostream>", "<cmath>", "<string>", "<iomanip>"], "answer": 0,
         "solution": "cin and cout are declared in <iostream>."},
        {"text": "What does endl do?",
         "options": ["Writes a newline and flushes the stream", "Ends the program",
                     "Reads a line", "Declares an integer"], "answer": 0,
         "solution": "endl inserts a newline and flushes the output buffer."},
        {"text": "Which header is needed for setw?",
         "options": ["<iomanip>", "<iostream>", "<cmath>", "<fstream>"], "answer": 0,
         "solution": "setw is a stream manipulator declared in <iomanip>."},
        {"text": "Which input pattern stops when the user enters -1?",
         "options": ["A sentinel-controlled loop", "A fixed for loop",
                     "A switch statement", "A function prototype"], "answer": 0,
         "solution": "A sentinel value ends the loop."},
    ],
    "debugging_testing": [
        {"text": "Which error is caused by a missing semicolon?",
         "options": ["Syntax error", "Logic error", "Runtime error", "Design error"],
         "answer": 0, "solution": "The compiler rejects invalid syntax."},
        {"text": "Which error produces incorrect output while the program still runs?",
         "options": ["Logic error", "Syntax error", "Compile error", "Linker error"],
         "answer": 0, "solution": "A logic error is a flaw in the algorithm or conditions."},
        {"text": "What is a dry run?",
         "options": ["Manually tracing values through an algorithm",
                     "Running the program without input",
                     "Compiling without warnings",
                     "Deleting the source file"], "answer": 0,
         "solution": "A dry run follows the algorithm step by step by hand."},
    ],
    "structures": [
        {"text": "Which keyword defines a C++ structure?",
         "options": ["struct", "classonly", "record", "object"], "answer": 0,
         "solution": "struct defines a structure type."},
        {"text": "How are structure members accessed through a variable?",
         "options": ["Using the dot operator", "Using the % operator",
                     "Using the newline character", "Using a loop only"], "answer": 0,
         "solution": "The dot operator accesses a member, for example book.price."},
    ],
}


def _mcq_bank(topic: str) -> list[dict]:
    return MCQ_BANK.get(topic) or MCQ_BANK["fundamentals"]


def _make_mcq(slot: dict, rng: random.Random, used: set[str]) -> dict:
    bank = _mcq_bank(slot["topic"])
    candidates = [item for item in bank if item["text"] not in used]
    if not candidates:
        candidates = bank
    item = rng.choice(candidates)
    used.add(item["text"])
    options = list(item["options"])
    correct = options[item["answer"]]
    rng.shuffle(options)
    answer = "ABCD"[options.index(correct)]
    return {
        "number": slot["slot"],
        "part": "A",
        "kind": "mcq",
        "marks": slot["marks"],
        "topic": slot["topic"],
        "stem": item["text"],
        "options": options,
        "answer": answer,
        "solution": item["solution"],
        "parts": [],
        "generator_id": f"csc402.mcq.{slot['topic']}",
        "slots": [slot["slot"]],
    }


def _b1(marks: list[int], rng: random.Random) -> dict:
    variants = [
        {
            "stem": "This question tests programming concepts and error terminology.",
            "parts": [
                {"text": "Define compiler and interpreter.",
                 "answer": "A compiler translates the whole source program before execution; an interpreter translates and executes one statement at a time.",
                 "solution": "Award 1 mark for each correct definition."},
                {"text": "State THREE differences between a compiler and an interpreter.",
                 "answer": "Compiler: whole program, produces object code, reports errors after compilation. Interpreter: statement by statement, no object file, stops at the first error; generally slower execution.",
                 "solution": "Award 1 mark for each valid difference."},
            ],
        },
        {
            "stem": "This question tests algorithms and programming errors.",
            "parts": [
                {"text": "Define algorithm and pseudocode.",
                 "answer": "An algorithm is a finite sequence of precise steps that solves a problem. Pseudocode is a structured English-like description of an algorithm.",
                 "solution": "Award 1 mark for each correct definition."},
                {"text": "Explain THREE types of programming errors and give one example of each.",
                 "answer": "Syntax error: missing semicolon. Runtime error: division by zero. Logic error: using < instead of <= in a condition.",
                 "solution": "Award 0.5 mark for each type and 0.5 mark for a valid example."},
            ],
        },
        {
            "stem": "This question tests the program development life cycle.",
            "parts": [
                {"text": "Define source code and object code.",
                 "answer": "Source code is the human-readable program text; object code is the machine-oriented output produced by a compiler.",
                 "solution": "Award 1 mark for each definition."},
                {"text": "Describe THREE stages of the program development life cycle.",
                 "answer": "Analysis (requirements), design (algorithm/flowchart), coding (implementation), testing (verification), maintenance (updates). Any three stages.",
                 "solution": "Award 1 mark for each correctly described stage."},
            ],
        },
        {
            "stem": "This question tests high-level languages and debugging.",
            "parts": [
                {"text": "Define syntax error and logic error.",
                 "answer": "A syntax error violates the language grammar and is detected by the compiler. A logic error produces incorrect output although the program runs.",
                 "solution": "Award 1 mark for each definition."},
                {"text": "Explain TWO advantages of high-level languages over machine language.",
                 "answer": "They are easier to read and write, portable across machines, and supported by compilers and debugging tools.",
                 "solution": "Award 1.5 marks for each valid advantage."},
            ],
        },
    ]
    item = rng.choice(variants)
    return {
        "stem": item["stem"],
        "parts": [
            {**part, "label": chr(ord("a") + index), "marks": marks[index]}
            for index, part in enumerate(item["parts"])
        ],
    }


B2_VARIANTS = [
    {
        "stem": "A program reads a student's score from 0 to 100 and displays the grade: 80-100 A, 60-79 B, 50-59 C, 40-49 D, below 40 F.",
        "parts": [
            {"text": "Draw a flowchart for the grade classification.",
             "answer": "Start -> read score -> decision score >= 80 -> A; else score >= 60 -> B; else score >= 50 -> C; else score >= 40 -> D; else F -> display grade -> end.",
             "solution": "Award marks for terminal symbols, input, four/five decisions, each output and correct flow."},
            {"text": "Write pseudocode for the algorithm and convert it into a complete C++ program.",
             "answer": "IF score >= 80 THEN grade = A ELSE IF score >= 60 THEN grade = B ... ENDIF; use if/else if in C++ and display grade.",
             "solution": "Award marks for correct pseudocode, complete C++ structure, conditions, input and output."},
        ],
    },
    {
        "stem": "A program reads a positive integer N and calculates the sum and average of the numbers 1 to N.",
        "parts": [
            {"text": "Draw a flowchart for the sum and average calculation.",
             "answer": "Start -> read N -> total = 0, count = 1 -> while count <= N add count -> average = total / N -> display total and average -> end.",
             "solution": "Award marks for input, initialisation, loop condition, accumulator, average and output."},
            {"text": "Write pseudocode and a complete C++ program for the algorithm.",
             "answer": "Use a for loop from 1 to N, accumulate total, compute average as double(total)/N, then display both values.",
             "solution": "Award marks for loop, accumulator, correct average type and output."},
        ],
    },
    {
        "stem": "A program reads three integer values and displays the largest value.",
        "parts": [
            {"text": "Draw a flowchart to find the largest of three values.",
             "answer": "Start -> read a, b, c -> largest = a -> if b > largest then largest = b -> if c > largest then largest = c -> display largest -> end.",
             "solution": "Award marks for input, initial assumption, two comparisons, output and flow."},
            {"text": "Write pseudocode and a complete C++ program for the flowchart.",
             "answer": "Use if statements to update largest, then cout the result.",
             "solution": "Award marks for correct comparisons, variable updates and output."},
        ],
    },
    {
        "stem": "A concert charges RM15 for ages 0-12, RM25 for ages 13-17 and RM40 for ages 18 and above. A negative age is invalid.",
        "parts": [
            {"text": "Draw a flowchart for the ticket price selection.",
             "answer": "Start -> read age -> if age < 0 display invalid; else if age <= 12 price = 15; else if age <= 17 price = 25; else price = 40 -> display price -> end.",
             "solution": "Award marks for validation, all ranges, output and flow."},
            {"text": "Write pseudocode and a complete C++ program for the ticket price selection.",
             "answer": "Use if/else if with the three ranges and an invalid-age branch.",
             "solution": "Award marks for validation, range conditions, assignment and output."},
        ],
    },
]


def _b2(marks: list[int], rng: random.Random) -> dict:
    item = rng.choice(B2_VARIANTS)
    return {
        "stem": item["stem"],
        "parts": [
            {**part, "label": chr(ord("a") + index), "marks": marks[index]}
            for index, part in enumerate(item["parts"])
        ],
    }


B3_VARIANTS = [
    {
        "stem": "This question tests declarations, constants and expressions.",
        "parts": [
            {"text": "Write C++ declarations for: an integer age, a double price, a constant discount rate of 0.10 and a character grade.",
             "answer": "int age; double price; const double DISCOUNT = 0.10; char grade;",
             "solution": "Award marks for correct types, names and const initialisation."},
            {"text": "Write C++ statements to read age and price, calculate price after discount, and display the result.",
             "answer": "cin >> age >> price; price = price - price * DISCOUNT; cout << price;",
             "solution": "Award marks for input, discount expression and output."},
        ],
    },
    {
        "stem": "This question tests operator precedence and assignment.",
        "parts": [
            {"text": "Evaluate the following expressions: (i) 7 + 3 * 2, (ii) (7 + 3) * 2, (iii) 17 % 5, (iv) 17 / 5, (v) 17.0 / 5.",
             "answer": "(i) 13, (ii) 20, (iii) 2, (iv) 3, (v) 3.4",
             "solution": "Award 1 mark per correct value."},
            {"text": "Write C++ statements to declare two integers a and b, read their values, and display their sum, difference, product and remainder.",
             "answer": "int a, b; cin >> a >> b; cout << a+b << a-b << a*b << a%b;",
             "solution": "Award marks for declarations, input, four operations and output."},
        ],
    },
    {
        "stem": "This question tests type conversion and constants.",
        "parts": [
            {"text": "Explain the difference between implicit and explicit type conversion, and give one C++ example of each.",
             "answer": "Implicit conversion is automatic (int to double); explicit conversion uses a cast such as double(total) or static_cast<double>(total).",
             "solution": "Award marks for both definitions and valid examples."},
            {"text": "Write a C++ program segment that calculates the average of three integer marks as a double and displays it to two decimal places.",
             "answer": "double average = (m1 + m2 + m3) / 3.0; cout << fixed << setprecision(2) << average;",
             "solution": "Award marks for floating-point division, fixed/setprecision and output."},
        ],
    },
]


def _b3(marks: list[int], rng: random.Random) -> dict:
    item = rng.choice(B3_VARIANTS)
    return {
        "stem": item["stem"],
        "parts": [
            {**part, "label": chr(ord("a") + index), "marks": marks[index]}
            for index, part in enumerate(item["parts"])
        ],
    }


B4_VARIANTS = [
    {
        "stem": "Study the following C++ program segment:\n\nint total = 0;\nfor (int i = 1; i <= 5; i++) {\n    total += i;\n}\ncout << total;",
        "parts": [
            {"text": "Trace the program and state the output.",
             "answer": "15",
             "solution": "The loop adds 1+2+3+4+5. Award marks for the sequence and final output."},
            {"text": "Rewrite the loop using a while loop. Then explain what changes if the condition is i < 5.",
             "answer": "int i = 1; while (i <= 5) { total += i; i++; } With i < 5 the result is 10 because 5 is not added.",
             "solution": "Award marks for correct while structure, update and changed result."},
        ],
    },
    {
        "stem": "Study the following nested loop:\n\nfor (int i = 1; i <= 3; i++) {\n    for (int j = 1; j <= i; j++) {\n        cout << j;\n    }\n    cout << endl;\n}",
        "parts": [
            {"text": "Trace the program and show the exact output.",
             "answer": "1\\n12\\n123",
             "solution": "Award marks for each line and the exact row lengths."},
            {"text": "Identify TWO logic errors in a version that prints four rows but reuses j without resetting it. Rewrite the corrected code.",
             "answer": "The inner loop must initialise j = 1 for every row and the outer loop must run to 4. Correct code: for (int i=1;i<=4;i++){for(int j=1;j<=i;j++) cout<<j; cout<<endl;}",
             "solution": "Award marks for each error and the corrected loop."},
        ],
    },
    {
        "stem": "Study the following array program segment:\n\nint a[5] = {2, 4, 6, 8, 10};\nint s = 0;\nfor (int i = 0; i < 5; i++) {\n    s += a[i];\n}\ncout << s;",
        "parts": [
            {"text": "Trace the program and state the output.",
             "answer": "30",
             "solution": "The sum of 2+4+6+8+10 is 30."},
            {"text": "Rewrite the segment using a do...while loop that sums only values greater than 5.",
             "answer": "int i=0,s=0; do { if(a[i]>5) s+=a[i]; i++; } while(i<5); cout<<s;",
             "solution": "Award marks for do...while, condition, filter and output."},
        ],
    },
]


def _b4(marks: list[int], rng: random.Random) -> dict:
    item = rng.choice(B4_VARIANTS)
    return {
        "stem": item["stem"],
        "parts": [
            {**part, "label": chr(ord("a") + index), "marks": marks[index]}
            for index, part in enumerate(item["parts"])
        ],
    }


B5_VARIANTS = [
    {
        "stem": "A shop stores the prices of five items in an array.",
        "parts": [
            {"text": "Declare an array named prices with the values 20.5, 55.0, 15.9, 75.0 and 10.0. Display all values.",
             "answer": "double prices[5] = {20.5, 55.0, 15.9, 75.0, 10.0}; for (int i=0;i<5;i++) cout << prices[i] << endl;",
             "solution": "Award marks for correct type, initialiser, loop and output."},
            {"text": "Write a program segment that applies a 10% discount to prices above RM50 and stores the results in a second array. Display both arrays.",
             "answer": "double sale[5]; for(int i=0;i<5;i++){ sale[i] = prices[i] > 50 ? prices[i]*0.9 : prices[i]; } then display both arrays.",
             "solution": "Award marks for second array, condition, discount, preservation and output."},
        ],
    },
    {
        "stem": "A class records ten student marks in an array.",
        "parts": [
            {"text": "Declare an integer array of ten marks and read the marks from the user.",
             "answer": "int marks[10]; for(int i=0;i<10;i++) cin >> marks[i];",
             "solution": "Award marks for array declaration, loop and input."},
            {"text": "Write a program segment to calculate and display the average, highest mark and number of marks above the average.",
             "answer": "Compute total and highest in one loop; average = double(total)/10; then second loop counts marks > average.",
             "solution": "Award marks for total, average, highest, second loop and output."},
        ],
    },
    {
        "stem": "A sports club stores sport names and medal counts in parallel arrays.",
        "parts": [
            {"text": "Declare two parallel arrays for five sports and initialise them with suitable values.",
             "answer": "string sports[5] = {\"Swimming\",\"Badminton\",\"Athletics\",\"Cycling\",\"Hockey\"}; int medals[5] = {8,12,7,5,9};",
             "solution": "Award marks for both declarations, correct sizes and related indices."},
            {"text": "Write a program segment to display each sport with its medals, then calculate the total and average medals.",
             "answer": "Loop i=0..4 to display sports[i] and medals[i], accumulate total, average = double(total)/5.",
             "solution": "Award marks for paired display, total, average and output."},
        ],
    },
]


def _b5(marks: list[int], rng: random.Random) -> dict:
    item = rng.choice(B5_VARIANTS)
    return {
        "stem": item["stem"],
        "parts": [
            {**part, "label": chr(ord("a") + index), "marks": marks[index]}
            for index, part in enumerate(item["parts"])
        ],
    }


C_VARIANTS = {
    "control_structures": {
        "stem": "A catering company charges RM12.50 per meal. Orders of 50-99 meals cost RM11.50 each, 100-199 cost RM10.50 each, and 200 or more cost RM9.50 each.",
        "task": "Write a complete C++ program that reads the customer name and quantity, validates the quantity, calculates the total, displays a receipt, and repeats until the user chooses to stop. At the end, display the total quantity and total sales.",
        "answer": textwrap.dedent("""
            #include <iostream>
            #include <iomanip>
            #include <string>
            using namespace std;
            int main() {
                string name;
                int quantity, grandQuantity = 0;
                double unitPrice, total, grandTotal = 0;
                char again;
                do {
                    cout << "Customer name: ";
                    getline(cin >> ws, name);
                    cout << "Quantity: ";
                    cin >> quantity;
                    if (quantity < 0) {
                        cout << "Invalid quantity" << endl;
                    } else {
                        if (quantity >= 200) unitPrice = 9.50;
                        else if (quantity >= 100) unitPrice = 10.50;
                        else if (quantity >= 50) unitPrice = 11.50;
                        else unitPrice = 12.50;
                        total = quantity * unitPrice;
                        grandTotal += total;
                        grandQuantity += quantity;
                        cout << fixed << setprecision(2);
                        cout << "Receipt for " << name << ": "
                             << quantity << " x RM" << unitPrice
                             << " = RM" << total << endl;
                    }
                    cout << "Another customer? (y/n): ";
                    cin >> again;
                } while (again == 'y' || again == 'Y');
                cout << "Total quantity: " << grandQuantity << endl;
                cout << "Total sales: RM" << fixed << setprecision(2)
                     << grandTotal << endl;
                return 0;
            }
        """).strip(),
        "solution": "Award 3 marks for input/validation, 6 for price selection and total, 3 for repetition, 2 for final totals and 1 for output clarity.",
    },
    "input_output": {
        "stem": "A cafe sells three items: coffee RM8.50, tea RM6.00 and juice RM9.50. A 10% discount is given when the subtotal is at least RM50.",
        "task": "Write a complete C++ program that reads the item code and quantity, calculates the subtotal and discount, and displays a formatted receipt with the item name, quantity, subtotal, discount and amount to pay.",
        "answer": textwrap.dedent("""
            #include <iostream>
            #include <iomanip>
            #include <string>
            using namespace std;
            int main() {
                int code, quantity;
                double price = 0, subtotal, discount = 0;
                string name;
                cout << "Item code (1 coffee, 2 tea, 3 juice): ";
                cin >> code;
                cout << "Quantity: ";
                cin >> quantity;
                if (code == 1) { name = "Coffee"; price = 8.50; }
                else if (code == 2) { name = "Tea"; price = 6.00; }
                else if (code == 3) { name = "Juice"; price = 9.50; }
                else { cout << "Invalid item code" << endl; return 1; }
                subtotal = price * quantity;
                if (subtotal >= 50) discount = subtotal * 0.10;
                cout << fixed << setprecision(2);
                cout << "Item: " << name << endl;
                cout << "Quantity: " << quantity << endl;
                cout << "Subtotal: RM" << subtotal << endl;
                cout << "Discount: RM" << discount << endl;
                cout << "Amount to pay: RM" << subtotal - discount << endl;
                return 0;
            }
        """).strip(),
        "solution": "Award 3 marks for input, 5 for price/subtotal, 4 for discount, 2 for formatting and 1 for completeness.",
    },
    "arrays": {
        "stem": "A lecturer records the marks of ten students in an array.",
        "task": "Write a complete C++ program that reads ten marks, displays the average, the highest mark and its index, and counts how many marks are above the average.",
        "answer": textwrap.dedent("""
            #include <iostream>
            using namespace std;
            int main() {
                int marks[10], total = 0, highest, highestIndex = 0;
                int aboveAverage = 0;
                for (int i = 0; i < 10; i++) {
                    cin >> marks[i];
                    total += marks[i];
                    if (i == 0 || marks[i] > highest) {
                        highest = marks[i];
                        highestIndex = i;
                    }
                }
                double average = total / 10.0;
                for (int i = 0; i < 10; i++) {
                    if (marks[i] > average) aboveAverage++;
                }
                cout << "Average: " << average << endl;
                cout << "Highest: " << highest
                     << " at index " << highestIndex << endl;
                cout << "Above average: " << aboveAverage << endl;
                return 0;
            }
        """).strip(),
        "solution": "Award 3 marks for input, 4 for total/average, 3 for highest/index, 3 for above-average count and 2 for output.",
    },
    "structures": {
        "stem": "A bookstore records up to five books. Each book has a title, price and quantity in stock.",
        "task": "Define a struct Book. Write a complete C++ program that reads the records, calculates the total inventory value, and displays the title of the most expensive book.",
        "answer": textwrap.dedent("""
            #include <iostream>
            #include <string>
            using namespace std;
            struct Book {
                string title;
                double price;
                int quantity;
            };
            int main() {
                Book books[5];
                double totalValue = 0;
                int mostExpensive = 0;
                for (int i = 0; i < 5; i++) {
                    cin.ignore();
                    cout << "Title: ";
                    getline(cin, books[i].title);
                    cout << "Price and quantity: ";
                    cin >> books[i].price >> books[i].quantity;
                    totalValue += books[i].price * books[i].quantity;
                    if (books[i].price > books[mostExpensive].price) {
                        mostExpensive = i;
                    }
                }
                cout << "Total inventory value: RM" << totalValue << endl;
                cout << "Most expensive: " << books[mostExpensive].title
                     << " (RM" << books[mostExpensive].price << ")" << endl;
                return 0;
            }
        """).strip(),
        "solution": "Award 3 marks for struct definition, 4 for input, 4 for inventory value, 3 for most expensive and 1 for output.",
    },
}


def _c_question(slot: dict, rng: random.Random) -> dict:
    topic = slot["topic"] if slot["topic"] in C_VARIANTS else "control_structures"
    item = C_VARIANTS[topic]
    if topic == "control_structures" and rng.random() < 0.5:
        item = C_VARIANTS["input_output"]
        topic = "input_output"
    elif topic == "input_output" and rng.random() < 0.5:
        item = C_VARIANTS["arrays"]
        topic = "arrays"
    elif topic == "arrays" and rng.random() < 0.5:
        item = C_VARIANTS["structures"]
        topic = "structures"
    return {
        "number": slot["slot"],
        "part": "C",
        "kind": "program",
        "marks": slot["marks"],
        "topic": topic,
        "stem": item["stem"],
        "options": [],
        "answer": item["answer"],
        "solution": item["solution"],
        "parts": [{
            "label": "",
            "marks": slot["marks"],
            "text": item["task"],
            "answer": item["answer"],
            "solution": item["solution"],
        }],
        "generator_id": f"csc402.complete_program.{topic}",
        "slots": [slot["slot"]],
    }


def generate_paper(plan: dict | None = None, seed: int | None = None) -> dict:
    if plan is None:
        plan = build_plan(seed if seed is not None else 1)
    rng = random.Random(int(plan["seed"]))
    used_mcq: set[str] = set()
    questions = []
    for slot in plan["slots"]:
        if slot["part"] == "A":
            questions.append(_make_mcq(slot, rng, used_mcq))
    by_question: dict[str, list[dict]] = {}
    for slot in plan["slots"]:
        if slot["part"] == "B":
            by_question.setdefault(slot["question"], []).append(slot)
    for question_label, slots in by_question.items():
        marks = [slot["marks"] for slot in slots]
        task = slots[0]["task"]
        builder = {
            "short_answer": _b1,
            "flowchart_or_pseudocode": _b2,
            "code_statement": _b3,
            "trace_or_debug": _b4,
            "array_program_segment": _b5,
        }.get(task)
        if builder is None:
            raise ValueError(f"no CSC402 generator for task {task}")
        item = builder(marks, rng)
        questions.append({
            "number": question_label,
            "part": "B",
            "kind": "structured",
            "marks": sum(marks),
            "topic": slots[0]["topic"],
            "stem": item["stem"],
            "options": [],
            "answer": "",
            "solution": "",
            "parts": item["parts"],
            "generator_id": f"csc402.{task}",
            "slots": [slot["slot"] for slot in slots],
        })
    for slot in plan["slots"]:
        if slot["part"] == "C":
            questions.append(_c_question(slot, rng))
    slot_map = {}
    for question in questions:
        for slot in question["slots"]:
            slot_map[slot] = question["number"]
    total = sum(question["marks"] for question in questions)
    return {
        "subject": SUBJECT,
        "seed": int(plan["seed"]),
        "generated_by": "src.subjects.csc402.generators",
        "planner": "src.subjects.csc402.planner",
        "total_marks": total,
        "question_count": len(questions),
        "slot_count": len(slot_map),
        "questions": questions,
        "slot_map": slot_map,
        "generator_ids": sorted({q["generator_id"] for q in questions}),
    }


def validate_paper(paper: dict, plan: dict) -> list[str]:
    problems = []
    if paper["total_marks"] != 100:
        problems.append(f"total marks {paper['total_marks']} != 100")
    if paper["question_count"] != 17:
        problems.append(f"question count {paper['question_count']} != 17")
    if paper["slot_count"] != len(plan["slots"]):
        problems.append(
            f"slot count {paper['slot_count']} != plan {len(plan['slots'])}")
    for slot in plan["slots"]:
        if slot["slot"] not in paper["slot_map"]:
            problems.append(f"missing slot {slot['slot']}")
    for question in paper["questions"]:
        if question["part"] == "A":
            if len(question["options"]) != 4:
                problems.append(f"{question['number']}: expected 4 options")
            if question["answer"] not in "ABCD":
                problems.append(f"{question['number']}: invalid answer key")
            if not question["solution"]:
                problems.append(f"{question['number']}: missing solution")
        else:
            if not question["parts"]:
                problems.append(f"{question['number']}: no parts")
            for part in question["parts"]:
                if not part["text"] or not part["answer"] or not part["solution"]:
                    problems.append(
                        f"{question['number']}{part['label']}: incomplete")
    blob = json.dumps(paper)
    for token in ("CSC662", "MAT133", "TODO", "placeholder", "data/reference"):
        if token in blob:
            problems.append(f"forbidden token in generated paper: {token}")
    if generate_paper(plan) != paper:
        problems.append("generator is not deterministic for the same seed")
    return problems


def validate_seeds(seed_min: int = 1, seed_max: int = 20) -> dict:
    results = []
    task_topics = set()
    generator_ids = Counter()
    for seed in range(seed_min, seed_max + 1):
        plan = build_plan(seed)
        paper = generate_paper(plan)
        problems = validate_paper(paper, plan)
        for question in paper["questions"]:
            task_topics.add((question["generator_id"], question["topic"]))
            generator_ids[question["generator_id"]] += 1
        results.append({
            "seed": seed,
            "total_marks": paper["total_marks"],
            "question_count": paper["question_count"],
            "slot_count": paper["slot_count"],
            "problems": problems,
        })
    report = {
        "subject": SUBJECT,
        "seeds": [seed_min, seed_max],
        "papers_valid": sum(1 for row in results if not row["problems"]),
        "papers_total": len(results),
        "generator_ids": dict(sorted(generator_ids.items())),
        "task_topic_pairs": sorted(f"{gid}|{topic}" for gid, topic in task_topics),
        "results": results,
    }
    VALIDATION_PATH.write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    if args.validate:
        report = validate_seeds()
        print(json.dumps({
            "papers_valid": report["papers_valid"],
            "papers_total": report["papers_total"],
            "generator_ids": report["generator_ids"],
        }, indent=2))
        if report["papers_valid"] != report["papers_total"]:
            raise SystemExit(1)
        return
    plan = build_plan(args.seed)
    paper = generate_paper(plan)
    path = Path(args.out) if args.out else (
        TRACKING / f"generator_sample_seed_{args.seed:02d}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(paper, indent=2), encoding="utf-8")
    problems = validate_paper(paper, plan)
    print(json.dumps({
        "path": str(path),
        "seed": args.seed,
        "total_marks": paper["total_marks"],
        "question_count": paper["question_count"],
        "slot_count": paper["slot_count"],
        "generator_ids": paper["generator_ids"],
        "problems": problems,
    }, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
