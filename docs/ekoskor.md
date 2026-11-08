# EkoSkor: kako računamo

> EkoSkor v1. Izračun je u `backend/app/services/ekoskor.py`, testovi u `backend/tests/test_ekoskor.py`.
> Svaka promjena praga ili pondera mijenja kod, testove i ovaj dokument u istoj izmjeni (commitu).

EkoSkor je broj od 0 do 100. Svaki od pet slojeva dobiva ocjenu od 0 do 100, zaokruženu na cijeli broj kako je prikazana na kartici adrese. EkoSkor je ponderirani prosjek tih prikazanih ocjena, **zaokružen na bliži cijeli broj, s polovinom prema gore** (42,5 → 43), pa ga svatko može sam izračunati s kartice.

## Slojevi, ponderi i pragovi

| Sloj | Ponder | 100 bodova | 50 bodova | 0 bodova | Izvor |
|---|---|---|---|---|---|
| Poplave | 20 % | izvan svih zona opasnosti | zona male vjerojatnosti | zona srednje ili velike vjerojatnosti | `hv-poplave` |
| Buka, L<sub>den</sub> | 20 % | ≤ 53 dB | 54–64 dB | ≥ 65 dB | `zg-buka` |
| Zrak, PM10 | 20 % | ≤ 15 µg/m³ | 27,5 µg/m³ | ≥ 40 µg/m³ | `zg-zrak-mjerenja` |
| Zelena mobilnost | 20 % | ≥ 3 perona ZET-a do 300 m **i** biciklistička staza ≤ 200 m | npr. 1 peron do 500 m i staza 600 m (4/5 javni prijevoz, 1/5 bicikl) | nijedan peron do 500 m **i** staza ≥ 1 km | `zg-zet`, `zg-biciklisticke-staze` |
| Zelenilo | 20 % | park ili šuma (≥ 0,5 ha) ≤ 300 m ili adresa unutar njega | 650 m | ≥ 1 km | `osm-parkovi` |

Pet slojeva, svaki 20 %, od 8. 11. 2026. (odluka): sloj Otpad uklonjen je iz EkoSkora. Reciklažna dvorišta i zeleni otoci ostaju na karti kao informacija. Ranije, 6. 11. 2026., zelenilo je izdvojeno iz zelene mobilnosti u zaseban sloj. Razlog: točka usred Parka-šume Maksimir dobivala je lošu ocjenu „zelene mobilnosti" jer je daleko od stajališta, iako je u parku. Sada park ocjenjuje sloj Zelenilo, a mobilnost samo kretanje bez automobila.

### Kako se čita pojedini sloj

- **Poplave.** Karta Hrvatskih voda ima tri scenarija vjerojatnosti. Točka dobiva scenarij najveće vjerojatnosti čiji obuhvat poplave je pokriva. Razred dubine prikazuje se kao dodatna informacija, ali ne mijenja ocjenu.
- **Buka.** Strateška karta buke Grada Zagreba daje zaseban razred L<sub>den</sub> za svaki izvor (cestovni, tramvajski, željeznički promet i industrija) u koracima od 5 dB. Uzimamo **najglasniji izvor** (odluka 5. 11. 2026.) i donju granicu razreda: razred 50–54 → 100, 55–59 i 60–64 → 50, 65 i glasnije → 0.
  - **Točke unutar zgrada (odluka 5. 11. 2026.):** karta nema razreda unutar tlocrta zgrada, a adresne točke često padaju unutar svoje zgrade. Primjerice, Trg bana Jelačića 6 očitavao se kao „bez razreda", iako je pročelje prema trgu u razredu 65–69 dB. Kad točka nema razred, kartica zato uzima najglasniji razred na prstenu od 8 točaka 15 m oko nje, a ako je i taj prazan, na prstenu od 30 m. To je **pročelje stana najizloženije buci**, referentno mjesto za izloženost prema Direktivi o buci okoliša (2002/49/EZ). API vraća polumjer prstena kao `facade_m`, a kartica navodi da je vrijednost očitana uz pročelje zgrade.
  - **Bez razreda** na točki i na oba prstena čita se kao tiše od 50 dB → 100. Obuhvat sloja cestovne buke pokriva cijeli Grad, što podupire takvo čitanje; `TODO(verify)` prema izvješću o karti buke.
  - Prag od 53 dB smjernica je Svjetske zdravstvene organizacije (2018.) za buku cestovnog prometa, L<sub>den</sub>.
