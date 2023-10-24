
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import numpy as np
from flask import Flask, jsonify
import datetime as dt
from dateutil.relativedelta import relativedelta


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///./Resources/hawaii.sqlite")

# Reflect an existing database into a new model.
Base = automap_base()
# Reflect the tables.
Base.prepare(engine, reflect=True)

# Save reference to the tables.
Measurement = Base.classes.measurement
Station = Base.classes.station
# print(Base.classes.keys())

#################################################
# Flask Setup
#################################################
app = Flask(__name__,static_url_path='/Images/surfs-up.png')


#################################################
# Flask Routes
#################################################

# Set the home page,and List all routes

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"<h1>Welcome</h1>"
     
        f"<h2>the available routes:</h2>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"

       
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
  
    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # Calculate the date 1 year ago from the last data point in the database.
    last_measurement_data_point_tuple = session.query(
        Measurement.date).order_by(Measurement.date.desc()).first()
    (the_latest, ) = last_measurement_data_point_tuple
    the_latest = dt.datetime.strptime(the_latest, '%Y-%m-%d')
    the_latest = the_latest.date()
    one_year_back = the_latest - relativedelta(years=1)

    # Perform a query to retrieve the data and precipitation scores.
    data_of_previous_year = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= one_year_back).all()

    session.close()

    # Convert the query results to a dictionary using date as the key and prcp as the value.
    all_ = []
    for date, prcp in data_of_previous_year:
        if prcp != None:
            p_dict = {}
            p_dict[date] = prcp
            all_.append(p_dict)

    # Return the JSON representation of dictionary.
    return jsonify(all_)


@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query for stations.
    stations = session.query(Station.station, Station.name,
                             Station.latitude, Station.longitude, Station.elevation).all()

    session.close()

    # Convert the query results to a dictionary.
    all_stations = []
    for station, name, latitude, longitude, elevation in stations:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        all_stations.append(station_dict)

    # Return the JSON representation of dictionary.
    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    """Query for the dates and temperature observations from a year from the last data point for the most active station."""
    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # Calculate the date 1 year ago from the last data point in the database.
    last_measurement_data_point_tuple = session.query(
        Measurement.date).order_by(Measurement.date.desc()).first()
    (the_latest, ) = last_measurement_data_point_tuple
    the_latest = dt.datetime.strptime(the_latest, '%Y-%m-%d')
    the_latest = the_latest.date()
    one_year_back = the_latest - relativedelta(years=1)

    # Find the most active station.
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count().desc()).\
        first()

    # Get the station id of the most active station.
    (most_active_station_id, ) = most_active_station
    print(
        f"The station id of the most active station is {most_active_station_id}.")

    # Perform a query to retrieve the data and temperature scores for the most active station from the last year.
    data_of_previous_year = session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station_id).filter(Measurement.date >= one_year_back).all()

    session.close()

    # Convert the query results to a dictionary using date as the key and temperature as the value.
    all_temperatures = []
    for date, temp in data_of_previous_year:
        if temp != None:
            temp_dict = {}
            temp_dict[date] = temp
            all_temperatures.append(temp_dict)
    # Return the JSON representation of dictionary.
    return jsonify(all_temperatures)





@app.route('/api/v1.0/<start>', defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
def determine_temps_for_date_range(start, end):

    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # If we have both a start date and an end date.
    if end != None:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).filter(
            Measurement.date <= end).all()
    # If we only have a start date.
    else:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()

    session.close()

    # Convert the query results to a list.
    temperature_list = []
    no_temperature_data = False
    for min_temp, avg_temp, max_temp in temperature_data:
        if min_temp == None or avg_temp == None or max_temp == None:
            no_temperature_data = True
        temperature_list.append(min_temp)
        temperature_list.append(avg_temp)
        temperature_list.append(max_temp)
    # Return the JSON representation of dictionary.
    if no_temperature_data == True:
        return f"temperature data not found for the entered date range. please Try again with alternative."
    else:
        return jsonify(temperature_list)


if __name__ == '__main__':
    app.run(debug=True)

