# Izvori podataka

Popis svih skupova podataka i servisa koje EkoAdresa koristi, s izdavačima, poveznicama i licencijama, u skladu s poglavljem III. Pravila za Datathon Portala otvorenih podataka. Isti popis aplikacija prikazuje na stranici **Izvori** (<https://ekoadresa.vercel.app/izvori>) i vraća ga API na `GET /api/sources` (registar `backend/app/sources.py`). Test `backend/tests/test_sources.py` ne prolazi ako neki `source_id` koji aplikacija koristi nije u registru ili u tablici ispod.

Tehnički zapisnik provjere svakog izvora (parametri servisa, problemi, odluke) nalazi se u dodatku [data-sources-zapisnik.md](data-sources-zapisnik.md).

## Sažetak

Licencija je navedena **točno onako kako ju je naveo izdavač**; „nije navedena" znači da metapodaci ne navode licenciju. Datumi su datumi podataka kako ih navodi izdavač ili kako smo ih zabilježili pri preuzimanju.

| `source_id` | Skup podataka | Izdavač | Pristup | Način korištenja | Licencija (kako je navedena) | Datum podataka |
|---|---|---|---|---|---|---|
| `hv-poplave` | Karte opasnosti od poplava | Hrvatske vode | OGC WMS 1.3.0 `https://servisi.voda.hr/poplave_opasnosti/wms` (metapodaci u NIPP-u, zapis `9119600a-fb7f-42e3-ad16-d9d10402eca5`) | Uživo: zona opasnosti i razred dubine na adresi; sloj karte | nije navedena (u servisu: naknade i ograničenja pristupa `NONE`) | nije navedeno |
| `zg-buka` | Strateška karta buke Grada Zagreba | Grad Zagreb | OGC WMS 1.3.0 `https://geoportal.zagreb.hr/Public/StrategijskoPlaniranje_Public/MapServer/WMSServer` (pronađeno putem NIPP-a, zapisi `6a586cec-…` i `40ef7b46-…`) | Uživo: L<sub>den</sub> i L<sub>night</sub> na adresi; sloj karte | nije navedena (u servisu: naknade i ograničenja pristupa `NONE`) | nije navedeno |
| `zg-zrak-postaje` | Geoportal Kvaliteta zraka | Grad Zagreb | <https://data.zagreb.hr/dataset/geoportal-kvaliteta-zraka> (isti paket i na data.gov.hr) | Snimka: lokacije 6 gradskih mjernih postaja | Otvorena dozvola (OD) | katalog ažuriran 6. 2. 2024. |
| `zg-zrak-mjerenja` | Podaci o kvaliteti zraka u Gradu Zagrebu – MP *postaja* 2023 (6 paketa) | Grad Zagreb (mjerenja: Institut za medicinska istraživanja i medicinu rada) | data.zagreb.hr, paketi `podaci-o-kvaliteti-zraka-u-gradu-zagrebu-*-2023`, npr. <https://data.zagreb.hr/dataset/podaci-o-kvaliteti-zraka-u-gradu-zagrebu-dordiceva-2023> | Snimka: prosjek PM10 za EkoSkor, posljednje vrijednosti, graf dnevnih mjerenja | Otvorena dozvola (OD) na data.zagreb.hr; na data.gov.hr za Đorđićevu i Ksaver navedena je CC BY 4.0 (razlika između portala) | dnevne vrijednosti 1. 1. – 31. 8. 2023. |
| `rh-zrak-indeks` | Indeks kvalitete zraka u Republici Hrvatskoj – INSPIRE | data.gov.hr navodi Državnu geodetsku upravu; servis je na servisi.azo.hr | OGC WFS 2.0.0 `https://servisi.azo.hr/inspire/geos1/hh/wfs`; paket `indeks-kvalitete-zraka-u-republici-hrvatskoj-inspire` na data.gov.hr | Uživo: indeks na najbližoj državnoj postaji (dodatna informacija, ne ulazi u EkoSkor) | nije navedena | vrijednosti istog dana |
| `dhmz-kvaliteta-zraka` | Kvaliteta zraka – podaci automatskih postaja, protekla 24 sata (postaje Zagreb 1–4) | Državni hidrometeorološki zavod (DHMZ) | Mrežne stranice <https://meteo.hr/kvaliteta_zraka.php?section=podaci_kz> (nema API-ja ni XML-a za kvalitetu zraka); lokacije postaja s karte <https://meteo.hr/index_kz.php?tab=kz> | Uživo: posljednjih 24 h PM10, PM2,5 i NO₂ na najbližoj državnoj postaji (dodatna informacija, ne ulazi u EkoSkor) | Uvjeti korištenja DHMZ-a (<https://meteo.hr/o_nama.php?section=naslovnica&param=uvjeti>): slobodno za ponovnu uporabu uz navođenje „(Izvor: DHMZ)"; licencija nije imenovana | satne vrijednosti, protekla 24 sata; DHMZ ih označava kao „izvorne nekontrolirane podatke" |
| `zg-reciklaza` | Geoportal Reciklažna dvorišta grada Zagreba | Grad Zagreb | <https://data.zagreb.hr/dataset/reciklazna-dvorista-grada-zagreba1> | Snimka: najbliže fiksno i mobilno reciklažno dvorište | Otvorena dozvola (OD) | resursi ažurirani 1. 12. 2022. |
| `zg-zeleni-otoci` | Lokacije zelenih otoka | Grad Zagreb | data.zagreb.hr, paket `lokacije-zelenih-otoka`, CSV <https://data.zagreb.hr/dataset/0b532fd6-fa24-4f90-8c5e-698b5cbe94b7/resource/5d15eae4-6aa7-426c-b02c-a8fdb3d61a74/download/zeleniotoci.csv> | Službeni popis kao referenca; nema koordinata, pa se udaljenost računa iz `osm-reciklaza` | Otvorena dozvola (OD) | 2016. |
| `osm-reciklaza` | Spremnici za reciklažu (zeleni otoci), Grad Zagreb | OpenStreetMap contributors | Overpass API `https://overpass-api.de/api/interpreter`, upit u `scripts/fetch_waste.py` | Snimka: najbliži zeleni otok (papir, plastika ili staklo) | ODbL 1.0, „© OpenStreetMap contributors" | stanje OSM-a 4. 11. 2026. |
| `zg-zet` | Geoportal Autobusna stajališta ZET i Geoportal Tramvajska stajališta ZET | Grad Zagreb | <https://data.zagreb.hr/dataset/autobusna-stajalista-zet>, <https://data.zagreb.hr/dataset/geoportal-tramvajska-stajalista-zet> | Snimka: broj perona do 300 m i 500 m, najbliže stajalište | Otvorena dozvola (OD) | autobusi 30. 10. 2026. (osvježava se svakih 90 dana), tramvaji 8. 12. 2022. |
| `zg-javni-bicikli` | Geoportal Geolokacije sustava javnih bicikala | Grad Zagreb | <https://data.zagreb.hr/dataset/geoportal-sustav-javnih-bicikala> | Snimka: 32 stanice; najbliža stanica (dio ocjene mobilnosti, bliža od staze se računa) i sloj na karti | Otvorena dozvola (OD) | resurs ažuriran 8. 12. 2022. |
| `zg-parkiralista-bicikli` | Geoportal Javna parkirališta za bicikle | Grad Zagreb | <https://data.zagreb.hr/dataset/geoportal-javna-parkiralista-za-bicikle> | Snimka: 318 mjesta za bicikle; sloj na karti (ne ulazi u ocjenu) | Otvorena dozvola (OD) | resurs ažuriran 10. 1. 2023. |
| `zg-biciklisticke-staze` | Geoportal Biciklističke staze | Grad Zagreb | <https://data.zagreb.hr/dataset/geoportal-biciklisticke-staze> | Snimka: najbliža biciklistička staza (1/5 ocjene zelene mobilnosti), sloj na karti | Otvorena dozvola (OD) | resurs ažuriran 23. 6. 2022. |
| `osm-parkovi` | Parkovi, šume, javni vrtovi i zaštićena područja, Grad Zagreb | OpenStreetMap contributors | Overpass API `https://overpass-api.de/api/interpreter`, upit u `scripts/fetch_green_mobility.py` | Snimka: najbliži park ili šuma od barem 0,5 ha (sloj Zelenilo), sloj na karti | ODbL 1.0, „© OpenStreetMap contributors" | stanje OSM-a 6. 11. 2026. |
| `osm-adrese` | Adrese i naselja u Gradu Zagrebu | OpenStreetMap contributors | Overpass API, upit u `scripts/fetch_addresses.py` | Snimka: pretraga adresa | ODbL 1.0, „© OpenStreetMap contributors" | stanje OSM-a 5. 11. 2026. |
| `osm-granice` | Administrativna granica Grada Zagreba (relacija 226224, ISO 3166-2 HR-21) | OpenStreetMap contributors | <https://www.openstreetmap.org/relation/226224>, upit u `scripts/build_heatmap.py` | Snimka: granica pilot područja, mreža karte grada | ODbL 1.0, „© OpenStreetMap contributors" | preuzeto 5. 11. 2026. |
| `rh-buka` | Informacijski sustav strateških karata buke i akcijskih planova | `TODO(verify)` (servis na servisi.azo.hr) | `http://servisi.azo.hr/zdravlje/wms`, `/wfs` | Ne koristi se; zabilježen kao mogući državni izvor buke izvan Zagreba | `TODO(verify)` | nije provjereno |

**Uživo** znači da backend pri upitu za adresu poziva javni servis (odgovor se privremeno sprema do 30 dana, za indeks zraka 1 sat). **Snimka** znači da je skup preuzet skriptom iz mape `scripts/`, očišćen i spremljen u mapu `data/` repozitorija, pa se može ponovno izraditi.

Podloga karte su vektorske pločice OpenFreeMap (© OpenMapTiles, podaci © OpenStreetMap contributors). Podloga služi samo za prikaz i ne ulazi u izračun.

## Licencije i navođenje izvora

- **Otvorena dozvola (OD)** dozvola je za ponovnu uporabu informacija prema Pravilniku o vrstama i sadržaju dozvola za ponovnu uporabu informacija (»Narodne novine«, br. 67/17.), pod kojom Grad Zagreb objavljuje svoje skupove na data.zagreb.hr i data.gov.hr. Uvjet je navođenje izvora.
- **CC BY 4.0** (dva paketa mjerenja zraka na data.gov.hr) također traži navođenje autora. Zbog razlike između portala navodimo obje licencije onako kako su objavljene.
- **ODbL 1.0** (OpenStreetMap) traži navođenje „© OpenStreetMap contributors" i dijeljenje izmijenjene baze pod istom licencijom. Navod je na karti, na stranici Izvori i u ovom dokumentu. Izvedene snimke u `data/` (adrese, zeleni otoci, granica) ostaju pod ODbL-om.
- **Licencija nije navedena** za tri javna servisa: `hv-poplave` (Hrvatske vode), `zg-buka` (Grad Zagreb) i `rh-zrak-indeks`. Servisi su javno dostupni bez prijave, upisani su u Nacionalnu infrastrukturu prostornih podataka (NIPP) odnosno na data.gov.hr, a njihov opis (GetCapabilities) za naknade i ograničenja pristupa navodi `NONE`. Pravila (pogl. III.) dopuštaju i druge javno dostupne izvore, uključujući API servise tijela javnog sektora; tim ih koristi u svrhu Datathona, uz navođenje izdavača. Ova tri izvora nigdje ne prikazujemo kao da imaju licenciju, a za trajnu javnu uslugu potrebna je izričita dozvola za ponovnu uporabu (vidi [integracija.md](integracija.md)).

**Kako aplikacija navodi izvor:** svaki redak kartice adrese prikazuje izdavača i naziv skupa; svaki broj u odgovoru API-ja nosi `source_id`; stranica Izvori i `GET /api/sources` daju potpun popis s poveznicama, licencijama i datumima; slojevi karte imaju navod izdavača u atribuciji karte.

## Opis izvora

### Poplave: `hv-poplave`

WMS servis Hrvatskih voda s tri scenarija (velika, srednja i mala vjerojatnost pojavljivanja), a boja poligona označava razred dubine vode. Servis odbija upit za točku (`GetFeatureInfo`: „LayerNotQueryable"), pa backend iscrtava malu kartu oko adrese (101 × 101 px, ~1 : 25 000) i čita boju središnjeg piksela prema legendi. Slojevi se ne iscrtavaju u mjerilu krupnijem od 1 : 20 000, pa sloj karte pri većem uvećanju povećava pločicu razine 14. Servis povremeno vraća pogrešku HTTP 502 ili prekinut odgovor (u testu 4 od 40 upita na Savici), pa backend ponavlja upit do 4 puta i sprema odgovore.

### Buka: `zg-buka`

WMS servis Grada Zagreba (slojevi s oznakom `SKB_R4_…`; koji krug izrade karte oznaka označava `TODO(verify)`), zaseban sloj za svaki izvor (cestovni, tramvajski, željeznički promet, industrija) i pokazatelj (L<sub>den</sub>, L<sub>night</sub>) u razredima od 5 dB. Upit za točku (`GetFeatureInfo`, JSON) vraća donju granicu razreda; parametar `propertyName` smanjuje odgovor s 1,1 MB na 394 B. Karta nema vrijednosti unutar zgrada, pa se za adresu unutar zgrade uzima najglasnije pročelje (vidi [ekoskor.md](ekoskor.md)). Servis ne šalje CORS zaglavlja, pa sloj karte ide preko backenda (`/api/tiles/noise/…`).

### Zrak: `zg-zrak-postaje`, `zg-zrak-mjerenja`, `rh-zrak-indeks`

Šest gradskih mjernih postaja (Đorđićeva ulica, Ksaverska cesta, Peščenica, Prilaz baruna Filipovića, Siget, Susedgrad) i njihova dnevna mjerenja za 2023. (jedna XLSX datoteka po mjesecu, siječanj–kolovoz; 48 datoteka). Skripta `scripts/fetch_air.py` zadržava NO₂, O₃, PM10 i PM2,5 (stupci se prepoznaju po nazivu jer se razlikuju po postajama), prazne ćelije izostavlja, a rezultat je `data/air_history.parquet` (4 790 redaka). Državni indeks (`rh-zrak-indeks`, 25 postaja u RH, od toga 2 u Zagrebu) dohvaća se uživo kao dodatna informacija; ljestvica indeksa nije navedena u odgovoru servisa (`TODO(verify)`), pa ga API označava s `scale_verified: false` i ne ulazi u EkoSkor.

### Zrak uživo: `dhmz-kvaliteta-zraka` (provjereno 6. 11. 2026.)

DHMZ upravlja državnim postajama Zagreb 1–4 i na svojim stranicama objavljuje satne vrijednosti za protekla 24 sata po postaji i onečišćujućoj tvari, kao **izvorne nekontrolirane podatke**. DHMZ za kvalitetu zraka **nema API ni XML** (njegov popis „XML za korisnike" ne sadrži kvalitetu zraka), a na data.gov.hr nema skupa koji objavljuje DHMZ. Arhiva je na portalu ministarstva (iszz.azo.hr), bez dokumentiranog API-ja. Backend zato čita vrijednosti iz podataka grafa na stranici (`[new Date(…), vrijednost]`), samo za najbližu od 4 zagrebačke postaje, najviše 3 upita na sat po postaji (PM10, PM2,5, NO₂; Zagreb 1 nema NO₂). Upit sadrži samo naziv postaje, ne koordinate korisnika. Koordinate postaja preuzete su s DHMZ-ove karte postaja; Zagreb 1 i Zagreb 3 poklapaju se s postajama državnog indeksa (`rh-zrak-indeks`). Podaci od 24 sata i nevalidirani ne mogu zamijeniti godišnji prosjek PM10 na kojem se temelji ocjena, pa se prikazuju samo kao dodatna informacija s oznakom „nevalidirano". Ako se stranica DHMZ-a promijeni ili ne odgovori u 2,5 s, kartica radi bez tog podatka.

### Otpad: `zg-reciklaza`, `zg-zeleni-otoci`, `osm-reciklaza`

Gradski skup ima 20 reciklažnih dvorišta: 10 fiksnih i 10 mobilnih (mobilna rade samo određenim danima i ne ulaze u ocjenu). Gradski popis zelenih otoka iz 2016. nema koordinata, samo opis lokacije, pa se udaljenost računa iz OpenStreetMapa: 628 spremnika za papir, plastiku ili staklo. Gradski popis ostaje službena referenca. Pokrivenost OSM-a izvan središta grada je rjeđa.

### Javni bicikli i parkirališta: `zg-javni-bicikli`, `zg-parkiralista-bicikli`

Stanice sustava javnih bicikala (32, s 208 stalaka) i javna parkirališta za bicikle (318 mjesta, 1 678 stalaka) iz gradskih geoportal skupova. Skup stanica nigdje ne navodi operatera; prema OpenStreetMapu stanice su sustava Bajs, pa se u aplikaciji naziv „Bajs“ ne koristi dok se ne provjeri (`TODO(verify)`). Stanice ulaze u ocjenu zelene mobilnosti kao alternativa biciklističkoj stazi (vidi `ekoskor.md`); parkirališta su samo na karti.

### Zelena mobilnost i zelenilo: `zg-zet`, `zg-biciklisticke-staze`, `osm-parkovi`

1 888 autobusnih i 260 tramvajskih perona ZET-a (jedna točka po stajalištu i smjeru). Broje se peroni do 300 m i 500 m zračne udaljenosti; najbliže stajalište prikazuje se s linijama. Na data.zagreb.hr nema GTFS paketa, pa vozni red i učestalost polazaka nisu uključeni.

**Biciklističke staze (provjereno 6. 11. 2026.):** gradski skup ima 2 889 dionica, ukupno 269 km (izračunato u EPSG:3765), s atributima lokacije, kategorije (`kategorija_id`: PB, CM, BT, BP, JS, PO, BS) i završnog sloja. Značenje kratica kategorija nije objavljeno (`TODO(verify)`), pa se sve dionice računaju jednako. Resurs je ažuriran 23. 6. 2022.; novije staze možda nisu uključene. Grad objavljuje i lokacije javnih bicikala i parkirališta za bicikle (`geoportal-sustav-javnih-bicikala`, `geoportal-javna-parkiralista-za-bicikle`); zasad se ne koriste.

**Parkovi i šume (provjereno 6. 11. 2026.):** Grad na data.zagreb.hr nema skup postojećih parkova. Skup *Planirana namjena* (GUP) ima javne parkove i park-šume, ali opisuje **planiranu** namjenu, a ne stanje na terenu, a preuzimanje GeoJSON-a 2026. vraća samo 2 000 od ~9 000 površina (ograničenje izvoza). Zato se koristi OpenStreetMap: `leisure=park`, `leisure=garden` (bez `access=private`), `leisure=nature_reserve`, `landuse=forest` i `natural=wood`, samo površine od barem 0,5 ha (prag iz WHO Europe, *Urban green spaces: a brief for action*, 2017.). Ukupno 1 136 površina. Jarun je u OSM-u označen kao sportski centar, pa nije uključen (oznaku sportskog centra imaju i dvorane), ali obala Jaruna ima park ili šumu na manje od 200 m. Pješačka zona (`geoportal-pjesacka-zona`) i pješačke staze iz OSM-a zasad se ne boduju: pješačke staze postoje gotovo uz svaku adresu u gradu, pa ne bi razlikovale adrese.

### Adrese i granica: `osm-adrese`, `osm-granice`

Pretraga adresa radi nad lokalnom snimkom adresa iz OpenStreetMapa (35 655 adresa, 2 570 ulica, 392 naselja), bez vanjskog servisa u radu: pravila korištenja Nominatima ne dopuštaju automatsko dovršavanje. OSM ne sadrži sve kućne brojeve; službeni adresni registar Državne geodetske uprave bio bi potpuniji (dostupnost kao otvoreni podatak `TODO(verify)`, vidi [daljnji-razvoj.md](daljnji-razvoj.md)). Granica Grada Zagreba iz OSM-a određuje pilot područje: za točke izvan nje API vraća pogrešku 422.
