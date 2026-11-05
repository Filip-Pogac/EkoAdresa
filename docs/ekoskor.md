# EkoSkor: kako računamo

> EkoSkor v1. Izračun je u `backend/app/services/ekoskor.py`, testovi u `backend/tests/test_ekoskor.py`.
> Svaka promjena praga ili pondera mijenja kod, testove i ovaj dokument u istoj izmjeni (commitu).

EkoSkor je broj od 0 do 100. Svaki od pet slojeva dobiva ocjenu od 0 do 100, zaokruženu na cijeli broj kako je prikazana na kartici adrese. EkoSkor je ponderirani prosjek tih prikazanih ocjena, **zaokružen na bliži cijeli broj, s polovinom prema gore** (42,5 → 43), pa ga svatko može sam izračunati s kartice.

## Slojevi, ponderi i pragovi

| Sloj | Ponder | 100 bodova | 50 bodova | 0 bodova | Izvor |
|---|---|---|---|---|---|
| Poplave | 25 % | izvan svih zona opasnosti | zona male vjerojatnosti | zona srednje ili velike vjerojatnosti | `hv-poplave` |
| Buka, L<sub>den</sub> | 25 % | ≤ 53 dB | 54–64 dB | ≥ 65 dB | `zg-buka` |
| Zrak, PM10 | 20 % | ≤ 15 µg/m³ | 27,5 µg/m³ | ≥ 40 µg/m³ | `zg-zrak-mjerenja` |
| Otpad | 15 % | fiksno reciklažno dvorište ≤ 1 km **i** zeleni otok ≤ 300 m | npr. dvorište 3 km i otok 900 m | dvorište ≥ 5 km **i** otok ≥ 1,5 km | `zg-reciklaza`, `osm-reciklaza` |
| Zelena mobilnost | 15 % | ≥ 3 perona ZET-a do 300 m | barem jedan peron do 500 m | nijedan peron do 500 m | `zg-zet` |

### Kako se čita pojedini sloj

- **Poplave.** Karta Hrvatskih voda ima tri scenarija vjerojatnosti. Točka dobiva scenarij najveće vjerojatnosti čiji obuhvat poplave je pokriva. Razred dubine prikazuje se kao dodatna informacija, ali ne mijenja ocjenu.
- **Buka.** Strateška karta buke Grada Zagreba daje zaseban razred L<sub>den</sub> za svaki izvor (cestovni, tramvajski, željeznički promet i industrija) u koracima od 5 dB. Uzimamo **najglasniji izvor** (odluka 5. 11. 2026.) i donju granicu razreda: razred 50–54 → 100, 55–59 i 60–64 → 50, 65 i glasnije → 0.
  - **Točke unutar zgrada (odluka 5. 11. 2026.):** karta nema razreda unutar tlocrta zgrada, a adresne točke često padaju unutar svoje zgrade. Primjerice, Trg bana Jelačića 6 očitavao se kao „bez razreda", iako je pročelje prema trgu u razredu 65–69 dB. Kad točka nema razred, kartica zato uzima najglasniji razred na prstenu od 8 točaka 15 m oko nje, a ako je i taj prazan, na prstenu od 30 m. To je **pročelje stana najizloženije buci**, referentno mjesto za izloženost prema Direktivi o buci okoliša (2002/49/EZ). API vraća polumjer prstena kao `facade_m`, a kartica navodi da je vrijednost očitana uz pročelje zgrade.
  - **Bez razreda** na točki i na oba prstena čita se kao tiše od 50 dB → 100. Obuhvat sloja cestovne buke pokriva cijeli Grad, što podupire takvo čitanje; `TODO(verify)` prema izvješću o karti buke.
  - Prag od 53 dB smjernica je Svjetske zdravstvene organizacije (2018.) za buku cestovnog prometa, L<sub>den</sub>.
