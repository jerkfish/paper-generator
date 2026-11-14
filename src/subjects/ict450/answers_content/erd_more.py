"""Model answers for the remaining ERD questions (V4 completion)."""
from __future__ import annotations

from ._blocks import erd, p, sub

COLLECTOR_ERD = {
    "width": 1500,
    "height": 780,
    "entities": [
        {"id": "COLLECTOR", "name": "COLLECTOR", "x": 50, "y": 60,
         "attrs": [{"name": "CollectorID", "key": "PK"},
                   {"name": "Name"}, {"name": "Address"},
                   {"name": "Phone"}, {"name": "Email"}]},
        {"id": "STAFF", "name": "STAFF", "x": 50, "y": 320,
         "attrs": [{"name": "StaffID", "key": "PK"},
                   {"name": "Name"}, {"name": "Phone"}, {"name": "Email"},
                   {"name": "ManagerID", "key": "FK"}]},
        {"id": "SALE", "name": "SALE", "x": 430, "y": 200,
         "attrs": [{"name": "SaleID", "key": "PK"},
                   {"name": "SaleDate"}, {"name": "SaleTime"},
                   {"name": "Quantity"}, {"name": "TotalSale"},
                   {"name": "CollectorID", "key": "FK"},
                   {"name": "StaffID", "key": "FK"},
                   {"name": "CollectibleID", "key": "FK"}]},
        {"id": "COLLECTIBLE", "name": "COLLECTIBLE", "x": 820, "y": 60,
         "attrs": [{"name": "CollectibleID", "key": "PK"},
                   {"name": "Name"}, {"name": "Description"},
                   {"name": "Price"}, {"name": "TypeID", "key": "FK"}]},
        {"id": "TYPE", "name": "TYPE", "x": 820, "y": 300,
         "attrs": [{"name": "TypeID", "key": "PK"},
                   {"name": "TypeName"}]},
        {"id": "MEMORABILIA", "name": "MEMORABILIA", "x": 1160, "y": 60,
         "attrs": [{"name": "CollectibleID", "key": "PK/FK"},
                   {"name": "MovieName"}]},
        {"id": "STATUE", "name": "STATUE", "x": 1160, "y": 170,
         "attrs": [{"name": "CollectibleID", "key": "PK/FK"},
                   {"name": "BuildType"}]},
        {"id": "MODEL_KIT", "name": "MODEL_KIT", "x": 1160, "y": 280,
         "attrs": [{"name": "CollectibleID", "key": "PK/FK"},
                   {"name": "Scale"}]},
        {"id": "ACTION_FIGURE", "name": "ACTION_FIGURE", "x": 1160,
         "y": 390, "attrs": [{"name": "CollectibleID", "key": "PK/FK"},
                             {"name": "WaveYear"}]},
        {"id": "BRICKS", "name": "BRICKS", "x": 1160, "y": 500,
         "attrs": [{"name": "CollectibleID", "key": "PK/FK"},
                   {"name": "NumberOfPieces"}]},
    ],
    "relationships": [
        {"from": "COLLECTOR", "to": "SALE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "buys"},
        {"from": "STAFF", "to": "SALE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "bottom",
         "label": "manages",
         "waypoints": [[330, 392], [330, 415], [535, 415]]},
        {"from": "COLLECTIBLE", "to": "SALE", "from_card": "one",
         "to_card": "many", "from_side": "left", "to_side": "right",
         "label": "sold in",
         "waypoints": [[760, 132], [760, 300], [640, 300]]},
        {"from": "TYPE", "to": "COLLECTIBLE", "from_card": "one",
         "to_card": "many", "from_side": "top", "to_side": "bottom",
         "label": "classifies"},
        {"from": "COLLECTIBLE", "to": "MEMORABILIA", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "is a"},
        {"from": "COLLECTIBLE", "to": "STATUE", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "is a"},
        {"from": "COLLECTIBLE", "to": "MODEL_KIT", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "is a"},
        {"from": "COLLECTIBLE", "to": "ACTION_FIGURE", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "is a"},
        {"from": "COLLECTIBLE", "to": "BRICKS", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "is a"},
        {"from": "STAFF", "to": "STAFF", "from_card": "one",
         "to_card": "many", "from_side": "left", "to_side": "top",
         "label": "manages",
         "waypoints": [[43, 280], [152, 280]]},
    ],
}

CAR_ERD = {
    "width": 1300,
    "height": 800,
    "entities": [
        {"id": "MANAGER", "name": "MANAGER", "x": 50, "y": 60,
         "attrs": [{"name": "ManagerID", "key": "PK"},
                   {"name": "FirstName"}, {"name": "LastName"}]},
        {"id": "SALESPERSON", "name": "SALESPERSON", "x": 50, "y": 250,
         "attrs": [{"name": "SalespersonID", "key": "PK"},
                   {"name": "FirstName"}, {"name": "LastName"},
                   {"name": "ManagerID", "key": "FK"}]},
        {"id": "CUSTOMER", "name": "CUSTOMER", "x": 50, "y": 500,
         "attrs": [{"name": "CustomerID", "key": "PK"},
                   {"name": "FirstName"}, {"name": "LastName"},
                   {"name": "Phone"}, {"name": "Address"}, {"name": "City"},
                   {"name": "State"}, {"name": "Country"},
                   {"name": "SalespersonID", "key": "FK"}]},
        {"id": "VEHICLE", "name": "VEHICLE", "x": 500, "y": 60,
         "attrs": [{"name": "VIN", "key": "PK"}, {"name": "Category"},
                   {"name": "Model"}, {"name": "Year"}]},
        {"id": "CAR", "name": "CAR", "x": 850, "y": 60,
         "attrs": [{"name": "VIN", "key": "PK/FK"},
                   {"name": "EngineSize"}]},
        {"id": "TRUCK", "name": "TRUCK", "x": 850, "y": 170,
         "attrs": [{"name": "VIN", "key": "PK/FK"},
                   {"name": "Tonnage"}]},
        {"id": "SUV", "name": "SUV", "x": 850, "y": 280,
         "attrs": [{"name": "VIN", "key": "PK/FK"},
                   {"name": "NumberOfSeats"}]},
        {"id": "INVOICE", "name": "INVOICE", "x": 500, "y": 330,
         "attrs": [{"name": "InvoiceNo", "key": "PK"},
                   {"name": "InvoiceDate"},
                   {"name": "SalespersonID", "key": "FK"},
                   {"name": "VIN", "key": "FK"},
                   {"name": "CustomerID", "key": "FK"}]},
    ],
    "relationships": [
        {"from": "MANAGER", "to": "SALESPERSON", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "manages"},
        {"from": "SALESPERSON", "to": "CUSTOMER", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "serves"},
        {"from": "SALESPERSON", "to": "INVOICE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "issues",
         "waypoints": [[360, 311], [360, 395]]},
        {"from": "CUSTOMER", "to": "INVOICE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "receives",
         "waypoints": [[330, 616], [330, 420]]},
        {"from": "VEHICLE", "to": "INVOICE", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "sold on"},
        {"from": "VEHICLE", "to": "CAR", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "is a", "waypoints": [[780, 132], [780, 150]]},
        {"from": "VEHICLE", "to": "TRUCK", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "is a", "waypoints": [[800, 132], [800, 200]]},
        {"from": "VEHICLE", "to": "SUV", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "is a", "waypoints": [[820, 132], [820, 250]]},
    ],
}

CONSULT_ERD = {
    "width": 1400,
    "height": 800,
    "entities": [
        {"id": "CLIENT", "name": "CLIENT", "x": 50, "y": 60,
         "attrs": [{"name": "ClientID", "key": "PK"},
                   {"name": "ClientName"}, {"name": "Address"},
                   {"name": "Phone"}]},
        {"id": "PROJECT", "name": "PROJECT", "x": 400, "y": 60,
         "attrs": [{"name": "ProjectID", "key": "PK"},
                   {"name": "ProjectName"}, {"name": "StartDate"},
                   {"name": "EndDate"}, {"name": "ClientID", "key": "FK"},
                   {"name": "LeadEmployeeID", "key": "FK"},
                   {"name": "CoordinatorEmployeeID", "key": "FK"}]},
        {"id": "EMPLOYEE", "name": "EMPLOYEE", "x": 800, "y": 60,
         "attrs": [{"name": "EmployeeID", "key": "PK"},
                   {"name": "Name"}, {"name": "Address"},
                   {"name": "Phone"}]},
        {"id": "JOB", "name": "JOB", "x": 800, "y": 300,
         "attrs": [{"name": "JobID", "key": "PK"},
                   {"name": "JobDescription"}]},
        {"id": "EMPLOYEE_JOB", "name": "EMPLOYEE_JOB", "x": 1120, "y": 300,
         "attrs": [{"name": "EmployeeID", "key": "PK/FK"},
                   {"name": "JobID", "key": "PK/FK"}]},
        {"id": "ASSIGNMENT", "name": "ASSIGNMENT", "x": 400, "y": 430,
         "attrs": [{"name": "EmployeeID", "key": "PK/FK"},
                   {"name": "ProjectID", "key": "PK/FK"},
                   {"name": "AssignHours"}, {"name": "Charge"}]},
    ],
    "relationships": [
        {"from": "CLIENT", "to": "PROJECT", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "contracts"},
        {"from": "EMPLOYEE", "to": "PROJECT", "from_card": "one",
         "to_card": "many", "from_side": "left", "to_side": "right",
         "label": "leads", "waypoints": [[760, 121], [760, 150]]},
        {"from": "EMPLOYEE", "to": "PROJECT", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "bottom",
         "label": "coordinates",
         "waypoints": [[902, 240], [902, 300], [500, 300], [500, 230]]},
        {"from": "EMPLOYEE", "to": "ASSIGNMENT", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "right",
         "label": "works on",
         "waypoints": [[902, 380], [700, 380], [700, 480], [610, 480]]},
        {"from": "PROJECT", "to": "ASSIGNMENT", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "has"},
        {"from": "EMPLOYEE", "to": "EMPLOYEE_JOB", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "top",
         "label": "has", "waypoints": [[1050, 121], [1050, 280]]},
        {"from": "JOB", "to": "EMPLOYEE_JOB", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "defines"},
    ],
}

CHANTEQ_ERD = {
    "width": 1300,
    "height": 700,
    "entities": [
        {"id": "PRODUCT", "name": "PRODUCT", "x": 50, "y": 60,
         "attrs": [{"name": "ProductID", "key": "PK"},
                   {"name": "ProductName"}]},
        {"id": "SKU", "name": "SKU", "x": 350, "y": 60,
         "attrs": [{"name": "SKUNumber", "key": "PK"},
                   {"name": "SKUDescription"},
                   {"name": "ProductID", "key": "FK"},
                   {"name": "ColorID", "key": "FK"}]},
        {"id": "COLOR", "name": "COLOR", "x": 650, "y": 60,
         "attrs": [{"name": "ColorID", "key": "PK"},
                   {"name": "ColorDescription"}]},
        {"id": "RETAILER", "name": "RETAILER", "x": 50, "y": 300,
         "attrs": [{"name": "RetailerID", "key": "PK"},
                   {"name": "RetailerName"}, {"name": "Phone"}]},
        {"id": "RETAILER_PRODUCT", "name": "RETAILER_PRODUCT", "x": 350,
         "y": 300, "attrs": [{"name": "RetailerID", "key": "PK/FK"},
                              {"name": "ProductID", "key": "PK/FK"}]},
        {"id": "STORE", "name": "STORE", "x": 650, "y": 300,
         "attrs": [{"name": "StoreID", "key": "PK"},
                   {"name": "StoreAddress"}, {"name": "CustomerID"},
                   {"name": "RetailerID", "key": "FK"}]},
    ],
    "relationships": [
        {"from": "PRODUCT", "to": "SKU", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "has"},
        {"from": "COLOR", "to": "SKU", "from_card": "one",
         "to_card": "many", "from_side": "left", "to_side": "right",
         "label": "colors"},
        {"from": "PRODUCT", "to": "RETAILER_PRODUCT", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "left",
         "label": "distributed by",
         "waypoints": [[152, 250], [300, 250], [300, 340]]},
        {"from": "RETAILER", "to": "RETAILER_PRODUCT", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "contracts"},
        {"from": "RETAILER", "to": "STORE", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "left",
         "label": "operates",
         "waypoints": [[152, 450], [600, 450], [600, 361]]},
    ],
}

HIKER_ERD = {
    "width": 1300,
    "height": 800,
    "entities": [
        {"id": "HIKER", "name": "HIKER", "x": 50, "y": 60,
         "attrs": [{"name": "HikerID", "key": "PK"},
                   {"name": "FullName"}, {"name": "Address"},
                   {"name": "Phone"}, {"name": "Email"}]},
        {"id": "FAMILY", "name": "FAMILY_MEMBER", "x": 50, "y": 300,
         "attrs": [{"name": "FamilyID", "key": "PK"},
                   {"name": "FullName"}, {"name": "EmergencyContact"},
                   {"name": "Address"}, {"name": "Email"},
                   {"name": "HikerID", "key": "FK"}]},
        {"id": "TRIP", "name": "TRIP", "x": 450, "y": 60,
         "attrs": [{"name": "TripID", "key": "PK"},
                   {"name": "TripName"}, {"name": "ApproxLength"},
                   {"name": "Fees"}, {"name": "MountainID", "key": "FK"}]},
        {"id": "MOUNTAIN", "name": "MOUNTAIN", "x": 850, "y": 60,
         "attrs": [{"name": "MountainID", "key": "PK"},
                   {"name": "MountainName"}, {"name": "Height"},
                   {"name": "Country"}]},
        {"id": "GUIDE", "name": "GUIDE", "x": 450, "y": 300,
         "attrs": [{"name": "GuideID", "key": "PK"},
                   {"name": "FullName"}, {"name": "Contact"},
                   {"name": "Address"}, {"name": "HireDate"}]},
        {"id": "TRIP_HIKER", "name": "TRIP_HIKER", "x": 850, "y": 300,
         "attrs": [{"name": "TripID", "key": "PK/FK"},
                   {"name": "HikerID", "key": "PK/FK"},
                   {"name": "StartDate"}, {"name": "EndDate"}]},
        {"id": "TRIP_GUIDE", "name": "TRIP_GUIDE", "x": 850, "y": 500,
         "attrs": [{"name": "TripID", "key": "PK/FK"},
                   {"name": "GuideID", "key": "PK/FK"},
                   {"name": "Payment"}]},
    ],
    "relationships": [
        {"from": "HIKER", "to": "FAMILY", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "gives"},
        {"from": "HIKER", "to": "TRIP_HIKER", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "joins", "waypoints": [[760, 132], [760, 361]]},
        {"from": "TRIP", "to": "TRIP_HIKER", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "has", "waypoints": [[780, 132], [780, 320]]},
        {"from": "GUIDE", "to": "TRIP_GUIDE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "paid", "waypoints": [[780, 361], [780, 540]]},
        {"from": "TRIP", "to": "TRIP_GUIDE", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "uses",
         "waypoints": [[552, 230], [552, 280], [952, 280], [952, 500]]},
        {"from": "MOUNTAIN", "to": "TRIP", "from_card": "one",
         "to_card": "many", "from_side": "left", "to_side": "right",
         "label": "located on"},
    ],
}

POLICE_ERD = {
    "width": 1300,
    "height": 760,
    "entities": [
        {"id": "OFFICER", "name": "OFFICER", "x": 50, "y": 60,
         "attrs": [{"name": "PoliceID", "key": "PK"},
                   {"name": "Name"}, {"name": "Position"},
                   {"name": "Email"}]},
        {"id": "DUTY", "name": "DUTY", "x": 50, "y": 300,
         "attrs": [{"name": "DutyID", "key": "PK"},
                   {"name": "DutyName"}]},
        {"id": "OFFICER_DUTY", "name": "OFFICER_DUTY", "x": 350, "y": 300,
         "attrs": [{"name": "PoliceID", "key": "PK/FK"},
                   {"name": "DutyID", "key": "PK/FK"},
                   {"name": "DutyDate"}, {"name": "DutyTime"}]},
        {"id": "SUMMON", "name": "SUMMON", "x": 650, "y": 60,
         "attrs": [{"name": "SummonID", "key": "PK"},
                   {"name": "SummonDate"},
                   {"name": "PoliceID", "key": "FK"},
                   {"name": "StudentID", "key": "FK"}]},
        {"id": "STUDENT", "name": "STUDENT", "x": 650, "y": 300,
         "attrs": [{"name": "StudentID", "key": "PK"},
                   {"name": "StudentName"}]},
        {"id": "OFFENSE", "name": "OFFENSE", "x": 950, "y": 60,
         "attrs": [{"name": "OffenseID", "key": "PK"},
                   {"name": "OffenseName"}, {"name": "Description"},
                   {"name": "FeeRate"}]},
        {"id": "SUMMON_OFFENSE", "name": "SUMMON_OFFENSE", "x": 950,
         "y": 300, "attrs": [{"name": "SummonID", "key": "PK/FK"},
                              {"name": "OffenseID", "key": "PK/FK"}]},
    ],
    "relationships": [
        {"from": "OFFICER", "to": "OFFICER_DUTY", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "assigned", "waypoints": [[300, 121], [300, 361]]},
        {"from": "DUTY", "to": "OFFICER_DUTY", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "carried out"},
        {"from": "OFFICER", "to": "SUMMON", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "issues", "waypoints": [[620, 121], [620, 100]]},
        {"from": "STUDENT", "to": "SUMMON", "from_card": "one",
         "to_card": "many", "from_side": "top", "to_side": "bottom",
         "label": "receives"},
        {"from": "SUMMON", "to": "SUMMON_OFFENSE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "top",
         "label": "contains",
         "waypoints": [[900, 121], [900, 280]]},
        {"from": "OFFENSE", "to": "SUMMON_OFFENSE", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "listed"},
    ],
}

FOOTBALL_ERD = {
    "width": 1300,
    "height": 900,
    "entities": [
        {"id": "TOURNAMENT", "name": "TOURNAMENT", "x": 50, "y": 60,
         "attrs": [{"name": "TournamentID", "key": "PK"},
                   {"name": "TournamentName"}, {"name": "StartDate"},
                   {"name": "EndDate"}, {"name": "Organizer"}]},
        {"id": "FIXTURE", "name": "FIXTURE", "x": 400, "y": 60,
         "attrs": [{"name": "FixtureID", "key": "PK"},
                   {"name": "KickOffTime"},
                   {"name": "TournamentID", "key": "FK"}]},
        {"id": "MATCH", "name": "MATCH", "x": 750, "y": 60,
         "attrs": [{"name": "MatchID", "key": "PK"},
                   {"name": "MatchDate"}, {"name": "HomeTeamID", "key": "FK"},
                   {"name": "AwayTeamID", "key": "FK"}, {"name": "Result"},
                   {"name": "VenueID", "key": "FK"},
                   {"name": "FixtureID", "key": "FK"}]},
        {"id": "TEAM", "name": "TEAM", "x": 400, "y": 330,
         "attrs": [{"name": "TeamID", "key": "PK"},
                   {"name": "TeamName"}, {"name": "CoachName"}]},
        {"id": "PLAYER", "name": "PLAYER", "x": 400, "y": 520,
         "attrs": [{"name": "PlayerID", "key": "PK"},
                   {"name": "PlayerName"}, {"name": "DOB"},
                   {"name": "Nationality"}, {"name": "Position"},
                   {"name": "TeamID", "key": "FK"}]},
        {"id": "VENUE", "name": "VENUE", "x": 1050, "y": 60,
         "attrs": [{"name": "VenueID", "key": "PK"},
                   {"name": "VenueName"}, {"name": "Location"},
                   {"name": "SeatingCapacity"}]},
    ],
    "relationships": [
        {"from": "TOURNAMENT", "to": "FIXTURE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "schedules"},
        {"from": "FIXTURE", "to": "MATCH", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "consists of"},
        {"from": "TEAM", "to": "PLAYER", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "has"},
        {"from": "TEAM", "to": "MATCH", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "home", "waypoints": [[700, 401], [700, 180]]},
        {"from": "TEAM", "to": "MATCH", "from_card": "one",
         "to_card": "many", "from_side": "top", "to_side": "left",
         "label": "away", "waypoints": [[502, 280], [502, 300], [700, 300]]},
        {"from": "VENUE", "to": "MATCH", "from_card": "one",
         "to_card": "many", "from_side": "left", "to_side": "right",
         "label": "hosts"},
    ],
}

CLEAN_ERD = {
    "width": 1400,
    "height": 900,
    "entities": [
        {"id": "COLLECTOR", "name": "COLLECTOR", "x": 50, "y": 60,
         "attrs": [{"name": "CollectorID", "key": "PK"},
                   {"name": "Name"}, {"name": "Phone"},
                   {"name": "SupervisorID", "key": "FK"}]},
        {"id": "DUTY", "name": "DUTY", "x": 50, "y": 300,
         "attrs": [{"name": "DutyID", "key": "PK"},
                   {"name": "DutyDate"},
                   {"name": "CollectorID", "key": "FK"},
                   {"name": "LocalityID", "key": "FK"},
                   {"name": "VehicleID", "key": "FK"}]},
        {"id": "LOCALITY", "name": "LOCALITY", "x": 450, "y": 60,
         "attrs": [{"name": "LocalityID", "key": "PK"},
                   {"name": "LocalityName"}, {"name": "Postcode"}]},
        {"id": "VEHICLE", "name": "VEHICLE", "x": 450, "y": 260,
         "attrs": [{"name": "PlateNumber", "key": "PK"}, {"name": "Model"},
                   {"name": "Size"}]},
        {"id": "HOUSE", "name": "HOUSE", "x": 450, "y": 430,
         "attrs": [{"name": "HouseID", "key": "PK"}, {"name": "Address"},
                   {"name": "Category"},
                   {"name": "LocalityID", "key": "FK"}]},
        {"id": "WASTE", "name": "WASTE", "x": 850, "y": 60,
         "attrs": [{"name": "WasteID", "key": "PK"}, {"name": "WasteName"},
                   {"name": "Category"}]},
        {"id": "DUTY_WASTE", "name": "DUTY_WASTE", "x": 850, "y": 260,
         "attrs": [{"name": "DutyID", "key": "PK/FK"},
                   {"name": "WasteID", "key": "PK/FK"},
                   {"name": "Weight"}]},
    ],
    "relationships": [
        {"from": "COLLECTOR", "to": "DUTY", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "assigned"},
        {"from": "COLLECTOR", "to": "COLLECTOR", "from_card": "one",
         "to_card": "many", "from_side": "left", "to_side": "bottom",
         "label": "supervises",
         "waypoints": [[20, 121], [20, 250], [152, 250]]},
        {"from": "LOCALITY", "to": "DUTY", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "right",
         "label": "scheduled", "waypoints": [[552, 200], [552, 361]]},
        {"from": "VEHICLE", "to": "DUTY", "from_card": "one",
         "to_card": "many", "from_side": "left", "to_side": "right",
         "label": "used", "waypoints": [[300, 321], [300, 361]]},
        {"from": "LOCALITY", "to": "HOUSE", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "contains"},
        {"from": "DUTY", "to": "DUTY_WASTE", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "collects", "waypoints": [[700, 361], [700, 321]]},
        {"from": "WASTE", "to": "DUTY_WASTE", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "recorded"},
    ],
}

FRESH_ERD = {
    "width": 1200,
    "height": 760,
    "entities": [
        {"id": "CUSTOMER", "name": "CUSTOMER", "x": 50, "y": 60,
         "attrs": [{"name": "CustomerID", "key": "PK"}, {"name": "Name"},
                   {"name": "Email"}, {"name": "Address"}]},
        {"id": "ORDER", "name": "ORDER", "x": 400, "y": 60,
         "attrs": [{"name": "OrderID", "key": "PK"}, {"name": "OrderDate"},
                   {"name": "CustomerID", "key": "FK"},
                   {"name": "SlotID", "key": "FK"}]},
        {"id": "PRODUCT", "name": "PRODUCT", "x": 750, "y": 60,
         "attrs": [{"name": "ProductID", "key": "PK"}, {"name": "Name"},
                   {"name": "Price"}, {"name": "Category"}]},
        {"id": "ORDER_ITEM", "name": "ORDER_ITEM", "x": 400, "y": 300,
         "attrs": [{"name": "OrderID", "key": "PK/FK"},
                   {"name": "ProductID", "key": "PK/FK"},
                   {"name": "Quantity"}]},
        {"id": "INVOICE", "name": "INVOICE", "x": 750, "y": 300,
         "attrs": [{"name": "InvoiceNo", "key": "PK"},
                   {"name": "InvoiceDate"}, {"name": "TotalAmount"},
                   {"name": "OrderID", "key": "FK"}]},
        {"id": "SLOT", "name": "DELIVERY_SLOT", "x": 50, "y": 300,
         "attrs": [{"name": "SlotID", "key": "PK"}, {"name": "Date"},
                   {"name": "Time"}, {"name": "Status"}]},
    ],
    "relationships": [
        {"from": "CUSTOMER", "to": "ORDER", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "places"},
        {"from": "ORDER", "to": "ORDER_ITEM", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "contains"},
        {"from": "PRODUCT", "to": "ORDER_ITEM", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "right",
         "label": "appears in", "waypoints": [[852, 270], [852, 380], [620, 380]]},
        {"from": "ORDER", "to": "INVOICE", "from_card": "one",
         "to_card": "one", "from_side": "right", "to_side": "left",
         "label": "issued"},
        {"from": "SLOT", "to": "ORDER", "from_card": "one",
         "to_card": "many", "from_side": "top", "to_side": "bottom",
         "label": "scheduled", "waypoints": [[152, 250], [152, 220], [502, 220], [502, 240]]},
    ],
}

ANSWERS = {
    "ICT450-2018-DEC-Q5": {
        "confidence": "medium",
        "assumptions": ["A sale transaction records one collectible line; "
                        "the manager relationship is recursive on STAFF."],
        "blocks": [
            p("The ERD separates collector, staff, sale and collectible data. "
              "SALE resolves the many-to-many purchase between collectors and "
              "collectibles, and COLLECTIBLE is specialised into the five "
              "collectible types."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("Collector's Hub ERD.", COLLECTOR_ERD)]),
            sub("b", 4, "Two reports from the ERD.", [
                "Sales by collectible type — total quantity and sales value "
                "per type, with the subtype attributes.",
                "Staff performance report — number and value of sales managed "
                "by each staff member, grouped by manager.",
            ]),
        ],
        "marking": [
            "a) 16 marks: collector, staff, sale and collectible entities (6); "
            "type and five subtype entities (4); relationships and "
            "cardinalities (4); keys (2).",
            "b) 2 marks for each report (4).",
        ],
    },
    "ICT450-2019-DEC-Q5": {
        "confidence": "medium",
        "assumptions": ["A vehicle is one of Car, Truck or SUV, and an "
                        "invoice records one vehicle sale."],
        "blocks": [
            p("The ERD models managers, salespersons, customers, vehicles and "
              "invoices. Vehicle is specialised into Car, Truck and SUV."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("Car Dealership System ERD.", CAR_ERD)]),
            sub("b", 4, "Two reports from the ERD.", [
                "Salesperson performance — invoices and sales value per "
                "salesperson, grouped by manager.",
                "Vehicle category report — number and value of cars, trucks "
                "and SUVs sold.",
            ]),
        ],
        "marking": [
            "a) 16 marks: manager/salesperson/customer (5); vehicle and three "
            "subtypes (5); invoice and relationships (4); keys (2).",
            "b) 2 marks for each report (4).",
        ],
    },
    "ICT450-2019-JUN-Q5": {
        "confidence": "medium",
        "assumptions": ["Lead and coordinate are optional roles; the diagram "
                        "labels them 0..1 in the answer text and uses one-side "
                        "Crow's Foot for readability."],
        "blocks": [
            p("The ERD models clients, projects, employees, jobs and "
              "assignments. Employees may hold many jobs and work on many "
              "projects; one employee leads and another coordinates each "
              "project."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("BestEverConsult ERD.", CONSULT_ERD)]),
            sub("b", 4, "Two reports from the ERD.", [
                "Project staffing report — employees assigned to each project "
                "with hours and charge.",
                "Employee utilisation report — jobs held and projects "
                "assigned per employee.",
            ]),
        ],
        "marking": [
            "a) 16 marks: client/project/employee/job entities (5); job and "
            "assignment associative entities (4); lead/coordinate/assignment "
            "relationships (5); keys (2).",
            "b) 2 marks for each report (4).",
        ],
    },
    "ICT450-2023-FEB-Q5": {
        "confidence": "medium",
        "assumptions": ["A store is identified by StoreID and carries a "
                        "CustomerID for shipping confirmation; a retailer "
                        "distributes many products through a contract."],
        "blocks": [
            p("The ERD models products, SKUs, colours, retailers and stores. "
              "SKU is the product-colour variant, and RETAILER_PRODUCT "
              "records the distribution contract."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("Chanteq Boutique ERD.", CHANTEQ_ERD)]),
            sub("b", 4, "Two reports from the ERD.", [
                "Product distribution report — products and the retailers "
                "contracted to distribute them.",
                "SKU and colour catalogue — every SKU with its product, colour "
                "description and store availability.",
            ]),
        ],
        "marking": [
            "a) 16 marks: product/SKU/colour (5); retailer and contract (4); "
            "store and relationships (5); keys (2).",
            "b) 2 marks for each report (4).",
        ],
    },
    "ICT450-2023-JUL-Q5": {
        "confidence": "medium",
        "assumptions": ["Payment is an attribute of the trip-guide "
                        "assignment; a hiker may have several family members."],
        "blocks": [
            p("The ERD models hikers, family members, trips, mountains, "
              "guides and the two associative entities that record trip "
              "participation and guide payment."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("Bristledbeast ERD.", HIKER_ERD)]),
            sub("b", 4, "Two reports from the ERD.", [
                "Trip participation report — hikers, start/end dates and fees "
                "for each trip.",
                "Guide payment report — trips assigned to each guide with the "
                "recorded payment.",
            ]),
        ],
        "marking": [
            "a) 16 marks: hiker/family/trip/mountain (6); guide and two "
            "associative entities (5); relationships and cardinalities (3); "
            "keys (2).",
            "b) 2 marks for each report (4).",
        ],
    },
    "ICT450-2024-JAN-Q5": {
        "confidence": "medium",
        "assumptions": ["Each summon is issued by one officer to one student "
                        "and contains one or more offenses; duty assignment "
                        "carries the date and time."],
        "blocks": [
            p("The ERD models officers, duties, summonses, students and "
              "offenses. OFFICER_DUTY records duty dates, and "
              "SUMMON_OFFENSE resolves the many-to-many summons-offense "
              "relationship."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("Auxiliary police ERD.", POLICE_ERD)]),
            sub("b", 4, "Two pieces of information from the ERD.", [
                "Which officers are assigned to each duty and when.",
                "Which offenses and fees are attached to each student "
                "summons.",
            ]),
        ],
        "marking": [
            "a) 16 marks: officer/duty/student (5); summon and offense (4); "
            "associative entities and relationships (5); keys (2).",
            "b) 2 marks for each information item (4).",
        ],
    },
    "ICT450-2024-JUL-Q5": {
        "confidence": "medium",
        "assumptions": ["A match belongs to one fixture; home and away teams "
                        "are both foreign keys to TEAM."],
        "blocks": [
            p("The ERD models tournaments, fixtures, matches, teams, players "
              "and venues. A fixture belongs to a tournament and contains "
              "matches; each match has a home team, an away team and a "
              "venue."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("S2 football club ERD.", FOOTBALL_ERD)]),
            sub("b", 4, "Four pieces of information from the ERD.", [
                "The fixture schedule for each tournament.",
                "The players registered under each team.",
                "The results and venues of all matches.",
                "The home and away teams for each match.",
            ]),
        ],
        "marking": [
            "a) 16 marks: tournament/fixture/match (5); team/player/venue (5); "
            "relationships and cardinalities (4); keys (2).",
            "b) 1 mark for each of four information items (4).",
        ],
    },
    "ICT450-2025-JUL-Q5": {
        "confidence": "medium",
        "assumptions": ["Supervisor is a recursive role on COLLECTOR; a "
                        "duty collects many waste types with a weight per "
                        "waste type."],
        "blocks": [
            p("The ERD models collectors, duties, localities, vehicles, "
              "houses and waste types. The supervisor relationship is "
              "recursive on COLLECTOR, and DUTY_WASTE records the weight "
              "collected for each waste type."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("Clean Environment ERD.", CLEAN_ERD)]),
            sub("b", 4, "Two pieces of information from the ERD.", [
                "The collection duties assigned to each collector, with date, "
                "locality and vehicle.",
                "The total weight collected for each waste type and locality.",
            ]),
        ],
        "marking": [
            "a) 16 marks: collector/duty/locality/vehicle (6); house and waste "
            "(4); recursive supervisor and DUTY_WASTE relationships (4); keys "
            "(2).",
            "b) 2 marks for each information item (4).",
        ],
    },
    "ICT450-2026-FEB-Q5": {
        "confidence": "high",
        "assumptions": ["An order has exactly one invoice and one delivery "
                        "slot; an order can contain many products."],
        "blocks": [
            p("The ERD models customers, orders, products, order lines, "
              "invoices and delivery slots. ORDER_ITEM resolves the "
              "many-to-many order-product relationship."),
            sub("a", 16, "Construct the ERD with Crow's Foot notation.",
                blocks=[erd("FreshBasket ERD.", FRESH_ERD)]),
            sub("b", 4, "Two pieces of information from the ERD.", [
                "The products and quantities in each customer order.",
                "The invoice total and delivery slot for each order.",
            ]),
        ],
        "marking": [
            "a) 16 marks: customer/order/product (5); order item, invoice and "
            "delivery slot (5); relationships and cardinalities (4); keys "
            "(2).",
            "b) 2 marks for each information item (4).",
        ],
    },
}
