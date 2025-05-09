import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import json

# Set page config
st.set_page_config(
    page_title="Oahu Sustainability Calculator",
    page_icon="🌴",
    layout="wide"
)

#############################
# UTILITY FUNCTIONS
#############################

def get_score_color(score):
    """Return a color corresponding to a sustainability score"""
    if score >= 80:
        return "#4CAF50"  # Green
    elif score >= 60:
        return "#8BC34A"  # Light Green
    elif score >= 40:
        return "#FFC107"  # Amber
    elif score >= 20:
        return "#FF9800"  # Orange
    else:
        return "#F44336"  # Red

def normalize_value(value, min_val, max_val, reverse=False):
    """Normalize a value to a 0-100 scale"""
    if max_val == min_val:
        return 50  # Default to middle if range is zero
        
    normalized = ((value - min_val) / (max_val - min_val)) * 100
    
    if reverse:
        normalized = 100 - normalized
        
    return max(0, min(100, normalized))

def format_percentage(value):
    """Format a decimal value as a percentage string"""
    return f"{int(value * 100)}%"

def format_carbon(tons):
    """Format carbon footprint value"""
    if tons < 1:
        kg = tons * 1000
        return f"{kg:.0f} kg CO₂e"
    else:
        return f"{tons:.1f} tons CO₂e"

def format_water(gallons):
    """Format water usage value"""
    return f"{gallons:,} gallons"

def get_recommendation_icon(category):
    """Return an icon for a recommendation category"""
    icons = {
        "transportation": "🚗",
        "energy": "⚡",
        "water": "💧",
        "waste": "🗑️",
        "food": "🍲",
        "general": "🌱"
    }
    
    return icons.get(category.lower(), "🌴")

#############################
# OAHU SPECIFIC DATA
#############################

def get_oahu_environmental_factors():
    """
    Return a dictionary of Oahu-specific environmental factors
    that influence sustainability calculations.
    """
    factors = {
        'transport': {
            'traffic_congestion_factor': 0.8,  # Higher means worse traffic
            'public_transport_quality': 0.6,   # Higher means better public transport
            'ev_grid_impact': 0.7,            # Impact of EVs on local grid (lower is better)
            'avg_commute_distance': 11.1      # Average one-way commute in miles
        },
        'energy': {
            'electricity_cost': 0.34,         # $ per kWh (highest in the US)
            'renewable_percentage': 0.35,     # Percentage of grid from renewables
            'fossil_fuel_dependency': 0.65,   # Dependency on imported fossil fuels
            'solar_potential': 0.9            # Solar energy potential (higher is better)
        },
        'water': {
            'freshwater_scarcity': 0.7,       # Higher means more scarce
            'rainfall_variation': 0.7,        # Geographic rainfall variation (higher means more variation)
            'groundwater_stress': 0.6,        # Stress on groundwater sources
            'avg_consumption': 115            # Average per capita daily consumption (gallons)
        },
        'waste': {
            'limited_landfill_space': 0.8,    # Limited landfill capacity
            'recycling_infrastructure': 0.5,  # Quality of recycling infrastructure
            'marine_debris_impact': 0.9,      # Impact of waste on marine environment
            'waste_to_energy': 0.7           # Availability of waste-to-energy processing
        },
        'food': {
            'import_dependency': 0.85,        # Percentage of food imported
            'local_agriculture_capacity': 0.3, # Capacity for local agriculture
            'fishing_sustainability': 0.6,    # Sustainability of local fishing
            'food_price_factor': 1.4          # Higher cost relative to mainland
        },
        'carbon': {
            'island_multiplier': 1.2,         # Island context multiplier for carbon emissions
            'tourism_impact': 0.3,            # Impact of tourism on carbon emissions
            'baseline_emissions': 16.9        # Average carbon footprint (tons/person/year)
        }
    }
    
    return factors