- **Zrak.** Prosjek PM10 na **najbližoj gradskoj mjernoj postaji** za razdoblje siječanj – kolovoz 2023. (razdoblje dostupno u objavljenom skupu podataka). Ocjena je 100 uz 15 µg/m³ ili manje (godišnja smjernica SZO-a iz 2021.), 0 uz 40 µg/m³ ili više (godišnja granična vrijednost EU-a, Direktiva 2008/50/EZ), a između raste linearno. Vrijednost se uvijek prikazuje s razdobljem mjerenja. Najbliža postaja gruba je procjena: gradskih postaja ima samo 6.
- **Otpad.** Zračna udaljenost do najbližeg **fiksnog** reciklažnog dvorišta (10 mobilnih dvorišta radi samo određenim danima i ne ulazi u ocjenu, odluka 5. 11. 2026.) i do najbližeg zelenog otoka (spremnici za papir, plastiku ili staklo iz OpenStreetMapa). Svaka udaljenost daje svoj dio od 0 do 100, linearno između „blizu" i „daleko": dvorište 100 uz ≤ 1 km → 0 uz ≥ 5 km, zeleni otok 100 uz ≤ 300 m → 0 uz ≥ 1,5 km. Ocjena otpada prosjek je ta dva dijela (odluka 5. 11. 2026.; ranije pravilo „dvorište ≤ 1 km i otok ≤ 300 m, inače 0" davalo je 0 za 89 % Grada).
- **Zelena mobilnost.** Broj **perona** autobusnih i tramvajskih stajališta ZET-a (jedna objavljena točka po stajalištu i smjeru, odluka 5. 11. 2026.) do 300 m i do 500 m zračne udaljenosti. Ako do 300 m nema perona, a do 500 m ima, ocjena je 50; 0 je samo ako do 500 m nema nijednog.

## Semafor po sloju

Svaki redak sloja na kartici adrese prikazuje stanje prema ocjeni, u jednakim trećinama: **Dobro** (zeleno) 67–100, **Umjereno** (žuto) 34–66, **Loše** (crveno) 0–33. Za poplave, buku i mobilnost, koje imaju samo ocjene 100, 50 ili 0, to je jednostavno 100 → zeleno, 50 → žuto, 0 → crveno. Uz boju je uvijek tekst i ikona, nikad samo boja.

## Nedostupni podaci

Ako sloj nije dostupan (servis ne radi ili nema podataka), izostavlja se, a ponderi ostalih slojeva preračunavaju se na 100 %. Uz manje od 3 dostupna sloja EkoSkor se ne računa.

## Karta grada (*Za grad*)

Karta grada koristi istu formulu na mreži ćelija 250 × 250 m (EPSG:3765, HTRS96/TM) unutar granice Grada Zagreba, izračunatu u središtu svake ćelije. Vidi `scripts/build_heatmap.py`.

- **Izračun od 5. 11. 2026. (linearno pravilo za otpad):** 10 260 ćelija, 641 km². EkoSkor najmanje 12, medijan 65, najviše 96 (10.–90. percentil 42–77). Buka je dostupna u svim ćelijama.
- **Ćelija je jedna točka uzorka.** Svaka ćelija prikazuje vrijednost u svom središtu, do ~175 m od bilo koje adrese u njoj. Primjer: središte ćelije s Trgom bana Jelačića 63 m je južno od trga, unutar bloka zgrada bez razreda buke, pa ćelija ima ocjenu buke 100, a sam trg (tramvaj, 70–74 dB) 0. Kartica adrese uvijek se računa točno na adresi, s pravilom pročelja; karta grada pravilo pročelja još ne koristi (ponovni izračun je otvoren).
- **Pokrivenost otpada.** Uz ranije pravilo „sve ili ništa" 89 % ćelija imalo je ocjenu 0, a nijedna 100, pa je pravilo zamijenjeno linearnim. Sada 51 % ćelija ima ocjenu 0: 72 % ćelija bez stajališta ZET-a do 500 m (rubni dijelovi, šuma) i 32 % ćelija sa stajalištem. Razlozi: samo 10 fiksnih dvorišta za cijeli Grad i rijetka pokrivenost zelenih otoka u OpenStreetMapu izvan središta. Najviše bi pomogao bolji izvor zelenih otoka (npr. geokodiranje gradskog popisa `zg-zeleni-otoci`).

## Ograničenja

- Udaljenosti su zračne, ne pješačke rute.
- Karte buke i poplava strateške su karte na razini grada; pojedina zgrada može odstupati.
- Zrak se temelji na podacima iz 2023. s najbliže od 6 postaja i ne opisuje zrak točno na adresi.
- Zeleni otoci su iz OpenStreetMapa i popis možda nije potpun.
- EkoSkor je orijentacija, a ne stručna procjena, i nije pravni, osiguravateljni ni savjet o nekretninama.
