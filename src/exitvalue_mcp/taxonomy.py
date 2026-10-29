"""Industry taxonomy, display names and plain-English aliases (ported from ExitValue.ai).

Names and mappings only - no deal data lives here.
"""

DISPLAY_OVERRIDES = {
    "hvac": "HVAC",
    "3pl": "3PL / Third-Party Logistics",
    "saas": "SaaS / Software-as-a-Service",
    "it-services": "IT Services",
    "accounting-cpa": "Accounting / CPA Firm",
    "restaurant-qsr": "Restaurant — Quick Service (QSR)",
    "restaurant-casual": "Restaurant — Casual Dining",
    "restaurant-fine-dining": "Restaurant — Fine Dining",
    "restaurant-franchise": "Restaurant — Franchise",
    "medical-practice-primary-care": "Medical Practice — Primary Care",
    "medical-practice-specialty": "Medical Practice — Specialty",
    "durable-medical-equipment": "Durable Medical Equipment (DME)",
    "healthcare-it": "Healthcare IT",
    "healthcare-staffing": "Healthcare Staffing",
    "managed-services-msp": "Managed Services (MSP)",
    "data-analytics": "Data & Analytics",
    "law-firm": "Law Firm",
    "funeral-home": "Funeral Home",
    "bank-community": "Community Bank",
    "general-contractor-commercial": "General Contractor — Commercial",
    "general-contractor-residential": "General Contractor — Residential",
    "oil-gas-services": "Oil & Gas Services",
    "ag-services": "Agricultural Services",
    "other-healthcare": "Healthcare — Other",
    "other-manufacturing": "Manufacturing — Other",
    "other-technology": "Technology — Other",
    "other-construction": "Construction — Other",
    "other-distribution": "Distribution — Other",
    "other-energy": "Energy — Other",
    "other-retail": "Retail — Other",
    "other-media": "Media — Other",
    "other-food-beverage": "Food & Beverage — Other",
    "other-personal-services": "Personal Services — Other",
    "other-professional-services": "Professional Services — Other",
    "other-financial-services": "Financial Services — Other",
    "other-automotive": "Automotive — Other",
    "other-home-services": "Home Services — Other",
    "other-agriculture": "Agriculture — Other",
    "other-education": "Education — Other",
    "other": "Other",
    "spa-medspa": "Spa / Med Spa",
    "bar-nightclub": "Bar / Nightclub",
    "radio-television": "Radio / Television",
    "software-enterprise": "Enterprise Software",
    "software-consumer": "Consumer Software",
    "cleaning-commercial": "Commercial Cleaning",
}

INDUSTRY_DISPLAY_NAMES = {
    "healthcare": "Healthcare",
    "manufacturing": "Manufacturing",
    "technology": "Technology",
    "energy-utilities": "Energy & Utilities",
    "professional-services": "Professional Services",
    "distribution-logistics": "Distribution & Logistics",
    "food-beverage": "Food & Beverage",
    "retail": "Retail",
    "construction": "Construction",
    "media-entertainment": "Media & Entertainment",
    "personal-services": "Personal Services",
    "automotive": "Automotive",
    "home-services": "Home Services",
    "financial-services": "Financial Services",
    "education": "Education",
    "agriculture": "Agriculture",
}

