import instaloader
from instaloader import Post
import re
import os
import json
import requests
from dotenv import load_dotenv
from google import genai

def get_client():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return None
    client = genai.Client(api_key=api_key)
    return client

def get_caption(post_url):
    L = instaloader.Instaloader()
    
    # extract shortcode
    pattern = r"(?:/reel/|/p/)([^/?]+)"
    match = re.search(pattern, post_url) # finds first occurrence of pattern
    if match:
        shortcode = match.group(1)
    else:
        raise ValueError("invalid post url:", post_url)
    
    post = Post.from_shortcode(L.context, shortcode)
    return post.caption

def extract_locations(caption, client, model_name="gemini-2.5-flash"):
    # TODO: can categorize points of interest (e.g., meal, drink/snack, activity/sightseeing, shopping)
    response = client.models.generate_content(
        model=model_name,
        contents=f"Extract all unique real-world location names from the following Instagram post caption. Look for specific points of interest and exclude geographic areas (e.g., neighborhood, city, state, country). Return the locations as a JSON list of objects, where each object has a 'name', 'city' ('none' if not specified), and 'address' ('none' if not specified). Caption: {caption}"
    )
    text = response.text
    try:
        start = text.index("[")
        end = text.index("]")
        locations = json.loads(text[start:end+1])
        return locations
    except ValueError:
        print("Input is not a valid JSON string")

def geocode_locations(locations):
    """
    Takes a JSON list of location objects, geocodes each one, and adds 'latitude' and 'longitude' tags to each. Updates 'name', 'city', and 'address' for consistency.
    """
    api_key = os.getenv("GEOAPIFY_API_KEY")
    if not api_key:
        print("Error: GEOAPIFY_API_KEY not found in environment variables")
        return locations

    for item in locations:
        place_name = item["name"]

        if item["address"] != "none": # use address if specified
            search_input = item["address"]
        else:
            search_input = place_name # otherwise, use name (and city)
            if item["city"] != "none":
                search_input += ", " + item["city"]
        
        # print(search_input)

        # input for API request
        params = {
            'text': search_input,
            'apiKey': api_key,
            'limit': 1
        }

        try:
            response = requests.get('https://api.geoapify.com/v1/geocode/autocomplete', params=params)

            if response.status_code == 200:
                data = response.json()
                if data.get('features'): # success, if at least 1 matching result
                    properties = data["features"][0]["properties"]
                    item["name"] = properties["name"]
                    item["city"] = properties["city"]
                    item["address"] = properties["address_line2"]
                    item["latitude"] = properties["lat"]
                    item["longitude"] = properties["lon"]
                else: # TODO: handle if no matching results
                    item["latitude"] = None
                    item["longitude"] = None
                    print(f"No results found for {place_name}")
            else:
                item["latitude"] = None
                item["longitude"] = None
                print(f"API error for {place_name}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            item["latitude"] = None
            item["longitude"] = None
            print(f"Request failed for {place_name}: {e}")

    return locations