- **Zrak.** Prosjek PM10 na **najbližoj gradskoj mjernoj postaji** za razdoblje siječanj – kolovoz 2023. (razdoblje dostupno u objavljenom skupu podataka). Ocjena je 100 uz 15 µg/m³ ili manje (godišnja smjernica SZO-a iz 2021.), 0 uz 40 µg/m³ ili više (godišnja granična vrijednost EU-a, Direktiva 2008/50/EZ), a između raste linearno. Vrijednost se uvijek prikazuje s razdobljem mjerenja. Najbliža postaja gruba je procjena: gradskih postaja ima samo 6.
- **Zelena mobilnost.** Kretanje bez automobila: javni prijevoz i bicikl. Ocjena sloja je ponderirani prosjek dvaju dijelova (odluka 6. 11. 2026.):

  | Dio | Udio u sloju | 100 | 0 | Između |
  |---|---|---|---|---|
  | **Javni prijevoz:** perona ZET-a (jedna objavljena točka po stajalištu i smjeru, odluka 5. 11. 2026.) | 4/5 | ≥ 3 perona do 300 m | nijedan do 500 m | 50 ako do 300 m nema 3 perona, a do 500 m ima barem jedan |
  | **Bicikl:** najbliža gradska biciklistička staza ili Bajs stanica (bliža se računa) | 1/5 | ≤ 200 m | ≥ 1 km | linearno |

  - Prag od 200 m za biciklističku stazu i stanicu naša je odluka (nema usporedive objavljene smjernice). Udaljenost je do najbliže točke staze ili do stanice. Stanica javnih bicikala ulazi u ocjenu od 7. 11. 2026. (odluka): ako je bliža od staze, ona određuje dio za bicikl. Od 8. 11. 2026. to su Bajs stanice iz OpenStreetMapa (200), umjesto zastarjelog gradskog popisa (32).
  - Kartica prikazuje oba dijela i njihove ocjene, pa se ocjena sloja može provjeriti.
  - Primjer: jedan peron do 500 m i nijedna staza do 1 km daje 0,8 × 50 = 40, dakle Umjereno. (Udio bicikla smanjen je s 1/3 na 1/5 istog dana, jer je uz 1/3 takva adresa dobivala 33, Loše, pa je 73 % Grada imalo lošu mobilnost.)
- **Zelenilo.** Zračna udaljenost do najbližeg parka, šume, javnog vrta ili zaštićenog područja od barem 0,5 ha (OpenStreetMap), do ruba površine; unutar nje udaljenost je 0. Ocjena 100 uz ≤ 300 m, 0 uz ≥ 1 km, linearno između. Prag od 300 m i najmanja površina od 0,5 ha preporuka su Regionalnog ureda SZO-a za Europu (*Urban green spaces: a brief for action*, 2017.): zelena površina od barem 0,5–1 ha na najviše 300 m zračne udaljenosti od stana. Pješačke staze se ne boduju zasebno: u gradu postoje gotovo uz svaku adresu, pa ne bi razlikovale adrese.

## Semafor po sloju

Svaki redak sloja na kartici adrese prikazuje stanje prema ocjeni, kako je prikazana (zaokružena na cijeli broj), u jednakim trećinama: **Dobro** (zeleno) 67–100, **Umjereno** (žuto) 34–66, **Loše** (crveno) 0–33. Za poplave i buku, koje imaju samo ocjene 100, 50 ili 0, to je jednostavno 100 → zeleno, 50 → žuto, 0 → crveno. Uz boju je uvijek tekst i ikona, nikad samo boja.

Kartica uz stanje prikazuje i bodove sloja (npr. „Dobro · 76/100”), jer „Dobro” ne znači 100 bodova: zrak s prosjekom PM10 od 20,9 µg/m³ ima 76 bodova, dakle Dobro, ali ne i punu ocjenu. Što stanje znači u jedinicama pojedinog sloja (rubovi su provjereni testom `test_*_status_edges_as_published` u `test_ekoskor.py`):

| Sloj | Dobro (67–100) | Umjereno (34–66) | Loše (0–33) |
|---|---|---|---|
| Poplave | izvan svih zona opasnosti | zona male vjerojatnosti | zona srednje ili velike vjerojatnosti |
| Buka, L<sub>den</sub> | do 53 dB | 54–64 dB | 65 dB ili više |
| Zrak, PM10 | do 23,3 µg/m³ | 23,4–31,6 µg/m³ | 31,7 µg/m³ ili više |
| Zelena mobilnost | ≥ 3 perona ZET-a do 300 m | manje od 3 do 300 m, a barem jedan do 500 m | nijedan peron do 500 m |
| Zelenilo | park ili šuma do 534 m (ili unutar) | 535–765 m | 766 m ili više |

