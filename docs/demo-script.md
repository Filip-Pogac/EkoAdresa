# Scenarij videa (do 3 minute)

Video prikazuje rješenje u primjeni i obuhvaća sve što traži javni poziv: problem, ciljne korisnike, izvore podataka, funkcionalnosti, tehničku arhitekturu, korisničku vrijednost i daljnji razvoj. Tekst naracije ima oko 400 riječi, što je mirnim tempom oko 2 min 45 s; ostatak je zaliha za prijelaze.

Brojevi u tekstu su provjereni na objavljenoj stranici 9. 11. 2026. Ako se prije snimanja promijene podaci ili formula, ponovno ih provjerite na stranici i ispravite ovdje.

## Priprema

- **Prije snimanja** pokrenite Playwright test (`cd frontend && pnpm e2e`); mora proći.
- **Preglednik:** svijetla tema, prozor 1440 × 900, povećanje 100 %, bez drugih kartica i oznaka.
- **Predmemorija:** dan prije i neposredno prije snimanja jednom otvorite sve tri adrese iz scenarija, da se odgovori učitaju odmah.
- **Dijagram arhitekture:** otvorite `docs/arhitektura.md` na GitHubu, odjeljak 1 (GitHub iscrtava Mermaid dijagram).
- **Snimanje:** zaslon i glas snimajte odvojeno ako je moguće. Glas snimajte u tihoj prostoriji, a sliku montirajte prema glasu.

## Scenarij

| Vrijeme | Na zaslonu | Naracija |
|---|---|---|
| **0:00–0:20**<br>Problem | Početna stranica EkoAdrese, karta Zagreba. Kratko: geoportal Hrvatskih voda ili Grada Zagreba s tablicom slojeva. | „Kad biramo stan, vrtić ili školu, pitamo se: kako je tu živjeti? Podaci o poplavama, buci i zraku već postoje, ali su raspršeni po geoportalima i tablicama koje običan građanin ne nalazi i ne zna čitati." |
| **0:20–0:35**<br>Korisnici | Ostaje početna stranica. | „EkoAdresa to mijenja. Namijenjena je građanima koji biraju gdje će živjeti, Gradu i javnim tijelima koja planiraju prostor, te drugim servisima, poput portala nekretnina." |
| **0:35–1:05**<br>Kartica adrese | Upisati „Trg bana", odabrati Trg bana Josipa Jelačića 6. Kartica: EkoSkor 74, zatim polako niz slojeve. | „Upišem adresu i odmah dobijem EkoSkor od 0 do 100 i šest slojeva: buku, zelenu mobilnost, zrak, zelenilo, poplave i otpad. Svaki sloj ima stanje riječima i ikonom, ne samo bojom, i jednu rečenicu na hrvatskom. Na Trgu bana Jelačića EkoSkor je 74: prijevoz i zelenilo su odlični, ali buka je loša, 65 do 69 decibela, iznad smjernice Svjetske zdravstvene organizacije." |
| **1:05–1:20**<br>Karta | Na karti uključiti sloj Buka, zatim Stajališta ZET-a. Kliknuti na točku na karti; naslov se mijenja u adresu te točke. | „Na karti uključujem slojeve: buku, poplave, stajališta, Bajs stanice, parkove. Klikom na bilo koju točku dobijem njezin EkoSkor." |
| **1:20–1:45**<br>Usporedba | „Usporedi s drugom adresom", druga adresa Ulica Vladimira Ruždjaka 20. Pomicati niz razlike po slojevima. | „Najjači trenutak je usporedba dvaju stanova. Centar ima 74, a Ruždjakova ulica na Savici 57. Odmah vidim zašto: Savica je u zoni male vjerojatnosti poplave, a prijevoz je slabiji. Za svaki sloj piše koja je adresa bolja." |
| **1:45–2:00**<br>Za grad | Stranica Za grad, karta Zagreba u bojama od crvene do zelene; kliknuti na jednu ćeliju. | „Za Grad imamo kartu EkoSkora za cijeli Zagreb, na mreži od 250 puta 250 metara. Ona pokazuje gdje nedostaju reciklaža, prijevoz ili zelenilo." |
| **2:00–2:20**<br>Izvori podataka | Stranica Izvori, polako niz popis. Zatim „Kako računamo?" s tablicom pondera. | „Sve je iz otvorenih podataka: 15 skupova od 5 izdavača — Hrvatskih voda, Grada Zagreba, DHMZ-a, državnog servisa kvalitete zraka i OpenStreetMapa. Uz svaki je izdavač, licencija i datum. Formula je javna: nema crne kutije." |
| **2:20–2:40**<br>Arhitektura | Dijagram iz `docs/arhitektura.md`, zatim kratko `/docs` (OpenAPI) na API-ju. | „Frontend u Reactu poziva FastAPI backend. Za svaku adresu backend istodobno uživo pita javne OGC servise za poplave i buku, spaja ih sa snimkama otvorenih skupova i za manje od sekunde vraća ocjenu. API je otvoren i dokumentiran, a kod je javan pod licencijom MIT." |
| **2:40–3:00**<br>Vrijednost i daljnji razvoj | Natrag na usporedbu dviju adresa; na kraju logo EkoAdrese i poveznica ekoadresa.vercel.app. | „Građanin u minuti dobije odgovor koji bi inače tražio danima. Sljedeći koraci su cijela Hrvatska, jer su karte poplava već državne, obavijesti o odvozu otpada i API za portale nekretnina. EkoAdresa: kako je živjeti na ovoj adresi?" |

## Na što paziti

- **Ne govoriti „uživo" za zrak u EkoSkoru:** ocjena zraka računa se iz mjerenja 2023. Uživo su poplave, buka i dodatni prikaz zadnja 24 sata (DHMZ), koji ne ulazi u EkoSkor.
- **Ne spominjati AI asistenta** kao dio rješenja: odgođen je i nije izgrađen. U daljnjem razvoju se smije spomenuti kao plan.
- **Udaljenosti su zračne,** ne pješačke; ako se spominju, reći „do 300 metara", ne „300 metara hoda".