def get_oahu_educational_resources():
    """
    Return a dictionary of Oahu-specific educational resources
    related to sustainability.
    """
    resources = {
        "Water Conservation": [
            {
                "name": "Board of Water Supply Conservation Program",
                "description": "Offers workshops, rebates for water-efficient fixtures, and educational materials about water conservation on Oahu.",
                "url": "https://www.boardofwatersupply.com/conservation"
            },
            {
                "name": "Wai Maoli: Hawaii Fresh Water Initiative",
                "description": "A Hawaii Community Foundation program working to protect Hawaii's fresh water supplies through conservation, recharge, and reuse strategies.",
                "url": "https://www.hawaiicommunityfoundation.org/fresh-water"
            }
        ],
        "Energy Efficiency": [
            {
                "name": "Hawaii Energy",
                "description": "Provides rebates, incentives and educational programs to help residents and businesses save energy and reduce bills.",
                "url": "https://hawaiienergy.com/"
            },
            {
                "name": "Blue Planet Foundation",
                "description": "Local non-profit working on clean energy initiatives through education and advocacy, particularly focused on helping Hawaii achieve 100% renewable energy.",
                "url": "https://blueplanetfoundation.org/"
            },
            {
                "name": "Hawaii State Energy Office",
                "description": "Government resources for energy efficiency, renewable energy, and transportation transformation in Hawaii.",
                "url": "https://energy.hawaii.gov/"
            }
        ],
        "Waste Reduction": [
            {
                "name": "Kokua Hawaii Foundation",
                "description": "Provides environmental education and programs in Hawaii schools, including the 3R's (reduce, reuse, recycle) and plastic-free initiatives.",
                "url": "https://kokuahawaiifoundation.org/"
            },
            {
                "name": "Zero Waste Oahu",
                "description": "Community coalition working toward zero waste on Oahu through education, advocacy, and policy change.",
                "url": "https://www.zerowasteoahu.org/"
            },
            {
                "name": "Sustainable Coastlines Hawaii",
                "description": "Organizes beach cleanups and educational programs about plastic pollution and its impact on Hawaii's marine ecosystems.",
                "url": "https://www.sustainablecoastlineshawaii.org/"
            }
        ],
        "Local Food & Agriculture": [
            {
                "name": "Hawaii Farmers Union United",
                "description": "Advocates for family agriculture and sustainable farming practices in Hawaii.",
                "url": "https://hfuuhi.org/"
            },
            {
                "name": "GoFarm Hawaii",
                "description": "Trains beginning farmers in sustainable agriculture practices specific to Hawaii's environment.",
                "url": "https://gofarmhawaii.org/"
            },
            {
                "name": "Oahu Fresh",
                "description": "Local food hub connecting Oahu residents with locally grown produce through CSA boxes and farmers markets.",
                "url": "https://oahufresh.com/"
            }
        ],
        "Transportation": [
            {
                "name": "Hawaii Bicycling League",
                "description": "Promotes cycling for transportation and recreation on Oahu through education, advocacy and events.",
                "url": "https://www.hbl.org/"
            },
            {
                "name": "TheBus - Oahu Transit Services",
                "description": "Information about Honolulu's public bus system routes, schedules, and sustainable transportation options.",
                "url": "http://www.thebus.org/"
            }
        ],
        "General Sustainability": [
            {
                "name": "Sustainable Hawaii",
                "description": "Promotes sustainable practices across all sectors of Hawaii's economy and society.",
                "url": "https://www.sustainablehawaii.org/"
            },
            {
                "name": "University of Hawaii Office of Sustainability",
                "description": "Researches and implements sustainability initiatives and offers educational resources for the wider community.",
                "url": "https://www.hawaii.edu/sustainability/"
            },
            {
                "name": "Hawaii Green Growth",
                "description": "Public-private partnership advancing economic, social, and environmental goals through the UN's Sustainable Development Goals framework.",
                "url": "https://www.hawaiigreengrowth.org/"
            }
        ]
    }
    
    return resources

#############################
# SUSTAINABILITY CALCULATOR
#############################

def calculate_impact(user_data):
    """
    Calculate environmental impact based on user inputs and Oahu-specific factors.
    Returns dictionary with impact scores and detailed metrics.
    """
    # Get Oahu-specific environmental factors
    oahu_factors = get_oahu_environmental_factors()
    
    # Calculate transport impact
    transport_score = calculate_transport_impact(user_data, oahu_factors)
    
    # Calculate energy impact
    energy_score = calculate_energy_impact(user_data, oahu_factors)
    
    # Calculate water impact
    water_score = calculate_water_impact(user_data, oahu_factors)
    
    # Calculate waste impact
    waste_score = calculate_waste_impact(user_data, oahu_factors)
    
    # Calculate food impact
    food_score = calculate_food_impact(user_data, oahu_factors)
    
    # Calculate carbon footprint (in tons of CO2 per year)
    carbon_footprint = calculate_carbon_footprint(user_data, oahu_factors)
    
    # Calculate water usage (in gallons per day)
    water_usage = calculate_water_usage(user_data, oahu_factors)
    
    # Calculate waste generation (in pounds per week)
    waste_generation = calculate_waste_generation(user_data, oahu_factors)
    
    # Calculate overall score (weighted average)
    weights = {
        'transport': 0.25,
        'energy': 0.25,
        'water': 0.2,
        'waste': 0.15,
        'food': 0.15
    }
    
    overall_score = (
        transport_score * weights['transport'] +
        energy_score * weights['energy'] +
        water_score * weights['water'] +
        waste_score * weights['waste'] +
        food_score * weights['food']
    )
    
    # Round to nearest integer
    overall_score = round(overall_score)
    
    # Compile results
    results = {
        'overall_score': overall_score,
        'transport_score': transport_score,
        'energy_score': energy_score,
        'water_score': water_score,
        'waste_score': waste_score,
        'food_score': food_score,
        'carbon_footprint': carbon_footprint,
        'water_usage': water_usage,
        'waste_generation': waste_generation,
        'impact_breakdown': {
            'transport': weights['transport'] * transport_score / overall_score,
            'energy': weights['energy'] * energy_score / overall_score,
            'water': weights['water'] * water_score / overall_score,
            'waste': weights['waste'] * waste_score / overall_score,
            'food': weights['food'] * food_score / overall_score
        }
    }
    
    return results

