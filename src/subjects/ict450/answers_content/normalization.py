"""Model answers for the normalization questions used in seeds 1–3."""
from __future__ import annotations

from ._blocks import p, schema, sub, table

ANSWERS = {
    "ICT450-2019-DEC-Q4": {
        "confidence": "high",
        "assumptions": [
            "LineTotal is Quantity × ItemPrice; TotalAmount is the sum of "
            "LineTotal for the invoice.",
            "The invoice is treated as one order form with a repeating group "
            "of item lines.",
        ],
        "blocks": [
            p("The invoice in Figure 3.0 contains customer, invoice and item "
              "data in one form. The item lines repeat for the same invoice, "
              "so the form is first flattened to a one-row-per-item relation "
              "in 1NF."),
            sub("a", 2, "Relational schema for the order form.", blocks=[
                schema([
                    "INVOICE_ITEM (InvoiceNo, InvoiceDate, CustomerNo, "
                    "CustomerName, CustomerAddress, ItemNo, ItemName, Model, "
                    "Quantity, ItemPrice, LineTotal, TotalAmount)",
                ], "Order-form relation in 1NF (one row per item line)."),
                table("Invoice header data",
                      ["InvoiceNo", "InvoiceDate", "CustomerNo",
                       "CustomerName", "Address", "TotalAmount"],
                      [["2088", "26-Aug-2019", "153",
                        "Puan Adriana Yusuf",
                        "Taman Rasah Jaya, Seremban", "902.95"]]),
                table("Item lines",
                      ["InvoiceNo", "ItemNo", "ItemName", "Model", "Qty",
                       "ItemPrice", "LineTotal"],
                      [["2088", "CRB101", "Electric Kids Car", "Buggati",
                        "1", "559.00", "559.00"],
                       ["2088", "LEG101", "City Fire Ladder Truck", "LEGO",
                        "1", "184.00", "184.00"],
                       ["2088", "LEG102", "City ATV Race Team", "LEGO",
                        "2", "79.99", "159.98"]]),
            ]),
            sub("b", 2, "Primary key of the relation.", blocks=[
                p("The primary key is the composite (InvoiceNo, ItemNo). "
                  "InvoiceNo alone is not unique because one invoice has many "
                  "items, and ItemNo alone is not unique because the same item "
                  "can appear on many invoices."),
            ]),
            sub("c", 16, "Normalise the relation to 3NF.", blocks=[
                p("Step 1 — First normal form (1NF): the relation in (a) "
                  "already stores one item line per row and all values are "
                  "atomic. Its key is (InvoiceNo, ItemNo)."),
                schema([
                    "INVOICE_ITEM_1NF (InvoiceNo, InvoiceDate, CustomerNo, "
                    "CustomerName, CustomerAddress, ItemNo, ItemName, Model, "
                    "Quantity, ItemPrice, LineTotal, TotalAmount)",
                ], "1NF — one row per invoice item."),
                p("Step 2 — Second normal form (2NF): remove partial "
                  "dependencies on part of the composite key."),
                schema([
                    "INVOICE (InvoiceNo, InvoiceDate, CustomerNo, "
                    "CustomerName, CustomerAddress, TotalAmount)",
                    "ITEM (ItemNo, ItemName, Model, ItemPrice)",
                    "INVOICE_ITEM (InvoiceNo, ItemNo, Quantity, LineTotal)",
                ], "2NF — invoice, item and invoice-item relations."),
                p("Step 3 — Third normal form (3NF): remove transitive "
                  "dependencies. CustomerNo determines CustomerName and "
                  "CustomerAddress, so customer data is moved to CUSTOMER."),
                schema([
                    "CUSTOMER (CustomerNo, CustomerName, CustomerAddress)",
                    "INVOICE (InvoiceNo, InvoiceDate, CustomerNo, "
                    "TotalAmount)",
                    "ITEM (ItemNo, ItemName, Model, ItemPrice)",
                    "INVOICE_ITEM (InvoiceNo, ItemNo, Quantity, LineTotal)",
                ], "3NF — customer, invoice, item and invoice-item relations."),
                table("3NF sample data: CUSTOMER",
                      ["CustomerNo", "CustomerName", "CustomerAddress"],
                      [["153", "Puan Adriana Yusuf",
                        "Taman Rasah Jaya, Seremban"]]),
                table("3NF sample data: INVOICE",
                      ["InvoiceNo", "InvoiceDate", "CustomerNo",
                       "TotalAmount"],
                      [["2088", "26-Aug-2019", "153", "902.95"]]),
                table("3NF sample data: ITEM",
                      ["ItemNo", "ItemName", "Model", "ItemPrice"],
                      [["CRB101", "Electric Kids Car", "Buggati", "559.00"],
                       ["LEG101", "City Fire Ladder Truck", "LEGO",
                        "184.00"],
                       ["LEG102", "City ATV Race Team", "LEGO", "79.99"]]),
                table("3NF sample data: INVOICE_ITEM",
                      ["InvoiceNo", "ItemNo", "Quantity", "LineTotal"],
                      [["2088", "CRB101", "1", "559.00"],
                       ["2088", "LEG101", "1", "184.00"],
                       ["2088", "LEG102", "2", "159.98"]]),
            ]),
        ],
        "marking": [
            "a) 2 marks: a relation containing the invoice, customer and "
            "repeating item data.",
            "b) 2 marks: composite key (InvoiceNo, ItemNo) with a reason.",
            "c) 16 marks: 1NF item relation stated with atomic rows (4), "
            "2NF partial dependencies removed into INVOICE, ITEM and "
            "INVOICE_ITEM (6), 3NF transitive dependency removed into "
            "CUSTOMER (6).",
        ],
    },
    "ICT450-2024-JAN-Q3": {
        "confidence": "medium",
        "assumptions": [
            "The report contains a repeating group of projects for one "
            "employee.",
            "Project code ST01 appears twice with different locations, so "
            "the project instance is identified by (ProjectCode, Location).",
            "Supervisor department names map to DepartmentID values; this "
            "supports the 3NF split into DEPARTMENT.",
        ],
        "blocks": [
            p("Figure 2 is an employee evaluation report. One employee has "
              "several project rows, so the report is an unnormalised "
              "relation with a repeating group."),
            sub("a", 3, "Normal form of Figure 2 and reasons.", blocks=[
                p("The report is in unnormalised form (UNF) because the "
                  "project rows repeat for the same employee. If it is "
                  "flattened to one row per project, it is in 1NF, but it "
                  "still contains partial and transitive dependencies. It is "
                  "not in 2NF or 3NF."),
                schema([
                    "REPORT (EmployeeID, EmployeeName, EmploymentYear, "
                    "DepartmentID, DepartmentName, Phone, Address, "
                    "ProjectCode, ProjectName, Location, Grade, "
                    "SupervisorID, SupervisorName, SupervisorDepartment)",
                ], "Unnormalised report relation."),
            ]),
            sub("b", 6, "Relational schema, primary keys and dependencies.",
                blocks=[
                    p("The repeated project code ST01 with two locations is "
                      "a key trap: ProjectCode alone does not identify a "
                      "project instance. The assignment key is (EmployeeID, "
                      "ProjectCode, Location)."),
                    schema([
                        "EMPLOYEE (EmployeeID, EmployeeName, EmploymentYear, "
                        "DepartmentID, DepartmentName, Phone, Address)",
                        "PROJECT (ProjectCode, ProjectName)",
                        "PROJECT_LOCATION (ProjectCode, Location)",
                        "SUPERVISOR (SupervisorID, SupervisorName, "
                        "SupervisorDepartment)",
                        "ASSIGNMENT (EmployeeID, ProjectCode, Location, "
                        "Grade, SupervisorID)",
                    ], "Relational schema before 3NF."),
                    p("Functional dependencies:"),
                    schema([
                        "EmployeeID → EmployeeName, EmploymentYear, "
                        "DepartmentID, DepartmentName, Phone, Address",
                        "ProjectCode → ProjectName",
                        "SupervisorID → SupervisorName, SupervisorDepartment",
                        "EmployeeID, ProjectCode, Location → Grade, "
                        "SupervisorID",
                        "DepartmentID → DepartmentName",
                    ], "Functional dependencies in the report."),
                ]),
            sub("c", 11, "Normalise to 3NF, showing all steps.", blocks=[
                p("Step 1 — 1NF: one row per employee-project assignment; "
                  "all cells atomic. Key: (EmployeeID, ProjectCode, "
                  "Location)."),
                p("Step 2 — 2NF: remove partial dependencies. Employee data "
                  "depends on EmployeeID; project data depends on "
                  "ProjectCode; supervisor data depends on SupervisorID."),
                schema([
                    "EMPLOYEE (EmployeeID, EmployeeName, EmploymentYear, "
                    "DepartmentID, DepartmentName, Phone, Address)",
                    "PROJECT (ProjectCode, ProjectName)",
                    "PROJECT_LOCATION (ProjectCode, Location)",
                    "SUPERVISOR (SupervisorID, SupervisorName, "
                    "SupervisorDepartment)",
                    "ASSIGNMENT (EmployeeID, ProjectCode, Location, Grade, "
                    "SupervisorID)",
                ], "2NF relations."),
                p("Step 3 — 3NF: remove transitive dependencies. "
                  "DepartmentName depends on DepartmentID, and the "
                  "supervisor's department depends on SupervisorID."),
                schema([
                    "DEPARTMENT (DepartmentID, DepartmentName)",
                    "EMPLOYEE (EmployeeID, EmployeeName, EmploymentYear, "
                    "DepartmentID, Phone, Address)",
                    "PROJECT (ProjectCode, ProjectName)",
                    "PROJECT_LOCATION (ProjectCode, Location)",
                    "SUPERVISOR (SupervisorID, SupervisorName, "
                    "DepartmentID)",
                    "ASSIGNMENT (EmployeeID, ProjectCode, Location, Grade, "
                    "SupervisorID)",
                ], "3NF relations."),
                table("3NF sample data: EMPLOYEE",
                      ["EmployeeID", "EmployeeName", "EmploymentYear",
                       "DepartmentID", "Phone", "Address"],
                      [["303303", "Siti Nur Fadilah", "2000", "S1", "017",
                        "JC 1234, Bandar Jasin Bestari Seksyen 7, Melaka"]]),
                table("3NF sample data: DEPARTMENT",
                      ["DepartmentID", "DepartmentName"],
                      [["S1", "Software Development"]]),
                table("3NF sample data: PROJECT and PROJECT_LOCATION",
                      ["ProjectCode", "ProjectName", "Location"],
                      [["MD01", "Mobile Apps Development",
                        "Kuala Terengganu"],
                       ["WD01", "Website Development", "Machang"],
                       ["ST01", "Software Integration", "Seremban"],
                       ["ST01", "Software Integration", "Tapah"]]),
                table("3NF sample data: SUPERVISOR",
                      ["SupervisorID", "SupervisorName", "DepartmentID"],
                      [["123123", "Willy", "S1"],
                       ["101101", "Mawar", "S1"]]),
                table("3NF sample data: ASSIGNMENT",
                      ["EmployeeID", "ProjectCode", "Location", "Grade",
                       "SupervisorID"],
                      [["303303", "MD01", "Kuala Terengganu", "A",
                        "123123"],
                       ["303303", "WD01", "Machang", "A+", "101101"],
                       ["303303", "ST01", "Seremban", "A-", "101101"],
                       ["303303", "ST01", "Tapah", "A", "101101"]]),
            ]),
        ],
        "marking": [
            "a) 3 marks: UNF/1NF identified (1), repeating group explained "
            "(1), reason why not 2NF/3NF (1).",
            "b) 6 marks: relations (3), keys (2), dependencies (1).",
            "c) 11 marks: 1NF (2), 2NF with partial dependencies removed (4), "
            "3NF with transitive dependencies removed and DEPARTMENT split "
            "(5).",
        ],
    },
    "ICT450-2018-DEC-Q4": {
        "confidence": "high",
        "assumptions": [
            "One order can contain many products; the same product appears "
            "once per order.",
            "City determines State for this data, so CITY is separated in "
            "3NF.",
        ],
        "blocks": [
            p("The order form contains order, customer, product and staff "
              "data, with a repeating group of product lines."),
            sub("a", 2, "Relational schema for the order form.", blocks=[
                schema([
                    "ORDER_FORM (OrderNo, OrderDate, CustomerNo, "
                    "CustomerName, CustomerAddress, City, State, ProductNo, "
                    "Description, Quantity, UnitPrice, StaffID, StaffName)",
                ], "Order-form relation in 1NF (one row per product line)."),
                table("Order header data",
                      ["OrderNo", "OrderDate", "CustomerNo", "Customer",
                       "Address", "City", "State"],
                      [["1234", "11-Apr-2018", "9876", "Sufian Ghani",
                        "456, Gemersik Street", "Kuala Krai",
                        "Kelantan"]]),
                p("Person in charge: S101 – Marina."),
                table("Item lines",
                      ["OrderNo", "ProductNo", "Description", "Qty",
                       "UnitPrice"],
                      [["1234", "A123", "Pencil", "100", "3.00"],
                       ["1234", "B234", "Eraser", "200", "1.50"],
                       ["1234", "C345", "Sharpener", "5", "8.00"],
                       ["1234", "A333", "Ruler", "50", "0.50"]]),
            ]),
            sub("b", 2, "Primary key of the relation.", blocks=[
                p("The primary key is (OrderNo, ProductNo). One order has "
                  "many products, and a product can appear on many orders, so "
                  "neither attribute alone is unique."),
            ]),
            sub("c", 16, "Normalise the order form to 3NF.", blocks=[
                p("Step 1 — 1NF: one row per order-product line; all values "
                  "atomic. Key: (OrderNo, ProductNo)."),
                p("Step 2 — 2NF: remove partial dependencies. Order data "
                  "depends on OrderNo; product data depends on ProductNo; "
                  "staff data depends on StaffID."),
                schema([
                    "ORDER (OrderNo, OrderDate, CustomerNo, CustomerName, "
                    "CustomerAddress, City, State, StaffID, StaffName)",
                    "PRODUCT (ProductNo, Description, UnitPrice)",
                    "ORDER_ITEM (OrderNo, ProductNo, Quantity)",
                ], "2NF relations."),
                p("Step 3 — 3NF: remove transitive dependencies. CustomerNo "
                  "determines customer details; City determines State; "
                  "StaffID determines StaffName."),
                schema([
                    "CUSTOMER (CustomerNo, CustomerName, Address, City)",
                    "CITY (City, State)",
                    "STAFF (StaffID, StaffName)",
                    "ORDER (OrderNo, OrderDate, CustomerNo, StaffID)",
                    "PRODUCT (ProductNo, Description, UnitPrice)",
                    "ORDER_ITEM (OrderNo, ProductNo, Quantity)",
                ], "3NF relations."),
                table("3NF sample data: CUSTOMER",
                      ["CustomerNo", "CustomerName", "Address", "City"],
                      [["9876", "Sufian Ghani", "456, Gemersik Street",
                        "Kuala Krai"]]),
                table("3NF sample data: CITY",
                      ["City", "State"],
                      [["Kuala Krai", "Kelantan"]]),
                table("3NF sample data: ORDER",
                      ["OrderNo", "OrderDate", "CustomerNo", "StaffID"],
                      [["1234", "11-Apr-2018", "9876", "S101"]]),
                table("3NF sample data: STAFF",
                      ["StaffID", "StaffName"],
                      [["S101", "Marina"]]),
                table("3NF sample data: PRODUCT",
                      ["ProductNo", "Description", "UnitPrice"],
                      [["A123", "Pencil", "3.00"],
                       ["B234", "Eraser", "1.50"],
                       ["C345", "Sharpener", "8.00"],
                       ["A333", "Ruler", "0.50"]]),
                table("3NF sample data: ORDER_ITEM",
                      ["OrderNo", "ProductNo", "Quantity"],
                      [["1234", "A123", "100"],
                       ["1234", "B234", "200"],
                       ["1234", "C345", "5"],
                       ["1234", "A333", "50"]]),
            ]),
        ],
        "marking": [
            "a) 2 marks: relation containing the order, customer, product "
            "and staff data.",
            "b) 2 marks: composite key (OrderNo, ProductNo) with a reason.",
            "c) 16 marks: 1NF order relation stated with atomic rows (4), "
            "2NF partial dependencies removed into ORDER, PRODUCT and "
            "ORDER_ITEM (6), 3NF transitive dependencies removed into "
            "CUSTOMER, CITY and STAFF (6).",
        ],
    },
}
