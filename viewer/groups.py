"""Groups of countries the viewer can compare at once: continents and political or economic groups.

Members are ISO 3166-1 alpha-2 codes, including countries that are not in
signs/ yet, so a country joins its groups as soon as it is added. The viewer
lists only the members it has signs for. Transcontinental countries are in
both continents (Turkey, Georgia, Armenia, Azerbaijan: Europe and Asia;
Russia: Europe; Kazakhstan: Asia). Memberships as of 2026.

tests/test_viewer.py checks that every country with a pipeline is on a
continent, so a new country cannot be left out of the continent filters.
"""

from __future__ import annotations

CONTINENT, GROUP = "continent", "group"

_EU = "at be bg cy cz de dk ee es fi fr gr hr hu ie it lt lu lv mt nl pl pt ro se si sk"

GROUPS: list[dict] = [
    # Continents
    {"id": "europe", "label": "Europe", "kind": CONTINENT, "members":
        "ad al am at az ba be bg by ch cy cz de dk ee es fi fr gb ge gr hr hu ie is it li lt lu lv mc md me mk mt nl no pl pt ro rs ru se si sk sm tr ua va xk"},
    {"id": "north-america", "label": "North America", "kind": CONTINENT, "members":
        "ag bb bs bz ca cr cu dm do gd gt hn ht jm kn lc mx ni pa pr sv tt us vc"},
    {"id": "south-america", "label": "South America", "kind": CONTINENT, "members": "ar bo br cl co ec gy pe py sr uy ve"},
    {"id": "asia", "label": "Asia", "kind": CONTINENT, "members":
        "ae af am az bd bh bn bt cn ge hk id il in iq ir jo jp kg kh kp kr kw kz la lb lk mm mn mo mv my np om ph pk ps qa sa sg sy th tj tl tm tr tw uz vn ye"},
    {"id": "africa", "label": "Africa", "kind": CONTINENT, "members":
        "ao bf bi bj bw cd cf cg ci cm cv dj dz eg er et ga gh gm gn gq gw ke km lr ls ly ma mg ml mr mu mw mz na ne ng rw sc sd sl sn so ss st sz td tg tn tz ug za zm zw"},
    {"id": "oceania", "label": "Oceania", "kind": CONTINENT, "members": "au fj fm ki mh nr nz pg pw sb to tv vu ws"},
    # Political and economic groups
    {"id": "eu", "label": "European Union", "kind": GROUP, "members": _EU},
    {"id": "eu-us", "label": "EU and the United States", "kind": GROUP, "members": _EU + " us"},
    {"id": "nato", "label": "NATO", "kind": GROUP, "members":
        "al be bg ca cz de dk ee es fi fr gb gr hr hu is it lt lu lv me mk nl no pl pt ro se si sk tr us"},
    {"id": "g7", "label": "G7", "kind": GROUP, "members": "ca de fr gb it jp us"},
    {"id": "five-eyes", "label": "Five Eyes", "kind": GROUP, "members": "au ca gb nz us"},
    {"id": "commonwealth", "label": "Commonwealth of Nations", "kind": GROUP, "members":
        "ag au bb bd bn bs bw bz ca cm cy dm fj ga gb gd gh gm gy in jm ke ki kn lc lk ls mt mu mv mw my mz na ng nr nz pg pk rw sb sc sg sl sz tg to tt tv tz ug vc vu ws za zm"},
    {"id": "visegrad", "label": "Visegrád Group", "kind": GROUP, "members": "cz hu pl sk"},
    {"id": "german-speaking", "label": "German-speaking countries", "kind": GROUP, "members": "at ch de li lu"},
    {"id": "nordic", "label": "Nordic countries", "kind": GROUP, "members": "dk fi is no se"},
    {"id": "baltic", "label": "Baltic states", "kind": GROUP, "members": "ee lt lv"},
    {"id": "benelux", "label": "Benelux", "kind": GROUP, "members": "be lu nl"},
    {"id": "former-soviet-union", "label": "Former Soviet Union", "kind": GROUP, "members":
        "am az by ee ge kg kz lt lv md ru tj tm ua uz"},
    {"id": "mercosur", "label": "Mercosur", "kind": GROUP, "members": "ar bo br py uy"},
    {"id": "arab-league", "label": "Arab League", "kind": GROUP, "members":
        "ae bh dj dz eg iq jo km kw lb ly ma mr om ps qa sa sd so sy tn ye"},
    {"id": "asean", "label": "ASEAN", "kind": GROUP, "members": "bn id kh la mm my ph sg th tl vn"},
]

for _group in GROUPS:
    _group["members"] = sorted(set(_group["members"].split()))


def groups_for(countries: list[str]) -> list[dict]:
    """Every group, with the members that have signs (`countries`) and how many it has in all."""
    present = set(countries)
    return [
        {
            "id": g["id"],
            "label": g["label"],
            "kind": g["kind"],
            "countries": [c for c in g["members"] if c in present],
            "members": len(g["members"]),
        }
        for g in GROUPS
    ]