def calculate_transport_impact(user_data, oahu_factors):
    """Calculate transport-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 100
    
    # Calculate car impact
    car_usage = user_data['car_usage']
    car_type = user_data['car_type']
    
    # Car type multipliers (lower is better - less emissions)
    car_multipliers = {
        "Electric vehicle": 0.3,
        "Hybrid vehicle": 0.6,
        "Small gas car (30+ mpg)": 1.0,
        "Medium gas car (20-30 mpg)": 1.5,
        "Large gas car/SUV/truck (under 20 mpg)": 2.0
    }
    
    # Car usage impact (more miles = more impact)
    car_impact = car_usage * car_multipliers[car_type] * 0.1
    base_score -= car_impact
    
    # Public transport (positive impact)
    public_transport_usage = user_data['public_transport_usage']
    public_transport_benefit = min(25, public_transport_usage * 1.5)
    base_score += public_transport_benefit
    
    # Flight impact (negative)
    flight_hours = user_data['flight_hours']
    flight_impact = flight_hours * 0.5
    base_score -= flight_impact
    
    # Oahu-specific factors
    if car_usage > 0 and car_type not in ["Electric vehicle", "Hybrid vehicle"]:
        # Island traffic congestion penalty
        base_score -= oahu_factors['transport']['traffic_congestion_factor'] * 5
    
    # Cap the score between 0 and 100
    return max(0, min(100, round(base_score)))

def calculate_energy_impact(user_data, oahu_factors):
    """Calculate energy-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 80  # Start with a baseline
    
    # Electricity usage impact
    electricity_bill = user_data['electricity_bill']
    household_size = user_data['household_size']
    
    # Per-person electricity usage
    per_person_electricity = electricity_bill / household_size
    
    # Adjust score based on per-person electricity usage
    # Hawaii has very expensive electricity, so we need to adjust expectations
    if per_person_electricity < 50:
        base_score += 15
    elif per_person_electricity < 75:
        base_score += 10
    elif per_person_electricity < 100:
        base_score += 5
    elif per_person_electricity > 150:
        base_score -= 10
    elif per_person_electricity > 125:
        base_score -= 5
    
    # Renewable energy bonus
    if user_data['renewable_energy'] == "Yes - solar panels":
        base_score += 20
    elif user_data['renewable_energy'] == "Yes - other":
        base_score += 15
    
    # Air conditioning impact (major in Hawaii)
    ac_hours = user_data['air_conditioning']
    ac_impact = ac_hours * 1.2  # Higher impact due to Oahu's energy costs
    base_score -= ac_impact
    
    # Oahu-specific factor: high energy costs and fossil fuel dependency
    base_score -= oahu_factors['energy']['fossil_fuel_dependency'] * 5
    
    # Cap the score between 0 and 100
    return max(0, min(100, round(base_score)))

def calculate_water_impact(user_data, oahu_factors):
    """Calculate water-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 75
    
    # Shower impact
    shower_length = user_data['shower_length']
    shower_frequency = user_data['shower_frequency']
    
    shower_impact = shower_length * shower_frequency * 0.2
    base_score -= shower_impact
    
    # Water conservation measures (positive impact)
    conservation_measures = user_data['water_conservation']
    if "None of the above" not in conservation_measures:
        base_score += len(conservation_measures) * 6
    
    # Oahu-specific factor: freshwater scarcity
    base_score -= oahu_factors['water']['freshwater_scarcity'] * 5
    
    # Cap the score between 0 and 100
    return max(0, min(100, round(base_score)))

def calculate_waste_impact(user_data, oahu_factors):
    """Calculate waste-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 60
    
    # Recycling habits
    recycling_score_map = {
        "Never": 0,
        "Rarely": 5,
        "Sometimes": 10,
        "Often": 15,
        "Always": 20
    }
    base_score += recycling_score_map[user_data['recycling_habit']]
    
    # Composting (positive impact)
    if user_data['composting']:
        base_score += 15
    
    # Single-use plastics (negative impact)
    plastic_score_map = {
        "Never": 20,
        "Rarely": 15,
        "Sometimes": 5,
        "Often": -5,
        "Always": -15
    }
    base_score += plastic_score_map[user_data['single_use_plastics']]
    
    # Local food percentage (less shipping/packaging)
    local_food_pct = user_data['local_food']
    base_score += local_food_pct * 0.1
    
    # Oahu-specific factor: limited landfill space
    base_score -= oahu_factors['waste']['limited_landfill_space'] * 5
    
    # Cap the score between 0 and 100
    return max(0, min(100, round(base_score)))

def calculate_food_impact(user_data, oahu_factors):
    """Calculate food-related environmental impact score (0-100)"""
    # Higher score = more sustainable
    base_score = 50
    
    # Diet type impact
    diet_score_map = {
        "Vegan": 40,
        "Vegetarian": 30,
        "Pescatarian": 20,
        "Flexitarian (mostly plant-based with occasional meat)": 15,
        "Omnivore (regular meat consumption)": 0
    }
    base_score += diet_score_map[user_data['diet_type']]
    
    # Local food percentage (positive impact)
    local_food_pct = user_data['local_food']
    base_score += local_food_pct * 0.15
    
    # Restaurant meals (typically higher impact than home cooking)
    meals_out = user_data['meals_out']
    base_score -= meals_out * 0.5
    
    # Oahu-specific factor: food import dependency
    base_score -= oahu_factors['food']['import_dependency'] * 5
    
    # Cap the score between 0 and 100
    return max(0, min(100, round(base_score)))

