# Integracija s javnim sustavima i preduvjeti

Kako se EkoAdresa oslanja na postojeće javne informacijske sustave, koje standarde koristi, kako se drugi sustavi mogu povezati s njom i što je potrebno da iz prototipa postane javna usluga. Tehnički detalji su u [arhitektura.md](arhitektura.md).

## 1. Standardi koje rješenje već koristi

| Standard | Gdje |
|---|---|
| **OGC WMS 1.3.0** (`GetCapabilities`, `GetMap`, `GetFeatureInfo`, `GetLegendGraphic`) | Karte opasnosti od poplava (Hrvatske vode), strateška karta buke (Grad Zagreb) |
| **OGC WFS 2.0.0**, podatkovni model **INSPIRE** Human Health and Safety | Indeks kvalitete zraka u RH |
| **OGC CSW 2.0.2** (katalog metapodataka, ISO 19115/19139) | Pronalazak servisa buke i poplava u NIPP-u (`geoportal.nipp.hr`) |
| **CKAN Action API** (`package_show`) | Preuzimanje skupova s data.zagreb.hr (isti sustav kao data.gov.hr) |
| **GeoJSON** (RFC 7946), **Apache Parquet** | Spremljene snimke podataka i odgovori API-ja |
| **OpenAPI 3** | Opis API-ja, automatski iz koda: <https://ekoadresa-api.vercel.app/docs> |
| **XYZ pločice** (EPSG:3857) | Slojevi poplava i buke na karti |
| **Koordinatni sustavi** EPSG:4326 (WGS 84), EPSG:3765 (HTRS96/TM, službena projekcija RH) | Interno WGS 84; udaljenosti u HTRS96/TM |
| **ISO 3166-2** (HR-21) | Granica pilot područja (Grad Zagreb) |

## 2. Postojeći javni sustavi

| Sustav | Uloga danas | Mogućnost u produkciji |
|---|---|---|
| **Portal otvorenih podataka** (data.gov.hr) | Izvor skupova (mjerne postaje, mjerenja zraka, indeks zraka) | Automatsko osvježavanje preko CKAN API-ja kad se skup izmijeni; objava rezultata (npr. mreža EkoSkora za grad) natrag na Portal kao novi otvoreni skup |
| **Portal otvorenih podataka Grada Zagreba** (data.zagreb.hr) | Izvor skupova (reciklažna dvorišta, stajališta ZET-a, zeleni otoci, mjerenja zraka) | Isto kao gore; ista platforma (CKAN) |
| **Nacionalna infrastruktura prostornih podataka** (NIPP, geoportal.nipp.hr) | Katalog u kojem su pronađeni WMS servisi buke i poplava | EkoAdresa API može se upisati u NIPP kao javni servis s metapodacima; isti pristup proširuje se na sve servise upisane u NIPP |
| **INSPIRE servisi** (servisi.azo.hr) | Indeks kvalitete zraka uživo | Državne strateške karte buke (`rh-buka`) za gradove izvan Zagreba |
| **Javni WMS servisi izdavača** (Hrvatske vode, Grad Zagreb) | Zona poplava i razina buke uživo | Bez promjene; vidi preduvjete u točki 4 |
| **e-Građani** | Ne koristi se | Poveznica na EkoAdresu kao javnu informacijsku uslugu. Prijava putem NIAS-a nije potrebna jer usluga ne obrađuje osobne podatke; trebala bi tek za osobne obavijesti (vidi [daljnji-razvoj.md](daljnji-razvoj.md)). Uvjeti uključivanja `TODO(verify)` |

## 3. Kako se drugi sustavi povezuju s EkoAdresom

- **Otvoreni REST API s OpenAPI opisom:** svaki sustav (portal nekretnina, gradska aplikacija, obrazovni alat) može za koordinatu dobiti profil i EkoSkor (`/api/profile`) ili usporedbu (`/api/compare`) u JSON-u. Svaki podatak nosi `source_id`, a `/api/sources` daje izdavača i licenciju, pa korisnik API-ja može ispravno navesti izvor.
- **GeoJSON krajnje točke** (`/api/heatmap`, `/api/layers/*`) mogu se izravno učitati u GIS alate (QGIS, ArcGIS) i druge web karte.
- **Kôd je otvoren (MIT)**, pa ga javno tijelo može pokrenuti na vlastitoj infrastrukturi (`docker-compose up`).
- **Prilagodbe za javni API:** danas CORS dopušta samo frontend EkoAdrese. Za otvaranje drugim sustavima potrebni su otvoreni CORS ili API ključevi, ograničenje broja upita i dogovor o dostupnosti (SLA).

