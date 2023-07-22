import falcon
import json
from datetime import datetime, timedelta
from pymongo import MongoClient
from urllib.parse import urlparse, parse_qs
from wsgiref import simple_server

class HelloWorld:
    def on_get(self, req, resp):
        resp.text = "Hello, world!"
        resp.status = falcon.HTTP_200


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

class Flight:
    departure_date_str = ""
    return_date_str = ""
    dst_city = ""
    
    def find_cheapest_flight(self, flight_data):
        if flight_data is None:
            return None;
        current_price = None
        cheapest_flight = []
        
        for flight in flight_data:
            if current_price is None:
                cheapest_flight.append(flight)
                current_price = flight['price']
                
            elif flight['price'] < current_price:
                cheapest_flight = []
                cheapest_flight.append(flight)
                current_price = flight['price']
                
            elif flight['price'] == current_price:
                cheapest_flight.append(flight)
        
        return cheapest_flight
   
    def generate_flight_results(self, cheapest_flight_to, cheapest_flight_back):
        """
        [
        {
            "City": "Frankfurt",
            "Departure Date": "2023-12-10",
            "Departure Airline": "US Airways",
            "Departure Price": 1766,
            "Return Date": "2023-12-16",
            "Return Airline": "US Airways",
            "Return Price": 716
        }
        ]
        """
        results = []
        template = {
            "City": self.dst_city,
            "Departure Date": self.departure_date_str,
            "Departure Airline": "",
            "Departure Price": None,
            "Return Date": self.return_date_str,
            "Return Airline": "",
            "Return Price": None
        }
        
        if cheapest_flight_to is None or cheapest_flight_back is None:
            return results
        for flight_to in cheapest_flight_to:
            for flight_back in cheapest_flight_back:
                current = template.copy()
                current["Departure Airline"] = flight_to["airlinename"]
                current["Departure Price"] = flight_to["price"]
                current["Return Airline"] = flight_back["airlinename"]
                current["Return Price"] = flight_back["price"]
                results.append(current)
        return results
        
    
    
    def on_get(self, req, resp):
         # Retrieve query parameters
        query_params = parse_qs(urlparse(req.url).query)
        
        self.departure_date_str = query_params.get('departureDate', [''])[0]
        self.return_date_str = query_params.get('returnDate', [''])[0]
        self.dst_city = query_params.get('destination', [''])[0]
        if not validate_req(self.departure_date_str, self.return_date_str, self.dst_city):
            resp.status = falcon.HTTP_BAD_REQUEST
            return
        
        # Convert query date to datetime format
        departure_date = datetime.strptime(self.departure_date_str, "%Y-%m-%d")
        return_date = datetime.strptime(self.return_date_str, "%Y-%m-%d")
        
        
        # Connect to MongoDB
        CONNECTION_STRING = 'mongodb+srv://userReadOnly:7ZT817O8ejDfhnBM@minichallenge.q4nve1r.mongodb.net/'
        client = MongoClient(CONNECTION_STRING)
        db = client['minichallenge']
        collection = db['flights']
        
        # Query MongoDB for flight data based on the parameters  
        flight_to = {
            'date': departure_date,
            'srccountry': "Singapore",
            'destcity': self.dst_city
        }

        flight_data = collection.find(flight_to)
        cheapest_flight_to = self.find_cheapest_flight(flight_data)
        # pprint.pprint(cheapest_flight_to)

        flight_back = {
            'date': return_date,
            'destcountry': "Singapore",
            'srccity': self.dst_city
        }

        flight_data = collection.find(flight_back)
        
        cheapest_flight_back = self.find_cheapest_flight(flight_data)
        # pprint.pprint(cheapest_flight_back)
        

        
        
        results = self.generate_flight_results(cheapest_flight_to, cheapest_flight_back)
        


        resp.body = json.dumps(results)
        resp.status = falcon.HTTP_OK
        
class Hotel:
    
    chk_in_date_str = ""
    chk_out_date_str = ""
    dst_city = ""
    
    def on_get(self, req, resp):
        # Retrieve query parameters
        query_params = parse_qs(urlparse(req.url).query)
        
        self.chk_in_date_str = query_params.get('checkInDate', [''])[0]
        self.chk_out_date_str = query_params.get('checkOutDate', [''])[0]
        self.dst_city = query_params.get('destination', [''])[0]
        if not validate_req(self.chk_in_date_str, self.chk_out_date_str, self.dst_city):
            resp.status = falcon.HTTP_BAD_REQUEST
            return
        
        # Convert query date to datetime format
        chk_in_date = datetime.strptime(self.chk_in_date_str, "%Y-%m-%d")
        chk_out_date = datetime.strptime(self.chk_out_date_str, "%Y-%m-%d")
        
        # Connect to MongoDB
        CONNECTION_STRING = 'mongodb+srv://userReadOnly:7ZT817O8ejDfhnBM@minichallenge.q4nve1r.mongodb.net/'
        client = MongoClient(CONNECTION_STRING)
        db = client['minichallenge']
        hotels_collection = db['hotels']
        
        
        
        
        
        cur_date = chk_in_date
        available_hotels = {}
    
        # Perform addition of all hotels on check in day
        daily_query = {
                "city" : self.dst_city,
                "date" : cur_date
        }
        expected_num_days = 1
        for hotel in hotels_collection.find(daily_query):
            available_hotels[hotel["hotelName"]] = [hotel["price"], expected_num_days]
        cur_date += timedelta(days=1)
        
        while cur_date <= chk_out_date:
            
            daily_query["date"] = cur_date
            
            for hotel in hotels_collection.find(daily_query):
                
                if hotel["hotelName"] in available_hotels:
                    cur_hotel_price, cur_num_days = available_hotels[hotel["hotelName"]]
                    available_hotels[hotel["hotelName"]] = [cur_hotel_price+hotel["price"], cur_num_days+1]
                
            cur_date += timedelta(days=1)
            expected_num_days += 1
        
        filtered_available_hotels = {}
        
        for hotel_name, info in available_hotels.items():
            price, num_days = info  # Unpack the information about the hotel
            if num_days == expected_num_days:
                filtered_available_hotels[hotel_name] = price
        
        if not filtered_available_hotels:
            resp.body = json.dumps([])
            resp.status = falcon.HTTP_200
            return 
        
        
        cheapest_hotel = min(filtered_available_hotels, key=filtered_available_hotels.get)
        cheapest_price = filtered_available_hotels[cheapest_hotel]
        
        results = [
            {
                "City": self.dst_city,
                "Check In Date": self.chk_in_date_str,
                "Check Out Date": self.chk_out_date_str,
                "Hotel": cheapest_hotel,
                "Price": cheapest_price
            }
        ]
        
        resp.body = json.dumps(results)
        resp.status = falcon.HTTP_200
        """
                [
        {
            "City": "Frankfurt",
            "Check In Date": "2023-12-10",
            "Check Out Date": "2023-12-16",
            "Hotel": "Hotel J",
            "Price": 2959
        }
        ]
        """
        
        
app = falcon.App()

# Define the routes
app.add_route('/', HelloWorld())
app.add_route('/flight', Flight())
app.add_route('/hotel', Hotel())

if __name__ == '__main__':
    
    # Create a simple WSGI server to run the application
    server = simple_server.make_server('0.0.0.0', 8080, app)
    print("Serving on http://localhost:8080/")
    server.serve_forever()
    
        