def calculate_carbon_footprint(user_data, oahu_factors):
    """Calculate approximate carbon footprint in tons of CO2 per year"""
    carbon_footprint = 0
    
    # Transport carbon
    miles_per_year = user_data['car_usage'] * 52  # Weekly to yearly
    
    # CO2 emissions per mile by car type (in kg)
    car_emissions = {
        "Electric vehicle": 0.1,  # Hawaii's grid is partially renewable
        "Hybrid vehicle": 0.2,
        "Small gas car (30+ mpg)": 0.3,
        "Medium gas car (20-30 mpg)": 0.4,
        "Large gas car/SUV/truck (under 20 mpg)": 0.6
    }
    
    # Add car emissions
    carbon_footprint += miles_per_year * car_emissions[user_data['car_type']] / 1000  # Convert kg to tons
    
    # Flight emissions (average 0.2 tons per hour)
    carbon_footprint += user_data['flight_hours'] * 0.2
    
    # Energy emissions
    # Hawaii's electricity is expensive and primarily from oil
    carbon_footprint += (user_data['electricity_bill'] / 100) * 0.8
    
    # Adjust for renewable energy
    if user_data['renewable_energy'] == "Yes - solar panels":
        carbon_footprint -= 2.0  # Approximate savings
    elif user_data['renewable_energy'] == "Yes - other":
        carbon_footprint -= 1.0
    
    # Food emissions
    diet_emissions = {
        "Vegan": 1.5,
        "Vegetarian": 2.0,
        "Pescatarian": 2.5,
        "Flexitarian (mostly plant-based with occasional meat)": 3.0,
        "Omnivore (regular meat consumption)": 4.0
    }
    carbon_footprint += diet_emissions[user_data['diet_type']]
    
    # Local food adjustment (reduced shipping emissions)
    carbon_footprint -= (user_data['local_food'] / 100) * 0.5
    
    # Waste emissions
    if user_data['recycling_habit'] == "Always":
        carbon_footprint -= 0.5
    elif user_data['recycling_habit'] == "Often":
        carbon_footprint -= 0.3
    
    if user_data['composting']:
        carbon_footprint -= 0.3
    
    # Oahu-specific factors
    carbon_footprint *= oahu_factors['carbon']['island_multiplier']
    
    # Add base emissions for basic living
    carbon_footprint += 5.0
    
    return round(carbon_footprint, 1)

def calculate_water_usage(user_data, oahu_factors):
    """Calculate approximate water usage in gallons per day"""
    water_usage = 0
    
    # Shower water usage (2.5 gallons per minute for standard shower)
    shower_gallons = user_data['shower_length'] * 2.5
    shower_daily = (shower_gallons * user_data['shower_frequency']) / 7  # Convert to daily
    water_usage += shower_daily
    
    # Other basic water usage (cooking, cleaning, toilet, etc.) - per person
    base_water = 30  # gallons per day per person
    water_usage += base_water * user_data['household_size']
    
    # Adjustments for conservation measures
    conservation_measures = user_data['water_conservation']
    
    if "Low-flow showerheads/faucets" in conservation_measures:
        water_usage *= 0.8  # 20% reduction
    
    if "Dual-flush toilets" in conservation_measures:
        water_usage *= 0.9  # 10% reduction
    
    if "Drought-resistant landscaping" in conservation_measures:
        water_usage -= 10  # Approximate savings
    
    return round(water_usage)

def calculate_waste_generation(user_data, oahu_factors):
    """Calculate approximate waste generation in pounds per week"""
    # Base waste generation (national average is about 4.5 lbs per person per day)
    base_waste = 4.5 * 7 * user_data['household_size']  # Convert to weekly
    
    # Adjustments based on user behavior
    if user_data['recycling_habit'] == "Always":
        base_waste *= 0.6  # 40% reduction
    elif user_data['recycling_habit'] == "Often":
        base_waste *= 0.7
    elif user_data['recycling_habit'] == "Sometimes":
        base_waste *= 0.85
    
    if user_data['composting']:
        base_waste *= 0.7  # 30% reduction from composting food waste
    
    # Single-use plastics impact
    if user_data['single_use_plastics'] == "Always":
        base_waste *= 1.2  # 20% increase
    elif user_data['single_use_plastics'] == "Never":
        base_waste *= 0.8  # 20% reduction
    
    return round(base_waste)

#############################
# VISUALIZATION FUNCTIONS
#############################

def create_impact_visualization(impact_results):
    """
    Create visualization of user's environmental impact
    
    Args:
        impact_results: Dictionary of calculated impact scores and metrics
        
    Returns:
        Plotly figure object
    """
    # Extract category scores
    categories = ['Transportation', 'Energy', 'Water', 'Waste', 'Food']
    scores = [
        impact_results['transport_score'],
        impact_results['energy_score'],
        impact_results['water_score'],
        impact_results['waste_score'],
        impact_results['food_score']
    ]
    
    # Create radar chart
    fig = go.Figure()
    
    # Add radar chart
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Your Impact',
        line_color='rgba(31, 119, 180, 0.8)',
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    # Add reference line for "good" score (60)
    fig.add_trace(go.Scatterpolar(
        r=[60, 60, 60, 60, 60],
        theta=categories,
        fill=None,
        name='Good Score (60)',
        line=dict(color='green', dash='dash')
    ))
    
    # Customize layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="Environmental Impact by Category",
        height=500
    )
    
    return fig

