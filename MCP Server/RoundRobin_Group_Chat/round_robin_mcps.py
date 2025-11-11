from fastmcp import FastMCP
import httpx
import json
import os
import wikipedia

main_mcp = FastMCP(name="Main MCP")
profile_mcp = FastMCP(name="profile mcp server")
gif_mcp = FastMCP(name='mcp server for getting gifs')
weather_mcp = FastMCP(name='weather mcp server for weather functions')
from dotenv import load_dotenv
load_dotenv()

GIPHY_API_KEY = os.environ['GIPHY_API_KEY']

WEATHER_CODES = {
    0: "Clear",
    1: "Clear",
    2: "Cloudy",
    3: "Overcast",
    45: "Fog",
    51: "Drizzle",
    61: "Rain",
    63: "Rain",
    71: "Snow",
    73: "Snow",
    95: "Thunderstorm"
}

profile_dict = {
    'devan': {
        'name':'Devan',
        'age': '24',
        'interests':['soccer','video games'],
        'location': 'New Jersey'
    },
    'guest': {
        'name': 'Guest',
        'age':'99',
        'interests':['coding'],
        'location': 'London'

    }
}


@profile_mcp.resource("data://user_profile/{profile_name}")
def get_user_profile_data(profile_name:str) -> dict:

    """Read about a user's profile, and get user's profile informations"""

    profile_data =profile_dict.get(profile_name.lower(), {"error":"this profile is not available"})

    return profile_data



@profile_mcp.tool
def add_interest(profile_name: str, interest: str) -> dict:

    """Adds a new interest to a user's profile in profile_dict dictionary"""
    
    profile_key = profile_name.lower()
   
    #only looks thru keys
    if profile_key not in profile_dict: 
        return {"error": f"Profile '{profile_key}' not found, cannot add interest"}
        
    profile = profile_dict[profile_key]
    interests = profile['interests']

    interests.append(interest)
    
    return profile

@profile_mcp.tool
def create_profile(name: str, age: str, location: str, interests: list[str]) -> dict:
    """
        Tool to create a profile in the profile_dict dictionary
        """
    profile_key = name.lower()
        
    if profile_key in profile_dict:
            return {"error": f"Profile '{profile_key}' already exists."}
        
        # 1. Create the new profile (the "house") FIRST
    new_profile = {
            "name": name,
            "age": age,
            "location": location,
            "interests": interests
        }
        
        # 2. NOW add the new profile (the "house") to the main dictionary
    profile_dict[profile_key] = new_profile
        
    return new_profile # Return the profile you just created


@gif_mcp.tool
def get_gif(search_query:str)-> str:
    api_url = "https://api.giphy.com/v1/gifs/search"

    #specs for request
    params = {
        "api_key": GIPHY_API_KEY,
        "q": search_query,   
        "limit": 1,          
        "rating": "g"        
    }
    try:
        response = httpx.get(url=api_url, params=params)

        #error if request fails
        response.raise_for_status()

        #turn to dictionary
        data = response.json()
        
        gif_url = data["data"][0]["images"]["original"]["url"]
        
        return gif_url
        
    except Exception as e:
        return f"Error finding GIF: {e}"
    


@weather_mcp.tool
def get_current_weather(city_name:str):
    """Tool used to get weather of a specific location
    
        Argumetns: city_name (str) you must input a city name
        
            Internally we find the coordinates and time zone and then find the weather of this location
        
        Return: Return type is a formatted string with the requested information """
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city_name, "count": 1}
            
        geo_response = httpx.get(geo_url, params=geo_params).json()

        if not geo_response.get("results"):
            return f"Error: Could not find coordinates for city '{city_name}'"
        
        result = geo_response["results"][0]

        lat = result["latitude"]
        lon = result["longitude"]
        timezone = result["timezone"]

        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code",
                "timezone": timezone
            }
            
        weather_response = httpx.get(weather_url, params=weather_params).json()
        current = weather_response["current"]

        temp = current['temperature_2m']
            
        return f"The current forecast for {city_name} is {temp}°C."
        
    except Exception as e:
        return f"Error getting weather for {city_name}: {e}"

@weather_mcp.tool
def get_weather_type(city_name:str):
    """Tool used to get weather TYPE of weather in a location
    
        Argumetns: city_name (str) you must input a city name
        
            Internally we find the coordinates and time zone and then find the weather TYPE of this location
        
        Return: Return type just the weather type code"""
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city_name, "count": 1}
            
        geo_response = httpx.get(geo_url, params=geo_params).json()

        if not geo_response.get("results"):
            return f"Error: Could not find coordinates for city '{city_name}'"
        
        result = geo_response["results"][0]

        lat = result["latitude"]
        lon = result["longitude"]
        timezone = result["timezone"]

        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "weather_code",
                "timezone": timezone
            }
            
        weather_response = httpx.get(weather_url, params=weather_params).json()
        current = weather_response["current"]

        weather_code = current['weather_code']

        my_weather_code = WEATHER_CODES.get(weather_code, 'Not available')
           
        return my_weather_code
        
    except Exception as e:
        return f"Error getting weather for {city_name}: {e}"

main_mcp.mount(profile_mcp, prefix = 'profile')
main_mcp.mount(gif_mcp, prefix = 'gif')
main_mcp.mount(weather_mcp, prefix = 'weather')

if __name__ == "__main__":
    main_mcp.run(transport="http", host="0.0.0.0", port=8000)