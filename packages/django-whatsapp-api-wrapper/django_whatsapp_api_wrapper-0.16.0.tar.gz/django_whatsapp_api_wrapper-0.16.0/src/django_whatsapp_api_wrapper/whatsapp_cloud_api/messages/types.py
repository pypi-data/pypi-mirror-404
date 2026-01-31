import dataclasses
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


def asdict_omit_none(obj):
    """Recursively convert a dataclass to a dict, omitting fields with None values."""
    if dataclasses.is_dataclass(obj):
        result = {}
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            if value is not None:
                result[f.name] = asdict_omit_none(value)
        return result
    if isinstance(obj, list):
        return [asdict_omit_none(v) for v in obj]
    if isinstance(obj, dict):
        return {k: asdict_omit_none(v) for k, v in obj.items() if v is not None}
    return obj


class Serializable:
    @property
    def object(self) -> Dict[str, Any]:  # convenient alias: obj.object -> dict
        return asdict_omit_none(self)

    def to_dict(self) -> Dict[str, Any]:
        return asdict_omit_none(self)


# Simple objects
@dataclass
class Text(Serializable):
    body: str
    preview_url: bool = False


@dataclass
class Reaction(Serializable):
    message_id: str
    emoji: str


@dataclass
class Location(Serializable):
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None


# Media base + specializations
@dataclass
class Media(Serializable):
    id: Optional[str] = None
    link: Optional[str] = None

    def __post_init__(self):
        if self.id is None and self.link is None:
            raise ValueError("Either 'id' or 'link' is required for media.")


@dataclass
class Image(Media):
    caption: Optional[str] = None


@dataclass
class Audio(Media):
    pass


@dataclass
class Document(Media):
    caption: Optional[str] = None
    filename: Optional[str] = None


@dataclass
class Video(Media):
    caption: Optional[str] = None


@dataclass
class Sticker(Media):
    pass


# Template
@dataclass
class Language(Serializable):
    code: str
    policy: str = "deterministic"


@dataclass
class Template(Serializable):
    name: str
    language: Union[Language, Dict]
    components: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        if isinstance(self.language, dict):
            self.language = Language(**self.language)


# Contacts
@dataclass
class Name(Serializable):
    formatted_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None


@dataclass
class Phone(Serializable):
    phone: Optional[str] = None
    type: Optional[str] = None
    wa_id: Optional[str] = None


@dataclass
class Email(Serializable):
    email: Optional[str] = None
    type: Optional[str] = None


@dataclass
class Address(Serializable):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    type: Optional[str] = None


@dataclass
class Org(Serializable):
    company: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None


@dataclass
class Url(Serializable):
    url: Optional[str] = None
    type: Optional[str] = None


@dataclass
class Contact(Serializable):
    name: Union[Name, Dict]
    addresses: Optional[List[Union[Address, Dict]]] = None
    birthday: Optional[str] = None  # YYYY-MM-DD
    emails: Optional[List[Union[Email, Dict]]] = None
    org: Optional[Union[Org, Dict]] = None
    phones: Optional[List[Union[Phone, Dict]]] = None
    urls: Optional[List[Union[Url, Dict]]] = None

    def __post_init__(self):
        if isinstance(self.name, dict):
            self.name = Name(**self.name)
        if self.addresses:
            self.addresses = [Address(**a) if isinstance(a, dict) else a for a in self.addresses]
        if self.emails:
            self.emails = [Email(**e) if isinstance(e, dict) else e for e in self.emails]
        if isinstance(self.org, dict):
            self.org = Org(**self.org)
        if self.phones:
            self.phones = [Phone(**p) if isinstance(p, dict) else p for p in self.phones]
        if self.urls:
            self.urls = [Url(**u) if isinstance(u, dict) else u for u in self.urls]


# Interactive
@dataclass
class InteractiveHeader(Serializable):
    type: str  # text, video, image, document
    text: Optional[str] = None
    video: Optional[Union[Video, Dict]] = None
    image: Optional[Union[Image, Dict]] = None
    document: Optional[Union[Document, Dict]] = None

    def __post_init__(self):
        if isinstance(self.video, dict):
            self.video = Video(**self.video)
        if isinstance(self.image, dict):
            self.image = Image(**self.image)
        if isinstance(self.document, dict):
            self.document = Document(**self.document)


@dataclass
class InteractiveBody(Serializable):
    text: str


@dataclass
class InteractiveFooter(Serializable):
    text: str


@dataclass
class ReplyButtonContent(Serializable):
    """Conteúdo interno do botão de resposta"""
    id: str
    title: str


@dataclass
class ReplyButton(Serializable):
    """Botão de resposta rápida para mensagens interativas"""
    type: str = "reply"
    reply: Union[ReplyButtonContent, Dict] = None

    def __post_init__(self):
        if isinstance(self.reply, dict):
            self.reply = ReplyButtonContent(**self.reply)


@dataclass
class SectionRow(Serializable):
    id: str
    title: str
    description: Optional[str] = None


@dataclass
class Product(Serializable):
    product_retailer_id: str


@dataclass
class Section(Serializable):
    title: Optional[str] = None
    rows: Optional[List[Union[SectionRow, Dict]]] = None
    product_items: Optional[List[Union[Product, Dict]]] = None

    def __post_init__(self):
        if self.rows:
            self.rows = [SectionRow(**r) if isinstance(r, dict) else r for r in self.rows]
        if self.product_items:
            self.product_items = [Product(**p) if isinstance(p, dict) else p for p in self.product_items]