def create_carbon_breakdown_chart(impact_results, user_data):
    """
    Create a pie chart showing breakdown of carbon footprint
    
    Args:
        impact_results: Dictionary of calculated impact scores and metrics
        user_data: Dictionary of user inputs
        
    Returns:
        Plotly figure object
    """
    # Estimate carbon breakdown (these values should sum to 100%)
    transport_pct = 0.30
    energy_pct = 0.25
    food_pct = 0.25
    waste_pct = 0.15
    other_pct = 0.05
    
    # Adjust based on user's specific profile
    if user_data['car_type'] in ["Electric vehicle", "Hybrid vehicle"]:
        transport_pct -= 0.1
        energy_pct += 0.05
        other_pct += 0.05
    
    if user_data['flight_hours'] > 10:
        transport_pct += 0.1
        other_pct -= 0.05
        waste_pct -= 0.05
    
    if user_data['diet_type'] in ["Vegan", "Vegetarian"]:
        food_pct -= 0.1
        transport_pct += 0.05
        energy_pct += 0.05
    
    # Create pie chart
    labels = ['Transportation', 'Energy Use', 'Food', 'Waste', 'Other']
    values = [
        transport_pct * impact_results['carbon_footprint'],
        energy_pct * impact_results['carbon_footprint'],
        food_pct * impact_results['carbon_footprint'],
        waste_pct * impact_results['carbon_footprint'],
        other_pct * impact_results['carbon_footprint']
    ]
    
    fig = px.pie(
        values=values, 
        names=labels, 
        title=f"Carbon Footprint Breakdown: {impact_results['carbon_footprint']} tons CO2/year",
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig

def create_comparison_bar_chart(impact_results):
    """
    Create bar chart comparing user to Oahu averages
    
    Args:
        impact_results: Dictionary of calculated impact scores and metrics
        
    Returns:
        Plotly figure object
    """
    # Oahu averages (approximate values)
    oahu_avg_carbon = 16.9  # tons CO2/year
    oahu_avg_water = 115  # gallons/day
    oahu_avg_waste = 31  # pounds/week
    
    # Create comparison data
    metrics = ['Carbon Footprint (tons/year)', 'Water Usage (gallons/day)', 'Waste (pounds/week)']
    user_values = [
        impact_results['carbon_footprint'],
        impact_results['water_usage'],
        impact_results['waste_generation']
    ]
    oahu_values = [oahu_avg_carbon, oahu_avg_water, oahu_avg_waste]
    
    # Normalize for better visualization (since scales are very different)
    user_normalized = [
        (user_values[0] / oahu_avg_carbon) * 100,
        (user_values[1] / oahu_avg_water) * 100,
        (user_values[2] / oahu_avg_waste) * 100
    ]
    oahu_normalized = [100, 100, 100]  # Always 100%
    
    # Create figure
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        x=metrics,
        y=user_normalized,
        name='Your Usage',
        marker_color='rgba(31, 119, 180, 0.7)'
    ))
    
    fig.add_trace(go.Bar(
        x=metrics,
        y=oahu_normalized,
        name='Oahu Average',
        marker_color='rgba(214, 39, 40, 0.7)'
    ))
    
    # Add value annotations
    for i, (user_val, oahu_val) in enumerate(zip(user_values, oahu_values)):
        fig.add_annotation(
            x=metrics[i],
            y=user_normalized[i] + 5,
            text=f"{user_val:.1f}",
            showarrow=False
        )
        
        fig.add_annotation(
            x=metrics[i],
            y=oahu_normalized[i] + 5,
            text=f"{oahu_val:.1f}",
            showarrow=False
        )
    
    # Customize layout
    fig.update_layout(
        title="Your Usage Compared to Oahu Averages (% of Average)",
        yaxis_title="Percentage of Oahu Average",
        barmode='group',
        height=400
    )
    
    return fig

#############################
# RECOMMENDATIONS SYSTEM
#############################

# Initialize OpenAI client if API key is available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
has_openai_key = OPENAI_API_KEY is not None and OPENAI_API_KEY != ""

if has_openai_key:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

