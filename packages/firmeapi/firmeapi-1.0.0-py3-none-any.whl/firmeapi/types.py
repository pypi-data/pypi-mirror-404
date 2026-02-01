"""
FirmeAPI Type Definitions
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Address:
    """Company address"""

    strada: Optional[str] = None
    numar: Optional[str] = None
    localitate: Optional[str] = None
    judet: Optional[str] = None
    cod_judet: Optional[str] = None
    cod_postal: Optional[str] = None
    detalii: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> Optional["Address"]:
        if not data:
            return None
        return cls(
            strada=data.get("strada"),
            numar=data.get("numar"),
            localitate=data.get("localitate"),
            judet=data.get("judet"),
            cod_judet=data.get("cod_judet"),
            cod_postal=data.get("cod_postal"),
            detalii=data.get("detalii"),
        )


@dataclass
class TvaPeriod:
    """TVA (VAT) registration period"""

    data_inceput: Optional[str] = None
    data_sfarsit: Optional[str] = None
    data_anul_fiscal: Optional[str] = None
    mesaj_scpTVA: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TvaPeriod":
        return cls(
            data_inceput=data.get("data_inceput"),
            data_sfarsit=data.get("data_sfarsit"),
            data_anul_fiscal=data.get("data_anul_fiscal"),
            mesaj_scpTVA=data.get("mesaj_scpTVA"),
        )


@dataclass
class TvaInfo:
    """TVA (VAT) information"""

    platitor: bool = False
    perioade: list[TvaPeriod] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TvaInfo":
        perioade = [TvaPeriod.from_dict(p) for p in data.get("perioade", [])]
        return cls(
            platitor=data.get("platitor", False),
            perioade=perioade,
        )


@dataclass
class StatusInactiv:
    """Company inactive status"""

    inactiv: bool = False
    data_inactivare: Optional[str] = None
    data_reactivare: Optional[str] = None
    data_radiere: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StatusInactiv":
        return cls(
            inactiv=data.get("inactiv", False),
            data_inactivare=data.get("data_inactivare"),
            data_reactivare=data.get("data_reactivare"),
            data_radiere=data.get("data_radiere"),
        )


@dataclass
class Company:
    """Company details"""

    cui: int
    denumire: str
    data_inregistrare: Optional[str] = None
    stare: Optional[str] = None
    cod_caen: Optional[str] = None
    nr_reg_com: Optional[str] = None
    telefon: Optional[str] = None
    fax: Optional[str] = None
    cod_postal: Optional[str] = None
    adresa_sediu_social: Optional[Address] = None
    adresa_domiciliu_fiscal: Optional[Address] = None
    tva: Optional[TvaInfo] = None
    status_inactiv: Optional[StatusInactiv] = None
    organ_fiscal: Optional[str] = None
    forma_organizare: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Company":
        return cls(
            cui=data.get("cui", 0),
            denumire=data.get("denumire", ""),
            data_inregistrare=data.get("data_inregistrare"),
            stare=data.get("stare"),
            cod_caen=data.get("cod_caen"),
            nr_reg_com=data.get("nr_reg_com"),
            telefon=data.get("telefon"),
            fax=data.get("fax"),
            cod_postal=data.get("cod_postal"),
            adresa_sediu_social=Address.from_dict(data.get("adresa_sediu_social")),
            adresa_domiciliu_fiscal=Address.from_dict(data.get("adresa_domiciliu_fiscal")),
            tva=TvaInfo.from_dict(data["tva"]) if data.get("tva") else None,
            status_inactiv=StatusInactiv.from_dict(data["status_inactiv"])
            if data.get("status_inactiv")
            else None,
            organ_fiscal=data.get("organ_fiscal"),
            forma_organizare=data.get("forma_organizare"),
        )


@dataclass
class BilantDetalii:
    """Balance sheet details"""

    I1: Optional[int] = None  # Cifra de afaceri neta
    I2: Optional[int] = None  # Venituri totale
    I3: Optional[int] = None  # Cheltuieli totale
    I4: Optional[int] = None  # Profit brut
    I5: Optional[int] = None  # Profit net
    I6: Optional[int] = None  # Active imobilizate
    I7: Optional[int] = None  # Active circulante
    I8: Optional[int] = None  # Datorii
    I9: Optional[int] = None  # Capitaluri proprii
    I10: Optional[int] = None  # Numar mediu salariati

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BilantDetalii":
        return cls(
            I1=data.get("I1"),
            I2=data.get("I2"),
            I3=data.get("I3"),
            I4=data.get("I4"),
            I5=data.get("I5"),
            I6=data.get("I6"),
            I7=data.get("I7"),
            I8=data.get("I8"),
            I9=data.get("I9"),
            I10=data.get("I10"),
        )


@dataclass
class BilantYear:
    """Balance sheet for a specific year"""

    an: int
    cui: int
    denumire: str
    caen: str
    denumire_caen: str
    detalii: BilantDetalii

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BilantYear":
        return cls(
            an=data.get("an", 0),
            cui=data.get("cui", 0),
            denumire=data.get("denumire", ""),
            caen=data.get("caen", ""),
            denumire_caen=data.get("denumire_caen", ""),
            detalii=BilantDetalii.from_dict(data.get("detalii", {})),
        )


@dataclass
class Bilant:
    """Company balance sheet"""

    cui: int
    ani: list[BilantYear]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Bilant":
        return cls(
            cui=data.get("cui", 0),
            ani=[BilantYear.from_dict(y) for y in data.get("ani", [])],
        )


@dataclass
class Restanta:
    """ANAF debt entry"""

    tip_obligatie: str
    suma_restanta: float
    data_obligatie: str
    stare: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Restanta":
        return cls(
            tip_obligatie=data.get("tip_obligatie", ""),
            suma_restanta=data.get("suma_restanta", 0.0),
            data_obligatie=data.get("data_obligatie", ""),
            stare=data.get("stare", ""),
        )


@dataclass
class RestanteResponse:
    """ANAF debts response"""

    cui: int
    restante: list[Restanta]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RestanteResponse":
        return cls(
            cui=data.get("cui", 0),
            restante=[Restanta.from_dict(r) for r in data.get("restante", [])],
        )


@dataclass
class MofPublication:
    """Monitorul Oficial publication"""

    denumire: str
    publicatieNr: str
    data: str
    titlu_publicatie: str
    continut: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MofPublication":
        return cls(
            denumire=data.get("denumire", ""),
            publicatieNr=data.get("publicatieNr", ""),
            data=data.get("data", ""),
            titlu_publicatie=data.get("titlu_publicatie", ""),
            continut=data.get("continut", ""),
        )


@dataclass
class MofResponse:
    """MOF publications response"""

    cui: int
    rezultate: list[MofPublication]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MofResponse":
        return cls(
            cui=data.get("cui", 0),
            rezultate=[MofPublication.from_dict(p) for p in data.get("rezultate", [])],
        )


@dataclass
class Pagination:
    """Pagination information"""

    total: int
    page: int
    per_page: int
    total_pages: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pagination":
        return cls(
            total=data.get("total", 0),
            page=data.get("page", 1),
            per_page=data.get("per_page", 20),
            total_pages=data.get("total_pages", 0),
        )


@dataclass
class SearchResponse:
    """Company search response"""

    items: list[Company]
    pagination: Pagination

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResponse":
        return cls(
            items=[Company.from_dict(c) for c in data.get("items", [])],
            pagination=Pagination.from_dict(data.get("pagination", {})),
        )


@dataclass
class FreeCompany:
    """Basic company info from free API"""

    cui: int
    denumire: str
    adresa: Optional[str] = None
    telefon: Optional[str] = None
    cod_caen: Optional[str] = None
    stare: Optional[str] = None
    judet: Optional[str] = None
    localitate: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FreeCompany":
        return cls(
            cui=data.get("cui", 0),
            denumire=data.get("denumire", ""),
            adresa=data.get("adresa"),
            telefon=data.get("telefon"),
            cod_caen=data.get("cod_caen"),
            stare=data.get("stare"),
            judet=data.get("judet"),
            localitate=data.get("localitate"),
        )


@dataclass
class FreeApiUsage:
    """Free API usage statistics"""

    requests_today: int
    requests_limit: int
    reset_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FreeApiUsage":
        return cls(
            requests_today=data.get("requests_today", 0),
            requests_limit=data.get("requests_limit", 0),
            reset_at=data.get("reset_at", ""),
        )