Kod zelene mobilnosti stanje ovisi samo o javnom prijevozu: biciklistička staza ili Bajs stanica (1/5 sloja) mijenja bodove unutar istog stanja.

## Zrak zadnja 24 sata (ne ulazi u EkoSkor)

Redak zraka ima i okvir *Zadnja 24 sata*: prosjek satnih vrijednosti s najbliže državne postaje DHMZ-a (Zagreb 1–4), nevalidirano. Okvir ima **vlastito stanje**, odvojeno od stanja sloja i od EkoSkora (odluka 6. 11. 2026.). EkoSkor ocjenjuje mjesto za život, pa koristi višemjesečni prosjek; jedan dan ovisi o vremenu (inverzija, vjetar, sezona grijanja) i ocjenu bi mijenjao iz sata u sat.

| Tvar | Dobro (do smjernice SZO-a za 24 h) | Umjereno (do privremenog cilja SZO-a) | Loše |
|---|---|---|---|
| PM10 | ≤ 45 µg/m³ | ≤ 50 µg/m³ (IT-4) | > 50 µg/m³ |
| PM2,5 | ≤ 15 µg/m³ | ≤ 25 µg/m³ (IT-4) | > 25 µg/m³ |
| NO₂ | ≤ 25 µg/m³ | ≤ 50 µg/m³ (IT-2) | > 50 µg/m³ |

Vrijednosti su iz smjernica SZO-a za kvalitetu zraka iz 2021. Stanje okvira određuje **najlošija tvar**. Tvar ulazi u stanje samo ako ima barem 18 satnih vrijednosti (75 %, kao za dnevni prosjek u Direktivi 2008/50/EZ, Prilog VII.); inače okvir piše „Nedostupno". Kod: `DAY_LIMITS` i `day_status` u `backend/app/services/dhmz.py`, testovi u `backend/tests/test_dhmz.py`.

## Nedostupni podaci

Ako sloj nije dostupan (servis ne radi ili nema podataka), izostavlja se, a ponderi ostalih slojeva preračunavaju se na 100 %. Uz manje od 3 dostupna sloja EkoSkor se ne računa.

## Karta grada (*Za grad*)

Karta grada koristi istu formulu na mreži ćelija 250 × 250 m (EPSG:3765, HTRS96/TM) unutar granice Grada Zagreba, izračunatu u središtu svake ćelije. Vidi `scripts/build_heatmap.py`.

- **Izračun od 8. 11. 2026. (pet slojeva po 20 %, bez otpada):** 10 260 ćelija, 641 km². EkoSkor najmanje 14, medijan 73, najviše 97 (10.–90. percentil 53–85); sa slojem otpada bilo je 17, 65, 96 (46–76), jer je otpad u većem dijelu Grada imao nisku ocjenu. EkoSkor ćelije promijenio se od −10 do +15 bodova. Ranije, 6. 11. 2026., uz šest slojeva: Po ćelijama: zelena mobilnost Loše 48 %, Umjereno 39 %, Dobro 13 %; zelenilo Loše 3 %, Umjereno 5 %, Dobro 93 %. EkoSkor ćelije promijenio se od −13 do +13 bodova. Buka je dostupna u svim ćelijama.
- **Ćelija je jedna točka uzorka.** Svaka ćelija prikazuje vrijednost u svom središtu, do ~175 m od bilo koje adrese u njoj. Primjer: središte ćelije s Trgom bana Jelačića 63 m je južno od trga, unutar bloka zgrada bez razreda buke, pa ćelija ima ocjenu buke 100, a sam trg (tramvaj, 70–74 dB) 0. Kartica adrese uvijek se računa točno na adresi, s pravilom pročelja; karta grada pravilo pročelja još ne koristi (ponovni izračun je otvoren).

## Ograničenja

- Udaljenosti su zračne, ne pješačke rute.
- Karte buke i poplava strateške su karte na razini grada; pojedina zgrada može odstupati.
- Zrak se temelji na podacima iz 2023. s najbliže od 6 postaja i ne opisuje zrak točno na adresi.
- Zeleni otoci, parkovi i šume su iz OpenStreetMapa i popis možda nije potpun; Jarun je u OSM-u označen kao sportski centar pa nije među zelenim površinama. Biciklističke staze su gradski podaci iz 2022.
- EkoSkor je orijentacija, a ne stručna procjena, i nije pravni, osiguravateljni ni savjet o nekretninama.