## 4. Preduvjeti za produkciju

### Tehnički

- **Hosting u javnom sektoru:** pokretanje na infrastrukturi koju odredi vlasnik usluge (npr. državni oblak), s praćenjem rada i sigurnosnim kopijama. Rješenje je kontejnerizirano (Docker) i nema posebnih zahtjeva.
- **Pouzdanost izvornih servisa:** WMS poplava povremeno vraća pogreške (502, prekinuti odgovori). Potreban je dogovor o dostupnosti ili zrcalna kopija podataka.
- **Upit za točku nad kartom poplava:** servis Hrvatskih voda ne podržava `GetFeatureInfo`, pa se zona čita iz boje piksela. Uključivanje `GetFeatureInfo` ili WFS-a s poligonima zona dalo bi točniji i brži upit.
- **CORS zaglavlja na javnim servisima** (karta buke) omogućila bi prikaz izravno u pregledniku, bez posrednika.
- **Novi podaci o kvaliteti zraka:** gradski skup mjerenja sadrži razdoblje siječanj–kolovoz 2023. Za produkciju je potreban izvor koji se redovito ažurira i opisana ljestvica državnog indeksa.
- **Potpune adrese:** OpenStreetMap ne sadrži sve kućne brojeve; službeni adresni registar Državne geodetske uprave bio bi potpun izvor (dostupnost kao otvoreni podatak `TODO(verify)`).
- **Zajednička predmemorija i baza** (npr. PostGIS, Redis) umjesto datoteka i SQLite-a kad usluga obuhvati cijelu Hrvatsku.

### Organizacijski

- **Vlasnik usluge:** javno tijelo nadležno za okoliš ili prostor, ili Grad Zagreb za pilot, koje odgovara za rad i sadržaj.
- **Dogovor s izdavačima podataka** (Hrvatske vode, Grad Zagreb, nadležno tijelo za kvalitetu zraka): obavijest o promjeni servisa ili skupa, stalne adrese servisa, kontakt osoba.
- **Stručna provjera metodologije EkoSkora:** pragove i pondere trebaju potvrditi stručnjaci (javno zdravstvo, vodno gospodarstvo, zaštita okoliša) i objaviti postupak izmjene. Otvorena pitanja već su označena s `TODO(verify)` u [ekoskor.md](ekoskor.md) i [data-sources.md](data-sources.md).
- **Održavanje:** redovito osvježavanje snimki (skripte postoje), praćenje rada servisa, korisnička podrška.

### Pravni

- **Licencije izvora:** za tri servisa (karta poplava Hrvatskih voda, karta buke Grada Zagreba, indeks kvalitete zraka) licencija nije izrijekom navedena. Za javnu uslugu potrebna je izričita dozvola za ponovnu uporabu, po mogućnosti Otvorena dozvola prema Pravilniku o vrstama i sadržaju dozvola za ponovnu uporabu informacija (»Narodne novine«, br. 67/17.).
- **OpenStreetMap (ODbL 1.0):** navođenje „© OpenStreetMap contributors" i objava izvedenih baza pod istom licencijom (već poštovano).
- **Zaštita osobnih podataka:** usluga danas ne obrađuje osobne podatke (nema računa, adrese se ne spremaju, nema zapisa IP adresa). Ako se uvedu obavijesti e-poštom, potrebni su pravna osnova (privola), obavijest o obradi i mogućnost brisanja, prema Općoj uredbi o zaštiti podataka i Zakonu o provedbi Opće uredbe o zaštiti podataka (»Narodne novine«, br. 42/18.).
- **Odricanje odgovornosti:** EkoSkor je orijentacija, a ne službena procjena rizika ni pravni, osiguravateljni ili savjet o nekretninama; to se mora jasno navesti u usluzi (navedeno u „Kako računamo?").
- **Pristupačnost:** kao usluga javnog sektora mora zadovoljiti propise o pristupačnosti mrežnih stranica tijela javnog sektora (cilj WCAG 2.2 AA; Lighthouse pristupačnost danas 100 na početnoj stranici i stranici adrese).
