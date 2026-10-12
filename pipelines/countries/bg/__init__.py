"""Bulgaria: the list of signs on the Bulgarian Wikipedia (Пътни знаци в България).

The section "Действащи пътни знаци" (signs in force) has one wikitable per
group of the regulation (Наредба № РД-02-21-1 от 23.11.2023 г. за
сигнализация на пътищата с пътни знаци, which replaced Наредба № 18 in
2024): А warning, Б priority, В prohibitory, Г mandatory, Д special
regulation, Е information, Ж direction and Т additional panels. Each row
has the code, the image, the name and an explanation; see parser.py. Codes
keep the regulation's Cyrillic letters (А1, Г14а, Ж20.1).

A row that shows several drawings of one sign (the green, blue and white
boards of Д1, Ж1, Ж14, the countdown markers А35.1–А35.3 for the right and
the left side) is one sign, drawn with the first image. The English page
(en:Road signs in Bulgaria) and the Commons category "Diagrams of road
signs of Bulgaria" have no code the Bulgarian page lacks: their extra files
(Д9a, Ж1b, Ж10b, Е23a ...) are such colour variants of a listed sign, or
withdrawn signs, so they are not read.

The section on combined signs (Ж20 and Ж21 on one board) and the withdrawn
signs below it (Е7.2, Ж17) are outside the section read.
"""

import os

from ...core import parsers
from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="bg",
    language="bg",
    country_name="Bulgaria",
    language_name="Bulgarian",
    wiki="bg.wikipedia.org",
    page="Пътни знаци в България",
    parser=parsers.between(
        parse,
        start=r"^==\s*Действащи пътни знаци\s*==",
        end=r"^==\s*Пътни знаци с променящи се съобщения\s*==",
    ),
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
