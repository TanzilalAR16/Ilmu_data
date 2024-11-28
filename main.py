from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List
import mysql.connector
from config import db_config
import mysql.connector
from mysql.connector import errorcode

app = FastAPI()

def drop_table_if_exists():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        drop_table_query = "DROP TABLE IF EXISTS sensor_data"
        cursor.execute(drop_table_query)
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

def create_table_if_not_exists():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            jarak FLOAT NOT NULL,
            kapasitas FLOAT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

# Panggil fungsi untuk membuat tabel saat aplikasi dimulai
create_table_if_not_exists()

# Model data yang diterima
class SensorData(BaseModel):
    timestamp: datetime
    jarak: float
    kapasitas: float

    @field_validator('timestamp', mode='before')
    def parse_timestamp(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ValueError('Invalid timestamp format')
        return value

# Fungsi untuk menyimpan data ke database
def save_to_database(data: SensorData):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO sensor_data (timestamp, jarak, kapasitas) VALUES (%s, %s, %s)"
        values = (data.timestamp, data.jarak, data.kapasitas)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database Error: {e}")
        return False

# Endpoint untuk menerima data sensor
@app.post("/save-data")
async def save_data(data: SensorData):
    if save_to_database(data):
        return {"message": "Data saved successfully!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save data to database.")

@app.get("/sensor-data")
async def get_sensor_data(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100)
):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM sensor_data")
        total_records = cursor.fetchone()['total']
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get paginated data
        query = """
            SELECT timestamp, jarak, kapasitas 
            FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (page_size, offset))
        data = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return {
            "data": data,
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": -(-total_records // page_size)  # Ceiling division
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.delete("/delete-table")
async def delete_table():
    drop_table_if_exists()
    return {"message": "Table deleted successfully!"}