INDUSTRY_TAXONOMY = {
    "healthcare": [
        "dental-practice", "medical-practice-primary-care", "medical-practice-specialty",
        "veterinary-practice", "optometry-practice", "physical-therapy", "mental-health",
        "home-health", "hospice", "urgent-care", "pharmacy", "imaging-center",
        "ambulatory-surgery-center", "laboratory-services", "medical-devices",
        "durable-medical-equipment", "healthcare-it", "healthcare-staffing", "other-healthcare",
    ],
    "home-services": [
        "hvac", "electrical", "pest-control", "landscaping", "roofing",
        "cleaning-commercial", "other-home-services",
    ],
    "professional-services": [
        "accounting-cpa", "law-firm", "consulting", "insurance-agency", "staffing-agency",
        "it-services", "marketing-agency", "advertising-agency",
        "real-estate-brokerage", "other-professional-services",
    ],
    "technology": [
        "saas", "software-enterprise", "software-consumer",
        "cybersecurity", "data-analytics", "managed-services-msp",
        "fintech", "healthtech", "other-technology",
    ],
    "food-beverage": [
        "restaurant-qsr", "restaurant-casual", "restaurant-fine-dining",
        "restaurant-franchise", "food-manufacturing", "beverage-manufacturing",
        "food-distribution", "other-food-beverage",
    ],
    "retail": [
        "specialty-retail", "convenience-store", "ecommerce", "pet-store",
        "apparel", "other-retail",
    ],
    "manufacturing": [
        "metal-fabrication", "packaging", "aerospace", "electronics",
        "industrial-equipment", "consumer-products", "plastics", "other-manufacturing",
    ],
    "automotive": [
        "auto-repair", "collision-repair", "car-wash",
        "auto-dealership", "auto-parts", "other-automotive",
    ],
    "construction": [
        "specialty-contractor", "general-contractor-commercial", "general-contractor-residential",
        "infrastructure", "other-construction",
    ],
    "distribution-logistics": [
        "wholesale-distribution", "trucking", "freight-brokerage",
        "warehousing", "3pl", "courier-delivery", "other-distribution",
    ],
    "media-entertainment": [
        "advertising-agency", "digital-media", "radio-television",
        "publishing", "gaming", "other-media",
    ],
    "personal-services": [
        "fitness-gym", "childcare-daycare", "funeral-home", "other-personal-services",
    ],
    "financial-services": [
        "bank-community", "other-financial-services",
    ],
    "energy-utilities": [
        "solar", "oil-gas-services", "electrical-utility",
        "water-wastewater", "other-energy",
    ],
    "education": [
        "vocational-training", "other-education",
    ],
    "agriculture": [
        "ag-services", "farming", "other-agriculture",
    ],
}

# Verticals whose deals are tagged under another category; always labelled as the parent's.
PARENT_CATEGORY = {
    "managed-services-msp": ("it-services", "IT services (MSP deals are tagged under it)"),
    "marketing-agency": ("advertising-agency", "advertising and marketing agencies"),
    "restaurant-casual": ("restaurant-qsr", "restaurants overall (includes casual-dining deals)"),
    "restaurant-franchise": ("restaurant-qsr", "restaurants overall (includes franchisee deals)"),
}

# Queries with no sub-vertical of their own, mapped to the closest category (with a note).
ALIAS_NOTES = {
    "plumbing": ("hvac", "Plumbing deals are classified with HVAC in our data; figures below are for HVAC (incl. plumbing)."),
    "plumber": ("hvac", "Plumbing deals are classified with HVAC in our data; figures below are for HVAC (incl. plumbing)."),
    "med-spa": ("other-healthcare", "Med spas are not tracked as a separate category; figures below are for other healthcare services, the closest category in our data."),
    "medspa": ("other-healthcare", "Med spas are not tracked as a separate category; figures below are for other healthcare services, the closest category in our data."),
    "medical-spa": ("other-healthcare", "Med spas are not tracked as a separate category; figures below are for other healthcare services, the closest category in our data."),
    "aesthetics": ("other-healthcare", "Aesthetics practices are not tracked as a separate category; figures below are for other healthcare services, the closest category in our data."),
    "chiropractic": ("other-healthcare", "Chiropractic practices are not tracked as a separate category; figures below are for other healthcare services, the closest category in our data."),
    "chiropractor": ("other-healthcare", "Chiropractic practices are not tracked as a separate category; figures below are for other healthcare services, the closest category in our data."),
    "dermatology": ('medical-practice-specialty', 'Dermatology is grouped with specialty medical practices; figures below are for specialty medical practices.'),
    "orthodontist": ('dental-practice', 'Orthodontic practices are grouped with dental practices; figures below are for dental practices.'),
    "orthodontics": ('dental-practice', 'Orthodontic practices are grouped with dental practices; figures below are for dental practices.'),
    "salon": ("other-personal-services", "Salons are not tracked as a separate category; figures below are for personal services, the closest category in our data."),
    "hair-salon": ("other-personal-services", "Salons are not tracked as a separate category; figures below are for personal services, the closest category in our data."),
    "spa": ("other-personal-services", "Day spas are not tracked as a separate category; figures below are for personal services, the closest category in our data."),
    "pool-service": ("other-home-services", "Pool service businesses are not tracked as a separate category; figures below are for home services, the closest category in our data."),
    "painting": ('specialty-contractor', 'Painting contractors are grouped with specialty contractors; figures below are for specialty contractors.'),
    "flooring": ('specialty-contractor', 'Flooring contractors are grouped with specialty contractors; figures below are for specialty contractors.'),
    "concrete": ('specialty-contractor', 'Concrete contractors are grouped with specialty contractors; figures below are for specialty contractors.'),
    "fire-protection": ('specialty-contractor', 'Fire protection contractors are grouped with specialty contractors; figures below are for specialty contractors.'),
    "security-guard": ("other-professional-services", "Security guard companies are not tracked as a separate category; figures below are for other professional services, the closest category in our data."),
    "tree-service": ('landscaping', 'Tree service companies are grouped with landscaping; figures below are for landscaping.'),
    "moving": ('courier-delivery', 'Moving companies are grouped with courier and delivery; figures below are for courier and delivery.'),
    "senior-living": ('home-health', 'Senior care is grouped with home health; figures below are for home health.'),
    "senior-care": ('home-health', 'Senior care is grouped with home health; figures below are for home health.'),
    "aba": ('mental-health', 'ABA therapy is grouped with mental and behavioral health; figures below are for mental health practices.'),
    "aba-therapy": ('mental-health', 'ABA therapy is grouped with mental and behavioral health; figures below are for mental health practices.'),
}

