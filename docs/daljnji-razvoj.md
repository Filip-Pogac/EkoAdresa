# Daljnji razvoj

Prototip pokriva Grad Zagreb i teme iz izazova B: zrak, zelena mobilnost, poplave i buka ulaze u EkoSkor uz zelenilo, a otpad (reciklažna dvorišta, zeleni otoci) prikazan je na karti. Ovdje su sljedeći koraci, poredani od najbližih prema najvećima. Izvori podataka koje još nismo provjerili označeni su s `TODO(verify)`: ništa od toga ne tvrdimo dok ne provjerimo izdavača, licenciju i pristup.

## 1. Kratkoročno (dani do tjedni)

- **Pravilo pročelja i na karti grada:** kartica adrese za točke unutar zgrada uzima najglasnije pročelje, a mreža za grad još ne; potreban je ponovni izračun mreže.
- **Bolji zeleni otoci:** gradski popis zelenih otoka (2016.) nema koordinate; geokodiranjem bi se dobio službeni izvor umjesto OpenStreetMapa.
- **Pješačke udaljenosti** umjesto zračnih (otvoreni usmjerivač nad OpenStreetMapom).
- **Učestalost javnog prijevoza:** osim broja stajališta, broj polazaka. Grad Zagreb na data.zagreb.hr nema GTFS paket; izvor voznog reda `TODO(verify)`.

## 2. Novi podaci za postojeće teme

- **Kvaliteta zraka u ocjeni:** kartica već prikazuje posljednja 24 sata s najbliže državne postaje DHMZ-a, s vlastitim stanjem prema dnevnim smjernicama SZO-a, ali kao nevalidirane podatke koji ne ulaze u EkoSkor. Najnoviji objavljeni otvoreni podaci gradskih postaja su iz 2023. (provjereno na data.zagreb.hr i data.gov.hr 6. 11. 2026.). Dva puta do ocjene iz aktualnih podataka:
  - **Vlastita povijest:** svaki dan spremiti 24-satni prosjek DHMZ-a po postaji i tvari, a nakon dovoljno dana (npr. 12 mjeseci, da su obuhvaćene sve sezone) ocjenu zraka računati iz tog godišnjeg prosjeka uz iste godišnje pragove. Ograničenje: podaci ostaju nevalidirani, a DHMZ ih objavljuje samo kao web-stranice.
  - **Validirana povijest** (npr. godišnji prosjek) iz državne baze kvalitete zraka (portal iszz.azo.hr), koja danas nema dokumentirani API (`TODO(verify)`).
- **Službeni adresni registar** Državne geodetske uprave umjesto OpenStreetMapa, za sve kućne brojeve (dostupnost kao otvoreni podatak `TODO(verify)`).

## 3. Nove teme iz izazova B

| Tema | Što bi korisnik dobio | Izvor |
|---|---|---|
| **Kakvoća mora i vode za kupanje** | Najbliže plaže i kupališta s ocjenom kakvoće (za obalne gradove) | `TODO(verify)` |
| **Rizik od požara** | Ugroženost okoliša adrese požarom raslinja, sezonski indeks opasnosti | `TODO(verify)` |
| **Zaštita prirode** | Blizina zaštićenih područja i područja ekološke mreže | `TODO(verify)` |
| **Društveni život** (hrana, kafići, izlasci na pješačkoj udaljenosti) | Koliko je četvrt živa, kao zaseban redak koji ne ulazi u EkoSkor | OpenStreetMap; prije toga provjera službenog registra ugostiteljskih objekata `TODO(verify)` |

## 4. Obavijesti

Obavijesti o događajima na adresi: **datumi odvoza otpada** (plastika, papir, biootpad, glomazni otpad), loša kvaliteta zraka, upozorenja na poplave.

- **Podaci:** otvoreni skup rasporeda odvoza po ulici ili četvrti `TODO(verify)` (operater je Zagrebački holding – Podružnica Čistoća). Bez takvog skupa obavijesti o odvozu nisu moguće.
- **Načini:** datoteka kalendara (.ics) koju korisnik doda u svoj kalendar, bez spremanja ičega na poslužitelju; prikaz sljedećeg odvoza na kartici; obavijesti e-poštom.
- **Privatnost:** za obavijesti e-poštom spremaju se adresa e-pošte i adresa ili četvrt. Korisniku se prije prijave mora jasno reći što se sprema, zašto i kako to obrisati, a svaka poruka ima poveznicu za odjavu.

## 5. AI asistent (odgođeno)

Planirani asistent odgovarao bi na pitanja o adresi na hrvatskom, na primjer *„Mogu li spavati s otvorenim prozorom?"* ili *„Treba li mi osiguranje od poplave?"*, i napisao sažetak usporedbe dviju adresa u 3–4 rečenice.

- **Samo iz podataka:** model jezika s alatima (`get_profile`, `compare`, `explain_layer`, `nearest_facility`) koji pozivaju postojeći API. Odgovara samo iz rezultata alata, uz svaki podatak navodi izvor i kaže „nemam taj podatak" kad podatka nema.
- **Provjera brojeva:** nakon odgovora provjerava se da se svaki broj u odgovoru nalazi u rezultatima alata; ako ne, odgovor se ponovno generira, a zatim zamjenjuje sigurnom porukom.
- **Bez savjeta:** ne daje pravne, osiguravateljne, medicinske ni savjete o cijeni nekretnina, nego upućuje na nadležnu instituciju.
- **Zamjenjiv model:** komercijalni API ili otvoreni model koji se pokreće lokalno, odabran postavkom, bez promjene koda.
- **Provjera kvalitete:** 10 pitanja s očekivanim odgovorima; cilj je najmanje 8/10 točnih i 10/10 bez izmišljenog broja.

Odgođeno je 5. 11. 2026. kako bi se rok predaje posvetio pouzdanosti i dovršenosti ostatka rješenja. Cijeli plan (arhitektura, testovi, procjena troška) zapisan je u repozitoriju.

## 6. Cijela Hrvatska

- **Buka:** strateške karte buke za ostale aglomeracije i velike ceste nalaze se u državnom informacijskom sustavu (servisi.azo.hr, `rh-buka`; zabilježen, ali nije provjeren).
- **Poplave:** karta Hrvatskih voda već pokriva cijelu Hrvatsku; mijenja se samo granica područja.
- **Zrak:** državna mreža postaja umjesto gradske.
- **Otpad i prijevoz:** reciklažna dvorišta i stajališta po gradovima, gdje su objavljeni kao otvoreni podaci; OpenStreetMap kao dopuna.
- **Adrese:** službeni adresni registar za cijelu državu.
- **Tehnički:** baza s prostornim indeksima (PostGIS) i zakazano osvježavanje podataka; vidi [arhitektura.md](arhitektura.md), točka 10.

Kad podatak za neki sloj ne postoji, sloj je „nedostupan", a EkoSkor se računa iz ostalih slojeva, pa se usluga može širiti postupno, grad po grad.

## 7. API za druge usluge

- **Portali nekretnina i oglasi za najam:** EkoSkor i pet slojeva uz svaki oglas, s izvorom za svaki podatak; EkoAdresa ostaje izvor podatka, a ne procjena cijene.
- **Javna tijela:** mreža EkoSkora i pojedinih slojeva kao otvoreni skup (GeoJSON) za planiranje, npr. gdje nedostaju reciklažna dvorišta ili stajališta.
- **Škole, vrtići, zdravstvo:** profil okoliša za lokaciju ustanove.

Preduvjeti (dozvole izvora, dostupnost, ograničenje broja upita) opisani su u [integracija.md](integracija.md).
