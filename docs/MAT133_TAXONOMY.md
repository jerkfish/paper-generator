# MAT133 Paper-Derived Taxonomy and Question Log

Source: 41 MAT133 papers in `data/papers/MAT133` (37 unique; four exact duplicate pairs).  
Text extraction: 25 papers from their PDF text layer, 16 scanned papers via Windows OCR.  
Question log: 978 rows (894 rows from unique papers, 84 duplicate-paper copies).  
Model: DeepSeek Flash 4.1 (`deepseek-flash`), temperature 0.1, JSON extraction.  
All numbers below exclude exact-duplicate paper copies.

## Topic taxonomy

| Priority | Topic id | Label | Entries | Papers | Subtopics |
|---|---|---|---:|---:|---|
| 1 | `functions` | Functions | 174 | 37 | domain_range (42), composition (36), inverse (29), piecewise (31), transformations (22), even_odd (9), function_arithmetic (3), graph (2) |
| 1 | `inequalities` | Inequalities | 60 | 37 | linear (7), compound (8), quadratic (9), rational (34), interval_notation (2) |
| 1 | `absolute_value` | Absolute Value | 29 | 26 | equation (1), inequality (21), graph (7) |
| 2 | `lines` | Lines | 49 | 34 | through_points (12), parallel_perpendicular (34), intercepts (3) |
| 2 | `parabolas` | Parabolas | 47 | 34 | standard_form (17), vertex_focus_directrix (28), graph (2) |
| 2 | `circles` | Circles | 41 | 35 | standard_form (14), general_to_standard (22), diameter_endpoints (5) |
| 3 | `trigonometry` | Trigonometry | 135 | 35 | equation (34), identity (15), exact_value (13), graph (36), compound_double_angle (37) |
| 3 | `circular_measure` | Circular Measure | 86 | 37 | arc_length (17), sector_area (36), perimeter (19), radians (14) |
| 3 | `triangle_geometry` | Triangle Geometry | 66 | 36 | solve_triangle (13), sine_rule (11), cosine_rule (11), area (29), combined_figures (2) |
| 3 | `exponential_logarithmic` | Exponential and Logarithmic Equations | 50 | 34 | exponential_equation (22), log_equation (22), log_laws (6) |
| 3 | `systems_of_equations` | Systems of Equations | 41 | 31 | linear_2var (2), linear_3var (21), nonlinear (18) |
| 3 | `complex_numbers` | Complex Numbers | 40 | 35 | arithmetic (12), division (25), powers (3) |
| 3 | `polynomials` | Polynomials | 39 | 33 | long_division (12), synthetic_division (14), factor_theorem (7), remainder_theorem (1), factorization (5) |
| 3 | `systems_of_inequalities` | Systems of Inequalities | 37 | 37 | graph_feasible_region (35), write_from_region (2) |

The `other` topic exists only as a review fallback; no unique question was assigned to it.

## Priority scope for generators

- **Priority 1 (foundations):** Functions, Inequalities, Absolute Value.
- **Priority 2 (coordinate geometry):** Lines, Circles, Parabolas.
- **Priority 3 (advanced and remaining paper-derived topics):** Complex Numbers, systems of equations, systems of inequalities, polynomials, exponential/logarithmic equations, trigonometry, circular measure and triangle geometry.

The question log shows that every topic below is recurrent in the papers, not a one-off.  Priority-1 topics occur in 26-37 of the 37 unique papers; priority-2 topics in 34-35; priority-3 topics in 25-37 (depending on subtopic).

Two generator subtopics are included for complete syllabus coverage but did not appear as standalone question-log rows: `circles.graph` (circle-sketching rows were classified under `circles.standard_form` / `circles.general_to_standard`) and `complex_numbers.modulus_argument`. They are marked here so they are not mistaken for observed patterns.

## Representative patterns

Each pattern is the canonical `topic.subtopic` pair.  The full record in `question_log.json` stores commands, parameter types, symbolic forms, a representative question pattern and an ordered marking-scheme blueprint.

