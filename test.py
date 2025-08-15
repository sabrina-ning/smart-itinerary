from utils import get_client, get_caption, extract_locations, geocode_locations
import json

def test(post_url):
    client = get_client()
    caption = get_caption(post_url)
    print("=" * 20 + " Caption " + "=" * 20)
    print(caption)

    print("=" * 20 + " Locations " + "=" * 20)
    locations = extract_locations(caption, client)
    print(locations)

    print("=" * 20 + " Geocoded Locations " + "=" * 20)
    locations_new = geocode_locations(locations)
    print(locations_new)

test("https://www.instagram.com/p/DHmBk_GzdNp/")
# test("https://www.instagram.com/reel/DGDem5byHW_/")
# test("https://www.instagram.com/reel/DMICDXCyT_6/")