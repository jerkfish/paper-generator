"""CSC413 deterministic stage-6 generators.

Builds 15 TRUE/FALSE items, 15 matching items, 30 MCQs and four 10-mark
structured questions from the approved planner.  Every choice is derived from
the seed; answers are stored in the paper JSON for the marking-scheme builder.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src import config
from src.subjects.csc413.planner import build_plan

SUBJECT = "CSC413"
TRACKING = config.TRACKING_DIR / "csc413"
VALIDATION_PATH = TRACKING / "generator_validation.json"

TOPIC_TITLES = {
    "multimedia_fundamentals": "Multimedia fundamentals and interactivity",
    "text": "Text and typography",
    "graphics": "Graphics, images and colour",
    "audio": "Audio and sound",
    "video": "Video and digital video",
    "animation": "Animation",
    "authoring_interactivity": "Authoring tools and interactive design",
    "hardware_devices": "Hardware and multimedia devices",
    "web_hypermedia": "Web and hypermedia",
    "design_project": "Design, planning and project management",
    "legal_ethics": "Legal, ethical and ownership issues",
    "virtual_reality": "Virtual and augmented reality",
}

# Each entry: (statement, answer, explanation).
TF_BANK = {
    "multimedia_fundamentals": [
        ("Multimedia combines text, graphics, audio, video and animation.", True,
         "These are the core multimedia elements."),
        ("A linear presentation allows users to choose their own path.", False,
         "A linear presentation follows a fixed sequence."),
        ("Hypermedia combines multimedia with hyperlinks.", True,
         "Hypermedia adds linked navigation to multimedia."),
        ("Interactivity gives users control over content and flow.", True,
         "Interactivity is a defining feature of many multimedia products."),
        ("A multimedia project always uses every media element.", False,
         "A project selects the elements it needs."),
    ],
    "text": [
        ("Sans serif fonts are generally preferred for screen display.", True,
         "They are cleaner at small screen sizes."),
        ("Kerning adjusts the space between individual character pairs.", True,
         "Kerning changes spacing for a specific pair."),
        ("Anti-aliasing makes the edges of text look more jagged.", False,
         "Anti-aliasing smooths jagged edges."),
        ("Hypertext contains links to other content.", True,
         "Hypertext is linked text."),
        ("Serif fonts are mainly used for printed material.", True,
         "Serifs aid readability in print."),
    ],
    "graphics": [
        ("A bitmap image is made up of pixels.", True,
         "Bitmap images use a pixel grid."),
        ("A vector image becomes pixelated when enlarged.", False,
         "Vector images scale without pixelation."),
        ("RGB is an additive colour model.", True,
         "RGB adds red, green and blue light."),
        ("CMYK is used for printed output.", True,
         "CMYK is a subtractive print model."),
        ("Higher resolution always means a smaller file.", False,
         "Higher resolution usually increases file size."),
    ],
    "audio": [
        ("The amplitude of a sound wave determines its loudness.", True,
         "Larger amplitude means louder sound."),
        ("MIDI files store digitized audio samples.", False,
         "MIDI stores musical instructions, not samples."),
        ("Sampling converts a continuous sound wave into digital values.", True,
         "Sampling measures the wave at intervals."),
        ("A higher sampling rate generally produces a more accurate recording.", True,
         "More samples capture more detail."),
        ("Hertz measures sound frequency.", True,
         "Hertz is cycles per second."),
    ],
    "video": [
        ("Frame rate is the number of video frames displayed per second.", True,
         "Frame rate is measured in fps."),
        ("Chroma key compositing replaces a colour background with another image.", True,
         "Chroma key removes a selected colour."),
        ("Interlacing displays every line of a video frame at the same time.", False,
         "Interlacing draws alternate lines."),
        ("MPEG is a common family of video compression formats.", True,
         "MPEG defines video compression standards."),
        ("Streaming requires the whole file to download before playback.", False,
         "Streaming can play while downloading."),
    ],
    "animation": [
        ("Cel animation is created by drawing each frame by hand.", True,
         "Cel animation uses hand-drawn frames."),
        ("Keyframes define important positions in an animation.", True,
         "Keyframes mark major changes."),
        ("Tweening creates intermediate frames between keyframes.", True,
         "Tweening fills the gaps."),
        ("Path animation moves an object along a predefined route.", True,
         "Path animation follows a motion path."),
        ("3D animation does not use modelling.", False,
         "3D animation relies on models."),
    ],
    "authoring_interactivity": [
        ("Authoring tools help developers organise and edit multimedia elements.", True,
         "Authoring tools assemble media."),
        ("A storyboard is a visual plan of a multimedia sequence.", True,
         "Storyboards show the planned flow."),
        ("Card-based authoring tools are best for messages with a clear beginning and end.", True,
         "Cards support sequential navigation."),
        ("Interactivity level is irrelevant when choosing an authoring tool.", False,
         "The required interactivity affects tool choice."),
        ("A prototype is an early model of a product.", True,
         "Prototypes test ideas before production."),
    ],
    "hardware_devices": [
        ("A scanner is an input device.", True,
         "A scanner captures documents into the computer."),
        ("RAM is a type of permanent storage.", False,
         "RAM is temporary working memory."),
        ("USB is a plug-and-play connection standard.", True,
         "USB devices are recognised automatically."),
        ("A graphics tablet is used to draw directly into a computer.", True,
         "A tablet is a drawing input device."),
        ("A plotter is an input device.", False,
         "A plotter produces output."),
    ],
    "web_hypermedia": [
        ("A web browser displays hypertext documents.", True,
         "Browsers render web pages."),
        ("HTML is used to structure content on web pages.", True,
         "HTML marks up web content."),
        ("A hyperlink can link only to another web page, not to a file.", False,
         "Links can target files and other resources."),
        ("Streaming allows media to begin playing before the whole file is downloaded.", True,
         "Streaming delivers media continuously."),
        ("A URL identifies the address of a web resource.", True,
         "A URL is a resource locator."),
    ],
    "design_project": [
        ("A low-fidelity prototype is used to test the basic layout and flow.", True,
         "Low-fidelity prototypes test structure."),
        ("The target audience has no influence on multimedia design.", False,
         "Design is shaped by the intended audience."),
        ("A storyboard is part of project planning.", True,
         "Storyboards plan the sequence."),
        ("Usability testing should be done only after the final product is released.", False,
         "Testing should happen during design."),
        ("A wireframe is a detailed final design.", False,
         "A wireframe is a low-fidelity layout."),
    ],
    "legal_ethics": [
        ("Copyright protects original multimedia works.", True,
         "Copyright protects creative expression."),
        ("Using a copyrighted image without permission is always allowed for private projects.", False,
         "Permission or a licence is still required."),
        ("A licence states how a work may be used.", True,
         "A licence defines permitted use."),
        ("Plagiarism is presenting someone else's work as your own.", True,
         "Plagiarism is uncredited copying."),
        ("Intellectual property includes copyright and trademarks.", True,
         "Both are forms of intellectual property."),
    ],
    "virtual_reality": [
        ("Virtual reality replaces the real environment with a simulated one.", True,
         "VR creates a simulated environment."),
        ("Augmented reality adds digital information to the real world.", True,
         "AR overlays digital content on reality."),
        ("A VR headset can provide an immersive display.", True,
         "Headsets provide immersive views."),
        ("Immersion is not important in virtual reality.", False,
         "Immersion is central to VR."),
        ("Haptic feedback provides tactile sensations.", True,
         "Haptics simulate touch."),
    ],
}

# Each entry: (term, definition).
MATCH_BANK = {
    "multimedia_fundamentals": [
        ("Multimedia", "integration of text, graphics, audio, video and animation"),
        ("Linear multimedia", "presentation without user control of sequence"),
        ("Hypermedia", "linked multimedia elements"),
        ("Interactivity", "user control over content and flow"),
        ("Convergence", "merging of computing, media and communications"),
    ],
    "text": [
        ("Serif", "font with small strokes at character ends"),
        ("Sans serif", "font without small strokes"),
        ("Kerning", "adjustment of space between character pairs"),
        ("Hypertext", "text containing links to other content"),
        ("Tracking", "uniform spacing across a range of characters"),
    ],
    "graphics": [
        ("Bitmap", "image made of pixels"),
        ("Vector", "image made of mathematical objects"),
        ("RGB", "additive colour model used by screens"),
        ("CMYK", "subtractive colour model used for print"),
        ("Resolution", "number of pixels in an image"),
    ],
    "audio": [
        ("Sampling", "converting sound into digital values"),
        ("MIDI", "standard for musical notes and instructions"),
        ("Amplitude", "height of a sound wave"),
        ("Hertz", "unit of frequency"),
        ("Waveform", "graph of a sound wave over time"),
    ],
    "video": [
        ("Frame rate", "frames displayed per second"),
        ("Chroma key", "replacing a colour background"),
        ("Streaming", "playing media while it downloads"),
        ("Interlacing", "drawing alternate lines of a frame"),
        ("Timecode", "label for a specific point in a video"),
    ],
    "animation": [
        ("Keyframe", "important frame in an animation"),
        ("Tweening", "generating in-between frames"),
        ("Cel animation", "hand-drawn frame-by-frame animation"),
        ("Path animation", "moving an object along a route"),
        ("Morphing", "transforming one shape into another"),
    ],
    "authoring_interactivity": [
        ("Storyboard", "visual sequence plan"),
        ("Card-based tool", "authoring tool organised like pages or cards"),
        ("Prototype", "early model of a product"),
        ("Timeline", "view that arranges events over time"),
        ("Authoring tool", "software for assembling multimedia elements"),
    ],
    "hardware_devices": [
        ("Scanner", "input device that digitises documents"),
        ("Plotter", "output device for large drawings"),
        ("Graphics tablet", "input device for drawing"),
        ("Plug and play", "automatic device recognition"),
        ("Touchscreen", "display that accepts touch input"),
    ],
    "web_hypermedia": [
        ("Browser", "software that displays web pages"),
        ("HTML", "language for web structure"),
        ("Hyperlink", "clickable link to another resource"),
        ("URL", "address of a web resource"),
        ("Web server", "computer that delivers web pages"),
    ],
    "design_project": [
        ("Target audience", "intended users of a product"),
        ("Usability", "ease of use"),
        ("Wireframe", "low-fidelity layout sketch"),
        ("Low-fidelity prototype", "simple model used to test layout and flow"),
        ("Milestone", "important checkpoint in a project schedule"),
    ],
    "legal_ethics": [
        ("Copyright", "exclusive rights of a creator"),
        ("Licence", "permission to use a work"),
        ("Plagiarism", "using another's work as one's own"),
        ("Intellectual property", "creations protected by law"),
        ("Trademark", "sign that identifies a brand"),
    ],
    "virtual_reality": [
        ("Virtual reality", "simulated environment"),
        ("Augmented reality", "real world plus digital overlay"),
        ("Immersion", "feeling of being inside an environment"),
        ("Haptic feedback", "tactile feedback"),
        ("Head-mounted display", "device worn on the head for VR"),
    ],
}

# Each entry: (stem, correct answer, [distractors]).
MCQ_BANK = {
    "multimedia_fundamentals": [
        ("Which best defines multimedia?", "Integration of text, graphics, audio, video and animation",
         ["Text only", "A single image", "A printed book"]),
        ("A presentation where the user controls the sequence is called:",
         "Non-linear", ["Linear", "Static", "Printed"]),
        ("Hypermedia is best described as:", "Multimedia with hyperlinks",
         ["Text-only media", "A printed manual", "A single video file"]),
        ("Which is NOT a multimedia element?", "Compiler",
         ["Text", "Audio", "Animation"]),
        ("Interactivity in multimedia means:", "The user can control content and flow",
         ["The system plays automatically", "Only text is shown", "There is no navigation"]),
        ("Which is an example of linear multimedia?", "A cinema presentation",
         ["A website with menus", "An interactive kiosk", "A game with choices"]),
        ("Convergence in multimedia refers to:", "Merging of computing, media and communications",
         ["Deleting media files", "Printing images", "Recording audio only"]),
        ("Which is a benefit of multimedia in education?",
         "It can combine explanation with visuals and sound",
         ["It removes all interaction", "It replaces all teachers", "It uses only text"]),
    ],
    "text": [
        ("A serif font has:", "Small strokes at character ends",
         ["No strokes", "Only uppercase letters", "No spacing"]),
        ("Kerning adjusts:", "Space between individual character pairs",
         ["Line length", "Font colour", "Page size"]),
        ("Hypertext contains:", "Links to other content",
         ["Only images", "Only audio", "No text"]),
    ],
    "graphics": [
        ("A bitmap image is made of:", "Pixels",
         ["Mathematical objects", "Text characters", "Sound samples"]),
        ("Which image type scales without losing quality?", "Vector",
         ["Bitmap", "Photograph", "Scan"]),
        ("RGB is used mainly for:", "Screen display",
         ["Printed output", "Audio recording", "Video editing only"]),
        ("CMYK is used mainly for:", "Printed output",
         ["Screen display", "Sound mixing", "Animation"]),
        ("Resolution refers to:", "Number of pixels in an image",
         ["Colour name", "File type", "Font size"]),
        ("Which colour model is subtractive?", "CMYK", ["RGB", "HSL", "HSV"]),
        ("Anti-aliasing is used to:", "Smooth jagged edges",
         ["Increase file size only", "Add sound", "Compress video"]),
        ("Which format is commonly used for bitmap images?", "PNG",
         ["HTML", "MIDI", "MPEG"]),
    ],
    "audio": [
        ("Sampling converts:", "Analog sound to digital values",
         ["Digital video to text", "Images to vectors", "Text to speech"]),
        ("MIDI stores:", "Musical notes and instructions",
         ["Digitized audio samples", "Video frames", "Images"]),
        ("Amplitude of a sound wave relates to:", "Loudness",
         ["Pitch", "Colour", "Frame rate"]),
        ("Hertz measures:", "Frequency", ["Loudness", "File size", "Resolution"]),
        ("A higher sampling rate generally:", "Improves accuracy",
         ["Reduces accuracy", "Removes audio", "Changes colour"]),
        ("Which is an audio file format?", "WAV", ["JPEG", "MPEG", "HTML"]),
    ],
    "video": [
        ("Frame rate is:", "Frames per second",
         ["Pixels per inch", "Samples per second", "Bits per second"]),
        ("Chroma key is used to:", "Replace a colour background",
         ["Add text", "Compress audio", "Scan images"]),
        ("Interlacing:", "Draws alternate lines of a frame",
         ["Draws every line at once", "Removes colour", "Adds sound"]),
        ("MPEG is:", "A video compression family",
         ["An image editor", "A font", "A storage device"]),
    ],
    "animation": [
        ("Cel animation is created by:", "Drawing each frame by hand",
         ["Recording sound", "Scanning text", "Printing images"]),
        ("Keyframes are:", "Important frames in an animation",
         ["Audio samples", "Colour profiles", "Web links"]),
        ("Tweening creates:", "In-between frames",
         ["Sound effects", "Text fonts", "Video codecs"]),
        ("Path animation moves an object:", "Along a predefined route",
         ["Randomly", "Only vertically", "Without motion"]),
        ("Morphing changes:", "One shape into another",
         ["Audio pitch", "File format", "Font size"]),
        ("Which is a 3D animation task?", "Modelling and rendering",
         ["Kerning", "Sampling", "Bookmarking"]),
    ],
    "authoring_interactivity": [
        ("An authoring tool is used to:", "Assemble multimedia elements",
         ["Only browse the web", "Only print text", "Only record audio"]),
        ("A storyboard is:", "A visual sequence plan",
         ["A sound file", "A colour model", "A video codec"]),
        ("Card-based authoring tools are suited to:",
         "Messages with a beginning and end",
         ["Live video only", "Audio editing only", "3D modelling only"]),
        ("A prototype is:", "An early model of a product",
         ["A final release", "A font", "A codec"]),
        ("Which is an authoring tool category?", "Card-based",
         ["RGB", "CMYK", "JPEG"]),
    ],
    "hardware_devices": [
        ("Which is an input device?", "Scanner", ["Printer", "Monitor", "Plotter"]),
        ("Which is an output device?", "Plotter", ["Scanner", "Keyboard", "Mouse"]),
        ("RAM is:", "Temporary working memory",
         ["Permanent storage", "An input device", "A web browser"]),
        ("Plug and play means:", "Automatic device recognition",
         ["Manual driver installation only", "No power needed", "Wireless only"]),
        ("A graphics tablet is used for:", "Drawing input",
         ["Printing", "Sound output", "Web browsing"]),
    ],
    "web_hypermedia": [
        ("A browser is used to:", "Display web pages",
         ["Print documents only", "Edit audio", "Scan images"]),
        ("HTML is used to:", "Structure web content",
         ["Compress video", "Store audio samples", "Model 3D objects"]),
        ("A hyperlink links to:", "Another resource",
         ["Only text", "Only images", "Only audio"]),
        ("Streaming allows media to:", "Play while downloading",
         ["Require full download first", "Only play offline", "Remove compression"]),
    ],
    "design_project": [
        ("A wireframe is:", "A low-fidelity layout sketch",
         ["A final video", "A sound file", "A codec"]),
        ("Target audience refers to:", "Intended users",
         ["Software licence", "File format", "Colour model"]),
    ],
    "legal_ethics": [
        ("Copyright protects:", "Original creative works",
         ["Computer hardware", "Internet speed", "File names"]),
        ("A licence gives:", "Permission to use a work",
         ["Ownership of all works", "Free hardware", "Unlimited bandwidth"]),
    ],
    "virtual_reality": [
        ("Virtual reality creates:", "A simulated environment",
         ["A printed page", "A text font", "A camera lens"]),
        ("Augmented reality:", "Adds digital information to the real world",
         ["Replaces the real world entirely", "Only uses audio", "Only uses text"]),
    ],
}

# Each entry: scenario plus three subparts.  Marks are assigned by the plan.
STRUCTURED_BANK = {
    "text": {
        "stem": (
            "Text is an essential element in a multimedia project. Its shape, "
            "size, design, colour, arrangement and linking all affect the "
            "message."),
        "parts": [
            ("State TWO reasons sans serif is mostly used for screen display "
             "and serif is used for printed material.",
             "Sans serif is cleaner at screen sizes; serif aids reading in print."),
            ("Describe TWO roles of hypertext in multimedia.",
             "It links related content and supports non-linear navigation."),
            ("Explain how text can have a massive impact on an informative "
             "multimedia project in the link and HTML context.",
             "Clear headings and links guide users through HTML pages and make "
             "the information easier to scan and follow."),
        ],
    },
    "animation": {
        "stem": (
            "You are required to animate a company logo. The logo depicts a "
            "planet orbiting the sun."),
        "parts": [
            ("State TWO animation file formats suitable for this project.",
             "GIF and MP4 are suitable; SWF is also acceptable."),
            ("Describe the steps of cel animation and ONE advantage of using it.",
             "Draw each frame, capture the frames in sequence, then play them "
             "back; it gives direct artistic control."),
            ("Differentiate 2-D and 2.5-D animation with ONE example for each.",
             "2-D uses flat drawings such as a cartoon; 2.5-D adds depth to "
             "flat artwork, such as parallax layers in a game."),
        ],
    },
    "graphics": {
        "stem": (
            "A product catalogue must show sharp images on screen and in "
            "print."),
        "parts": [
            ("State TWO differences between bitmap and vector images.",
             "Bitmap images use pixels and can pixelate; vector images use "
             "mathematical objects and scale cleanly."),
            ("Describe TWO factors that affect image quality.",
             "Resolution and colour depth both affect how much detail an image "
             "can show."),
            ("Explain how colour model and resolution affect screen and print "
             "output.",
             "Screens use RGB and print uses CMYK; print normally needs a "
             "higher resolution for sharp output."),
        ],
    },
    "web_hypermedia": {
        "stem": (
            "A museum wants a website that presents its collection and lets "
            "visitors explore related exhibits."),
        "parts": [
            ("State TWO differences between linear and non-linear navigation.",
             "Linear follows a fixed sequence; non-linear lets users choose "
             "their own path."),
            ("Describe TWO roles of hyperlinks in the website.",
             "They connect related exhibits and let users move between pages."),
            ("Explain how streaming and compression affect multimedia delivery "
             "on the web.",
             "Compression reduces file size for faster transfer; streaming lets "
             "audio or video play while it downloads."),
        ],
    },
    "authoring_interactivity": {
        "stem": (
            "A company wants an interactive product demonstration that runs on "
            "a kiosk and on the web."),
        "parts": [
            ("State TWO features to consider when choosing authoring software.",
             "Interactivity support and export formats are important features."),
            ("Explain the interactivity level suitable for the demonstration.",
             "A medium level with menus and buttons lets users explore without "
             "overwhelming them."),
            ("Explain TWO authoring tool categories appropriate for this project.",
             "Card-based tools suit structured screens; timeline-based tools "
             "suit animation and media sequencing."),
        ],
    },
    "design_project": {
        "stem": (
            "A shopping complex requires a kiosk that gives customers location "
            "and retailer information."),
        "parts": [
            ("State TWO important project team roles for completing the kiosk.",
             "A project manager and an interface designer are important roles."),
            ("Design a low-fidelity prototype for a pre-school courseware home "
             "page. The page must show topic menus, the course title and the "
             "school logo.",
             "A simple sketch with a title, logo and large topic buttons is "
             "sufficient at low fidelity."),
            ("Discuss TWO factors that lead to the wide use of mobile devices "
             "in games and shopping applications.",
             "Portability and constant connectivity make mobile devices "
             "convenient for games and shopping."),
        ],
    },
}


def _take(pool: list, rng: random.Random):
    if not pool:
        raise ValueError("generator pool exhausted")
    return pool.pop(rng.randrange(len(pool)))


def _take_from(pools: dict[str, list], topic: str, rng: random.Random):
    pool = pools.get(topic) or []
    if pool:
        return pool.pop(rng.randrange(len(pool)))
    for candidate in pools.values():
        if candidate:
            return candidate.pop(rng.randrange(len(candidate)))
    raise ValueError("all generator pools exhausted")


def _mcq_question(slot: dict, item: tuple, rng: random.Random) -> dict:
    stem, answer, distractors = item
    options = [answer] + list(distractors)
    rng.shuffle(options)
    letter = chr(ord("A") + options.index(answer))
    return {
        "number": slot["slot"],
        "part": "C",
        "kind": "mcq",
        "marks": 1,
        "topic": slot["topic"],
        "stem": stem,
        "options": options,
        "answer": letter,
        "answer_text": answer,
        "solution": f"The correct answer is {answer}.",
    }


def generate_paper(plan: dict | None = None, seed: int = 1) -> dict:
    if plan is None:
        plan = build_plan(seed)
    if plan["subject"] != SUBJECT:
        raise ValueError("plan belongs to another subject")
    rng = random.Random(int(plan["seed"]))
    slots = plan["slots"]
    questions: list[dict] = []

    tf_pools = {topic: list(items) for topic, items in TF_BANK.items()}
    for slot in (s for s in slots if s["part"] == "A"):
        statement, answer, solution = _take_from(
            tf_pools, slot["topic"], rng)
        questions.append({
            "number": slot["slot"],
            "part": "A",
            "kind": "true_false",
            "marks": 1,
            "topic": slot["topic"],
            "stem": statement,
            "answer": "TRUE" if answer else "FALSE",
            "solution": solution,
        })

    match_pools = {topic: list(items) for topic, items in MATCH_BANK.items()}
    matching_items = []
    used_terms: set[str] = set()
    for slot in (s for s in slots if s["part"] == "B"):
        pair = None
        pool = match_pools.get(slot["topic"]) or []
        for index in range(len(pool)):
            term, definition = pool[index]
            if term not in used_terms:
                pair = pool.pop(index)
                break
        if pair is None:
            for topic, candidate in match_pools.items():
                for index, (term, definition) in enumerate(candidate):
                    if term not in used_terms:
                        pair = candidate.pop(index)
                        break
                if pair is not None:
                    break
        if pair is None:
            raise ValueError("not enough unique matching terms")
        term, definition = pair
        used_terms.add(term)
        matching_items.append({
            "slot": slot["slot"],
            "topic": slot["topic"],
            "term": term,
            "stem": definition,
        })
    terms = [item["term"] for item in matching_items]
    rng.shuffle(terms)
    options = [
        {"label": chr(ord("A") + index), "text": term}
        for index, term in enumerate(terms)
    ]
    label_for = {option["text"]: option["label"] for option in options}
    for item in matching_items:
        questions.append({
            "number": item["slot"],
            "part": "B",
            "kind": "matching",
            "marks": 1,
            "topic": item["topic"],
            "stem": item["stem"],
            "answer": label_for[item["term"]],
            "answer_term": item["term"],
            "solution": f"{item['term']} matches this description.",
        })

    mcq_pools = {topic: list(items) for topic, items in MCQ_BANK.items()}
    for slot in (s for s in slots if s["part"] == "C"):
        item = _take_from(mcq_pools, slot["topic"], rng)
        questions.append(_mcq_question(slot, item, rng))

    d_slots = [s for s in slots if s["part"] == "D"]
    d_questions = []
    for question_number in ("D1", "D2", "D3", "D4"):
        group = [s for s in d_slots if s["question"] == question_number]
        if len(group) != 3:
            raise ValueError(f"{question_number} must have three subparts")
        topic = group[0]["topic"]
        template = STRUCTURED_BANK[topic]
        parts = []
        for index, slot in enumerate(group):
            text, answer = template["parts"][index]
            parts.append({
                "label": chr(ord("a") + index),
                "marks": slot["marks"],
                "text": text,
                "answer": answer,
            })
        d_questions.append({
            "number": question_number,
            "part": "D",
            "kind": "structured",
            "marks": sum(part["marks"] for part in parts),
            "topic": topic,
            "stem": template["stem"],
            "parts": parts,
        })
    questions.extend(d_questions)

    slot_map = {}
    for question in questions:
        if question["part"] == "D":
            for part in question["parts"]:
                slot_map[f"{question['number']}{part['label']}"] = question["number"]
        else:
            slot_map[question["number"]] = question["number"]

    topic_marks: dict[str, int] = {}
    for question in questions:
        topic_marks[question["topic"]] = (
            topic_marks.get(question["topic"], 0) + question["marks"])
    part_marks = {}
    for question in questions:
        part_marks[question["part"]] = (
            part_marks.get(question["part"], 0) + question["marks"])
    paper = {
        "subject": SUBJECT,
        "seed": plan["seed"],
        "generated_by": "src.subjects.csc413.generators",
        "planner": "src.subjects.csc413.planner",
        "total_marks": sum(part_marks.values()),
        "part_marks": part_marks,
        "topic_marks": topic_marks,
        "question_count": len(questions),
        "slot_count": len(slot_map),
        "questions": questions,
        "matching_options": options,
        "slot_map": slot_map,
        "style_profile": {
            "true_false": 15,
            "matching": 15,
            "mcq": 30,
            "structured": 4,
            "structured_subparts": 12,
            "matching_options": len(options),
        },
    }
    return paper


def validate_paper(paper: dict, plan: dict | None = None) -> list[str]:
    problems: list[str] = []
    if paper.get("total_marks") != 100:
        problems.append("total marks must be 100")
    if paper.get("question_count") != 64:
        problems.append("question count must be 64")
    if paper.get("slot_count") != 72:
        problems.append("slot count must be 72")
    if paper.get("part_marks") != {"A": 15, "B": 15, "C": 30, "D": 40}:
        problems.append(f"unexpected part marks: {paper.get('part_marks')}")
    a = [q for q in paper.get("questions", []) if q["part"] == "A"]
    b = [q for q in paper.get("questions", []) if q["part"] == "B"]
    c = [q for q in paper.get("questions", []) if q["part"] == "C"]
    d = [q for q in paper.get("questions", []) if q["part"] == "D"]
    if len(a) != 15 or len(b) != 15 or len(c) != 30 or len(d) != 4:
        problems.append("part question counts are wrong")
    for question in a:
        if question["answer"] not in {"TRUE", "FALSE"}:
            problems.append(f"{question['number']} has invalid TRUE/FALSE answer")
    terms = [q["answer_term"] for q in b]
    if len(set(terms)) != 15:
        problems.append("matching answers must use 15 distinct terms")
    options = paper.get("matching_options", [])
    if len(options) != 15:
        problems.append("matching options must contain 15 entries")
    labels = {option["label"] for option in options}
    for question in b:
        if question["answer"] not in labels:
            problems.append(f"{question['number']} has invalid matching answer")
    for question in c:
        if len(question.get("options", [])) != 4:
            problems.append(f"{question['number']} must have four options")
        if question["answer"] not in {"A", "B", "C", "D"}:
            problems.append(f"{question['number']} has invalid MCQ answer")
    for question in d:
        parts = question.get("parts", [])
        if len(parts) != 3:
            problems.append(f"{question['number']} must have three subparts")
        if sum(part["marks"] for part in parts) != 10:
            problems.append(f"{question['number']} subparts must total 10 marks")
        for part in parts:
            if not part.get("text") or not part.get("answer"):
                problems.append(
                    f"{question['number']}{part['label']} has empty content")
    blob = json.dumps(paper, ensure_ascii=False).lower()
    for marker in ("todo", "tbd", "placeholder"):
        if marker in blob:
            problems.append(f"forbidden marker in paper: {marker}")
    if plan is not None and paper.get("seed") != plan.get("seed"):
        problems.append("paper seed does not match plan seed")
    return problems


def validate_seeds(start: int = 1, end: int = 20,
                   path: Path | None = None) -> dict:
    results = []
    for seed in range(int(start), int(end) + 1):
        plan = build_plan(seed)
        paper = generate_paper(plan)
        problems = validate_paper(paper, plan)
        if generate_paper(plan) != paper:
            problems.append("generator is not deterministic")
        results.append({
            "seed": seed,
            "problems": problems,
            "question_count": paper["question_count"],
            "slot_count": paper["slot_count"],
            "total_marks": paper["total_marks"],
        })
    report = {
        "subject": SUBJECT,
        "papers_total": len(results),
        "papers_valid": sum(1 for row in results if not row["problems"]),
        "results": results,
    }
    target = Path(path) if path is not None else VALIDATION_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    plan = build_plan(args.seed)
    paper = generate_paper(plan)
    problems = validate_paper(paper, plan)
    if args.out:
        Path(args.out).write_text(
            json.dumps(paper, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "seed": paper["seed"],
        "total_marks": paper["total_marks"],
        "question_count": paper["question_count"],
        "slot_count": paper["slot_count"],
        "problems": problems,
    }, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