def get_personalized_recommendations(user_data, impact_results):
    """
    Generate personalized sustainability recommendations for Oahu residents
    
    Args:
        user_data: Dictionary of user inputs
        impact_results: Dictionary of calculated impact scores and metrics
        
    Returns:
        Dictionary of recommendations
    """
    # Identify areas needing improvement
    oahu_factors = get_oahu_environmental_factors()
    areas_for_improvement = []
    
    if impact_results['transport_score'] < 60:
        areas_for_improvement.append("transportation")
    if impact_results['energy_score'] < 60:
        areas_for_improvement.append("energy")
    if impact_results['water_score'] < 60:
        areas_for_improvement.append("water")
    if impact_results['waste_score'] < 60:
        areas_for_improvement.append("waste")
    if impact_results['food_score'] < 60:
        areas_for_improvement.append("food")
        
    if not areas_for_improvement:
        # If all scores are good, still suggest some improvements
        lowest_score = min(
            impact_results['transport_score'], 
            impact_results['energy_score'],
            impact_results['water_score'],
            impact_results['waste_score'],
            impact_results['food_score']
        )
        
        if lowest_score == impact_results['transport_score']:
            areas_for_improvement.append("transportation")
        elif lowest_score == impact_results['energy_score']:
            areas_for_improvement.append("energy")
        elif lowest_score == impact_results['water_score']:
            areas_for_improvement.append("water")
        elif lowest_score == impact_results['waste_score']:
            areas_for_improvement.append("waste")
        elif lowest_score == impact_results['food_score']:
            areas_for_improvement.append("food")
    
    # Return Oahu-specific recommendations
    return {
        "top_recommendations": [
            {
                "title": "Install Solar Panels",
                "description": "Given Oahu's abundant sunshine and high electricity costs, solar panels have an excellent return on investment. This can significantly reduce your carbon footprint and energy bills.",
                "impact": "Could reduce your household carbon emissions by up to 30%",
                "local_resources": ["Hawaii Energy Solar Rebates", "Blue Planet Foundation"]
            },
            {
                "title": "Reduce Water Consumption",
                "description": "Install low-flow fixtures and consider rain catchment systems. Fresh water is a precious resource on Oahu.",
                "impact": "Could reduce your water usage by 20-30%",
                "local_resources": ["Board of Water Supply Conservation Program"]
            },
            {
                "title": "Buy Local Food",
                "description": "Shop at farmers markets to support local agriculture and reduce the carbon footprint of imported foods.",
                "impact": "Reduces food miles and supports Oahu's food security",
                "local_resources": ["Hawaii Farm Bureau Markets", "Oahu Fresh"]
            }
        ],
        "category_recommendations": {
            "transportation": [
                {
                    "title": "Consider an Electric Vehicle",
                    "description": "With Oahu's short driving distances, an electric vehicle is ideal. Solar panels can help offset charging costs."
                },
                {
                    "title": "Use TheBus for Commuting",
                    "description": "Oahu's public bus system can help reduce your transportation emissions and avoid parking hassles."
                }
            ],
            "energy": [
                {
                    "title": "Install Solar Hot Water",
                    "description": "Solar hot water systems are very effective in Hawaii's climate and can significantly reduce energy bills."
                },
                {
                    "title": "Use Fans Instead of AC",
                    "description": "Ceiling fans use much less electricity than air conditioning and can be effective with Hawaii's trade winds."
                }
            ],
            "water": [
                {
                    "title": "Install Rain Catchment",
                    "description": "Collecting rainwater for garden use can significantly reduce municipal water consumption."
                },
                {
                    "title": "Plant Native Species",
                    "description": "Native Hawaiian plants are adapted to local rainfall patterns and typically need less irrigation."
                }
            ],
            "waste": [
                {
                    "title": "Start Composting",
                    "description": "Food waste in landfills is a significant issue on Oahu with limited space. Composting can help reduce this waste."
                },
                {
                    "title": "Avoid Single-Use Plastics",
                    "description": "Oahu's marine environment is particularly vulnerable to plastic pollution. Bring reusable bags, bottles and containers."
                }
            ],
            "food": [
                {
                    "title": "Grow Some of Your Own Food",
                    "description": "Even a small garden can supplement your diet with fresh, zero-mile produce."
                },
                {
                    "title": "Reduce Meat Consumption",
                    "description": "The high environmental cost of meat is amplified on Oahu due to import requirements."
                }
            ]
        }
    }

def create_recommendation_prompt(user_data, impact_results, areas_for_improvement, oahu_factors):
    """Create a detailed prompt for the OpenAI API"""
    
    prompt = f"""
I need personalized sustainability recommendations for a resident of Oahu, Hawaii.

USER PROFILE:
- Transportation: Uses a {user_data['car_type']}, drives {user_data['car_usage']} miles per week, takes {user_data['public_transport_usage']} public transit trips per week
- Energy: Household of {user_data['household_size']} people, ${user_data['electricity_bill']} monthly electricity bill, uses {user_data['air_conditioning']} hours of AC daily
- Water: Takes {user_data['shower_length']} minute showers {user_data['shower_frequency']} times per week
- Waste: Recycling habit: {user_data['recycling_habit']}, Composting: {'Yes' if user_data['composting'] else 'No'}, Single-use plastics: {user_data['single_use_plastics']}
- Food: Diet type: {user_data['diet_type']}, {user_data['local_food']}% local food, {user_data['meals_out']} restaurant meals per week

IMPACT SCORES (0-100, higher is better):
- Transport score: {impact_results['transport_score']}
- Energy score: {impact_results['energy_score']}
- Water score: {impact_results['water_score']}
- Waste score: {impact_results['waste_score']}
- Food score: {impact_results['food_score']}
- Overall sustainability score: {impact_results['overall_score']}

OAHU-SPECIFIC FACTORS:
- Fresh water is a limited resource on the island
- The energy grid relies heavily on imported fossil fuels and has very high rates
- Limited landfill space on the island
- High dependency on imported goods (85-90% of food is imported)
- Fragile marine ecosystem susceptible to pollution, runoff, and climate change
- Transportation challenges with limited public transit
- Tourism impacts on natural resources

FOCUS AREAS FOR IMPROVEMENT: {', '.join(areas_for_improvement)}

Please create personalized recommendations in JSON format with the following structure:
{{
    "top_recommendations": [
        {{
            "title": "Clear recommendation title",
            "description": "Detailed explanation of the recommendation tailored to user's data and Oahu context",
            "impact": "Potential environmental impact of this change",
            "local_resources": ["Specific Oahu resource/organization that can help", "Another local resource"]
        }},
        // Additional recommendations...
    ],
    "category_recommendations": {{
        "transportation": [
            {{
                "title": "Transportation recommendation",
                "description": "Detailed explanation considering Oahu's limited public transit, traffic, etc."
            }},
            // More transportation recommendations...
        ],
        "energy": [...],
        "water": [...],
        "waste": [...],
        "food": [...]
    }}
}}

Focus specifically on Oahu's unique environmental context and provide actionable recommendations that consider the island's infrastructure, climate, and resources. Do not include any references to community features, social networking, or mobile apps. Only provide recommendations that can be implemented locally on Oahu.
"""

    return prompt

