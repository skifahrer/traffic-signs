# Country plan

Countries whose road signs are listed on Wikipedia, to be added here one pull request at a time, at most three countries per pull request.

Source: every “Road signs in …” article on the English Wikipedia (103 in October 2026), surveyed for sign galleries and codes. Many countries also have a list on their own Wikipedia (as Germany, France, Poland, Czechia, Slovakia and Hungary use); check it first, as it usually has the official names and codes.

A country added here also joins its groups in the viewer's *Countries* menu
(continents, EU, NATO, Commonwealth, Mercosur, …): membership is listed in
[`viewer/groups.py`](viewer/groups.py) for every country, added or not, and a
test fails if a new country is on no continent.

**Ready**: most images have a sign code in the caption or the file name. **Needs work**: codes are missing for many signs, or the page mixes layouts.

## Already added

Australia (`au`), Austria (`at`), Belgium (`be`), Canada (`ca`), Czech Republic (`cz`), Denmark (`dk`), Finland (`fi`), France (`fr`), Germany (`de`), Greece (`gr`), Hungary (`hu`), Ireland (`ie`), Netherlands (`nl`), Poland (`pl`), Portugal (`pt`), Romania (`ro`), Slovakia (`sk`), Ukraine (`ua`), Great Britain (`gb`), United States (`us`).

## Not planned

- Czechoslovakia: historic
- East Germany: historic
- Soviet Union: historic
- Central America: region (SIECA), not a country
- Southern African Development Community: region (SADC), not a country
- South America: region, no gallery
- Wales: part of Great Britain, no gallery
- European microstates: several countries, no gallery
- Traffic signs in post-Soviet states: region, no gallery

## Order of pull requests

1. ~~Greece (`gr`), Romania (`ro`), Finland (`fi`)~~ added
2. ~~Portugal (`pt`), Ukraine (`ua`), Denmark (`dk`)~~ added
3. ~~Ireland (`ie`), Netherlands (`nl`), Belgium (`be`)~~ added
4. Sweden (`se`), Norway (`no`), Iceland (`is`)
5. Russia (`ru`), Latvia (`lv`), Lithuania (`lt`)
6. Croatia (`hr`), Moldova (`md`), Belarus (`by`)
7. Switzerland and Liechtenstein (`ch`), Georgia (`ge`), Serbia (`rs`)
8. Montenegro (`me`), Bosnia and Herzegovina (`ba`), Azerbaijan (`az`)
9. North Macedonia (`mk`), Slovenia (`si`), Turkey (`tr`)
10. Armenia (`am`), Spain (`es`), Bulgaria (`bg`)
11. Italy (`it`), Estonia (`ee`), Cyprus (`cy`)
12. Albania (`al`), Malta (`mt`), Mexico (`mx`)
13. Puerto Rico (`pr`), Ecuador (`ec`), Colombia (`co`)
14. Chile (`cl`), Paraguay (`py`), Cuba (`cu`)
15. Argentina (`ar`), Jamaica (`jm`), New Zealand (`nz`)
16. China (`cn`), Vietnam (`vn`), Taiwan (`tw`)
17. Uzbekistan (`uz`), Japan (`jp`), Tajikistan (`tj`)
18. Philippines (`ph`), Kazakhstan (`kz`), Turkmenistan (`tm`)
19. Cambodia (`kh`), Hong Kong (`hk`), South Korea (`kr`)
20. Mongolia (`mn`), Myanmar (`mm`), Bangladesh (`bd`)
21. Laos (`la`), Kyrgyzstan (`kg`), Macau (`mo`)
22. Sri Lanka (`lk`), Nepal (`np`), Pakistan (`pk`)
23. Thailand (`th`), Malaysia (`my`), Indonesia (`id`)
24. India (`in`), Singapore (`sg`), Morocco (`ma`)
25. Qatar (`qa`), Angola (`ao`), Israel (`il`)
26. United Arab Emirates (`ae`), Uganda (`ug`), Oman (`om`)
27. Iran (`ir`), Saudi Arabia (`sa`), Kuwait (`kw`)
28. Mauritius (`mu`)
29. Later, once a source is found: Brazil (`br`), Luxembourg (`lu`)

## Europe

