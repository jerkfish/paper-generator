"""Model answers for the ERD questions used in seeds 1–3."""
from __future__ import annotations

from ._blocks import erd, p, sub, table

VOLUNTEER = {
    "width": 1160,
    "height": 430,
    "entities": [
        {"id": "FACULTY", "name": "FACULTY", "x": 70, "y": 50,
         "attrs": [{"name": "FacultyID", "key": "PK"},
                   {"name": "FacultyName"}]},
        {"id": "PROJECT", "name": "PROJECT", "x": 70, "y": 220,
         "attrs": [{"name": "ProjectID", "key": "PK"},
                   {"name": "ProjectName"}]},
        {"id": "VOLUNTEER", "name": "VOLUNTEER", "x": 470, "y": 50,
         "attrs": [{"name": "VolunteerID", "key": "PK"},
                   {"name": "VolunteerType"},
                   {"name": "RegisterDate"},
                   {"name": "TotalHours"}]},
        {"id": "ASSIGNMENT", "name": "ASSIGNMENT", "x": 880, "y": 160,
         "attrs": [{"name": "VolunteerID", "key": "PK/FK"},
                   {"name": "ProjectID", "key": "PK/FK"},
                   {"name": "StartDate"}, {"name": "EndDate"},
                   {"name": "Hours"}, {"name": "Station"},
                   {"name": "Status"}]},
    ],
    "relationships": [
        {"from": "FACULTY", "to": "PROJECT", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "leads"},
        {"from": "VOLUNTEER", "to": "ASSIGNMENT", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "has",
         "waypoints": [[760, 99], [760, 236]]},
        {"from": "PROJECT", "to": "ASSIGNMENT", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "bottom",
         "label": "includes",
         "waypoints": [[360, 271], [360, 330], [982, 330]]},
    ],
}