| Priority | Pattern | Entries | Papers | Marks (mean) | Parameter types |
|---|---|---:|---:|---:|---|
| 1 | `functions.domain_range` | 42 | 33 | 2.22 | boundaries, breakpoints, coefficients, constant_terms, constants, denominator |
| 1 | `functions.composition` | 36 | 31 | 3.51 | constant_terms, denominator_coefficients, denominator_shift, domain_restrictions, evaluation_point, function_coefficients |
| 1 | `inequalities.rational` | 34 | 31 | 4.97 | constant, constant_denominator, constant_denominators, constant_lhs, constant_rhs, linear_coefficient |
| 1 | `functions.piecewise` | 31 | 17 | 3.37 | boundaries, breakpoints, coefficients, constant, constants, evaluation_point |
| 1 | `functions.inverse` | 29 | 28 | 3.36 | constant_p, constant_terms, constant_value, denominator_coefficients, domain_restriction, evaluation_point |
| 1 | `functions.transformations` | 22 | 19 | 4.45 | function_coefficients, function_family, horizontal_shift, quadratic_coefficients, reflection, scale |
| 1 | `absolute_value.inequality` | 21 | 21 | 4.19 | constant, constant_bound, constant_lhs, constant_outer, constant_rhs, constant_terms |
| 1 | `functions.even_odd` | 9 | 8 | 3.67 | absolute_value_term, coefficients, function_coefficients, polynomial_coefficients, polynomial_term, quadratic_coefficients |
| 1 | `inequalities.quadratic` | 9 | 9 | 4.78 | constant_rhs, linear_binomial, linear_coefficients, quadratic_coefficients |
| 1 | `inequalities.compound` | 8 | 8 | 3.75 | constant_terms, constants, linear_coefficients, lower_bound, upper_bound |
| 1 | `absolute_value.graph` | 7 | 7 | 4.71 | horizontal_shift, reflection, scale, shift, transformation_parameters, vertical_shift |
| 1 | `inequalities.linear` | 7 | 5 | 4.43 | constant_rhs, constant_terms, constants, linear_coefficients |
| 1 | `functions.function_arithmetic` | 3 | 3 | 2.33 | denominator_coefficients, function_coefficients, function_expression, numerator_coefficients |
| 1 | `functions.graph` | 2 | 2 | 1 | domain_bounds, function_expression, interval_bounds |
| 1 | `inequalities.interval_notation` | 2 | 2 | 3.5 | inequality_direction, linear_coefficients, rational_bounds |
| 1 | `absolute_value.equation` | 1 | 1 | 4 | constant_rhs, linear_coefficients |
| 2 | `lines.parallel_perpendicular` | 34 | 33 | 4.24 | circle_coefficients, intercept, intercept_form_constants, intercept_value, intersection_points, line_coefficients |
| 2 | `parabolas.vertex_focus_directrix` | 28 | 22 | 3.46 | directrix_constant, directrix_equation, directrix_line, directrix_value, focal_length, focus_coordinates |
| 2 | `circles.general_to_standard` | 22 | 21 | 4.77 | centre_coordinates, circle_coefficients, coefficients, coefficients_D_E_F, constant, constant_term |
| 2 | `parabolas.standard_form` | 17 | 15 | 3.82 | constant, focus_coordinates, focus_point, linear_coefficient, linear_coefficients, parabola_coefficients |
| 2 | `circles.standard_form` | 14 | 10 | 3.5 | center_coordinates, centre_coordinates, circle_centre, line_coefficients, point_coordinates, point_on_circle |
| 2 | `lines.through_points` | 12 | 8 | 2.67 | coordinates, distance, intercept, line_coefficients, linear_coefficients, point_coordinates |
| 2 | `circles.diameter_endpoints` | 5 | 5 | 4.4 | centre_coordinates, point_coordinates |
| 2 | `lines.intercepts` | 3 | 3 | 3.33 | circle_coefficients, intercept, intercept_points, line_coefficients, point_coordinates, slope |
| 2 | `parabolas.graph` | 2 | 2 | 5 | line_coefficients, parabola_coefficients, quadratic_coefficients |
| 3 | `trigonometry.compound_double_angle` | 37 | 25 | 3.38 | angle_conditions, angle_quadrants, angle_range, angle_ranges, angle_values, cos_value |
| 3 | `circular_measure.sector_area` | 36 | 34 | 3.89 | angle, angle_degrees, angle_radians, angles, arc_length, arc_lengths |
| 3 | `trigonometry.graph` | 36 | 32 | 4.11 | amplitude, amplitude_coefficient, angle_interval, angle_range, frequency, frequency_coefficient |
| 3 | `systems_of_inequalities.graph_feasible_region` | 35 | 35 | 4.94 | boundary_curves, bounds, circle_center, circle_center_radius, circle_centre_radius, circle_radius |
| 3 | `trigonometry.equation` | 34 | 32 | 5.03 | angle_coefficients, angle_interval, angle_range, coefficients, constant_rhs, constant_term |
| 3 | `triangle_geometry.area` | 29 | 26 | 3.17 | angle, angle_degrees, angle_values, angles, area, area_value |
| 3 | `complex_numbers.division` | 25 | 25 | 4.52 | complex_coefficients, complex_denominator, complex_denominators, complex_imaginary, complex_imaginary_part, complex_numerator |
| 3 | `exponential_logarithmic.exponential_equation` | 22 | 19 | 4.73 | base, base_a, base_b, base_values, coefficients, constant |
| 3 | `exponential_logarithmic.log_equation` | 22 | 22 | 5.33 | base, base_values, coefficient, coefficients, constant, constant_coefficient |
| 3 | `systems_of_equations.linear_3var` | 21 | 21 | 5.14 | coefficients, constants, linear_coefficients, linear_coefficients_3var |
| 3 | `circular_measure.perimeter` | 19 | 19 | 3.16 | angle, angle_radians, angles, arc_length, arc_lengths, area |
| 3 | `systems_of_equations.nonlinear` | 18 | 17 | 5.39 | base, circle_centre, circle_radius, coefficients, constants, equation_coefficients |
| 3 | `circular_measure.arc_length` | 17 | 17 | 3.76 | angle, angle_degrees, angle_radians, arc_length, arc_lengths, area |
| 3 | `trigonometry.identity` | 15 | 15 | 4.27 | angle, angle_interval, angle_quadrants, angle_range, angle_variable, quadrant |
| 3 | `circular_measure.radians` | 14 | 14 | 2.64 | angle_degrees, arc_length, arc_lengths, coordinates, radii, radius |
| 3 | `polynomials.synthetic_division` | 14 | 14 | 4.43 | cubic_coefficients, divisor, divisor_root, factor_constant, factor_root, known_factor |
| 3 | `triangle_geometry.solve_triangle` | 13 | 12 | 4.08 | angle, angle_degrees, angles, area, radius, side_coefficients |
| 3 | `trigonometry.exact_value` | 13 | 12 | 4.15 | angle_interval, angle_range, angle_ranges, cosine_ratio, cosine_value, cot_value |
| 3 | `complex_numbers.arithmetic` | 12 | 10 | 4 | complex_coefficients, complex_imaginary_part, complex_real_part, exponent, imaginary_part, real_parameters |
| 3 | `polynomials.long_division` | 12 | 12 | 4.5 | complex_root, cubic_coefficients, divisor, divisor_root, factor_root, linear_divisor |
| 3 | `triangle_geometry.cosine_rule` | 11 | 11 | 3.09 | angle_degrees, angle_radians, angle_ratio, angles, included_angle, lengths |
| 3 | `triangle_geometry.sine_rule` | 11 | 10 | 2.73 | angle, angle_degrees, angle_values, angles, angles_degrees, side_length |
| 3 | `polynomials.factor_theorem` | 7 | 7 | 4.14 | candidate_factor, constant_term, cubic_coefficients, factor_constant, factor_root, linear_coefficient |
| 3 | `exponential_logarithmic.log_laws` | 6 | 5 | 3.5 | bases, coefficients, constant, exponents, log_argument, log_arguments |
| 3 | `polynomials.factorization` | 5 | 5 | 5.4 | cubic_coefficients, known_factor, linear_factor, polynomial_coefficients |
| 3 | `complex_numbers.powers` | 3 | 3 | 4.33 | coefficients, complex_base, complex_coefficients, exponent, exponents, power_of_i |
| 3 | `systems_of_equations.linear_2var` | 2 | 2 | 4 | constants, linear_coefficients |
| 3 | `systems_of_inequalities.write_from_region` | 2 | 2 | 4.5 | boundary_line_coefficients, boundary_lines, intercepts, region_vertices |
| 3 | `triangle_geometry.combined_figures` | 2 | 2 | 3 | arc_length, radius, right_angle, segment_length |
| 3 | `polynomials.remainder_theorem` | 1 | 1 | 2 | divisor_coefficients, polynomial_coefficients |