#############################
# STREAMLIT APPLICATION
#############################

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'impact_results' not in st.session_state:
    st.session_state.impact_results = None
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None

# Navigation functions
def go_to_page(page_name):
    st.session_state.page = page_name
    st.rerun()

# Welcome page
def welcome_page():
    st.title("🌴 Oahu Sustainability Calculator")
    
    st.markdown("""
    ### Aloha! Welcome to the Oahu Sustainability Calculator
    
    This tool helps you understand your environmental impact on the beautiful island of Oahu
    and provides personalized recommendations for sustainable living specific to Oahu.
    
    **Why is this important?**
    
    Oahu faces unique environmental challenges including:
    - Limited freshwater resources
    - Waste management on an island with limited space
    - Reliance on imported goods and fossil fuels
    - Protection of delicate marine and terrestrial ecosystems
    - High energy costs due to imported fossil fuels
    - Limited public transportation options
    
    By understanding your impact, you can take meaningful steps to protect our island paradise for future generations.
    """)
    
    st.button("Get Started", on_click=go_to_page, args=('input',), use_container_width=True)

# Input page to collect user data
def input_page():
    st.title("🌴 Oahu Sustainability Calculator")
    st.subheader("Tell us about your lifestyle")
    
    with st.form("lifestyle_form"):
        # Transportation section
        st.subheader("🚗 Transportation")
        
        transport_options = {
            "car_usage": st.slider("Average miles driven per week", 0, 500, 100),
            "car_type": st.selectbox("Vehicle type", [
                "Electric vehicle", 
                "Hybrid vehicle", 
                "Small gas car (30+ mpg)", 
                "Medium gas car (20-30 mpg)", 
                "Large gas car/SUV/truck (under 20 mpg)"
            ]),
            "public_transport_usage": st.slider("Number of public transport trips per week", 0, 30, 0),
            "flight_hours": st.number_input("Flight hours per year (to/from Oahu)", min_value=0, value=6)
        }
        
        # Energy usage section
        st.subheader("⚡ Energy Usage")
        
        energy_options = {
            "household_size": st.number_input("Number of people in household", min_value=1, value=2),
            "electricity_bill": st.slider("Average monthly electricity bill ($)", 50, 500, 200),
            "renewable_energy": st.selectbox("Do you use any renewable energy at home?", ["No", "Yes - solar panels", "Yes - other"]),
            "air_conditioning": st.slider("Hours of air conditioning use per day", 0, 24, 6)
        }
        
        # Water consumption
        st.subheader("💧 Water Consumption")
        
        water_options = {
            "shower_length": st.slider("Average shower length (minutes)", 1, 30, 8),
            "shower_frequency": st.slider("Showers per week", 1, 14, 7),
            "water_conservation": st.multiselect("Water conservation measures", [
                "Low-flow showerheads/faucets", 
                "Dual-flush toilets", 
                "Rainwater collection", 
                "Drought-resistant landscaping",
                "None of the above"
            ])
        }
        
        # Waste and Consumption
        st.subheader("🗑️ Waste and Consumption")
        
        waste_options = {
            "recycling_habit": st.select_slider("How consistently do you recycle?", 
                options=["Never", "Rarely", "Sometimes", "Often", "Always"]),
            "composting": st.checkbox("Do you compost food waste?"),
            "single_use_plastics": st.select_slider("How often do you use single-use plastics?", 
                options=["Never", "Rarely", "Sometimes", "Often", "Always"]),
            "local_food": st.slider("Percentage of food from local sources", 0, 100, 30)
        }
        
        # Food choices
        st.subheader("🍲 Food Choices")
        
        food_options = {
            "diet_type": st.selectbox("Dietary preference", [
                "Vegan", 
                "Vegetarian", 
                "Pescatarian", 
                "Flexitarian (mostly plant-based with occasional meat)", 
                "Omnivore (regular meat consumption)"
            ]),
            "meals_out": st.slider("Meals eaten at restaurants per week", 0, 21, 4)
        }
        
        # Combine all data
        user_data = {
            **transport_options,
            **energy_options,
            **water_options,
            **waste_options,
            **food_options
        }
        
        # Submit button
        submitted = st.form_submit_button("Calculate My Impact", use_container_width=True)
        
        if submitted:
            # Store the user data and calculate impact
            st.session_state.user_data = user_data
            with st.spinner("Analyzing your impact..."):
                impact_results = calculate_impact(user_data)
                st.session_state.impact_results = impact_results
            go_to_page('results')