ART = {
    "width": 1180,
    "height": 800,
    "entities": [
        {"id": "STUDIO", "name": "STUDIO", "x": 50, "y": 60,
         "attrs": [{"name": "StudioID", "key": "PK"},
                   {"name": "StudioName"}, {"name": "Address"},
                   {"name": "Phone"}, {"name": "Email"}, {"name": "GPS"}]},
        {"id": "EMPLOYEE", "name": "EMPLOYEE", "x": 50, "y": 300,
         "attrs": [{"name": "EmployeeID", "key": "PK"},
                   {"name": "FirstName"}, {"name": "LastName"},
                   {"name": "JobTitle"}, {"name": "DOB"},
                   {"name": "StudioID", "key": "FK"}]},
        {"id": "MARRIAGE", "name": "MARRIAGE", "x": 50, "y": 530,
         "attrs": [{"name": "EmployeeID", "key": "PK/FK"},
                   {"name": "SpouseEmployeeID", "key": "PK/FK"},
                   {"name": "MarriageDate"}]},
        {"id": "SKILL", "name": "SKILL", "x": 50, "y": 700,
         "attrs": [{"name": "SkillType", "key": "PK"},
                   {"name": "SkillDescription"}]},
        {"id": "SUPPLIER", "name": "SUPPLIER", "x": 480, "y": 60,
         "attrs": [{"name": "SupplierID", "key": "PK"},
                   {"name": "SupplierName"}, {"name": "Address"},
                   {"name": "Email"}]},
        {"id": "ART_MATERIAL", "name": "ART_MATERIAL", "x": 480, "y": 260,
         "attrs": [{"name": "MaterialID", "key": "PK"},
                   {"name": "MaterialName"}, {"name": "Description"},
                   {"name": "Price"}]},
        {"id": "PROGRAM", "name": "PROGRAM", "x": 880, "y": 60,
         "attrs": [{"name": "ProgramID", "key": "PK"},
                   {"name": "ProgramName"}, {"name": "Description"},
                   {"name": "Price"}, {"name": "ProgramType"}]},
    ],
    "relationships": [
        {"from": "STUDIO", "to": "EMPLOYEE", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "employs"},
        {"from": "STUDIO", "to": "PROGRAM", "from_card": "one",
         "to_card": "many", "from_side": "top", "to_side": "left",
         "label": "offers",
         "waypoints": [[152, 20], [850, 20], [850, 108]]},
        {"from": "STUDIO", "to": "SUPPLIER", "from_card": "many",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "deals with"},
        {"from": "SUPPLIER", "to": "ART_MATERIAL", "from_card": "many",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "supplies"},
        {"from": "EMPLOYEE", "to": "MARRIAGE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "spouse 1"},
        {"from": "EMPLOYEE", "to": "MARRIAGE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "right",
         "label": "spouse 2",
         "waypoints": [[340, 367], [340, 570]]},
        {"from": "EMPLOYEE", "to": "SKILL", "from_card": "many",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "acquires",
         "waypoints": [[152, 470], [300, 470], [300, 680], [152, 680]]},
    ],
}
DENTAL = {
    "width": 1160,
    "height": 730,
    "entities": [
        {"id": "DENTIST", "name": "DENTIST", "x": 50, "y": 50,
         "attrs": [{"name": "DentistID", "key": "PK"},
                   {"name": "Name"}, {"name": "Address"},
                   {"name": "Phone"}, {"name": "Specialty"},
                   {"name": "Email"}, {"name": "YearsExperience"}]},
        {"id": "PATIENT", "name": "PATIENT", "x": 50, "y": 270,
         "attrs": [{"name": "PatientID", "key": "PK"},
                   {"name": "Name"}, {"name": "Address"},
                   {"name": "Phone"}, {"name": "DOB"},
                   {"name": "MaritalStatus"}, {"name": "Gender"},
                   {"name": "DentistID", "key": "FK"}]},
        {"id": "APPOINTMENT", "name": "APPOINTMENT", "x": 50, "y": 560,
         "attrs": [{"name": "AppointmentID", "key": "PK"},
                   {"name": "PatientID", "key": "FK"},
                   {"name": "Date"}, {"name": "StartTime"},
                   {"name": "EndTime"}]},
        {"id": "TREATMENT", "name": "TREATMENT", "x": 450, "y": 50,
         "attrs": [{"name": "TreatmentID", "key": "PK"},
                   {"name": "TreatmentName"}, {"name": "Price"},
                   {"name": "Image"}, {"name": "DentistID", "key": "FK"}]},
        {"id": "PATIENT_TREATMENT", "name": "PATIENT_TREATMENT", "x": 450,
         "y": 270, "attrs": [
             {"name": "PatientID", "key": "PK/FK"},
             {"name": "TreatmentID", "key": "PK/FK"},
             {"name": "ToothNumber"}, {"name": "Diagnosis"}]},
        {"id": "DISEASE_TREATMENT", "name": "DISEASE_TREATMENT", "x": 860,
         "y": 50, "attrs": [{"name": "TreatmentID", "key": "PK/FK"},
                            {"name": "DiseaseName"}]},
        {"id": "ORTHODONTIC_TREATMENT", "name": "ORTHODONTIC_TREATMENT",
         "x": 860, "y": 190, "attrs": [
             {"name": "TreatmentID", "key": "PK/FK"},
             {"name": "TypesOfBraces"}]},
    ],
    "relationships": [
        {"from": "DENTIST", "to": "PATIENT", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "treats"},
        {"from": "DENTIST", "to": "TREATMENT", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "performs",
         "waypoints": [[350, 126], [350, 108]]},
        {"from": "PATIENT", "to": "PATIENT_TREATMENT", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "receives",
         "waypoints": [[350, 355], [350, 319]]},
        {"from": "TREATMENT", "to": "PATIENT_TREATMENT", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "given in"},
        {"from": "PATIENT", "to": "APPOINTMENT", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "books"},
        {"from": "TREATMENT", "to": "DISEASE_TREATMENT", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "disease",
         "waypoints": [[760, 108], [760, 81]]},
        {"from": "TREATMENT", "to": "ORTHODONTIC_TREATMENT",
         "from_card": "one", "to_card": "one", "from_side": "right",
         "to_side": "left", "label": "orthodontic",
         "waypoints": [[780, 108], [780, 221]]},
    ],
}

ANSWERS = {
    "ICT450-2022-FEB-Q5": {
        "confidence": "medium",
        "assumptions": [
            "A volunteer is recorded once with VolunteerType (Student or "
            "Staff); student- and staff-specific attributes are outside the "
            "given requirements.",
            "The project assignment is an associative entity because it has "
            "its own attributes: start date, end date, hours, station and "
            "status.",
        ],
        "blocks": [
            p("The ERD treats a volunteer as one entity that may be a student "
              "or a staff member. The many-to-many participation between "
              "volunteers and projects becomes the ASSIGNMENT associative "
              "entity, which carries the assignment details. Each project is "
              "led by one faculty."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("Crow's Foot ERD for the volunteer management "
                            "system.", VOLUNTEER)]),
            sub("b", 4, "Two reports from the ERD.", [
                "Volunteer hours by project and faculty — join FACULTY, "
                "PROJECT and ASSIGNMENT to total Hours for each project, "
                "with the leading faculty shown.",
                "Volunteer participation report — list each volunteer with "
                "the projects, stations, start/end dates and status, so "
                "coordinators can see who is assigned where.",
                "Project status report — count assignments and total hours "
                "per project, grouped by status.",
            ]),
        ],
        "marking": [
            "a) 16 marks: VOLUNTEER (2), PROJECT (2), FACULTY (2), "
            "ASSIGNMENT with its five attributes (4), correct 1:N "
            "relationships and Crow's Foot cardinalities (4), primary and "
            "foreign keys (2).",
            "b) 2 marks for each of two relevant reports explained "
            "(2 × 2 = 4).",
        ],
    },
    "ICT450-2025-FEB-Q5": {
        "confidence": "medium",
        "assumptions": [
            "PROGRAM subtypes share the ProgramID key. Their subtype "
            "attributes are listed below the diagram rather than drawn as "
            "separate boxes, keeping the ERD readable.",
            "A marriage is represented as an associative entity linking two "
            "EMPLOYEE rows, because it has a marriage date and involves two "
            "employees.",
            "STUDIO deals with many SUPPLIERs, and SUPPLIER supplies many "
            "ART_MATERIALs; both many-to-many relationships are drawn "
            "directly and become junction tables at implementation.",
        ],
        "blocks": [
            p("The ERD separates studios, employees, programs, suppliers, "
              "materials and skills. The many-to-many relationships are drawn "
              "directly between entities. At implementation they become "
              "junction tables: STUDIO_SUPPLIER, SUPPLIER_MATERIAL and "
              "EMPLOYEE_SKILL. The PROGRAM subtype attributes are listed "
              "below the diagram."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[
                    erd("Crow's Foot ERD for the Excellent Art database.",
                        ART),
                    table("PROGRAM subtype attributes",
                          ["Program type", "Subtype attribute"],
                          [["Visual Art", "ClassType"],
                           ["Glass Painting", "ProgramLevel (1–5)"],
                           ["Handicraft", "CraftData"]]),
                ]),
            sub("b", 4, "Two reports from the ERD.", [
                "Studio programme report — list each studio with its "
                "programmes, programme type and subtype-specific details "
                "such as class type, program level or craft data.",
                "Supplier and material report — show each studio's suppliers "
                "and the art materials each supplier provides, with prices.",
                "Employee skills report — list employees by studio with "
                "their acquired skills.",
            ]),
        ],
        "marking": [
            "a) 16 marks: STUDIO, EMPLOYEE, PROGRAM and SUPPLIER (4); "
            "ART_MATERIAL, SKILL and MARRIAGE (3); PROGRAM subtype "
            "attributes (2); direct many-to-many relationships and their "
            "junction tables (3); keys and Crow's Foot cardinalities (4).",
            "b) 2 marks for each of two relevant reports explained "
            "(2 × 2 = 4).",
        ],
    },
    "ICT450-2018-JUN-Q5": {
        "confidence": "medium",
        "assumptions": [
            "A treatment is a treatment type performed by one dentist; the "
            "patient-treatment relationship stores the tooth number and "
            "diagnosis for each patient.",
            "APPOINTMENT belongs to a patient; the requirements do not list "
            "a dentist attribute for an appointment, so none is invented.",
            "DISEASE_TREATMENT and ORTHODONTIC_TREATMENT are subtypes of "
            "TREATMENT.",
        ],
        "blocks": [
            p("The ERD models dentists, patients, treatments and appointments. "
              "The many-to-many treatment history is resolved by "
              "PATIENT_TREATMENT, which carries the tooth number and "
              "diagnosis. TREATMENT is specialised into disease and "
              "orthodontic subtypes."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("Crow's Foot ERD for the dental clinic.", DENTAL)]),
            sub("b", 4, "Two reports from the ERD.", [
                "Patient treatment history — list each patient's treatments, "
                "tooth numbers, diagnoses and treating dentist.",
                "Dentist workload report — count patients, appointments and "
                "treatments performed by each dentist.",
                "Orthodontic case report — list orthodontic treatments with "
                "the type of braces and the patients concerned.",
            ]),
        ],
        "marking": [
            "a) 16 marks: DENTIST and PATIENT with attributes and the 1:N "
            "relationship (4); TREATMENT and PATIENT_TREATMENT with tooth "
            "number and diagnosis (4); APPOINTMENT (2); disease and "
            "orthodontic subtypes (3); keys and Crow's Foot cardinalities "
            "(3).",
            "b) 2 marks for each of two relevant reports explained "
            "(2 × 2 = 4).",
        ],
    },
}
