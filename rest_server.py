import falcon
import json
from datetime import datetime, timedelta
from pymongo import MongoClient
from urllib.parse import urlparse, parse_qs
from wsgiref import simple_server

CONNECTION_STRING = "mongodb+srv://userReadOnly:7ZT817O8ejDfhnBM@minichallenge.q4nve1r.mongodb.net/"

def connect_to_db(collection_name:str):
        client = MongoClient(CONNECTION_STRING)
        db = client["minichallenge"]
        return db[collection_name]


def is_iso_date(date_str):
    try:
        # Attempt to parse the date string using the datetime.strptime function
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        # If the parsing fails, it's not in ISO date format
        return False


def validate_req(date1, date2, dst_city):
    if any(not value for value in [dst_city, date1, date2]):
        return False
    if not is_iso_date(date1) or not is_iso_date(date2):
        return False
    return True


class HelloWorld:
    def on_get(self, req, resp):
        resp.text = "Hello, world!"
        resp.status = falcon.HTTP_200


class Flight:
    def __init__(self):
        self.departure_date_str = ""
        self.return_date_str = ""
        self.dst_city = ""

    def find_cheapest_flight(self, flight_data):
        if not flight_data:
            return None
        
        min_price = None
        cheapest_flight = []

        for flight in flight_data:
            if min_price is None or flight["price"] < min_price:
                cheapest_flight = [flight]
                min_price = flight["price"]

            elif flight["price"] == min_price:
                cheapest_flight.append(flight)

        return cheapest_flight

    def generate_flight_results(self, cheapest_flight_to, cheapest_flight_back):
        if cheapest_flight_to is None or cheapest_flight_back is None:
            return []
        
        return [
            {
                "City": self.dst_city,
                "Departure Date": self.departure_date_str,
                "Departure Airline": flight_to["airlinename"],
                "Departure Price": flight_to["price"],
                "Return Date": self.return_date_str,
                "Return Airline": flight_back["airlinename"],
                "Return Price": flight_back["price"],
            }
            for flight_to in cheapest_flight_to
            for flight_back in cheapest_flight_back
        ]

    def on_get(self, req, resp):
        # Retrieve query parameters
        query_params = parse_qs(urlparse(req.url).query)

        self.departure_date_str = query_params.get("departureDate", [""])[0]
        self.return_date_str = query_params.get("returnDate", [""])[0]
        self.dst_city = query_params.get("destination", [""])[0]
        
        if not validate_req(
            self.departure_date_str, self.return_date_str, self.dst_city
        ):
            resp.status = falcon.HTTP_BAD_REQUEST
            return

        # Convert query date to datetime format
        departure_date = datetime.strptime(self.departure_date_str, "%Y-%m-%d")
        return_date = datetime.strptime(self.return_date_str, "%Y-%m-%d")

        # Connect to MongoDB
        flight_collection = connect_to_db("flights")

        # Query MongoDB for flight data based on the parameters
        flight_to_query = {
            "date": departure_date,
            "srccountry": "Singapore",
            "destcity": self.dst_city,
        }

        flight_back_query = {
            "date": return_date,
            "destcountry": "Singapore",
            "srccity": self.dst_city,
        }

        cheapest_flight_to = self.find_cheapest_flight(flight_collection.find(flight_to_query))
        cheapest_flight_back = self.find_cheapest_flight(flight_collection.find(flight_back_query))

        results = self.generate_flight_results(cheapest_flight_to, cheapest_flight_back)

        resp.body = json.dumps(results)
        resp.status = falcon.HTTP_OK


class Hotel:
    def __init__(self):
        self.chk_in_date_str = ""
        self.chk_out_date_str = ""
        self.dst_city = ""

    def on_get(self, req, resp):
        # Retrieve query parameters
        query_params = parse_qs(urlparse(req.url).query)

        self.chk_in_date_str = query_params.get("checkInDate", [""])[0]
        self.chk_out_date_str = query_params.get("checkOutDate", [""])[0]
        self.dst_city = query_params.get("destination", [""])[0]
        
        if not validate_req(self.chk_in_date_str, self.chk_out_date_str, self.dst_city):
            resp.status = falcon.HTTP_BAD_REQUEST
            return

        # Convert query date to datetime format
        chk_in_date = datetime.strptime(self.chk_in_date_str, "%Y-%m-%d")
        chk_out_date = datetime.strptime(self.chk_out_date_str, "%Y-%m-%d")

        # Connect to MongoDB
        hotels_collection = connect_to_db("hotels")

        cur_date = chk_in_date
        available_hotels = {}

        # Perform addition of all hotels on check in day
        daily_query = {"city": self.dst_city, "date": cur_date}
        expected_num_days = 1
        for hotel in hotels_collection.find(daily_query):
            available_hotels[hotel["hotelName"]] = [hotel["price"], expected_num_days]
        cur_date += timedelta(days=1)

        while cur_date <= chk_out_date:

            daily_query["date"] = cur_date

            for hotel in hotels_collection.find(daily_query):

                if hotel["hotelName"] in available_hotels:
                    cur_hotel_price, cur_num_days = available_hotels[hotel["hotelName"]]
                    available_hotels[hotel["hotelName"]] = [
                        cur_hotel_price + hotel["price"],
                        cur_num_days + 1,
                    ]

            cur_date += timedelta(days=1)
            expected_num_days += 1

        filtered_available_hotels = {hotel_name: price for hotel_name, (price, num_days) in available_hotels.items() if num_days == expected_num_days}

        if not filtered_available_hotels:
            resp.body = json.dumps([])
            resp.status = falcon.HTTP_200
            return

        min_price = min(filtered_available_hotels.values())
        
        cheapest_hotels = [hotel for hotel, price in filtered_available_hotels.items() if price == min_price]

        results = [
            {
                "City": self.dst_city,
                "Check In Date": self.chk_in_date_str,
                "Check Out Date": self.chk_out_date_str,
                "Hotel": hotel_name,
                "Price": min_price,
            }
             for hotel_name in cheapest_hotels
        ]

        resp.body = json.dumps(results)
        resp.status = falcon.HTTP_200


app = falcon.App()

app.add_route("/", HelloWorld())
app.add_route("/flight", Flight())
app.add_route("/hotel", Hotel())

if __name__ == "__main__":

    server = simple_server.make_server("0.0.0.0", 8080, app)
    print("Serving on http://localhost:8080/")
    server.serve_forever()