@dataclass
class Action(Serializable):
    button: Optional[str] = None
    buttons: Optional[List[Union[ReplyButton, Dict]]] = None
    catalog_id: Optional[str] = None
    product_retailer_id: Optional[str] = None
    sections: Optional[List[Union[Section, Dict]]] = None

    def __post_init__(self):
        if self.buttons:
            self.buttons = [ReplyButton(**b) if isinstance(b, dict) else b for b in self.buttons]
        if self.sections:
            self.sections = [Section(**s) if isinstance(s, dict) else s for s in self.sections]


@dataclass
class Interactive(Serializable):
    type: str  # list, button, product, product_list
    action: Union[Action, Dict]
    header: Optional[Union[InteractiveHeader, Dict]] = None
    body: Optional[Union[InteractiveBody, Dict]] = None
    footer: Optional[Union[InteractiveFooter, Dict]] = None

    def __post_init__(self):
        if isinstance(self.action, dict):
            self.action = Action(**self.action)
        if isinstance(self.header, dict):
            self.header = InteractiveHeader(**self.header)
        if isinstance(self.body, dict):
            self.body = InteractiveBody(**self.body)
        if isinstance(self.footer, dict):
            self.footer = InteractiveFooter(**self.footer)


# Helper classes for simplified message creation
@dataclass
class ButtonMessage(Serializable):
    """
    Mensagem simplificada com botões de resposta rápida (máximo 3 botões).

    Exemplo:
        ButtonMessage(
            body_text="Você gostou do atendimento?",
            buttons=[
                {"id": "sim", "title": "Sim"},
                {"id": "nao", "title": "Não"}
            ]
        )
    """
    body_text: str
    buttons: List[Dict[str, str]]
    header_text: Optional[str] = None
    footer_text: Optional[str] = None

    def __post_init__(self):
        if len(self.buttons) > 3:
            raise ValueError("Reply buttons support a maximum of 3 buttons")
        if len(self.buttons) < 1:
            raise ValueError("At least 1 button is required")
        for btn in self.buttons:
            if "id" not in btn or "title" not in btn:
                raise ValueError("Each button must have 'id' and 'title' keys")
            if len(btn["title"]) > 20:
                raise ValueError(f"Button title must be max 20 chars: {btn['title']}")

    def to_interactive(self) -> Interactive:
        """Converte para o formato Interactive da API do WhatsApp"""
        reply_buttons = [
            ReplyButton(
                type="reply",
                reply=ReplyButtonContent(id=btn["id"], title=btn["title"])
            )
            for btn in self.buttons
        ]

        header = InteractiveHeader(type="text", text=self.header_text) if self.header_text else None
        footer = InteractiveFooter(text=self.footer_text) if self.footer_text else None

        return Interactive(
            type="button",
            header=header,
            body=InteractiveBody(text=self.body_text),
            footer=footer,
            action=Action(buttons=reply_buttons)
        )


@dataclass
class ListMessage(Serializable):
    """
    Mensagem simplificada com menu de lista (máximo 10 seções, 10 itens por seção).

    Exemplo:
        ListMessage(
            body_text="Escolha um departamento",
            button_text="Ver opções",
            sections=[
                {
                    "title": "Atendimento",
                    "rows": [
                        {"id": "vendas", "title": "Vendas", "description": "Fale com vendas"},
                        {"id": "suporte", "title": "Suporte"}
                    ]
                }
            ]
        )
    """
    body_text: str
    button_text: str
    sections: List[Dict]
    header_text: Optional[str] = None
    footer_text: Optional[str] = None

    def __post_init__(self):
        if len(self.button_text) > 20:
            raise ValueError("Button text must be max 20 characters")
        if len(self.sections) > 10:
            raise ValueError("List messages support a maximum of 10 sections")
        if len(self.sections) < 1:
            raise ValueError("At least 1 section is required")

        total_rows = 0
        for section in self.sections:
            if "rows" not in section:
                raise ValueError("Each section must have 'rows'")
            rows = section["rows"]
            if len(rows) > 10:
                raise ValueError("Each section can have a maximum of 10 rows")
            total_rows += len(rows)
            for row in rows:
                if "id" not in row or "title" not in row:
                    raise ValueError("Each row must have 'id' and 'title' keys")
                if len(row["title"]) > 24:
                    raise ValueError(f"Row title must be max 24 chars: {row['title']}")

        if total_rows > 10:
            raise ValueError("List messages support a maximum of 10 total rows")

    def to_interactive(self) -> Interactive:
        """Converte para o formato Interactive da API do WhatsApp"""
        section_objects = []
        for sec in self.sections:
            rows = [
                SectionRow(
                    id=row["id"],
                    title=row["title"],
                    description=row.get("description")
                )
                for row in sec["rows"]
            ]
            section_objects.append(Section(title=sec.get("title"), rows=rows))

        header = InteractiveHeader(type="text", text=self.header_text) if self.header_text else None
        footer = InteractiveFooter(text=self.footer_text) if self.footer_text else None

        return Interactive(
            type="list",
            header=header,
            body=InteractiveBody(text=self.body_text),
            footer=footer,
            action=Action(button=self.button_text, sections=section_objects)
        )
