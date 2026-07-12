"""Kenya geographic reference data."""

KENYA_COUNTIES = [
    "Baringo",
    "Bomet",
    "Bungoma",
    "Busia",
    "Elgeyo-Marakwet",
    "Embu",
    "Garissa",
    "Homa Bay",
    "Isiolo",
    "Kajiado",
    "Kakamega",
    "Kericho",
    "Kiambu",
    "Kilifi",
    "Kirinyaga",
    "Kisii",
    "Kisumu",
    "Kitui",
    "Kwale",
    "Laikipia",
    "Lamu",
    "Machakos",
    "Makueni",
    "Mandera",
    "Marsabit",
    "Meru",
    "Migori",
    "Mombasa",
    "Murang'a",
    "Nairobi",
    "Nakuru",
    "Nandi",
    "Narok",
    "Nyamira",
    "Nyandarua",
    "Nyeri",
    "Samburu",
    "Siaya",
    "Taita-Taveta",
    "Tana River",
    "Tharaka-Nithi",
    "Trans Nzoia",
    "Turkana",
    "Uasin Gishu",
    "Vihiga",
    "Wajir",
    "West Pokot",
]

KENYA_COUNTY_CHOICES = [(county, county) for county in KENYA_COUNTIES]

NAIROBI_COUNTY = "Nairobi"
FREE_DELIVERY_AREA = "within Nairobi CBD"

NAIROBI_CBD_CITY_MARKERS = (
    "cbd",
    "nairobi cbd",
    "city centre",
    "city center",
    "central business district",
)


def is_nairobi_county(county):
    """True when the county is Nairobi (tolerates 'Nairobi County' etc.)."""
    if not county:
        return False
    normalized = county.strip().lower().replace(" county", "").strip()
    return normalized == NAIROBI_COUNTY.lower()


def is_nairobi_cbd_delivery(county, city=None):
    """True when delivery qualifies for free Nairobi CBD shipping."""
    if not is_nairobi_county(county):
        return False
    if not city or not str(city).strip():
        return False
    normalized = str(city).strip().lower()
    return any(marker in normalized for marker in NAIROBI_CBD_CITY_MARKERS)


def whatsapp_link(phone):
    """Build a wa.me link for a Kenyan phone number."""
    digits = "".join(char for char in str(phone) if char.isdigit())
    if digits.startswith("0"):
        digits = "254" + digits[1:]
    elif not digits.startswith("254"):
        digits = "254" + digits
    return f"https://wa.me/{digits}"


def phone_tel_link(phone):
    """Build a tel: link for a Kenyan phone number."""
    digits = "".join(char for char in str(phone) if char.isdigit())
    if digits.startswith("0"):
        digits = "254" + digits[1:]
    elif not digits.startswith("254"):
        digits = "254" + digits
    return f"tel:+{digits}"
