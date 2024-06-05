import streamlit as st
import os
import instructor 
from typing import Optional, List
from pydantic import BaseModel
from openai import OpenAI
from pydantic import model_validator
import json
import base64
import pandas as pd

class Item(BaseModel):
    name: str
    item_price: float
    item_quantity: int
    line_total: float

class Receipt(BaseModel):
    items: list[Item]
    total: float
    tip_gratuity: Optional[float]
    tax: Optional[float]
    subtotal: Optional[float]
    line_total: Optional[float]
    surcharge: Optional[float]
    service_charge: Optional[float]

@model_validator(mode="after")
def check_total(cls, values: "Receipt"):
    items = values.items
    total = values.total
    tip_gratuity = values.tip_gratuity
    tax = values.tax
    subtotal = values.subtotal
    surcharge = values.surcharge
    service_charge = values.service_charge
    line_total = values.line_total
    calculated_total = sum(item.line_total for item in items)
    if calculated_total != subtotal:
        raise ValueError(
            f"Total {total} does not match the sum of item prices {calculated_total}"
        )
    return values

# Get user-provided API key
api_key = st.text_input('Enter your OpenAI API key', type='password')

# Create OpenAI client with the user-provided API key
client = instructor.from_openai(
    client=OpenAI(api_key=api_key),
    mode=instructor.Mode.TOOLS,
)

def extract(url: str) -> Receipt:
    return client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4000,
        response_model=Receipt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": url, "detail": "high"},
                    },
                    {
                        "type": "text",
                        "text": "Analyze the image carefully. Return line items names, quantities, prices, and totals, and be careful for out-of-order items.",
                    },
                ],
            }
        ],
    )

# Streamlit code
st.title('Receipt Analyzer')

url = st.text_input('Enter the URL of the receipt image')

if url:
    try:
        receipt = extract(url)
        receipt_data = receipt.dict()
        st.json(receipt_data)
    except Exception as e:
        st.error(f'An error occurred: {e}')
