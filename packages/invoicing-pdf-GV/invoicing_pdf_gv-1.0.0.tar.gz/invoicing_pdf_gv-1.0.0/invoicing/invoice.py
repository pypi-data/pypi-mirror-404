import pandas as pd
import glob
from fpdf import FPDF, XPos, YPos
from pathlib import Path
import os


def generate(invoices_path, pdfs_path, image_path, product_id, product_name,
             amount_purchased, price_per_unit, total_price):
    """
    This function converts invoice Excel files into PDF invoices
    :param invoices_path:
    :param pdfs_path:
    :param image_path:
    :param product_id:
    :param product_name:
    :param amount_purchased:
    :param price_per_unit:
    :param total_price:
    :return:
    """
    filepaths = glob.glob(f"{invoices_path}/*.xlsx")

    for filepath in filepaths:

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        filename = Path(filepath).stem
        invoice_nr, date = filename.split("-")

        pdf.set_font(family="Times", size=16, style="B")
        pdf.cell(w=50, h=8, text=f"Invoice nr.{invoice_nr}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font(family="Times", size=16, style="B")
        pdf.cell(w=50, h=8, text=f"Date: {date}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        df = pd.read_excel(filepath, sheet_name="Sheet 1")

        # Add a header
        columns = df.columns
        columns = [item.replace("_", " ").title() for item in columns]
        pdf.set_font(family="Times", size=10, style="B")
        pdf.set_text_color(80, 80, 80)
        pdf.cell(w=30, h=8, text=columns[0], border=1)
        pdf.cell(w=70, h=8, text=columns[1], border=1)
        pdf.cell(w=30, h=8, text=columns[2], border=1)
        pdf.cell(w=30, h=8, text=columns[3], border=1)
        pdf.cell(w=30, h=8, text=columns[4], border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Add rows to the table
        for index, row in df.iterrows():
            pdf.set_font(family="Times", size=10)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(w=30, h=8, text=str(row[product_id]), border=1)
            pdf.cell(w=70, h=8, text=str(row[product_name]), border=1)
            pdf.cell(w=30, h=8, text=str(row[amount_purchased]), border=1)
            pdf.cell(w=30, h=8, text=str(row[price_per_unit]), border=1)
            pdf.cell(w=30, h=8, text=str(row[total_price]), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        total_sum = df["total_price"].sum()
        pdf.set_font(family="Times", size=10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(w=30, h=8, text="", border=1)
        pdf.cell(w=70, h=8, text="", border=1)
        pdf.cell(w=30, h=8, text="", border=1)
        pdf.cell(w=30, h=8, text="", border=1)
        pdf.cell(w=30, h=8, text=str(total_sum), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Add total sum sentence
        pdf.set_font(family="Times", size=10, style="B")
        pdf.cell(w=30, h=8, text=f"The total price is {total_sum}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Add company name and logo
        pdf.set_font(family="Times", size=14, style="B")
        pdf.cell(w=25, h=8, text=f"PythonHow")
        pdf.image(image_path, w=10)

        if not os.path.exists(pdfs_path):
            os.makedirs(pdfs_path)
        pdf.output(f"{pdfs_path}/{filename}.pdf")
