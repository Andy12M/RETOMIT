import sqlalchemy as db
import cv2
import ctypes
import mysql.connector
import pyzbar
import PIL as pil
from flask import Flask, jsonify
from collections import Counter
import time
from pyzbar import pyzbar
from pyzbar.pyzbar import decode
from sqlalchemy import text, create_engine



def get_barcode():
    # Open the camera
    duration = 12  
    start_time = time.time()

    barcodes_set = set()
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
    # Decode barcodes in the fram
        barcodes = decode(frame)
        for barcode in barcodes:
            x, y, w, h = barcode.rect
            scale_factor = 1.8
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            # Adjust x and y to keep the rectangle centered
            new_x = x - (new_w - w) // 2
            new_y = y - (new_h - h) // 2
            # Draw the bigger rectangle
            cv2.rectangle(frame, (new_x, new_y), (new_x + new_w, new_y + new_h), (0, 255, 0), 2)
            # Decode and display the barcode value
            barcode_value = barcode.data.decode("utf-8")
            barcode_type = barcode.type
            barcodes_set.add(barcode_value)
            time.sleep(.5)
            if barcode_value and barcode_type:
                print(f"Decoded Barcode Value: {barcode_value}")
                cv2.putText(frame, barcode_value, (new_x, new_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Display the frame with barcode information
        cv2.imshow("Barcode Scanner", frame)
        
        if cv2.waitKey(1) & 0xFF == ord("q") or time.time() - start_time > duration:
            break

    barcodes_list = list(barcodes_set)
    counter = Counter(barcodes_list)
    barcode = counter.most_common(1)
    barcode_final = barcode[0][0]
    return(barcode_final)



def refresh_sql(barcode, cantidad):
    
    engine = create_engine('mysql+mysqlconnector://root:@localhost/quirondb')
    
   
    with engine.connect() as connection:
        row = connection.execute(text("SELECT * FROM barcodes WHERE number = :barcode"), {'barcode': barcode})
        barcode_data = row.fetchone()
        
        if barcode_data:
            row = connection.execute(text("SELECT * FROM products WHERE id = :product_id"), {'product_id': barcode_data[2]})
            product = row.fetchone()
            
        if product:
            print(product)
            update_query = text("UPDATE products SET cantidad = :new_cantidad WHERE id = :product_id")
            connection.execute(update_query, {'new_cantidad': product[2] + cantidad, 'product_id': barcode_data[2]})

            update_query = text("UPDATE products SET cantidad = :new_cantidad WHERE id = :product_id")
            connection.execute(update_query, {'new_cantidad': product[2] + cantidad, 'product_id': barcode_data[2]})


        insert_query = text("""
        INSERT INTO ventas (idProduct, items, monto, timestamp)
        VALUES (:idProduct, :items, :monto, CURRENT_TIMESTAMP)
                """)
        connection.execute(insert_query, {
        'idProduct': barcode_data[2],
        'items': cantidad,
        'monto': cantidad * product[3]
                })
        print("New row inserted successfully.")

        connection.commit()


    engine.dispose()
    
def barcode_activate(a):
    barcode = get_barcode()
    refresh_sql(barcode, a)


barcode_activate(3)






