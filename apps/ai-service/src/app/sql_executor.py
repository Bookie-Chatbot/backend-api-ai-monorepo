# app/sql_executor.py

def pseudo_execute_sql(query_key, db_data):
    """
    query_key에 따라 가상 DB(db_data)를 조회한 결과를 반환함
    virtual_db에서 객체로 병합된 db_data 구조 :
    {
      "Hotel": [...],
      "Flight": [...],
      "Reservation": [...],
      "User": [...],
      "AdminSettings": [...],
      ...
    }
    """
    if query_key == "SHOW_AVAILABLE_ROOMS":
        hotels = db_data.get("Hotel", [])
        available_hotels = [h for h in hotels if h["available_rooms"] > 0]
        return {"available_rooms": available_hotels}
    elif query_key == "SHOW_UPCOMING_RESERVATIONS":
        flights = db_data.get("Flight", [])
        upcoming = [f for f in flights if f["available_seats"] > 0]
        return {"upcoming_flights": upcoming}
    elif query_key == "SHOW_CUSTOMER_RESERVATION":
        reservations = db_data.get("Reservation", [])
        return {"customer_reservation": reservations}
    elif query_key == "SHOW_REVENUE_SUMMARY":
        flights = db_data.get("Flight", [])
        total = sum(item["price"] for item in flights)
        return {"revenue_summary": total}
    elif query_key == "SHOW_RESERVATION_DETAILS":
        reservations = db_data.get("Reservation", [])
        if reservations:
            return {"reservation_details": reservations[0]}
        else:
            return {"reservation_details": None}
    else:
        return {"error": f"No mapping for query_key={query_key}"}