| # | Country | Code | Signs on the page | Ready | Notes |
| --- | --- | --- | ---: | --- | --- |
| 1 | [Greece](https://en.wikipedia.org/wiki/Road_signs_in_Greece) | `gr` | 517 | ✅ added | codes in image names |
| 2 | [Romania](https://en.wikipedia.org/wiki/Road_signs_in_Romania) | `ro` | 488 | ✅ added | codes in image names |
| 3 | [Finland](https://en.wikipedia.org/wiki/Road_signs_in_Finland) | `fi` | 481 | ✅ added | codes in image names |
| 4 | [Portugal](https://en.wikipedia.org/wiki/Road_signs_in_Portugal) | `pt` | 478 | ✅ added | codes in image names |
| 5 | [Ukraine](https://en.wikipedia.org/wiki/Road_signs_in_Ukraine) | `ua` | 475 | ✅ added | codes in image names |
| 6 | [Denmark](https://en.wikipedia.org/wiki/Road_signs_in_Denmark) | `dk` | 474 | ✅ added | codes in image names |
| 7 | [Ireland](https://en.wikipedia.org/wiki/Road_signs_in_Ireland) | `ie` | 465 | ✅ added | codes in captions |
| 8 | [Netherlands](https://en.wikipedia.org/wiki/Road_signs_in_the_Netherlands) | `nl` | 450 | ✅ added | codes in captions |
| 9 | [Belgium](https://en.wikipedia.org/wiki/Road_signs_in_Belgium) | `be` | 427 | ✅ added | codes in image names |
| 10 | [Sweden](https://en.wikipedia.org/wiki/Road_signs_in_Sweden) | `se` | 422 | ✅ ready | codes in image names |
| 11 | [Norway](https://en.wikipedia.org/wiki/Road_signs_in_Norway) | `no` | 412 | ✅ ready | codes in image names |
| 12 | [Iceland](https://en.wikipedia.org/wiki/Road_signs_in_Iceland) | `is` | 385 | ✅ ready | codes in image names |
| 13 | [Russia](https://en.wikipedia.org/wiki/Road_signs_in_Russia) | `ru` | 377 | ✅ ready | codes in captions |
| 14 | [Latvia](https://en.wikipedia.org/wiki/Road_signs_in_Latvia) | `lv` | 362 | ✅ ready | codes in image names |
| 15 | [Lithuania](https://en.wikipedia.org/wiki/Road_signs_in_Lithuania) | `lt` | 354 | ✅ ready | codes in image names |
| 16 | [Croatia](https://en.wikipedia.org/wiki/Road_signs_in_Croatia) | `hr` | 329 | ✅ ready | codes in image names |
| 17 | [Moldova](https://en.wikipedia.org/wiki/Road_signs_in_Moldova) | `md` | 328 | ✅ ready | codes in image names |
| 18 | [Belarus](https://en.wikipedia.org/wiki/Road_signs_in_Belarus) | `by` | 310 | ✅ ready | codes in image names |
| 19 | [Switzerland and Liechtenstein](https://en.wikipedia.org/wiki/Road_signs_in_Switzerland_and_Liechtenstein) | `ch` | 301 | ✅ ready | codes in captions |
| 20 | [Georgia](https://en.wikipedia.org/wiki/Road_signs_in_Georgia) | `ge` | 295 | ✅ ready | codes in image names |
| 21 | [Serbia](https://en.wikipedia.org/wiki/Road_signs_in_Serbia) | `rs` | 289 | ✅ ready | codes in image names |
| 22 | [Montenegro](https://en.wikipedia.org/wiki/Road_signs_in_Montenegro) | `me` | 285 | ✅ ready | codes in captions |
| 23 | [Bosnia and Herzegovina](https://en.wikipedia.org/wiki/Road_signs_in_Bosnia_and_Herzegovina) | `ba` | 281 | ✅ ready | codes in image names |
| 24 | [Azerbaijan](https://en.wikipedia.org/wiki/Road_signs_in_Azerbaijan) | `az` | 278 | ✅ ready | codes in captions |
| 25 | [North Macedonia](https://en.wikipedia.org/wiki/Road_signs_in_North_Macedonia) | `mk` | 264 | ✅ ready | codes in image names |
| 26 | [Slovenia](https://en.wikipedia.org/wiki/Road_signs_in_Slovenia) | `si` | 216 | ✅ ready | codes in image names |
| 27 | [Turkey](https://en.wikipedia.org/wiki/Road_signs_in_Turkey) | `tr` | 212 | ✅ ready | codes in image names |
| 28 | [Armenia](https://en.wikipedia.org/wiki/Road_signs_in_Armenia) | `am` | 168 | ✅ ready | codes in image names |
| 29 | [Spain](https://en.wikipedia.org/wiki/Road_signs_in_Spain) | `es` | 829 | ⚠️ needs work | codes for part of the signs; check the local Wikipedia |
| 30 | [Bulgaria](https://en.wikipedia.org/wiki/Road_signs_in_Bulgaria) | `bg` | 330 | ⚠️ needs work | few codes: names from captions, codes via corrections or the local Wikipedia |
| 31 | [Italy](https://en.wikipedia.org/wiki/Road_signs_in_Italy) | `it` | 330 | ⚠️ needs work | few codes: names from captions, codes via corrections or the local Wikipedia |
| 32 | [Estonia](https://en.wikipedia.org/wiki/Road_signs_in_Estonia) | `ee` | 263 | ⚠️ needs work | codes for part of the signs; check the local Wikipedia |
| 33 | [Cyprus](https://en.wikipedia.org/wiki/Road_signs_in_Cyprus) | `cy` | 186 | ⚠️ needs work | codes for part of the signs; check the local Wikipedia |
| 34 | [Albania](https://en.wikipedia.org/wiki/Road_signs_in_Albania) | `al` | 165 | ⚠️ needs work | few codes: names from captions, codes via corrections or the local Wikipedia |
| 35 | [Malta](https://en.wikipedia.org/wiki/Road_signs_in_Malta) | `mt` | 88 | ⚠️ needs work | codes for part of the signs; check the local Wikipedia |
| 36 | Luxembourg | `lu` | 0 | ❌ no gallery | no English “Road signs in Luxembourg” page: look for a list on the French, German or Luxembourgish Wikipedia |

## Americas

| # | Country | Code | Signs on the page | Ready | Notes |
| --- | --- | --- | ---: | --- | --- |
| 1 | [Mexico](https://en.wikipedia.org/wiki/Road_signs_in_Mexico) | `mx` | 420 | ✅ ready | codes in captions |
| 2 | [Puerto Rico](https://en.wikipedia.org/wiki/Road_signs_in_Puerto_Rico) | `pr` | 354 | ✅ ready | codes in captions |
| 3 | [Ecuador](https://en.wikipedia.org/wiki/Road_signs_in_Ecuador) | `ec` | 265 | ✅ ready | codes in image names |
| 4 | [Colombia](https://en.wikipedia.org/wiki/Road_signs_in_Colombia) | `co` | 168 | ✅ ready | codes in captions |
| 5 | [Chile](https://en.wikipedia.org/wiki/Road_signs_in_Chile) | `cl` | 158 | ✅ ready | codes in captions |
| 6 | [Paraguay](https://en.wikipedia.org/wiki/Road_signs_in_Paraguay) | `py` | 150 | ✅ ready | codes in captions |
| 7 | [Cuba](https://en.wikipedia.org/wiki/Road_signs_in_Cuba) | `cu` | 145 | ✅ ready | codes in image names |
| 8 | [Argentina](https://en.wikipedia.org/wiki/Road_signs_in_Argentina) | `ar` | 140 | ✅ ready | codes in image names |
| 9 | [Jamaica](https://en.wikipedia.org/wiki/Road_signs_in_Jamaica) | `jm` | 120 | ✅ ready | codes in captions |
| 10 | [Brazil](https://en.wikipedia.org/wiki/Road_signs_in_Brazil) | `br` | 0 | ❌ no gallery | no sign gallery on the English page: look for a list on the local Wikipedia |

## Asia and Oceania

| # | Country | Code | Signs on the page | Ready | Notes |
| --- | --- | --- | ---: | --- | --- |
| 1 | [New Zealand](https://en.wikipedia.org/wiki/Road_signs_in_New_Zealand) | `nz` | 727 | ✅ ready | codes in image names |
| 2 | [China](https://en.wikipedia.org/wiki/Road_signs_in_China) | `cn` | 527 | ✅ ready | codes in image names |
| 3 | [Vietnam](https://en.wikipedia.org/wiki/Road_signs_in_Vietnam) | `vn` | 416 | ✅ ready | codes in image names |
| 4 | [Taiwan](https://en.wikipedia.org/wiki/Road_signs_in_Taiwan) | `tw` | 352 | ✅ ready | codes in image names |
| 5 | [Uzbekistan](https://en.wikipedia.org/wiki/Road_signs_in_Uzbekistan) | `uz` | 307 | ✅ ready | codes in captions |
| 6 | [Japan](https://en.wikipedia.org/wiki/Road_signs_in_Japan) | `jp` | 305 | ✅ ready | codes in image names |
| 7 | [Tajikistan](https://en.wikipedia.org/wiki/Road_signs_in_Tajikistan) | `tj` | 303 | ✅ ready | codes in captions |
| 8 | [Philippines](https://en.wikipedia.org/wiki/Road_signs_in_the_Philippines) | `ph` | 278 | ✅ ready | codes in image names |
| 9 | [Kazakhstan](https://en.wikipedia.org/wiki/Road_signs_in_Kazakhstan) | `kz` | 268 | ✅ ready | codes in image names |
| 10 | [Turkmenistan](https://en.wikipedia.org/wiki/Road_signs_in_Turkmenistan) | `tm` | 264 | ✅ ready | codes in captions |
| 11 | [Cambodia](https://en.wikipedia.org/wiki/Road_signs_in_Cambodia) | `kh` | 262 | ✅ ready | codes in image names |
| 12 | [Hong Kong](https://en.wikipedia.org/wiki/Road_signs_in_Hong_Kong) | `hk` | 256 | ✅ ready | codes in image names |
| 13 | [South Korea](https://en.wikipedia.org/wiki/Road_signs_in_South_Korea) | `kr` | 249 | ✅ ready | codes in image names |
| 14 | [Mongolia](https://en.wikipedia.org/wiki/Road_signs_in_Mongolia) | `mn` | 233 | ✅ ready | codes in image names |
| 15 | [Myanmar](https://en.wikipedia.org/wiki/Road_signs_in_Myanmar) | `mm` | 233 | ✅ ready | codes in image names |
| 16 | [Bangladesh](https://en.wikipedia.org/wiki/Road_signs_in_Bangladesh) | `bd` | 180 | ✅ ready | codes in image names |
| 17 | [Laos](https://en.wikipedia.org/wiki/Road_signs_in_Laos) | `la` | 179 | ✅ ready | codes in image names |
| 18 | [Kyrgyzstan](https://en.wikipedia.org/wiki/Road_signs_in_Kyrgyzstan) | `kg` | 156 | ✅ ready | codes in image names |
| 19 | [Macau](https://en.wikipedia.org/wiki/Road_signs_in_Macau) | `mo` | 138 | ✅ ready | codes in captions |
| 20 | [Sri Lanka](https://en.wikipedia.org/wiki/Road_signs_in_Sri_Lanka) | `lk` | 134 | ✅ ready | codes in image names |
| 21 | [Nepal](https://en.wikipedia.org/wiki/Road_signs_in_Nepal) | `np` | 133 | ✅ ready | codes in captions |
| 22 | [Pakistan](https://en.wikipedia.org/wiki/Road_signs_in_Pakistan) | `pk` | 88 | ✅ ready | codes in image names |
| 23 | [Thailand](https://en.wikipedia.org/wiki/Road_signs_in_Thailand) | `th` | 493 | ⚠️ needs work | codes for part of the signs; check the local Wikipedia |
| 24 | [Malaysia](https://en.wikipedia.org/wiki/Road_signs_in_Malaysia) | `my` | 416 | ⚠️ needs work | codes for part of the signs; check the local Wikipedia |
| 25 | [Indonesia](https://en.wikipedia.org/wiki/Road_signs_in_Indonesia) | `id` | 368 | ⚠️ needs work | codes for part of the signs; check the local Wikipedia |
| 26 | [India](https://en.wikipedia.org/wiki/Road_signs_in_India) | `in` | 333 | ⚠️ needs work | codes for part of the signs; check the local Wikipedia |
| 27 | [Singapore](https://en.wikipedia.org/wiki/Road_signs_in_Singapore) | `sg` | 166 | ⚠️ needs work | few codes: names from captions, codes via corrections or the local Wikipedia |

## Middle East and Africa

| # | Country | Code | Signs on the page | Ready | Notes |
| --- | --- | --- | ---: | --- | --- |
| 1 | [Morocco](https://en.wikipedia.org/wiki/Road_signs_in_Morocco) | `ma` | 293 | ✅ ready | codes in captions |
| 2 | [Qatar](https://en.wikipedia.org/wiki/Road_signs_in_Qatar) | `qa` | 178 | ✅ ready | codes in image names |
| 3 | [Angola](https://en.wikipedia.org/wiki/Road_signs_in_Angola) | `ao` | 161 | ✅ ready | codes in image names |
| 4 | [Israel](https://en.wikipedia.org/wiki/Road_signs_in_Israel) | `il` | 152 | ✅ ready | codes in image names |
| 5 | [United Arab Emirates](https://en.wikipedia.org/wiki/Road_signs_in_the_United_Arab_Emirates) | `ae` | 143 | ✅ ready | codes in image names |
| 6 | [Uganda](https://en.wikipedia.org/wiki/Road_signs_in_Uganda) | `ug` | 142 | ✅ ready | codes in image names |
| 7 | [Oman](https://en.wikipedia.org/wiki/Road_signs_in_Oman) | `om` | 133 | ✅ ready | codes in image names |
| 8 | [Iran](https://en.wikipedia.org/wiki/Road_signs_in_Iran) | `ir` | 131 | ✅ ready | codes in image names |
| 9 | [Saudi Arabia](https://en.wikipedia.org/wiki/Road_signs_in_Saudi_Arabia) | `sa` | 175 | ⚠️ needs work | few codes: names from captions, codes via corrections or the local Wikipedia |
| 10 | [Kuwait](https://en.wikipedia.org/wiki/Road_signs_in_Kuwait) | `kw` | 119 | ⚠️ needs work | codes for part of the signs; check the local Wikipedia |
| 11 | [Mauritius](https://en.wikipedia.org/wiki/Road_signs_in_Mauritius) | `mu` | 105 | ⚠️ needs work | few codes: names from captions, codes via corrections or the local Wikipedia |