# Plain-English aliases -> sub-vertical id.
ALIASES = {
    "dentist": "dental-practice", "dental": "dental-practice", "dso": "dental-practice",
    "vet": "veterinary-practice", "veterinary": "veterinary-practice", "veterinary-clinic": "veterinary-practice",
    "optometrist": "optometry-practice", "optometry": "optometry-practice",
    "pt": "physical-therapy", "behavioral-health": "mental-health",
    "asc": "ambulatory-surgery-center", "surgery-center": "ambulatory-surgery-center",
    "dme": "durable-medical-equipment", "lab": "laboratory-services",
    "medical-practice": "medical-practice-specialty",
    "air-conditioning": "hvac", "heating": "hvac",
    "electrician": "electrical", "electrical-contractor": "electrical",
    "commercial-cleaning": "cleaning-commercial", "janitorial": "cleaning-commercial",
    "lawn-care": "landscaping", "roofer": "roofing",
    "cpa": "accounting-cpa", "accounting": "accounting-cpa", "accounting-practice": "accounting-cpa",
    "accounting-firm": "accounting-cpa", "bookkeeping": "accounting-cpa",
    "law": "law-firm", "lawyer": "law-firm", "insurance": "insurance-agency",
    "staffing": "staffing-agency", "msp": "managed-services-msp", "managed-services": "managed-services-msp",
    "marketing": "marketing-agency", "advertising": "advertising-agency",
    "real-estate": "real-estate-brokerage", "software": "saas", "saas-software": "saas",
    "restaurant": "restaurant-qsr", "qsr": "restaurant-qsr", "fast-food": "restaurant-qsr",
    "franchise-restaurant": "restaurant-franchise",
    "e-commerce": "ecommerce", "online-store": "ecommerce",
    "machine-shop": "metal-fabrication", "fabrication": "metal-fabrication",
    "auto-repair-shop": "auto-repair", "mechanic": "auto-repair", "body-shop": "collision-repair",
    "dealership": "auto-dealership", "car-dealership": "auto-dealership",
    "contractor": "specialty-contractor", "construction-company": "specialty-contractor",
    "trucking-company": "trucking", "freight": "freight-brokerage", "logistics": "3pl",
    "distribution": "wholesale-distribution", "distributor": "wholesale-distribution",
    "gym": "fitness-gym", "fitness": "fitness-gym", "daycare": "childcare-daycare",
    "childcare": "childcare-daycare", "childcare-center": "childcare-daycare",
    "funeral": "funeral-home", "bank": "bank-community", "solar-installer": "solar",
    "oil-gas": "oil-gas-services", "water": "water-wastewater", "farm": "farming",
    "trade-school": "vocational-training",
}


def display_name(slug: str) -> str:
    """Sub-vertical slug -> display name."""
    if slug in DISPLAY_OVERRIDES:
        return DISPLAY_OVERRIDES[slug]
    return slug.replace("-", " ").title()