# Results page
def results_page():
    st.title("🌴 Your Environmental Impact on Oahu")
    
    impact_results = st.session_state.impact_results
    
    if impact_results is None:
        st.error("No results found. Please complete the questionnaire.")
        st.button("Go to Questionnaire", on_click=go_to_page, args=('input',))
        return
    
    # Display overall impact score
    overall_score = impact_results['overall_score']
    st.subheader("Your Overall Sustainability Score")
    
    # Create a gauge chart for overall score
    score_color = get_score_color(overall_score)
    st.markdown(f"<h1 style='text-align: center; color: {score_color};'>{overall_score}/100</h1>", unsafe_allow_html=True)
    
    # Interpretation of score
    if overall_score >= 80:
        st.success("Excellent! You're leading a very sustainable lifestyle on Oahu.")
    elif overall_score >= 60:
        st.info("Good job! You're making positive contributions to Oahu's sustainability.")
    elif overall_score >= 40:
        st.warning("There's room for improvement in your environmental impact.")
    else:
        st.error("Your lifestyle has a significant environmental impact on Oahu.")
    
    # Display visualizations
    st.subheader("Impact Breakdown")
    impact_viz = create_impact_visualization(impact_results)
    st.plotly_chart(impact_viz, use_container_width=True)
    
    # Display category scores
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Transport Impact", f"{impact_results['transport_score']}/100")
    with col2:
        st.metric("Energy Impact", f"{impact_results['energy_score']}/100")
    with col3:
        st.metric("Water Impact", f"{impact_results['water_score']}/100")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Waste Impact", f"{impact_results['waste_score']}/100")
    with col2:
        st.metric("Food Impact", f"{impact_results['food_score']}/100")
    with col3:
        # Calculate carbon footprint comparison
        oahu_average = 16.9  # tons of CO2 per year for average Oahu resident
        user_footprint = impact_results['carbon_footprint']
        percentage_diff = ((user_footprint - oahu_average) / oahu_average) * 100
        delta_text = f"{percentage_diff:.1f}% {'above' if percentage_diff > 0 else 'below'} Oahu average"
        
        st.metric(
            "Carbon Footprint", 
            f"{user_footprint:.1f} tons CO2/year", 
            delta=delta_text,
            delta_color="inverse"
        )
    
    # Generate recommendations if not already done
    if st.session_state.recommendations is None:
        with st.spinner("Generating personalized recommendations..."):
            recommendations = get_personalized_recommendations(st.session_state.user_data, impact_results)
            st.session_state.recommendations = recommendations
    
    # Display button to view recommendations
    st.button("View My Personalized Recommendations", on_click=go_to_page, args=('recommendations',), use_container_width=True)

# Recommendations page
def recommendations_page():
    st.title("🌴 Your Personalized Sustainability Recommendations")
    
    if st.session_state.recommendations is None:
        st.error("No recommendations found. Please complete the questionnaire.")
        st.button("Go to Questionnaire", on_click=go_to_page, args=('input',))
        return
    
    recommendations = st.session_state.recommendations
    
    # Display key recommendations
    st.subheader("Top Recommendations for Your Lifestyle")
    
    for i, rec in enumerate(recommendations['top_recommendations']):
        with st.expander(f"{i+1}. {rec['title']}", expanded=i < 3):
            st.write(rec['description'])
            if 'impact' in rec:
                st.info(f"**Potential Impact:** {rec['impact']}")
            if 'local_resources' in rec:
                st.markdown("**Local Resources:**")
                for resource in rec['local_resources']:
                    st.markdown(f"- {resource}")
    
    # Category-specific recommendations
    st.subheader("Category-Specific Recommendations")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Transportation", "Energy", "Water", "Waste", "Food"])
    
    with tab1:
        for rec in recommendations['category_recommendations']['transportation']:
            st.markdown(f"**{rec['title']}**")
            st.write(rec['description'])
            st.markdown("---")
    
    with tab2:
        for rec in recommendations['category_recommendations']['energy']:
            st.markdown(f"**{rec['title']}**")
            st.write(rec['description'])
            st.markdown("---")
    
    with tab3:
        for rec in recommendations['category_recommendations']['water']:
            st.markdown(f"**{rec['title']}**")
            st.write(rec['description'])
            st.markdown("---")
    
    with tab4:
        for rec in recommendations['category_recommendations']['waste']:
            st.markdown(f"**{rec['title']}**")
            st.write(rec['description'])
            st.markdown("---")
    
    with tab5:
        for rec in recommendations['category_recommendations']['food']:
            st.markdown(f"**{rec['title']}**")
            st.write(rec['description'])
            st.markdown("---")
    
    # Educational resources
    st.subheader("Oahu Environmental Educational Resources")
    
    resources = get_oahu_educational_resources()
    
    for category, res_list in resources.items():
        with st.expander(category):
            for resource in res_list:
                st.markdown(f"**{resource['name']}**")
                st.write(resource['description'])
                if 'url' in resource:
                    st.markdown(f"[Learn more]({resource['url']})")
                st.markdown("---")
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        st.button("View My Impact Results", on_click=go_to_page, args=('results',), use_container_width=True)
    with col2:
        st.button("Start Over", on_click=go_to_page, args=('welcome',), use_container_width=True)

# Main app logic
def main():
    # Page router
    if st.session_state.page == 'welcome':
        welcome_page()
    elif st.session_state.page == 'input':
        input_page()
    elif st.session_state.page == 'results':
        results_page()
    elif st.session_state.page == 'recommendations':
        recommendations_page()
    else:
        welcome_page()

if __name__ == "__main__":
    main()
