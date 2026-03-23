from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="patient_assistant_app")


def get_location_details(user_input: str):
    try:
        location = geolocator.geocode(user_input)

        if not location:
            return None

        address = location.raw.get("address", {})

        return {
            "full_address": location.address,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "city": address.get("city") or address.get("town") or address.get("village"),
            "country": address.get("country")
        }

    except:
        return None