## Schema and validation

The formal schema is `src/mat133/schema.py`; a generated JSON Schema is in `data/tracking/mat133/question_log.schema.json`.  Each entry records:

- paper, month, year and whether it is a duplicate copy;
- question and part labels, marks, topic and subtopic;
- dominant command, reusable question pattern and concrete givens;
- generator parameter types and symbolic formula forms;
- an ordered solution blueprint suitable for a marking scheme;
- required diagram type, source evidence, confidence and review flags.

Validation currently flags:

- 288 low-confidence unique rows (mostly OCR-damaged scanned papers);
- 82 unique rows whose evidence fragment could not be matched after normalisation;
- 5 unique rows with no visible mark;
- duplicate-paper copies are retained but excluded from pattern frequency and taxonomy counts;
- some older papers print one mark after a group of subparts; the extractor may repeat that group mark, so mark totals for those papers are indicative rather than exact.

These flags are intentionally retained instead of fabricated values.  Generators should use patterns and blueprints, not the OCR-damaged numeric examples.

## Files

- `data/tracking/mat133/taxonomy.json` - canonical taxonomy plus observed frequencies.
- `data/tracking/mat133/question_log.json` - papers, 978 entries, 55 patterns, validation summary.
- `data/tracking/mat133/question_log.schema.json` - generated JSON Schema.
- `data/tracking/mat133/question_log/raw/` - cached per-paper LLM extraction; reruns are free.
- `scripts/build_mat133_question_log.py` - extraction, validation and aggregation.
