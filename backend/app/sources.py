"""Registry of every dataset and service EkoAdresa uses (CLAUDE.md §2.4).

One entry per `source_id` that appears in an API response or a committed data file.
Facts are copied from docs/data-sources.md, which records how each was checked; keep the
two in sync. Licences are quoted as stated by the publisher; None means none is stated.
"""

from app.models import Source

_DATA_ZAGREB = "https://data.zagreb.hr/dataset/"
_OVERPASS = "https://overpass-api.de/api/interpreter"
_AIR_PACKAGES = ["dordiceva", "ksaver", "pescenica", "prilaz-baruna-filipovica", "siget",
                 "susedgrad"]  # fmt: skip

SOURCES: dict[str, Source] = {
    s.id: s
    for s in [
        Source(
            id="hv-poplave",
            name="Karte opasnosti od poplava",
            publisher="Hrvatske vode",
            access="live",
            urls=["https://servisi.voda.hr/poplave_opasnosti/wms"],
            licence=None,
            data_as_of="nije navedeno",
            used_for="Zona opasnosti od poplava na adresi (OGC WMS)",
        ),
        Source(
            id="zg-buka",
            name="Strateška karta buke Grada Zagreba",
            publisher="Grad Zagreb",
            access="live",
            urls=[
                "https://geoportal.zagreb.hr/Public/StrategijskoPlaniranje_Public/MapServer/WMSServer"
            ],
            licence=None,
            data_as_of="nije navedeno",
            used_for="Razine buke Lden i Lnight na adresi (OGC WMS)",
        ),
        Source(
            id="zg-zrak-postaje",
            name="Geoportal Kvaliteta zraka",
            publisher="Grad Zagreb",
            access="snapshot",
            urls=[_DATA_ZAGREB + "geoportal-kvaliteta-zraka"],
            licence="Otvorena dozvola (OD)",
            data_as_of="katalog ažuriran 2024-02-06",
            used_for="Lokacije gradskih mjernih postaja kvalitete zraka",
        ),
        Source(
            id="zg-zrak-mjerenja",
            name="Podaci o kvaliteti zraka u Gradu Zagrebu – MP 2023 (6 postaja)",
            publisher="Grad Zagreb (mjerenja: IMI)",
            access="snapshot",
            urls=[
                _DATA_ZAGREB + f"podaci-o-kvaliteti-zraka-u-gradu-zagrebu-{p}-2023"
                for p in _AIR_PACKAGES
            ],  # fmt: skip
            licence=(
                "Otvorena dozvola (OD) na data.zagreb.hr; data.gov.hr za Đorđićevu i Ksaver "
                "navodi CC BY 4.0"
            ),
            data_as_of="dnevne vrijednosti 2023-01-01 – 2023-08-31",
            used_for="Prosjek PM10 za EkoSkor, posljednje vrijednosti i povijest mjerenja",
        ),
        Source(
            id="rh-zrak-indeks",
            name="Indeks kvalitete zraka u Republici Hrvatskoj – INSPIRE",
            publisher="Državna geodetska uprava (prema data.gov.hr)",
            access="live",
            urls=["https://servisi.azo.hr/inspire/geos1/hh/wfs", "https://iszz.azo.hr/iskzl/"],
            licence=None,
            data_as_of="vrijednosti od istog dana",
            used_for="Trenutni indeks na najbližoj državnoj postaji (dodatna informacija)",
        ),
        Source(
            id="dhmz-kvaliteta-zraka",
            name="Kvaliteta zraka – podaci automatskih postaja, protekla 24 sata",
            publisher="Državni hidrometeorološki zavod (DHMZ)",
            access="live",
            urls=[
                "https://meteo.hr/kvaliteta_zraka.php?section=podaci_kz",
                "https://meteo.hr/o_nama.php?section=naslovnica&param=uvjeti",
            ],
            licence=(
                "Uvjeti korištenja DHMZ-a: podaci su slobodno dostupni za ponovnu uporabu "
                'uz navođenje izvora „(Izvor: DHMZ)"'
            ),
            data_as_of="satne vrijednosti za protekla 24 sata, nevalidirane",
            used_for="Trenutne vrijednosti PM10, PM2,5 i NO₂ na najbližoj državnoj postaji "
            "(dodatna informacija, ne ulazi u EkoSkor)",
        ),
        Source(
            id="zg-reciklaza",
            name="Geoportal Reciklažna dvorišta grada Zagreba",
            publisher="Grad Zagreb",
            access="snapshot",
            urls=[_DATA_ZAGREB + "reciklazna-dvorista-grada-zagreba1"],
            licence="Otvorena dozvola (OD)",
            data_as_of="2022-12-01",
            used_for="Najbliže fiksno i mobilno reciklažno dvorište",
        ),
        Source(
            id="osm-reciklaza",
            name="Spremnici za reciklažu (zeleni otoci), Grad Zagreb",
            publisher="OpenStreetMap contributors",
            access="snapshot",
            urls=[_OVERPASS],
            licence="ODbL 1.0, © OpenStreetMap contributors",
            data_as_of="2026-11-04",
            used_for="Najbliži zeleni otok (papir, plastika ili staklo)",
        ),
        Source(
            id="zg-biciklisticke-staze",
            name="Geoportal Biciklističke staze",
            publisher="Grad Zagreb",
            access="snapshot",
            urls=[_DATA_ZAGREB + "geoportal-biciklisticke-staze"],
            licence="Otvorena dozvola (OD)",
            data_as_of="2022-06-23",
            used_for="Najbliža biciklistička staza (1/5 ocjene zelene mobilnosti)",
        ),
        Source(
            id="osm-bajs",
            name="Bajs stanice javnih bicikala, Grad Zagreb",
            publisher="OpenStreetMap contributors",
            access="snapshot",
            urls=[_OVERPASS],
            licence="ODbL 1.0, © OpenStreetMap contributors",
            data_as_of="2026-11-08",
            used_for="Najbliža Bajs stanica (dio ocjene mobilnosti); sloj na karti",
        ),
        Source(
            id="osm-parkovi",
            name="Parkovi, šume, javni vrtovi i zaštićena područja, Grad Zagreb",
            publisher="OpenStreetMap contributors",
            access="snapshot",
            urls=[_OVERPASS],
            licence="ODbL 1.0, © OpenStreetMap contributors",
            data_as_of="2026-11-06",
            used_for="Najbliži park ili šuma od barem 0,5 ha (sloj Zelenilo)",
        ),
        Source(
            id="zg-zet",
            name="Geoportal Autobusna i Tramvajska stajališta ZET",
            publisher="Grad Zagreb",
            access="snapshot",
            urls=[
                _DATA_ZAGREB + "autobusna-stajalista-zet",
                _DATA_ZAGREB + "geoportal-tramvajska-stajalista-zet",
            ],
            licence="Otvorena dozvola (OD)",
            data_as_of="autobusi 2026-10-30, tramvaji 2022-12-08",
            used_for="Broj stajališta ZET-a do 300 m i 500 m i najbliže stajalište",
        ),
        Source(
            id="osm-adrese",
            name="Adrese i naselja u Gradu Zagrebu",
            publisher="OpenStreetMap contributors",
            access="snapshot",
            urls=[_OVERPASS],
            licence="ODbL 1.0, © OpenStreetMap contributors",
            data_as_of="2026-11-05",
            used_for="Pretraga adresa",
        ),
        Source(
            id="osm-granice",
            name="Administrativna granica Grada Zagreba",
            publisher="OpenStreetMap contributors",
            access="snapshot",
            urls=["https://www.openstreetmap.org/relation/226224"],
            licence="ODbL 1.0, © OpenStreetMap contributors",
            data_as_of="2026-11-05",
            used_for="Granica pilot područja i mreža karte EkoSkora",
        ),
    ]
}
