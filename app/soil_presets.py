"""Soil presets providing baseline agronomic parameters for various soil types.
Useful for farmers who do not have laboratory soil test reports.
"""

from typing import Dict, Any

SOIL_PRESETS: Dict[str, Dict[str, Any]] = {
    "Alluvial Soil": {
        "name": "Alluvial Soil",
        "description": "Fertile river basin soil rich in potash and lime. Excellent moisture retention and nutrient capacity.",
        "default_n": 220.0,  # kg/ha
        "default_p": 45.0,   # kg/ha
        "default_k": 280.0,  # kg/ha
        "default_ph": 7.0,
        "drainage": "Moderate to High",
        "organic_matter": "Medium",
        "suitable_categories": ["Cereal", "Pulse", "Oilseed", "Cash Crop", "Vegetable"],
        "color_hint": "Light grey to ash / brownish",
        "texture": "Sandy loam to clay loam"
    },
    "Black Soil (Regur)": {
        "name": "Black Soil (Regur)",
        "description": "Clay-rich volcanic soil with exceptional water holding capacity. Ideal for cotton, soybean, and pulses.",
        "default_n": 180.0,
        "default_p": 35.0,
        "default_k": 320.0,
        "default_ph": 7.8,
        "drainage": "Slow / High water retention",
        "organic_matter": "Medium to High",
        "suitable_categories": ["Fiber", "Oilseed", "Pulse", "Cereal", "Cash Crop"],
        "color_hint": "Deep black to dark brown",
        "texture": "Heavy clay / self-ploughing"
    },
    "Red Soil": {
        "name": "Red Soil",
        "description": "Porous and aerated soil developed over crystalline rocks. Responds well to irrigation and fertilizers.",
        "default_n": 160.0,
        "default_p": 25.0,
        "default_k": 190.0,
        "default_ph": 6.2,
        "drainage": "High / Rapid drainage",
        "organic_matter": "Low",
        "suitable_categories": ["Millets", "Oilseed", "Pulse", "Vegetable", "Fruit"],
        "color_hint": "Reddish to yellow",
        "texture": "Sandy to gravelly loam"
    },
    "Laterite Soil": {
        "name": "Laterite Soil",
        "description": "Formed in intense tropical leaching conditions. Naturally acidic and low in nitrogen and phosphorus.",
        "default_n": 130.0,
        "default_p": 18.0,
        "default_k": 140.0,
        "default_ph": 5.4,
        "drainage": "Very High",
        "organic_matter": "Low",
        "suitable_categories": ["Plantation", "Cash Crop", "Fruit", "Spices"],
        "color_hint": "Rusty red / coarse",
        "texture": "Vesicular coarse / clayey"
    },
    "Sandy Loam Soil": {
        "name": "Sandy Loam Soil",
        "description": "Well-aerated, easy to till, fast-draining soil. Ideal for root crops, groundnuts, and drought-hardy millets.",
        "default_n": 140.0,
        "default_p": 28.0,
        "default_k": 160.0,
        "default_ph": 6.5,
        "drainage": "Rapid / Low water retention",
        "organic_matter": "Low to Medium",
        "suitable_categories": ["Oilseed", "Pulse", "Millets", "Vegetable"],
        "color_hint": "Light brownish / gritty",
        "texture": "Coarse to fine sand with loam"
    },
    "Clay Loam Soil": {
        "name": "Clay Loam Soil",
        "description": "Heavy nutrient-dense soil that retains water well. Great for paddy, wheat, and sugarcane with controlled drainage.",
        "default_n": 240.0,
        "default_p": 48.0,
        "default_k": 260.0,
        "default_ph": 7.3,
        "drainage": "Moderate to Slow",
        "organic_matter": "High",
        "suitable_categories": ["Cereal", "Cash Crop", "Vegetable"],
        "color_hint": "Dark brown to grey",
        "texture": "Smooth and cohesive when wet"
    }
}

SEASON_METADATA = {
    "Kharif": {
        "name": "Kharif (Monsoon / Summer)",
        "sowing_period": "June - July",
        "harvest_period": "September - November",
        "typical_temp_c": 28.0,
        "typical_rainfall_mm": 800.0,
        "typical_humidity_pct": 75.0,
        "description": "Sown at the onset of South-West monsoon. Warm and humid climate."
    },
    "Rabi": {
        "name": "Rabi (Winter / Post-Monsoon)",
        "sowing_period": "October - December",
        "harvest_period": "March - May",
        "typical_temp_c": 20.0,
        "typical_rainfall_mm": 150.0,
        "typical_humidity_pct": 55.0,
        "description": "Sown after monsoon rains subside. Cooler temperatures and dry weather for ripening."
    },
    "Zaid": {
        "name": "Zaid (Summer / Pre-Monsoon)",
        "sowing_period": "March - April",
        "harvest_period": "May - June",
        "typical_temp_c": 32.0,
        "typical_rainfall_mm": 60.0,
        "typical_humidity_pct": 40.0,
        "description": "Short summer window between Rabi and Kharif. Requires assured irrigation."
    },
    "All Season / Flexible": {
        "name": "All Season / Flexible",
        "sowing_period": "Flexible / Year-Round",
        "harvest_period": "Dependent on sowing month",
        "typical_temp_c": 25.0,
        "typical_rainfall_mm": 400.0,
        "typical_humidity_pct": 60.0,
        "description": "Year-round crops or greenhouse/irrigated crops adaptable across seasons."
    }
}

WATER_AVAILABILITY_LEVELS = {
    "Low (Rainfed / Drought-prone)": {
        "key": "Low",
        "score_penalty_high_water": 45.0,
        "description": "Depends solely on irregular rains. Minimal or no supplementary irrigation."
    },
    "Moderate (Canal / Tube-well / Seasonal)": {
        "key": "Moderate",
        "score_penalty_high_water": 10.0,
        "description": "Access to seasonal canal or borewell. Adequate for 2-4 protective irrigations."
    },
    "High (Assured Irrigation / River / Drip)": {
        "key": "High",
        "score_penalty_high_water": 0.0,
        "description": "Consistent, uninterrupted water supply through river, perennial canal, or drip system."
    }
}
